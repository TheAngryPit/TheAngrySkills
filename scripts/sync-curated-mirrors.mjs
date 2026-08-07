#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import {
  cpSync,
  existsSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  renameSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST_PATH = path.join(REPO_ROOT, "config", "mirror-sources.json");
const MARKETPLACE_PATH = path.join(REPO_ROOT, ".claude-plugin", "marketplace.json");
const TEXT_FILE = /(?:^|\.)(?:md|mdx|txt|json|ya?ml|toml|sh|bash|zsh|fish|ps1|py|rb|php|go|rs|java|kt|swift|c|cc|cpp|h|hpp|css|scss|html|xml|svg|[cm]?js|[cm]?ts|jsx|tsx|csv)$/i;
const MAX_DESCRIPTION_CHARS = 980;
const checkOnly = process.argv.includes("--check");
const familyArg = process.argv.indexOf("--family");
const requestedFamily = familyArg === -1 ? null : process.argv[familyArg + 1];

function run(command, args, options = {}) {
  const output = execFileSync(command, args, {
    cwd: options.cwd ?? REPO_ROOT,
    encoding: "utf8",
    stdio: options.stdio ?? "pipe",
  });
  return typeof output === "string" ? output.trim() : "";
}

function loadManifest() {
  const manifest = JSON.parse(readFileSync(MANIFEST_PATH, "utf8"));
  if (manifest.schema_version !== 1 || !Array.isArray(manifest.sources)) {
    throw new Error("invalid_mirror_manifest");
  }
  const ids = manifest.sources.map((source) => source.id);
  if (new Set(ids).size !== ids.length) throw new Error("duplicate_mirror_source_id");
  for (const source of manifest.sources) {
    if (!/^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\.git$/.test(source.repository)) {
      throw new Error(`${source.id}: repository must be an explicit GitHub HTTPS URL`);
    }
    if (!source.branch || !source.prefix || !source.source_root || !source.destination_root) {
      throw new Error(`${source.id}: incomplete mirror source`);
    }
    const destination = path.resolve(REPO_ROOT, source.destination_root);
    const mirrorRoot = `${path.join(REPO_ROOT, "skills", "mirrors-")}`;
    if (!destination.startsWith(mirrorRoot) || path.relative(REPO_ROOT, destination).includes("..")) {
      throw new Error(`${source.id}: destination outside skills/mirrors-*`);
    }
    if (path.isAbsolute(source.source_root) || source.source_root.split(/[\\/]/).includes("..")) {
      throw new Error(`${source.id}: unsafe source root`);
    }
  }
  return manifest.sources;
}

function selectSources(sources) {
  if (!requestedFamily) return sources;
  const selected = sources.filter((source) => source.id === requestedFamily);
  if (!selected.length) throw new Error(`unknown_mirror_family=${requestedFamily}`);
  return selected;
}

function frontmatter(text) {
  return text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/)?.[1] ?? "";
}

function frontmatterName(skillFile) {
  return frontmatter(readFileSync(skillFile, "utf8")).match(/^name:\s*([^\r\n]+)/m)?.[1]?.trim();
}

function normalizeDescription(text) {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (!match) return text;
  const newline = text.startsWith("---\r\n") ? "\r\n" : "\n";
  const lines = match[1].split(/\r?\n/);
  const index = lines.findIndex((line) => /^description:\s*/.test(line));
  if (index === -1) return text;

  let end = index + 1;
  while (end < lines.length && (lines[end].trim() === "" || /^\s+/.test(lines[end]))) end += 1;
  const raw = lines[index].replace(/^description:\s*/, "");
  const scalar = raw.trim();
  const continuation = lines.slice(index + 1, end).map((line) => line.trim()).filter(Boolean);
  let first = scalar;
  if ((first.startsWith('"') && first.endsWith('"')) || (first.startsWith("'") && first.endsWith("'"))) {
    first = first.slice(1, -1).replace(/''/g, "'");
  }
  let description = /^[>|][-+]?$/.test(scalar)
    ? continuation.join(scalar.startsWith(">") ? " " : "\n")
    : [first, ...continuation].filter(Boolean).join(" ");
  if (description.length > MAX_DESCRIPTION_CHARS) {
    description = `${description.slice(0, MAX_DESCRIPTION_CHARS - 3).trimEnd()}...`;
  }
  lines.splice(index, end - index, `description: ${JSON.stringify(description)}`);
  return text.replace(match[1], lines.join(newline));
}

