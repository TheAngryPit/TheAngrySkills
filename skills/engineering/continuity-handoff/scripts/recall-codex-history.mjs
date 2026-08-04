#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import readline from "node:readline";
import { backup, DatabaseSync } from "node:sqlite";
import { fileURLToPath, pathToFileURL } from "node:url";

function fail(message) {
  throw new Error(message);
}

function parseArgs(argv) {
  const allowed = new Set([
    "codexHome", "threadId", "query", "date", "matchRole", "before", "after",
    "maxMatches", "maxMessageChars", "maxOutputChars",
  ]);
  const args = {
    codexHome: process.env.CODEX_HOME || path.join(os.homedir(), ".codex"),
    before: 1,
    after: 5,
    maxMatches: 3,
    maxMessageChars: 2400,
    maxOutputChars: 16000,
    matchRole: "any",
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith("--")) fail(`Unexpected argument: ${arg}`);
    const key = arg.slice(2).replace(/-([a-z])/g, (_, char) => char.toUpperCase());
    if (!allowed.has(key)) fail(`Unknown option: ${arg}`);
    args[key] = argv[++index];
  }
  for (const key of ["threadId", "query"]) {
    if (!args[key]) fail(`--${key.replace(/[A-Z]/g, (char) => `-${char.toLowerCase()}`)} is required`);
  }
  for (const key of ["before", "after", "maxMatches", "maxMessageChars", "maxOutputChars"]) {
    args[key] = Number(args[key]);
    if (!Number.isInteger(args[key]) || args[key] < 0) fail(`--${key} must be a non-negative integer`);
  }
  if (args.maxMatches < 1 || args.maxMatches > 10) fail("--max-matches must be between 1 and 10");
  if (args.before > 10 || args.after > 20) fail("Context window is too broad");
  if (args.maxOutputChars < 1000 || args.maxOutputChars > 50000) fail("--max-output-chars must be between 1000 and 50000");
  if (args.date && !/^\d{4}-\d{2}-\d{2}$/.test(args.date)) fail("--date must use YYYY-MM-DD");
  if (!["any", "user", "assistant"].includes(args.matchRole)) fail("--match-role must be any, user, or assistant");
  const sensitive = /(password|credential|secret|auth\.json|cookie|api[- ]?key|access[- ]?token|refresh[- ]?token)/i;
  if (sensitive.test(args.query)) fail("Sensitive-history queries are not allowed");
  return args;
}

