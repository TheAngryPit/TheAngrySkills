#!/usr/bin/env python3
"""Deterministic, offline security admission scans for skill directories."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


TEXT_SUFFIXES = {
    ".bash",
    ".css",
    ".dockerfile",
    ".env",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

ACTIVE_FILE_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pyproject.toml",
    "requirements.txt",
    "uv.lock",
}

BLOCKING_VERDICTS = {"blocked_malicious", "blocked_unscannable", "quarantine"}

VERDICT_RANK = {
    "safe_docs_only": 0,
    "safe_to_install": 1,
    "needs_human_review": 2,
    "needs_llm_review": 3,
    "quarantine": 4,
    "blocked_unscannable": 5,
    "blocked_malicious": 6,
}

SECRET_VALUE_RE = re.compile(
    r"(?i)(sk-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{12,}|"
    r"(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\"\s]{8,})"
)
HOME_PATH_RE = re.compile(r"/Users/[^/\s`]+|~")


@dataclass
class SecurityFinding:
    severity: str
    rule_id: str
    path: str
    line: int | None
    summary: str
    sample: str | None = None


@dataclass
class ScannedFile:
    path: str
    bytes: int
    executable: bool
    symlink: bool


@dataclass
class Rule:
    rule_id: str
    severity: str
    pattern: re.Pattern[str]
    summary: str


@dataclass
class FileFingerprint:
    path: str
    bytes: int
    executable: bool
    symlink: bool
    active_surface: bool
    digest: str | None
    target: str | None = None


RULES = [
    Rule(
        "remote-download-exec",
        "critical",
        re.compile(r"\b(curl|wget)\b[^\n|;]*(https?://|www\.)[^\n|;]*\|\s*(sh|bash|zsh|python3?|node|ruby|perl)\b", re.I),
        "Remote download piped into an interpreter.",
    ),
    Rule(
        "inline-shell-exec",
        "critical",
        re.compile(r"\b(bash|zsh|sh)\s+-c\s+['\"]", re.I),
        "Inline shell execution present.",
    ),
    Rule(
        "inline-runtime-exec",
        "critical",
        re.compile(r"\b(python3?|node|ruby|perl)\s+(-c|-e)\s+['\"]", re.I),
        "Inline runtime execution present.",
    ),
    Rule(
        "encoded-payload-exec",
        "critical",
        re.compile(r"\b(base64|openssl)\b[^\n|;]*(--decode|-d|enc)[^\n|;]*\|\s*(sh|bash|zsh|python3?|node)\b", re.I),
        "Encoded payload decoded into execution.",
    ),
    Rule(
        "credential-path-read",
        "critical",
        re.compile(
            r"\b(cat|grep|rg|awk|sed|cp|scp|rsync|open|read|less|tail|head)\b[^\n]*(\.env|\.ssh/|id_rsa|id_ed25519|"
            r"auth\.json|keychain|login\.keychain|\.codex/(config|auth|tokens)|browser profile|cookies\.sqlite)",
            re.I,
        ),
        "Command appears to read or copy credential-bearing paths.",
    ),
    Rule(
        "persistence-mutation",
        "critical",
        re.compile(r"\b(launchctl|crontab|osascript)\b|(?:^|[\s'\"/])LaunchAgents(?:[\s'\"/]|$)|Login Items|(?<![A-Za-z0-9_])\.(zshrc|bashrc|profile)\b", re.I),
        "Persistence or shell-startup mutation surface present.",
    ),
    Rule(
        "privilege-escalation",
        "critical",
        re.compile(r"\bsudo\b|\bchmod\s+[+]s\b|\bchown\s+root\b|Accessibility permission|TCC", re.I),
        "Privilege escalation or sensitive permission surface present.",
    ),
    Rule(
        "network-exfiltration",
        "critical",
        re.compile(r"\b(curl|wget|nc|netcat|scp|rsync)\b[^\n]*(--data|-d\s+|--upload-file|-F\s+|>\s*/dev/tcp|webhook|pastebin|discordapp)", re.I),
        "Possible network exfiltration command present.",
    ),
    Rule(
        "policy-bypass-instruction",
        "critical",
        re.compile(r"(ignore|disregard|override)[^\n]{0,80}(system|developer|operator|security|sandbox|approval|policy|instructions)", re.I),
        "Instruction attempts to bypass higher-priority policy.",
    ),
    Rule(
        "concealment-instruction",
        "critical",
        re.compile(r"(do not tell|hide this|conceal|silently|without informing)[^\n]{0,80}(operator|user|reviewer|approval)", re.I),
        "Instruction appears to conceal behavior from the operator.",
    ),
    Rule(
        "global-package-install",
        "warning",
        re.compile(r"\b(npm|pnpm|yarn|pip3?|uv|brew)\b[^\n]*(install|add)[^\n]*(-g|--global|/usr/local|/opt/homebrew)", re.I),
        "Global or host-level package install instruction present.",
    ),
    Rule(
        "mcp-plugin-hook-install",
        "warning",
        re.compile(r"(mcpServers|MCP server|plugin install|request_plugin_install|codex_hooks|hooks/|\.codex/config\.toml)", re.I),
        "MCP, plugin, hook, or Codex config mutation surface present.",
    ),
    Rule(
        "broad-filesystem-scan",
        "warning",
        re.compile(r"\b(find|rg|grep)\b[^\n]*(/Users|~|\$HOME|/private|/var|/etc)\b", re.I),
        "Broad filesystem scan instruction present.",
    ),
]


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    if path.name in ACTIVE_FILE_NAMES:
        return True
    return False


def rel_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def sanitize_sample(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = SECRET_VALUE_RE.sub("[REDACTED_SECRET]", cleaned)
    cleaned = HOME_PATH_RE.sub("[HOME]", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    if len(cleaned) > 180:
        cleaned = f"{cleaned[:177]}..."
    return cleaned


def find_skill_name(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return skill_dir.name
    for line in skill_md.read_text(encoding="utf-8", errors="replace").splitlines()[:20]:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return skill_dir.name


def iter_files(skill_dir: Path) -> Iterable[Path]:
    for root, dirnames, filenames in os.walk(skill_dir, followlinks=False):
        dirnames.sort()
        for filename in sorted(filenames):
            yield Path(root) / filename


def add_finding(findings: list[SecurityFinding], severity: str, rule_id: str, path: str, line: int | None, summary: str, sample: str | None = None) -> None:
    findings.append(SecurityFinding(severity, rule_id, path, line, summary, sanitize_sample(sample) if sample else None))


def scan_file_content(skill_dir: Path, path: Path, findings: list[SecurityFinding]) -> None:
    if not is_text_file(path):
        return
    rel = rel_path(skill_dir, path)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        add_finding(findings, "critical", "file-unreadable", rel, None, f"Could not read file: {exc}")
        return

    for line_number, line in enumerate(text.splitlines(), start=1):
        if should_skip_code_literal_line(path, line):
            continue
        for rule in RULES:
            if rule.pattern.search(line):
                add_finding(findings, rule.severity, rule.rule_id, rel, line_number, rule.summary, line)


def should_skip_code_literal_line(path: Path, line: str) -> bool:
    if path.suffix.lower() not in {".py", ".js", ".mjs", ".ts", ".tsx", ".jsx"}:
        return False
    stripped = line.strip()
    if "re.compile(" in stripped:
        return True
    if stripped.startswith(("r\"", "r'", "\"", "'")):
        return True
    return False


def has_active_surface(skill_dir: Path, path: Path, executable: bool) -> bool:
    try:
        parts = path.relative_to(skill_dir).parts
    except ValueError:
        return True

    if executable:
        return True
    if parts and parts[0] == "scripts":
        return True
    if path.name in {"AGENTS.md", "CLAUDE.md", "GEMINI.md"} and path.name != "SKILL.md":
        return True
    if path.name in {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
        return True
    if path.name in {"package.json", "pyproject.toml", "requirements.txt", "uv.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}:
        return True
    if ".github" in parts and "workflows" in parts:
        return True
    return False


def classify_active_surface(skill_dir: Path, path: Path, executable: bool, findings: list[SecurityFinding]) -> None:
    rel = rel_path(skill_dir, path)
    parts = path.relative_to(skill_dir).parts

    if executable:
        add_finding(findings, "warning", "executable-file", rel, None, "Executable file present; review before global admission.")

    if parts and parts[0] == "scripts":
        add_finding(findings, "warning", "bundled-script-review", rel, None, "Bundled script present; review required before global admission.")

    if path.name in {"AGENTS.md", "CLAUDE.md", "GEMINI.md"} and path.name != "SKILL.md":
        add_finding(findings, "warning", "nested-active-instructions", rel, None, "Nested agent instruction file present.")

    if path.name in {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
        add_finding(findings, "warning", "container-execution-surface", rel, None, "Container execution surface present.")

    if path.name in {"package.json", "pyproject.toml", "requirements.txt", "uv.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}:
        add_finding(findings, "warning", "dependency-manifest-surface", rel, None, "Dependency or package manager surface present.")

    if ".github" in parts and "workflows" in parts:
        add_finding(findings, "warning", "github-actions-surface", rel, None, "GitHub Actions workflow surface present.")


def scan_symlink(skill_dir: Path, path: Path, findings: list[SecurityFinding]) -> bool:
    rel = rel_path(skill_dir, path)
    try:
        resolved = path.resolve(strict=False)
        root = skill_dir.resolve(strict=True)
    except OSError as exc:
        add_finding(findings, "critical", "symlink-unscannable", rel, None, f"Could not resolve symlink: {exc}")
        return False
    if not str(resolved).startswith(f"{root}{os.sep}") and resolved != root:
        add_finding(findings, "critical", "symlink-path-escape", rel, None, "Symlink points outside the skill directory.")
        return False
    add_finding(findings, "warning", "symlink-present", rel, None, "Symlink present; verify target before admission.")
    return True


def determine_verdict(findings: list[SecurityFinding], scanned_files: list[ScannedFile]) -> tuple[str, str]:
    critical_rules = {finding.rule_id for finding in findings if finding.severity == "critical"}
    warning_count = sum(1 for finding in findings if finding.severity == "warning")

    if critical_rules & {"file-unreadable", "symlink-unscannable", "symlink-path-escape"}:
        return "blocked_unscannable", "do_not_install_review_unscannable_surface"

    malicious_rules = {
        "remote-download-exec",
        "inline-shell-exec",
        "inline-runtime-exec",
        "encoded-payload-exec",
        "credential-path-read",
        "network-exfiltration",
        "policy-bypass-instruction",
        "concealment-instruction",
    }
    if critical_rules & malicious_rules:
        return "blocked_malicious", "block_and_preserve_evidence"

    if critical_rules:
        return "quarantine", "quarantine_or_human_review_required"

    if warning_count:
        return "needs_human_review", "review_active_surfaces_before_install"

    non_metadata_files = [
        item
        for item in scanned_files
        if item.path not in {"SKILL.md", "agents/openai.yaml"} and not item.path.startswith("references/")
    ]
    if not non_metadata_files:
        return "safe_docs_only", "may_install_after_quality_gate_if_source_is_expected"

    return "safe_to_install", "may_install_after_quality_gate_if_source_is_expected"


def scan_skill(skill_path: Path) -> dict:
    skill_dir = skill_path.expanduser().resolve()
    findings: list[SecurityFinding] = []
    scanned_files: list[ScannedFile] = []

    if not skill_dir.exists():
        add_finding(findings, "critical", "skill-path-missing", str(skill_path), None, "Skill path does not exist.")
        return build_report(skill_path, skill_path.name, scanned_files, findings)
    if not skill_dir.is_dir():
        add_finding(findings, "critical", "skill-path-not-directory", str(skill_path), None, "Skill path is not a directory.")
        return build_report(skill_dir, skill_dir.name, scanned_files, findings)
    if not (skill_dir / "SKILL.md").exists():
        add_finding(findings, "critical", "missing-skill-md", ".", None, "SKILL.md is missing.")

    for path in iter_files(skill_dir):
        rel = rel_path(skill_dir, path)
        try:
            file_stat = path.lstat()
        except OSError as exc:
            add_finding(findings, "critical", "file-unreadable", rel, None, f"Could not stat file: {exc}")
            continue

        is_symlink = path.is_symlink()
        is_executable = bool(file_stat.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        scanned_files.append(ScannedFile(rel, file_stat.st_size, is_executable, is_symlink))

        if is_symlink:
            if not scan_symlink(skill_dir, path, findings):
                continue

        classify_active_surface(skill_dir, path, is_executable, findings)
        if not is_symlink:
            scan_file_content(skill_dir, path, findings)

    return build_report(skill_dir, find_skill_name(skill_dir), scanned_files, findings)


def find_skill_dirs(root_path: Path) -> list[Path]:
    root = root_path.expanduser().resolve()
    if (root / "SKILL.md").exists():
        return [root]
    if not root.exists() or not root.is_dir():
        return []

    ignored_dirs = {".git", "node_modules", "__pycache__", ".pytest_cache"}
    skill_dirs: list[Path] = []

    def walk(directory: Path) -> None:
        for path in sorted(directory.iterdir()):
            if not path.is_dir() or path.name in ignored_dirs:
                continue
            if (path / "SKILL.md").exists():
                skill_dirs.append(path)
                continue
            walk(path)

    walk(root)
    return skill_dirs


def strongest_verdict(verdicts: Iterable[str]) -> str:
    verdict_list = list(verdicts)
    if not verdict_list:
        return "blocked_unscannable"
    return max(verdict_list, key=lambda verdict: VERDICT_RANK.get(verdict, 99))


def next_action_for_verdict(verdict: str) -> str:
    if verdict == "blocked_malicious":
        return "block_and_preserve_evidence"
    if verdict == "blocked_unscannable":
        return "do_not_install_review_unscannable_surface"
    if verdict == "quarantine":
        return "quarantine_or_human_review_required"
    if verdict in {"needs_human_review", "needs_llm_review"}:
        return "review_active_surfaces_before_install"
    return "may_install_after_quality_gate_if_source_is_expected"


def scan_root(root_path: Path) -> dict:
    root = root_path.expanduser().resolve()
    skill_dirs = find_skill_dirs(root)
    reports = [scan_skill(path) for path in skill_dirs]
    verdict_counts = Counter(report["verdict"] for report in reports)
    finding_counts = Counter(
        finding["rule_id"]
        for report in reports
        for finding in report["security_findings"]
    )
    verdict = strongest_verdict(report["verdict"] for report in reports)
    if not reports:
        verdict = "blocked_unscannable"

    return {
        "schema_version": 1,
        "tool": "theangry-skills-security",
        "report_type": "skill_root_scan",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": {
            "path": str(root),
            "skill_count": len(reports),
        },
        "verdict": verdict,
        "next_action": next_action_for_verdict(verdict),
        "summary": {
            "verdict_counts": dict(sorted(verdict_counts.items())),
            "finding_counts": dict(sorted(finding_counts.items())),
            "blocking_skill_count": sum(1 for report in reports if report["verdict"] in BLOCKING_VERDICTS),
            "review_skill_count": sum(1 for report in reports if report["verdict"] in {"needs_human_review", "needs_llm_review"}),
        },
        "skills": [
            {
                "name": report["skill"]["name"],
                "path": report["skill"]["path"],
                "verdict": report["verdict"],
                "next_action": report["next_action"],
                "finding_count": len(report["security_findings"]),
            }
            for report in reports
        ],
    }


def file_digest(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def fingerprint_files(skill_path: Path) -> dict[str, FileFingerprint]:
    skill_dir = skill_path.expanduser().resolve()
    fingerprints: dict[str, FileFingerprint] = {}
    if not skill_dir.exists() or not skill_dir.is_dir():
        return fingerprints

    for path in iter_files(skill_dir):
        rel = rel_path(skill_dir, path)
        try:
            file_stat = path.lstat()
        except OSError:
            fingerprints[rel] = FileFingerprint(rel, 0, False, False, True, None)
            continue
        is_symlink = path.is_symlink()
        is_executable = bool(file_stat.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        target = None
        digest = None
        if is_symlink:
            try:
                target = os.readlink(path)
            except OSError:
                target = None
        else:
            digest = file_digest(path)
        fingerprints[rel] = FileFingerprint(
            path=rel,
            bytes=file_stat.st_size,
            executable=is_executable,
            symlink=is_symlink,
            active_surface=has_active_surface(skill_dir, path, is_executable),
            digest=digest,
            target=target,
        )
    return fingerprints


def changed_file_entries(old_index: dict[str, FileFingerprint], new_index: dict[str, FileFingerprint]) -> tuple[list[str], list[str], list[str]]:
    old_paths = set(old_index)
    new_paths = set(new_index)
    added = sorted(new_paths - old_paths)
    removed = sorted(old_paths - new_paths)
    modified = sorted(
        path
        for path in old_paths & new_paths
        if asdict(old_index[path]) != asdict(new_index[path])
    )
    return added, removed, modified


def security_diff(old_skill_path: Path, new_skill_path: Path) -> dict:
    old_skill = old_skill_path.expanduser().resolve()
    new_skill = new_skill_path.expanduser().resolve()
    old_report = scan_skill(old_skill)
    new_report = scan_skill(new_skill)
    old_index = fingerprint_files(old_skill)
    new_index = fingerprint_files(new_skill)
    added, removed, modified = changed_file_entries(old_index, new_index)

    def is_active(path: str) -> bool:
        return old_index.get(path, new_index.get(path)).active_surface

    active_surface_changes = [
        {"path": path, "change": "added"}
        for path in added
        if is_active(path)
    ] + [
        {"path": path, "change": "removed"}
        for path in removed
        if is_active(path)
    ] + [
        {"path": path, "change": "modified"}
        for path in modified
        if is_active(path)
    ]

    old_rule_ids = Counter(finding["rule_id"] for finding in old_report["security_findings"])
    new_rule_ids = Counter(finding["rule_id"] for finding in new_report["security_findings"])
    introduced_rule_ids = sorted(
        rule_id
        for rule_id, count in new_rule_ids.items()
        if count > old_rule_ids.get(rule_id, 0)
    )
    resolved_rule_ids = sorted(
        rule_id
        for rule_id, count in old_rule_ids.items()
        if count > new_rule_ids.get(rule_id, 0)
    )

    verdict = new_report["verdict"]
    return {
        "schema_version": 1,
        "tool": "theangry-skills-security",
        "report_type": "skill_diff",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "old_skill": {
            "path": str(old_skill),
            "name": old_report["skill"]["name"],
            "verdict": old_report["verdict"],
        },
        "new_skill": {
            "path": str(new_skill),
            "name": new_report["skill"]["name"],
            "verdict": new_report["verdict"],
        },
        "verdict": verdict,
        "next_action": next_action_for_verdict(verdict),
        "summary": {
            "added_files": len(added),
            "removed_files": len(removed),
            "modified_files": len(modified),
            "active_surface_change_count": len(active_surface_changes),
            "introduced_rule_ids": introduced_rule_ids,
            "resolved_rule_ids": resolved_rule_ids,
        },
        "changed_files": {
            "added": added,
            "removed": removed,
            "modified": modified,
        },
        "active_surface_changes": active_surface_changes,
        "new_security_findings": new_report["security_findings"],
    }


def build_report(skill_path: Path, skill_name: str, scanned_files: list[ScannedFile], findings: list[SecurityFinding]) -> dict:
    verdict, next_action = determine_verdict(findings, scanned_files)
    return {
        "schema_version": 1,
        "tool": "theangry-skills-security",
        "report_type": "skill_scan",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill": {
            "name": skill_name,
            "path": str(skill_path),
            "file_count": len(scanned_files),
            "byte_count": sum(item.bytes for item in scanned_files),
        },
        "verdict": verdict,
        "next_action": next_action,
        "security_findings": [asdict(finding) for finding in findings],
        "scanned_files": [asdict(item) for item in scanned_files],
        "quality": {
            "status": "not_run",
            "note": "Run theangry-skills audit/score separately; quality is not security admission.",
        },
        "skillspector": {
            "available": False,
            "used": False,
            "note": "Run the security_admission_pipeline.py skillspector command for optional external evidence; it is not required for deterministic scan.",
        },
    }


def render_human(report: dict) -> str:
    if report.get("report_type") == "skill_root_scan":
        return render_root_human(report)
    if report.get("report_type") == "skill_diff":
        return render_diff_human(report)

    lines = [
        "# Skill security admission scan",
        "",
        f"Skill: {report['skill']['name']}",
        f"Path: {report['skill']['path']}",
        f"Verdict: {report['verdict']}",
        f"Next action: {report['next_action']}",
        f"Files scanned: {report['skill']['file_count']}",
        "",
    ]
    findings = report["security_findings"]
    if findings:
        lines.append("## Findings")
        lines.append("")
        for finding in findings:
            location = finding["path"]
            if finding["line"] is not None:
                location = f"{location}:{finding['line']}"
            lines.append(f"- {finding['severity']} / {finding['rule_id']} / {location}: {finding['summary']}")
            if finding.get("sample"):
                lines.append(f"  sample: `{finding['sample']}`")
    else:
        lines.append("No security findings.")
    return "\n".join(lines)


def render_root_human(report: dict) -> str:
    lines = [
        "# Skill root security admission scan",
        "",
        f"Root: {report['root']['path']}",
        f"Verdict: {report['verdict']}",
        f"Next action: {report['next_action']}",
        f"Skills scanned: {report['root']['skill_count']}",
        f"Blocking skills: {report['summary']['blocking_skill_count']}",
        f"Review skills: {report['summary']['review_skill_count']}",
        "",
        "## Skills",
        "",
    ]
    if not report["skills"]:
        lines.append("No skill directories found.")
    for item in report["skills"]:
        lines.append(f"- {item['name']}: {item['verdict']} ({item['finding_count']} findings)")
    return "\n".join(lines)


def render_diff_human(report: dict) -> str:
    lines = [
        "# Skill security admission diff",
        "",
        f"Old: {report['old_skill']['name']} - {report['old_skill']['verdict']} - {report['old_skill']['path']}",
        f"New: {report['new_skill']['name']} - {report['new_skill']['verdict']} - {report['new_skill']['path']}",
        f"Verdict: {report['verdict']}",
        f"Next action: {report['next_action']}",
        "",
        "## File changes",
        "",
        f"- Added: {report['summary']['added_files']}",
        f"- Removed: {report['summary']['removed_files']}",
        f"- Modified: {report['summary']['modified_files']}",
        f"- Active surface changes: {report['summary']['active_surface_change_count']}",
    ]
    if report["summary"]["introduced_rule_ids"]:
        lines.append(f"- Introduced rules: {', '.join(report['summary']['introduced_rule_ids'])}")
    if report["summary"]["resolved_rule_ids"]:
        lines.append(f"- Resolved rules: {', '.join(report['summary']['resolved_rule_ids'])}")

    if report["active_surface_changes"]:
        lines.extend(["", "## Active surface changes", ""])
        for item in report["active_surface_changes"]:
            lines.append(f"- {item['change']}: {item['path']}")
    return "\n".join(lines)


def exit_status_for_report(report: dict) -> int:
    return 1 if report["verdict"] in BLOCKING_VERDICTS else 0


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] not in {"scan", "scan-root", "diff", "-h", "--help"}:
        argv = ["scan", *argv]

    parser = argparse.ArgumentParser(description="Offline security admission scans for skill directories.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan one skill directory.")
    scan_parser.add_argument("skill_path", help="Path to a skill directory containing SKILL.md.")
    scan_parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable markdown.")

    root_parser = subparsers.add_parser("scan-root", help="Scan skill directories under a root recursively.")
    root_parser.add_argument("root_path", help="Path to a directory containing skill directories.")
    root_parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable markdown.")

    diff_parser = subparsers.add_parser("diff", help="Compare old and new skill directories.")
    diff_parser.add_argument("old_skill_path", help="Path to the old skill directory.")
    diff_parser.add_argument("new_skill_path", help="Path to the new skill directory.")
    diff_parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable markdown.")

    args = parser.parse_args(argv)

    if args.command == "scan":
        report = scan_skill(Path(args.skill_path))
    elif args.command == "scan-root":
        report = scan_root(Path(args.root_path))
    elif args.command == "diff":
        report = security_diff(Path(args.old_skill_path), Path(args.new_skill_path))
    else:
        parser.error("unknown command")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_human(report))

    return exit_status_for_report(report)


if __name__ == "__main__":
    sys.exit(main())