function normalizeMetadata(text) {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (!match) return text;
  const newline = text.startsWith("---\r\n") ? "\r\n" : "\n";
  const normalized = match[1]
    .replace(/^metadata:\s*\{\s*"tags":\s*"([^"]*)"\s*\}\s*$/m, `metadata:${newline}  tags: $1`)
    .replace(/^metadata:\s*\r?\n\s*\{\s*\r?\n\s*"tags":\s*"([^"]*)",?\s*\r?\n\s*\}\s*$/m, `metadata:${newline}  tags: $1`);
  return text.replace(match[1], normalized);
}

function publishedName(source, upstreamName) {
  return upstreamName.startsWith(source.prefix) ? upstreamName : `${source.prefix}${upstreamName}`;
}

function inventory(sourceSkills, source) {
  const entries = readdirSync(sourceSkills, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => ({ directory: entry.name, root: path.join(sourceSkills, entry.name) }))
    .filter((entry) => existsSync(path.join(entry.root, "SKILL.md")))
    .map((entry) => {
      const upstreamName = frontmatterName(path.join(entry.root, "SKILL.md"));
      if (!upstreamName) throw new Error(`${source.id}/${entry.directory}: missing frontmatter name`);
      return { ...entry, upstreamName, destinationName: publishedName(source, upstreamName) };
    })
    .sort((a, b) => a.destinationName.localeCompare(b.destinationName));
  const names = entries.map((entry) => entry.destinationName);
  if (!entries.length) throw new Error(`${source.id}: upstream skill inventory is empty`);
  if (new Set(names).size !== names.length) throw new Error(`${source.id}: published name collision`);
  return entries;
}

function walkFiles(root) {
  const files = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const absolute = path.join(root, entry.name);
    if (entry.isDirectory()) files.push(...walkFiles(absolute));
    else if (entry.isFile()) files.push(absolute);
  }
  return files;
}

