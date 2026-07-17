#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import {
  cpSync,
  existsSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DESTINATION_ROOT = path.join(REPO_ROOT, "skills", "mirrors-hyperframes");
const MARKETPLACE = path.join(REPO_ROOT, ".claude-plugin", "marketplace.json");
const SOURCE_URL = "https://github.com/heygen-com/hyperframes.git";
const PREFIX = "hyperframes-";
// Leave room for parser normalization differences between local and CI checkouts.
const MAX_DESCRIPTION_CHARS = 980;
const TEXT_FILE = /(?:^|\.)(?:md|mdx|txt|json|ya?ml|toml|sh|bash|zsh|fish|ps1|py|rb|php|go|rs|java|kt|swift|c|cc|cpp|h|hpp|css|scss|html|xml|svg|[cm]?js|[cm]?ts|jsx|tsx)$/i;

const sourceDirArg = process.argv.indexOf("--source-dir");
const checkOnly = process.argv.includes("--check");
let temporaryRoot = "";

function run(command, args, options = {}) {
  const output = execFileSync(command, args, {
    cwd: options.cwd ?? REPO_ROOT,
    encoding: "utf8",
    stdio: options.stdio ?? "pipe",
    env: options.env ?? process.env,
  });
  return typeof output === "string" ? output.trim() : "";
}

function resolveSourceRoot() {
  if (sourceDirArg !== -1) {
    const supplied = process.argv[sourceDirArg + 1];
    if (!supplied) throw new Error("--source-dir requires a path");
    return path.resolve(supplied);
  }
  if (process.env.HYPERFRAMES_SOURCE_DIR) return path.resolve(process.env.HYPERFRAMES_SOURCE_DIR);
  temporaryRoot = mkdtempSync(path.join(os.tmpdir(), "theangryskills-hyperframes-"));
  const checkout = path.join(temporaryRoot, "source");
  run("git", ["clone", "--depth", "1", SOURCE_URL, checkout], {
    stdio: "inherit",
    env: { ...process.env, GIT_LFS_SKIP_SMUDGE: "1" },
  });
  return checkout;
}

function publishedName(sourceName) {
  if (
    sourceName === "hyperframes" ||
    sourceName.startsWith("hyperframes-") ||
    sourceName.endsWith("-to-hyperframes")
  ) {
    return sourceName;
  }
  return `${PREFIX}${sourceName}`;
}

function skillNames(sourceSkills) {
  return readdirSync(sourceSkills, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .filter((name) => existsSync(path.join(sourceSkills, name, "SKILL.md")))
    .sort();
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
  let frontmatter = match[1]
    .replace(
      /^metadata:\s*\{\s*"tags":\s*"([^"]*)"\s*\}\s*$/m,
      `metadata:${newline}  tags: $1`,
    )
    .replace(
      /^metadata:\s*\r?\n\s*\{\s*\r?\n\s*"tags":\s*"([^"]*)",?\s*\r?\n\s*\}\s*$/m,
      `metadata:${newline}  tags: $1`,
    );
  return text.replace(match[1], frontmatter);
}

