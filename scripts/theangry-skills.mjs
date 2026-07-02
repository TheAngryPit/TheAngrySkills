#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const REPO_ROOT = path.resolve(path.dirname(SCRIPT_PATH), "..");
const INVOCATION_CWD = process.cwd();
const CURATOR_ROOT = path.join(REPO_ROOT, "skills", "core", "skill-catalog-curator");
const AUDITOR = path.join(CURATOR_ROOT, "scripts", "audit_skill_frontmatter.py");
const EXTERNAL_AUDITORS = path.join(CURATOR_ROOT, "scripts", "check_external_auditors.py");
const TRIGGER_TESTS = path.join(CURATOR_ROOT, "scripts", "generate_trigger_tests.py");
const SECURITY_SCANNER = path.join(CURATOR_ROOT, "scripts", "security_scan_skill.py");
const SECURITY_PIPELINE = path.join(CURATOR_ROOT, "scripts", "security_admission_pipeline.py");

const args = process.argv.slice(2);

function usage(exitCode = 2) {
  const text = `Usage:
  theangry-skills score <skill-path> [--profile shared|codex|agentskills] [--json]
  theangry-skills audit <skill-path> [--profile shared|codex|agentskills] [--json]
  theangry-skills check --root <skills-root> [--profile shared|codex|agentskills] [--strict] [--emit-proof [path]] [--json]
  theangry-skills trigger-tests <skill-path> [--write [tests-dir]]
  theangry-skills security scan <skill-path> [--json]
  theangry-skills security scan-root <skills-root> [--json]
  theangry-skills security diff <old-skill-path> <new-skill-path> [--json]
  theangry-skills security skillspector <skill-path> --report-dir <dir> [--command <cmd>] [--json]
  theangry-skills update-plan --candidate-root <skills-root> --installed-root <skills-root> [--skill <name>] [--write <path>] [--json]
  theangry-skills update-apply --plan <plan.json> --only-safe --confirm [--json]
  theangry-skills quarantine <skill-path-or-name> --root <skills-root> --quarantine-root <dir> --reason <reason> --confirm [--json]
  theangry-skills check-external-auditors [--json]
  theangry-skills sensei-version [--json]

Examples:
  scripts/theangry-skills.mjs score skills/core/ask-theangrypit
  scripts/theangry-skills.mjs audit skills/core/ask-theangrypit
  scripts/theangry-skills.mjs check --root skills --profile shared --strict
  scripts/theangry-skills.mjs check --root skills --emit-proof reports/skill-audit.md

The score/audit/check commands include frontmatter, routing, local metadata leak,
and possible no-op instruction checks.
The security commands are deterministic, offline, and separate from quality scoring.
`;
  process.stderr.write(text);
  process.exit(exitCode);
}

function takeFlag(argv, flag) {
  const index = argv.indexOf(flag);
  if (index === -1) return null;
  const value = argv[index + 1] ?? null;
  argv.splice(index, value && !value.startsWith("--") ? 2 : 1);
  return value && !value.startsWith("--") ? value : true;
}

function hasFlag(argv, flag) {
  const index = argv.indexOf(flag);
  if (index === -1) return false;
  argv.splice(index, 1);
  return true;
}

function run(command, commandArgs, options = {}) {
  const result = spawnSync(command, commandArgs, {
    cwd: options.cwd ?? REPO_ROOT,
    encoding: "utf8",
    stdio: options.inherit ? "inherit" : "pipe",
  });
  if (result.error) throw result.error;
  return result;
}

function printResult(result) {
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
}

function resolveInputPath(item) {
  if (item === "~") return os.homedir();
  if (item.startsWith("~/")) return path.join(os.homedir(), item.slice(2));
  return path.isAbsolute(item) ? item : path.resolve(INVOCATION_CWD, item);
}

function pythonArgs(paths, profile, json = false) {
  const resolvedPaths = paths.map((item) => resolveInputPath(item));
  const out = [AUDITOR, ...resolvedPaths, "--profile", profile];
  if (json) out.push("--json");
  return out;
}

