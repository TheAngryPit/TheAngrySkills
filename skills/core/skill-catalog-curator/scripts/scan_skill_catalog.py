#!/usr/bin/env python3
"""Read-only audit for Codex skill catalogs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any


DEFAULT_ROOTS = [
    "~/.agents/skills",
    "~/.codex/skills",
    "~/TheAngrySkills/skills",
]

IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
IGNORED_FILES = {".DS_Store"}


def expand_root(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"').strip("'")
        data[key.strip()] = value
    return data


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def directory_hash(skill_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.name in IGNORED_FILES:
            continue
        rel = path.relative_to(skill_dir).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def read_skill_dir(item: Path, root: Path) -> dict[str, Any]:
    skill_md = item / "SKILL.md"
    text = read_text(skill_md)
    frontmatter = parse_frontmatter(text)
    openai_yaml = item / "agents" / "openai.yaml"
    return {
        "folder": item.name,
        "name": frontmatter.get("name", ""),
        "description": frontmatter.get("description", ""),
        "path": str(item),
        "root": str(root),
        "skill_md": str(skill_md),
        "has_openai_yaml": openai_yaml.exists(),
        "openai_yaml": str(openai_yaml),
        "openai_yaml_text": read_text(openai_yaml) if openai_yaml.exists() else "",
        "body": text,
        "hash": directory_hash(item),
    }


def discover(root: Path) -> list[dict[str, Any]]:
    if not root.exists() or not root.is_dir():
        return []
    if (root / "SKILL.md").exists():
        return [read_skill_dir(root, root.parent)]
    skills: list[dict[str, Any]] = []
    for item in sorted(root.iterdir(), key=lambda p: p.name):
        if not item.is_dir():
            continue
        skill_md = item / "SKILL.md"
        if not skill_md.exists():
            continue
        skills.append(read_skill_dir(item, root))
    return skills


def issue(severity: str, code: str, message: str, paths: list[str]) -> dict[str, Any]:
    return {"severity": severity, "code": code, "message": message, "paths": paths}


def analyze(skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    by_name: dict[str, list[dict[str, Any]]] = {}
    by_folder: dict[str, list[dict[str, Any]]] = {}

    for skill in skills:
        name = skill["name"]
        folder = skill["folder"]
        if name:
            by_name.setdefault(name, []).append(skill)
        by_folder.setdefault(folder, []).append(skill)

        if not name:
            issues.append(issue("error", "missing_name", f"{folder} has no frontmatter name", [skill["skill_md"]]))
        elif name != folder:
            issues.append(
                issue(
                    "error",
                    "name_folder_mismatch",
                    f"{folder} frontmatter name is {name}",
                    [skill["skill_md"]],
                )
            )

        description = skill["description"].strip()
        if len(description) < 80:
            issues.append(
                issue("warning", "short_description", f"{folder} frontmatter description is short", [skill["skill_md"]])
            )
        if re.search(r"\[TODO:|## \[TODO|Complete and informative explanation", skill["body"]):
            issues.append(issue("error", "template_residue", f"{folder} still has template/TODO residue", [skill["skill_md"]]))

        if not skill["has_openai_yaml"]:
            issues.append(issue("warning", "missing_openai_yaml", f"{folder} has no agents/openai.yaml", [skill["path"]]))
        else:
            yaml_text = skill["openai_yaml_text"]
            if f"${folder}" not in yaml_text:
                issues.append(
                    issue(
                        "warning",
                        "default_prompt_missing_skill_name",
                        f"{folder} agents/openai.yaml does not mention ${folder}",
                        [skill["openai_yaml"]],
                    )
                )
            match = re.search(r"short_description:\s*[\"'](.+?)[\"']", yaml_text)
            if match:
                short = match.group(1)
                if not 25 <= len(short) <= 64:
                    issues.append(
                        issue(
                            "warning",
                            "ui_short_description_length",
                            f"{folder} UI short_description length is {len(short)}",
                            [skill["openai_yaml"]],
                        )
                    )

    for name, entries in sorted(by_name.items()):
        if len(entries) > 1:
            paths = [entry["path"] for entry in entries]
            severities = "info" if len({entry["hash"] for entry in entries}) == 1 else "error"
            code = "duplicate_name_same_content" if severities == "info" else "duplicate_name_drift"
            issues.append(issue(severities, code, f"frontmatter name {name} appears in {len(entries)} roots", paths))

    for folder, entries in sorted(by_folder.items()):
        if len(entries) > 1:
            paths = [entry["path"] for entry in entries]
            hashes = {entry["hash"] for entry in entries}
            if len(hashes) == 1:
                issues.append(issue("info", "duplicate_folder_same_content", f"{folder} appears in {len(entries)} roots with same content", paths))
            else:
                issues.append(issue("error", "duplicate_folder_drift", f"{folder} appears in {len(entries)} roots with different content", paths))

    order = {"error": 0, "warning": 1, "info": 2}
    return sorted(issues, key=lambda item: (order[item["severity"]], item["code"], item["message"]))


def render_text(roots: list[Path], skills: list[dict[str, Any]], issues: list[dict[str, Any]]) -> str:
    counts = {severity: 0 for severity in ("error", "warning", "info")}
    for item in issues:
        counts[item["severity"]] += 1

    lines = [
        "Scope:",
        *[f"- {root}" for root in roots],
        "",
        f"Skills scanned: {len(skills)}",
        f"Issues: errors={counts['error']} warnings={counts['warning']} info={counts['info']}",
        "",
        "Findings:",
    ]
    if not issues:
        lines.append("- none")
    for item in issues:
        lines.append(f"- [{item['severity']}] {item['code']}: {item['message']}")
        for path in item["paths"]:
            lines.append(f"  path: {path}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only audit for Codex skill catalogs.")
    parser.add_argument("--root", action="append", help="Skill root to scan. May be provided multiple times.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    roots = [expand_root(root) for root in (args.root or DEFAULT_ROOTS)]
    existing_roots = [root for root in roots if root.exists() and root.is_dir()]
    skills = [skill for root in existing_roots for skill in discover(root)]
    issues = analyze(skills)

    payload = {
        "roots": [str(root) for root in existing_roots],
        "skills_scanned": len(skills),
        "issues": issues,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(existing_roots, skills, issues))
    return 1 if any(item["severity"] == "error" for item in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