function rewriteText(text, ownerSourceName, relativePath, names) {
  let result = text;
  if (relativePath === "SKILL.md") {
    result = result.replace(
      /^(---\r?\n[\s\S]*?^name:\s*)([^\r\n]+)(\r?\n)/m,
      `$1${publishedName(ownerSourceName)}$3`,
    );
  }

  for (const sourceName of [...names].sort((a, b) => b.length - a.length || a.localeCompare(b))) {
    const escaped = sourceName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const published = publishedName(sourceName);
    result = result
      .replace(new RegExp(`((?:\\.\\./)+)${escaped}(?=/|\\b)`, "g"), `$1${published}`)
      .replace(new RegExp(`(skills/)${escaped}(?=/|\\b)`, "g"), `$1${published}`)
      .replace(
        new RegExp(`(join\\(HERE,\\s*["']\\.\\.["'],\\s*["']\\.\\.["'],\\s*["'])${escaped}(["'],)`, "g"),
        `$1${published}$2`,
      )
      .replace(new RegExp(`(?<![\\w-])\\$${escaped}(?![A-Za-z0-9-])`, "g"), `$${published}`);
  }
  return relativePath === "SKILL.md" ? normalizeMetadata(normalizeDescription(result)) : result;
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

function rewriteTree(root, sourceName, names) {
  for (const file of walkFiles(root)) {
    if (!TEXT_FILE.test(file)) continue;
    const original = readFileSync(file, "utf8");
    if (original.includes("\u0000")) continue;
    const rewritten = rewriteText(original, sourceName, path.relative(root, file), names);
    if (rewritten !== original) writeFileSync(file, rewritten);
  }
}

function mirrorNote(sourceName, destinationName, sourceCommit) {
  return `# heygen-com/hyperframes Skill Mirror\n\n` +
    `Mirrored skill: ${sourceName}\n` +
    `Published skill: ${destinationName}\n` +
    `Source: ${SOURCE_URL}\n` +
    `Source path: skills/${sourceName}\n` +
    `Branch: main\n` +
    `Commit: ${sourceCommit}\n\n` +
    `This skill is vendored from heygen-com/hyperframes. Naturally namespaced ` +
    `\`hyperframes*\` names are preserved; generic names receive a \`${PREFIX}\` prefix ` +
    `to avoid global skill-name collisions. Only frontmatter names and concrete references ` +
    `to renamed skill directories are adapted so sibling scripts and documentation remain ` +
    `resolvable after installation. Product and CLI commands, internal identifiers, scripts, ` +
    `tests, assets, and workflow behavior remain upstream material. Automatic source updates ` +
    `arrive through this mirror workflow. See \`LICENSE\` for the preserved ` +
    `Apache-2.0 terms.\n`;
}

function updateMarketplace(destinationNames) {
  const marketplace = JSON.parse(readFileSync(MARKETPLACE, "utf8"));
  const plugin = {
    name: "mirrors-hyperframes",
    skills: destinationNames.map((name) => `./skills/mirrors-hyperframes/${name}`),
  };
  const index = marketplace.plugins.findIndex((entry) => entry.name === plugin.name);
  if (index === -1) marketplace.plugins.push(plugin);
  else marketplace.plugins[index] = plugin;
  writeFileSync(MARKETPLACE, `${JSON.stringify(marketplace, null, 2)}\n`);
}

function validateMirror(sourceNames) {
  const expected = sourceNames.map(publishedName).sort();
  const actual = readdirSync(DESTINATION_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`mirror_directory_mismatch\nexpected=${expected.join(",")}\nactual=${actual.join(",")}`);
  }

  const failures = [];
  const genericNames = sourceNames.filter((name) => publishedName(name) !== name);
  const genericPattern = genericNames.map((name) => name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|");
  const unresolvedPath = new RegExp(`(?:(?:\\.\\./)+|skills/|\\$)(?:${genericPattern})(?:/|\\b)`);
  const unresolvedJoinPath = new RegExp(
    `join\\(HERE,\\s*["']\\.\\.["'],\\s*["']\\.\\.["'],\\s*["'](?:${genericPattern})["'],`,
  );
  for (const directory of actual) {
    const skillRoot = path.join(DESTINATION_ROOT, directory);
    const skillFile = path.join(skillRoot, "SKILL.md");
    const frontmatterName = readFileSync(skillFile, "utf8").match(/^name:\s*([^\r\n]+)/m)?.[1]?.trim();
    if (frontmatterName !== directory) failures.push(`${directory}: frontmatter=${frontmatterName ?? "missing"}`);
    if (!existsSync(path.join(skillRoot, "LICENSE"))) failures.push(`${directory}: missing LICENSE`);
    if (!existsSync(path.join(skillRoot, "MIRROR.md"))) failures.push(`${directory}: missing MIRROR.md`);

    for (const file of walkFiles(skillRoot)) {
      if (!TEXT_FILE.test(file) || file.endsWith("MIRROR.md")) continue;
      const text = readFileSync(file, "utf8");
      const relative = path.relative(REPO_ROOT, file);
      if (genericPattern && unresolvedPath.test(text)) failures.push(`${relative}: unresolved unprefixed sibling path`);
      if (genericPattern && unresolvedJoinPath.test(text)) {
        failures.push(`${relative}: unresolved unprefixed join(HERE) sibling path`);
      }
    }
  }

  const marketplace = JSON.parse(readFileSync(MARKETPLACE, "utf8"));
  const listed = marketplace.plugins
    .find((entry) => entry.name === "mirrors-hyperframes")?.skills
    ?.map((entry) => path.basename(entry))
    .sort() ?? [];
  if (JSON.stringify(listed) !== JSON.stringify(expected)) failures.push("marketplace skill list mismatch");
  if (failures.length) throw new Error(`hyperframes_mirror_validation_failed\n${failures.join("\n")}`);
}

function resolvesRelativeImport(file, specifier) {
  const base = path.resolve(path.dirname(file), specifier);
  return [
    base,
    `${base}.js`,
    `${base}.mjs`,
    `${base}.cjs`,
    path.join(base, "index.js"),
    path.join(base, "index.mjs"),
    path.join(base, "index.cjs"),
  ].some(existsSync);
}

function validateRuntimeFiles() {
  const failures = [];
  let syntaxChecks = 0;
  let relativeImports = 0;
  const pycache = mkdtempSync(path.join(os.tmpdir(), "theangryskills-pycache-"));
  try {
    for (const file of walkFiles(DESTINATION_ROOT)) {
      try {
        if (/\.(?:mjs|cjs|js)$/.test(file)) {
          run(process.execPath, ["--check", file]);
          syntaxChecks += 1;
          const text = readFileSync(file, "utf8");
          const importPattern = /(?:from\s+|import\s*\(|require\s*\()\s*["'](\.{1,2}\/[^"']+)["']/g;
          for (const match of text.matchAll(importPattern)) {
            relativeImports += 1;
            if (!resolvesRelativeImport(file, match[1])) {
              failures.push(`${path.relative(REPO_ROOT, file)}: unresolved import ${match[1]}`);
            }
          }
        } else if (/\.py$/.test(file)) {
          run("python3", ["-m", "py_compile", file], {
            env: { ...process.env, PYTHONPYCACHEPREFIX: pycache },
          });
          syntaxChecks += 1;
        } else if (/\.sh$/.test(file)) {
          run("bash", ["-n", file]);
          syntaxChecks += 1;
        }
      } catch (error) {
        failures.push(`${path.relative(REPO_ROOT, file)}: ${error.message.split("\n")[0]}`);
      }
    }
  } finally {
    rmSync(pycache, { recursive: true, force: true });
  }
  if (failures.length) throw new Error(`hyperframes_runtime_validation_failed\n${failures.join("\n")}`);
  console.log(`hyperframes_runtime_valid syntax=${syntaxChecks} relative_imports=${relativeImports}`);
}

const sourceRoot = checkOnly ? null : resolveSourceRoot();
try {
  if (!checkOnly) {
    const sourceSkills = path.join(sourceRoot, "skills");
    const names = skillNames(sourceSkills);
    const sourceCommit = run("git", ["rev-parse", "HEAD"], { cwd: sourceRoot });
    const license = readFileSync(path.join(sourceRoot, "LICENSE"), "utf8");
    rmSync(DESTINATION_ROOT, { recursive: true, force: true });

    for (const sourceName of names) {
      const destinationName = publishedName(sourceName);
      const destination = path.join(DESTINATION_ROOT, destinationName);
      cpSync(path.join(sourceSkills, sourceName), destination, {
        recursive: true,
        preserveTimestamps: false,
        verbatimSymlinks: true,
      });
      rewriteTree(destination, sourceName, names);
      writeFileSync(path.join(destination, "LICENSE"), license);
      writeFileSync(path.join(destination, "MIRROR.md"), mirrorNote(sourceName, destinationName, sourceCommit));
    }
    updateMarketplace(names.map(publishedName).sort());
    validateMirror(names);
    validateRuntimeFiles();
    console.log(`hyperframes_mirror_synced commit=${sourceCommit} skills=${names.length}`);
  } else {
    const names = readdirSync(DESTINATION_ROOT, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => readFileSync(path.join(DESTINATION_ROOT, entry.name, "MIRROR.md"), "utf8")
        .match(/^Mirrored skill:\s*(.+)$/m)?.[1])
      .filter(Boolean)
      .sort();
    validateMirror(names);
    validateRuntimeFiles();
    console.log(`hyperframes_mirror_valid skills=${names.length}`);
  }
} finally {
  if (temporaryRoot) rmSync(temporaryRoot, { recursive: true, force: true });
}