function parseAuditJson(paths, profile) {
  const result = run("python3", pythonArgs(paths, profile, true));
  if (result.status !== 0) printResult(result);
  if (result.status !== 0) process.exit(result.status ?? 1);
  return JSON.parse(result.stdout);
}

function hasWarningsOrErrors(payload) {
  return payload.results.some((result) => result.counts.error > 0 || result.counts.warning > 0);
}

function writeProof(paths, profile, proofPath) {
  const result = run("python3", pythonArgs(paths, profile, false));
  if (result.status !== 0 && !result.stdout) printResult(result);
  fs.mkdirSync(path.dirname(proofPath), { recursive: true });
  fs.writeFileSync(proofPath, result.stdout);
  return result;
}

function commandScore(argv) {
  const profile = takeFlag(argv, "--profile") || "shared";
  const json = hasFlag(argv, "--json");
  if (argv.length !== 1) usage();
  const result = run("python3", pythonArgs([argv[0]], profile, json));
  printResult(result);
  process.exit(result.status ?? 1);
}

function commandCheck(argv) {
  const profile = takeFlag(argv, "--profile") || "shared";
  const root = takeFlag(argv, "--root") || argv[0];
  const json = hasFlag(argv, "--json");
  const strict = hasFlag(argv, "--strict");
  const emitProof = takeFlag(argv, "--emit-proof");
  if (!root) usage();

  const proofPath =
    emitProof === true
      ? path.join(REPO_ROOT, "reports", `skill-audit-${profile}.md`)
      : emitProof || null;

  if (proofPath) {
    const proof = writeProof([root], profile, path.resolve(REPO_ROOT, proofPath));
    if (!json) process.stdout.write(`wrote_proof: ${path.resolve(REPO_ROOT, proofPath)}\n`);
    if (proof.status !== 0 && !strict) process.exit(proof.status ?? 1);
  }

  if (strict) {
    const payload = parseAuditJson([root], profile);
    if (json) process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
    else if (!proofPath) {
      const result = run("python3", pythonArgs([root], profile, false));
      printResult(result);
    }
    process.exit(hasWarningsOrErrors(payload) ? 1 : 0);
  }

  if (!proofPath || json) {
    const result = run("python3", pythonArgs([root], profile, json));
    printResult(result);
    process.exit(result.status ?? 1);
  }
}

function commandExternal(argv) {
  const json = hasFlag(argv, "--json");
  const result = run("python3", [EXTERNAL_AUDITORS]);
  if (json) {
    printResult(result);
  } else if (result.status === 0) {
    const payload = JSON.parse(result.stdout);
    for (const check of payload.checks) {
      process.stdout.write(`${check.package}: ${check.version ?? "unknown"}${check.modified ? ` modified ${check.modified}` : ""}\n`);
    }
  } else {
    printResult(result);
  }
  process.exit(result.status ?? 1);
}

function commandTriggerTests(argv) {
  const write = takeFlag(argv, "--write");
  if (argv.length !== 1) usage();
  const skillPath = resolveInputPath(argv[0]);
  const commandArgs = [TRIGGER_TESTS, skillPath];
  if (write) {
    commandArgs.push("--write");
    if (write !== true) commandArgs.push(resolveInputPath(write));
  }
  const result = run("python3", commandArgs);
  printResult(result);
  process.exit(result.status ?? 1);
}