function tableExists(db, name) {
  return Boolean(db.prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?").get(name));
}

const SENSITIVE_KEY = String.raw`(?:password|passwd|secret|api[-_ ]?key|access[-_ ]?token|refresh[-_ ]?token|auth(?:orization)?|cookie|set-cookie)`;

function redactSecretsFromOutput(value) {
  return String(value)
    .replace(/-----BEGIN ([A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?)-----[\s\S]*?-----END \1-----/gi, "[REDACTED_PRIVATE_KEY]")
    .replace(/^(\s*(?:Cookie|Set-Cookie)\s*:\s*).*$/gim, "$1[REDACTED]")
    .replace(/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [REDACTED]")
    .replace(/\bBasic\s+[A-Za-z0-9+/=]+/gi, "Basic [REDACTED]")
    .replace(/\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|npm_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})\b/g, "[REDACTED_TOKEN]")
    .replace(/\b(https?:\/\/[^\s:/@]+:)[^\s/@]+@/gi, "$1[REDACTED]@")
    .replace(new RegExp(`(["']?${SENSITIVE_KEY}["']?\\s*[:=]\\s*["'])([^"'\\r\\n]+)(["'])`, "gi"), "$1[REDACTED]$3")
    .replace(new RegExp(`(${SENSITIVE_KEY}\\s*[:=]\\s*)([^\\s,;]+)`, "gi"), "$1[REDACTED]");
}

function redactOptionalOutput(value) {
  return typeof value === "string" ? redactSecretsFromOutput(value) : null;
}

function boundedMessageText(text, maxChars, matchIndex = null) {
  if (text.length <= maxChars) return text;
  if (matchIndex === null) return `${text.slice(0, maxChars)}\n[TRUNCATED]`;
  const start = Math.max(0, Math.min(matchIndex - Math.floor(maxChars / 2), text.length - maxChars));
  const end = Math.min(text.length, start + maxChars);
  return `${start > 0 ? "[TRUNCATED PREFIX]\n" : ""}${text.slice(start, end)}${end < text.length ? "\n[TRUNCATED SUFFIX]" : ""}`;
}

function immutableDatabaseLocation(dbPath) {
  const location = pathToFileURL(dbPath);
  location.searchParams.set("mode", "ro");
  location.searchParams.set("immutable", "1");
  return location;
}

function removeSnapshot(snapshotPath, snapshotDirectory) {
  if (fs.existsSync(snapshotPath)) fs.unlinkSync(snapshotPath);
  fs.rmdirSync(snapshotDirectory);
}

async function resolveThread(codexHome, threadId) {
  const dbPath = path.join(codexHome, "state_5.sqlite");
  if (!fs.existsSync(dbPath)) fail(`Missing state database: ${dbPath}`);
  const snapshotDirectory = fs.mkdtempSync(path.join(os.tmpdir(), "continuity-recall-"));
  const snapshotPath = path.join(snapshotDirectory, "state.sqlite");
  try {
    const source = new DatabaseSync(dbPath, { readOnly: true });
    try {
      await backup(source, snapshotPath);
    } finally {
      source.close();
    }

    const snapshot = new DatabaseSync(immutableDatabaseLocation(snapshotPath), { readOnly: true });
    try {
      if (!tableExists(snapshot, "threads")) fail("State database has no threads table");
      const row = snapshot.prepare("SELECT * FROM threads WHERE id=?").get(threadId);
      if (!row) fail(`No thread row for ${threadId}`);
      if (!row.rollout_path) fail("Thread row has no rollout_path");
      return { dbPath, row };
    } finally {
      snapshot.close();
    }
  } finally {
    removeSnapshot(snapshotPath, snapshotDirectory);
  }
}

function sessionTitle(codexHome, threadId, fallback) {
  const indexPath = path.join(codexHome, "session_index.jsonl");
  if (!fs.existsSync(indexPath)) return fallback;
  let title = fallback;
  for (const line of fs.readFileSync(indexPath, "utf8").split(/\r?\n/)) {
    if (!line) continue;
    try {
      const row = JSON.parse(line);
      const id = row.id || row.session_id || row.thread_id;
      if (id === threadId && typeof row.thread_name === "string") title = row.thread_name;
    } catch {}
  }
  return title;
}

function messageFromRow(row, lineNumber, maxChars) {
  if (row.type !== "response_item" || row.payload?.type !== "message") return null;
  if (!["user", "assistant"].includes(row.payload.role)) return null;
  const fullText = redactSecretsFromOutput((row.payload.content || [])
    .filter((item) => item?.type === "input_text" || item?.type === "output_text")
    .map((item) => item.text || "")
    .join("\n"));
  if (!fullText) return null;
  return {
    fullText,
    evidence: {
      line: lineNumber,
      timestamp: row.timestamp || null,
      role: row.payload.role || "unknown",
      text: boundedMessageText(fullText, maxChars),
    },
  };
}

async function scanRollout({ rolloutPath, threadId, query, date, before, after, maxMatches, maxMessageChars, matchRole }) {
  if (!fs.existsSync(rolloutPath)) fail(`Missing rollout: ${rolloutPath}`);
  const stream = fs.createReadStream(rolloutPath, { encoding: "utf8" });
  const lines = readline.createInterface({ input: stream, crlfDelay: Infinity });
  const needle = query.toLocaleLowerCase();
  const previous = [];
  const captures = [];
  let embeddedId = null;
  let lineNumber = 0;
  let messageCount = 0;

  for await (const line of lines) {
    lineNumber += 1;
    if (!line) continue;
    let row;
    try {
      row = JSON.parse(line);
    } catch {
      continue;
    }
    if (row.type === "session_meta" && !embeddedId) embeddedId = row.payload?.id || null;
    const record = messageFromRow(row, lineNumber, maxMessageChars);
    if (!record) continue;
    const message = record.evidence;
    messageCount += 1;

    for (const capture of captures) {
      if (capture.remaining > 0 && message.line > capture.matchLine) {
        capture.messages.push(message);
        capture.remaining -= 1;
      }
    }

    const dateMatches = !date || String(message.timestamp || "").startsWith(date);
    const matchIndex = record.fullText.toLocaleLowerCase().indexOf(needle);
    const queryMatches = matchIndex !== -1;
    const roleMatches = matchRole === "any" || message.role === matchRole;
    if (captures.length < maxMatches && dateMatches && queryMatches && roleMatches) {
      captures.push({
        matchLine: message.line,
        remaining: after,
        messages: [
          ...previous,
          { ...message, text: boundedMessageText(record.fullText, maxMessageChars, matchIndex) },
        ],
      });
    }

    previous.push(message);
    if (previous.length > before) previous.shift();
  }

  if (embeddedId !== threadId) fail(`Rollout identity mismatch: expected ${threadId}, found ${embeddedId || "none"}`);
  return {
    embedded_thread_id: embeddedId,
    lines_scanned: lineNumber,
    messages_scanned: messageCount,
    match_count: captures.length,
    captures: captures.map(({ matchLine, messages }) => ({ match_line: matchLine, messages })),
  };
}

function boundedJson(value, maxChars) {
  const rendered = `${JSON.stringify(value, null, 2)}\n`;
  if (rendered.length > maxChars) fail(`Bounded output exceeded ${maxChars} characters; narrow the query or context window`);
  return rendered;
}

export async function run(argv) {
  const args = parseArgs(argv);
  const resolved = await resolveThread(path.resolve(args.codexHome), args.threadId);
  const rolloutPath = path.isAbsolute(resolved.row.rollout_path)
    ? resolved.row.rollout_path
    : path.resolve(args.codexHome, resolved.row.rollout_path);
  const scan = await scanRollout({ ...args, rolloutPath });
  const result = {
    mode: "bounded_read_only_recall",
    identity: {
      title: redactOptionalOutput(sessionTitle(args.codexHome, args.threadId, resolved.row.title || null)),
      thread_id: args.threadId,
      cwd: redactOptionalOutput(resolved.row.cwd),
      rollout_path: redactSecretsFromOutput(rolloutPath),
      archived: Boolean(resolved.row.archived),
    },
    query: { literal: redactSecretsFromOutput(args.query), date: args.date || null, match_role: args.matchRole },
    scope: {
      before_messages: args.before,
      after_messages: args.after,
      max_matches: args.maxMatches,
      lines_scanned: scan.lines_scanned,
      messages_scanned: scan.messages_scanned,
      matched_windows: scan.match_count,
    },
    evidence: scan.captures,
    mutation_performed: false,
  };
  process.stdout.write(boundedJson(result, args.maxOutputChars));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  run(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