function escapePattern(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function rewriteReferences(text, mappings) {
  let result = text;
  const ordered = [...mappings].sort((a, b) => b.sourceName.length - a.sourceName.length);
  for (const { sourceName, destinationName } of ordered) {
    const escaped = escapePattern(sourceName);
    result = result
      .replace(new RegExp(`((?:\\.agents|\\.codex)/skills/)${escaped}(?=/|\\b)`, "g"), `$1${destinationName}`)
      .replace(new RegExp(`(skills/)${escaped}(?=/|\\b)`, "g"), `$1${destinationName}`)
      .replace(new RegExp(`(\\.\\./)${escaped}(?=/|\\b)`, "g"), `$1${destinationName}`)
      .replace(new RegExp(`(\\*/)${escaped}(?=/|\\b)`, "g"), `$1${destinationName}`);
  }
  return result;
}

function rewriteTree(root, owner, mappings) {
  for (const file of walkFiles(root)) {
    if (!TEXT_FILE.test(file)) continue;
    const original = readFileSync(file, "utf8");
    if (original.includes("\u0000")) continue;
    let rewritten = rewriteReferences(original, mappings);
    if (path.relative(root, file) === "SKILL.md") {
      rewritten = rewritten.replace(
        /^(---\r?\n[\s\S]*?^name:\s*)([^\r\n]+)(\r?\n)/m,
        `$1${owner.destinationName}$3`,
      );
      rewritten = normalizeMetadata(normalizeDescription(rewritten));
    }
    if (rewritten !== original) writeFileSync(file, rewritten);
  }
}

function mirrorNote(source, item, sourceCommit) {
  return `# ${source.repository.replace(/^https:\/\/github\.com\//, "").replace(/\.git$/, "")} Skill Mirror\n\n` +
    `Mirrored skill: ${item.upstreamName}\n` +
    `Published skill: ${item.destinationName}\n` +
    `Source: ${source.repository}\n` +
    `Source path: ${source.source_root}/${item.directory}\n` +
    `Branch: ${source.branch}\n` +
    `Commit: ${sourceCommit}\n\n` +
    `This skill is vendored from upstream with a \`${source.prefix}\` prefix to avoid ` +
    `global skill-name collisions. The mirrored frontmatter name and references to ` +
    `sibling skill paths are adapted to the published names; upstream scripts, assets, ` +
    `instructions, licensing, and workflow logic otherwise remain upstream material.\n`;
}

function rootLicense(checkout) {
  return ["LICENSE", "LICENSE.md", "LICENSE.txt"]
    .map((name) => path.join(checkout, name))
    .find(existsSync);
}

function materialize(source, checkout, sourceCommit) {
  const sourceSkills = path.join(checkout, source.source_root);
  if (!existsSync(sourceSkills)) throw new Error(`${source.id}: missing source root ${source.source_root}`);
  const entries = inventory(sourceSkills, source);
  const mappings = entries.flatMap((item) => [
    { sourceName: item.directory, destinationName: item.destinationName },
    { sourceName: item.upstreamName, destinationName: item.destinationName },
  ]);
  const destinationRoot = path.join(REPO_ROOT, source.destination_root);
  const stagingRoot = mkdtempSync(path.join(path.dirname(destinationRoot), `.${source.id}-`));
  const license = rootLicense(checkout);

  try {
    for (const item of entries) {
      const destination = path.join(stagingRoot, item.destinationName);
      cpSync(item.root, destination, { recursive: true, dereference: false });
      rewriteTree(destination, item, mappings);
      if (license && !rootLicense(destination)) cpSync(license, path.join(destination, path.basename(license)));
      writeFileSync(path.join(destination, "MIRROR.md"), mirrorNote(source, item, sourceCommit));
    }
    rmSync(destinationRoot, { recursive: true, force: true });
    renameSync(stagingRoot, destinationRoot);
  } catch (error) {
    rmSync(stagingRoot, { recursive: true, force: true });
    throw error;
  }
  return entries;
}

function updateMarketplace(source, entries) {
  const marketplace = JSON.parse(readFileSync(MARKETPLACE_PATH, "utf8"));
  const plugin = {
    name: `mirrors-${source.id}`,
    skills: entries.map((entry) => `./${source.destination_root}/${entry.destinationName}`),
  };
  const index = marketplace.plugins.findIndex((entry) => entry.name === plugin.name);
  if (index === -1) marketplace.plugins.push(plugin);
  else marketplace.plugins[index] = plugin;
  writeFileSync(MARKETPLACE_PATH, `${JSON.stringify(marketplace, null, 2)}\n`);
}

function validateFamily(source) {
  const destinationRoot = path.join(REPO_ROOT, source.destination_root);
  if (!existsSync(destinationRoot)) throw new Error(`${source.id}: missing destination root`);
  const directories = readdirSync(destinationRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
  if (!directories.length) throw new Error(`${source.id}: empty mirror`);

  const failures = [];
  for (const directory of directories) {
    const root = path.join(destinationRoot, directory);
    const skillFile = path.join(root, "SKILL.md");
    const mirrorFile = path.join(root, "MIRROR.md");
    if (!existsSync(skillFile)) failures.push(`${source.id}/${directory}: missing SKILL.md`);
    else if (frontmatterName(skillFile) !== directory) {
      failures.push(`${source.id}/${directory}: frontmatter=${frontmatterName(skillFile) ?? "missing"}`);
    }
    if (!existsSync(mirrorFile)) failures.push(`${source.id}/${directory}: missing MIRROR.md`);
    else {
      const note = readFileSync(mirrorFile, "utf8");
      if (!note.includes(`Published skill: ${directory}`)) failures.push(`${source.id}/${directory}: bad provenance`);
      if (!note.match(/^Commit: [0-9a-f]{40}$/m)) failures.push(`${source.id}/${directory}: invalid commit pin`);
    }
  }

  const marketplace = JSON.parse(readFileSync(MARKETPLACE_PATH, "utf8"));
  const listed = marketplace.plugins
    .find((entry) => entry.name === `mirrors-${source.id}`)?.skills
    ?.map((entry) => path.basename(entry))
    .sort() ?? [];
  if (JSON.stringify(listed) !== JSON.stringify(directories)) failures.push(`${source.id}: marketplace mismatch`);
  if (failures.length) throw new Error(`mirror_validation_failed\n${failures.join("\n")}`);
  console.log(`mirror_valid family=${source.id} skills=${directories.length}`);
}

function checkoutSource(source, temporaryRoot) {
  const checkout = path.join(temporaryRoot, source.id);
  run("git", ["clone", "--depth", "1", "--branch", source.branch, source.repository, checkout], { stdio: "inherit" });
  return checkout;
}

function main() {
  const sources = selectSources(loadManifest());
  if (checkOnly) {
    for (const source of sources) validateFamily(source);
    return;
  }

  const temporaryRoot = mkdtempSync(path.join(os.tmpdir(), "theangryskills-mirrors-"));
  try {
    for (const source of sources) {
      const checkout = checkoutSource(source, temporaryRoot);
      const sourceCommit = run("git", ["rev-parse", "HEAD"], { cwd: checkout });
      const entries = materialize(source, checkout, sourceCommit);
      updateMarketplace(source, entries);
      validateFamily(source);
      console.log(`mirror_synced family=${source.id} commit=${sourceCommit} skills=${entries.length}`);
    }
  } finally {
    rmSync(temporaryRoot, { recursive: true, force: true });
  }
}

main();