function commandSecurity(argv) {
  const subcommand = argv.shift();
  switch (subcommand) {
    case "scan": {
      const json = hasFlag(argv, "--json");
      if (argv.length !== 1) usage();
      const skillPath = resolveInputPath(argv[0]);
      const commandArgs = [SECURITY_SCANNER, "scan", skillPath];
      if (json) commandArgs.push("--json");
      const result = run("python3", commandArgs);
      printResult(result);
      process.exit(result.status ?? 1);
      break;
    }
    case "scan-root": {
      const json = hasFlag(argv, "--json");
      if (argv.length !== 1) usage();
      const rootPath = resolveInputPath(argv[0]);
      const commandArgs = [SECURITY_SCANNER, "scan-root", rootPath];
      if (json) commandArgs.push("--json");
      const result = run("python3", commandArgs);
      printResult(result);
      process.exit(result.status ?? 1);
      break;
    }
    case "diff": {
      const json = hasFlag(argv, "--json");
      if (argv.length !== 2) usage();
      const oldSkillPath = resolveInputPath(argv[0]);
      const newSkillPath = resolveInputPath(argv[1]);
      const commandArgs = [SECURITY_SCANNER, "diff", oldSkillPath, newSkillPath];
      if (json) commandArgs.push("--json");
      const result = run("python3", commandArgs);
      printResult(result);
      process.exit(result.status ?? 1);
      break;
    }
    case "skillspector": {
      if (argv.length < 1) usage();
      const skillPathRaw = argv.shift();
      const skillPath = resolveInputPath(skillPathRaw);
      const commandArgs = [SECURITY_PIPELINE, "skillspector", skillPath];
      while (argv.length) {
        const item = argv.shift();
        if (item === "--report-dir" || item === "--command" || item === "--timeout") {
          const value = argv.shift();
          if (!value) usage();
          commandArgs.push(item, item === "--report-dir" ? resolveInputPath(value) : value);
        } else if (item === "--json") {
          commandArgs.push(item);
        } else {
          usage();
        }
      }
      const result = run("python3", commandArgs);
      printResult(result);
      process.exit(result.status ?? 1);
      break;
    }
    default:
      usage();
  }
}

function commandUpdatePlan(argv) {
  const commandArgs = [SECURITY_PIPELINE, "update-plan"];
  while (argv.length) {
    const item = argv.shift();
    if (item === "--candidate-root" || item === "--installed-root" || item === "--write") {
      const value = argv.shift();
      if (!value) usage();
      commandArgs.push(item, resolveInputPath(value));
    } else if (item === "--skill") {
      const value = argv.shift();
      if (!value) usage();
      commandArgs.push(item, value);
    } else if (item === "--json") {
      commandArgs.push(item);
    } else {
      usage();
    }
  }
  const result = run("python3", commandArgs);
  printResult(result);
  process.exit(result.status ?? 1);
}

function commandUpdateApply(argv) {
  const commandArgs = [SECURITY_PIPELINE, "update-apply"];
  while (argv.length) {
    const item = argv.shift();
    if (item === "--plan") {
      const value = argv.shift();
      if (!value) usage();
      commandArgs.push(item, resolveInputPath(value));
    } else if (item === "--only-safe" || item === "--confirm" || item === "--json") {
      commandArgs.push(item);
    } else {
      usage();
    }
  }
  const result = run("python3", commandArgs);
  printResult(result);
  process.exit(result.status ?? 1);
}

function commandQuarantine(argv) {
  if (argv.length < 1) usage();
  const target = argv.shift();
  const commandArgs = [SECURITY_PIPELINE, "quarantine", target];
  while (argv.length) {
    const item = argv.shift();
    if (item === "--root" || item === "--quarantine-root") {
      const value = argv.shift();
      if (!value) usage();
      commandArgs.push(item, resolveInputPath(value));
    } else if (item === "--reason") {
      const value = argv.shift();
      if (!value) usage();
      commandArgs.push(item, value);
    } else if (item === "--confirm" || item === "--json") {
      commandArgs.push(item);
    } else {
      usage();
    }
  }
  const result = run("python3", commandArgs);
  printResult(result);
  process.exit(result.status ?? 1);
}

const command = args.shift();
switch (command) {
  case "score":
  case "audit":
    commandScore(args);
    break;
  case "check":
    commandCheck(args);
    break;
  case "trigger-tests":
  case "triggers":
    commandTriggerTests(args);
    break;
  case "security":
    commandSecurity(args);
    break;
  case "update-plan":
    commandUpdatePlan(args);
    break;
  case "update-apply":
    commandUpdateApply(args);
    break;
  case "quarantine":
    commandQuarantine(args);
    break;
  case "check-external-auditors":
  case "sensei-version":
    commandExternal(args);
    break;
  case "help":
  case "--help":
  case "-h":
    usage(0);
    break;
  default:
    usage();
}
