#!/usr/bin/env python3
"""Operational security admission helpers for skill updates.

This script is intentionally local-first and conservative:
- plan commands are read-only
- apply/quarantine commands require explicit confirmation
- external scanner evidence cannot override local hard-deny verdicts
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import security_scan_skill as scanner


SAFE_VERDICTS = {"safe_to_install", "safe_docs_only"}
REVIEW_VERDICTS = {"needs_human_review", "needs_llm_review"}
BLOCKING_VERDICTS = {"blocked_malicious", "blocked_unscannable", "quarantine"}


@dataclass
class PlanEntry:
    skill: str
    candidate_path: str
    installed_path: str | None
    candidate_verdict: str
    action: str
    safe_to_apply: bool
    reason: str
    finding_count: int
    diff_summary: dict | None = None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def render_json_or_human(payload: dict, as_json: bool) -> str:
    if as_json:
        return json.dumps(payload, indent=2)

    report_type = payload.get("report_type")
    if report_type == "update_plan":
        lines = [
            "# Skill update security plan",
            "",
            f"Candidate root: {payload['candidate_root']}",
            f"Installed root: {payload['installed_root']}",
            f"Verdict: {payload['verdict']}",
            f"Entries: {payload['summary']['entry_count']}",
            f"Safe to apply: {payload['summary']['safe_to_apply_count']}",
            f"Needs review: {payload['summary']['review_count']}",
            f"Blocked: {payload['summary']['blocked_count']}",
            "",
            "## Entries",
            "",
        ]
        for entry in payload["entries"]:
            lines.append(f"- {entry['skill']}: {entry['action']} / {entry['candidate_verdict']} / safe={entry['safe_to_apply']}")
        return "\n".join(lines)

    if report_type == "update_apply":
        lines = [
            "# Skill update apply report",
            "",
            f"Plan: {payload['plan_path']}",
            f"Applied: {payload['summary']['applied_count']}",
            f"Skipped: {payload['summary']['skipped_count']}",
            "",
        ]
        for item in payload["results"]:
            lines.append(f"- {item['skill']}: {item['status']} {item.get('destination', '')}".rstrip())
        return "\n".join(lines)

    if report_type == "quarantine":
        return "\n".join([
            "# Skill quarantine report",
            "",
            f"Skill: {payload['skill']}",
            f"Status: {payload['status']}",
            f"Source: {payload['source_path']}",
            f"Destination: {payload.get('quarantine_path') or 'not moved'}",
            f"Reason: {payload['reason']}",
        ])

    if report_type == "skillspector_evidence":
        external = payload["skillspector"]
        return "\n".join([
            "# SkillSpector evidence report",
            "",
            f"Skill: {payload['skill']['name']}",
            f"Deterministic verdict: {payload['deterministic_verdict']}",
            f"Final verdict: {payload['verdict']}",
            f"SkillSpector available: {external['available']}",
            f"SkillSpector used: {external['used']}",
            f"SkillSpector status: {external['status']}",
        ])

    return json.dumps(payload, indent=2)


def skill_dirs_by_name(root: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for skill_dir in scanner.find_skill_dirs(root):
        out[scanner.find_skill_name(skill_dir)] = skill_dir
    return out


def plan_action(candidate_report: dict, installed_path: Path | None, diff_report: dict | None) -> tuple[str, bool, str]:
    verdict = candidate_report["verdict"]
    if verdict in BLOCKING_VERDICTS:
        return "block", False, "candidate security verdict blocks admission"
    if verdict in REVIEW_VERDICTS:
        return "review", False, "candidate requires human review before admission"
    if installed_path is None:
        return "install", verdict in SAFE_VERDICTS, "new candidate with safe security verdict"
    if diff_report and diff_report["summary"]["added_files"] == 0 and diff_report["summary"]["removed_files"] == 0 and diff_report["summary"]["modified_files"] == 0:
        return "keep", False, "installed skill already matches candidate"
    return "update", verdict in SAFE_VERDICTS, "candidate update has safe security verdict"


def build_update_plan(candidate_root: Path, installed_root: Path, skill_names: list[str] | None = None) -> dict:
    candidate_root = candidate_root.expanduser().resolve()
    installed_root = installed_root.expanduser().resolve()
    candidates = skill_dirs_by_name(candidate_root)
    installed = skill_dirs_by_name(installed_root)
    selected = sorted(skill_names or candidates.keys())
    entries: list[PlanEntry] = []

    for skill_name in selected:
        candidate_path = candidates.get(skill_name)
        if candidate_path is None:
            entries.append(PlanEntry(
                skill=skill_name,
                candidate_path="",
                installed_path=str(installed[skill_name]) if skill_name in installed else None,
                candidate_verdict="blocked_unscannable",
                action="block",
                safe_to_apply=False,
                reason="candidate skill not found under candidate root",
                finding_count=0,
            ))
            continue

        candidate_report = scanner.scan_skill(candidate_path)
        installed_path = installed.get(skill_name)
        diff_report = scanner.security_diff(installed_path, candidate_path) if installed_path else None
        action, safe_to_apply, reason = plan_action(candidate_report, installed_path, diff_report)
        entries.append(PlanEntry(
            skill=skill_name,
            candidate_path=str(candidate_path),
            installed_path=str(installed_path) if installed_path else None,
            candidate_verdict=candidate_report["verdict"],
            action=action,
            safe_to_apply=safe_to_apply,
            reason=reason,
            finding_count=len(candidate_report["security_findings"]),
            diff_summary=diff_report["summary"] if diff_report else None,
        ))

    verdict = "safe_to_apply"
    if any(entry.action == "block" for entry in entries):
        verdict = "blocked"
    elif any(entry.action == "review" for entry in entries):
        verdict = "needs_human_review"

    return {
        "schema_version": 1,
        "tool": "theangry-skills-security",
        "report_type": "update_plan",
        "generated_at": now_iso(),
        "candidate_root": str(candidate_root),
        "installed_root": str(installed_root),
        "verdict": verdict,
        "summary": {
            "entry_count": len(entries),
            "safe_to_apply_count": sum(1 for entry in entries if entry.safe_to_apply),
            "review_count": sum(1 for entry in entries if entry.action == "review"),
            "blocked_count": sum(1 for entry in entries if entry.action == "block"),
            "keep_count": sum(1 for entry in entries if entry.action == "keep"),
        },
        "apply_policy": {
            "requires_confirm": True,
            "safe_verdicts": sorted(SAFE_VERDICTS),
            "only_safe_default": True,
        },
        "entries": [asdict(entry) for entry in entries],
    }


def copy_skill(candidate_path: Path, destination_path: Path, backup_root: Path) -> dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = None
    staging_root = destination_path.parent / ".theangry-skills-staging"
    staging_root.mkdir(parents=True, exist_ok=True)
    staging_path = staging_root / f"{destination_path.name}-{timestamp}"
    shutil.copytree(candidate_path, staging_path, symlinks=False)

    try:
        if destination_path.exists():
            backup_root.mkdir(parents=True, exist_ok=True)
            backup_path = backup_root / f"{destination_path.name}-{timestamp}"
            shutil.move(str(destination_path), str(backup_path))
        shutil.move(str(staging_path), str(destination_path))
    except Exception:
        if backup_path and backup_path.exists() and not destination_path.exists():
            shutil.move(str(backup_path), str(destination_path))
        if staging_path.exists():
            shutil.rmtree(staging_path)
        raise

    return {
        "destination": str(destination_path),
        "backup": str(backup_path) if backup_path else None,
    }


def apply_update_plan(plan_path: Path, only_safe: bool, confirm: bool) -> dict:
    if not confirm:
        raise RuntimeError("update-apply requires --confirm")
    if not only_safe:
        raise RuntimeError("update-apply currently requires --only-safe")

    plan_path = plan_path.expanduser().resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("report_type") != "update_plan":
        raise RuntimeError("plan file is not an update_plan report")

    candidate_root = Path(plan["candidate_root"]).expanduser().resolve()
    installed_root = Path(plan["installed_root"]).expanduser().resolve()
    backup_root = installed_root / ".theangry-skills-backups"
    results = []

    for entry in plan["entries"]:
        if not entry.get("safe_to_apply"):
            results.append({"skill": entry["skill"], "status": "skipped", "reason": entry["reason"]})
            continue
        if entry["action"] not in {"install", "update"}:
            results.append({"skill": entry["skill"], "status": "skipped", "reason": f"action {entry['action']} is not applyable"})
            continue

        candidate_path = Path(entry["candidate_path"]).expanduser().resolve()
        destination_path = installed_root / entry["skill"]
        if not is_relative_to(candidate_path, candidate_root):
            results.append({"skill": entry["skill"], "status": "skipped", "reason": "candidate path escapes candidate root"})
            continue
        if not is_relative_to(destination_path, installed_root):
            results.append({"skill": entry["skill"], "status": "skipped", "reason": "destination path escapes installed root"})
            continue

        copied = copy_skill(candidate_path, destination_path, backup_root)
        results.append({"skill": entry["skill"], "status": "applied", **copied})

    return {
        "schema_version": 1,
        "tool": "theangry-skills-security",
        "report_type": "update_apply",
        "generated_at": now_iso(),
        "plan_path": str(plan_path),
        "summary": {
            "applied_count": sum(1 for item in results if item["status"] == "applied"),
            "skipped_count": sum(1 for item in results if item["status"] == "skipped"),
        },
        "results": results,
    }


def quarantine_skill(target: str, root: Path, quarantine_root: Path, reason: str, confirm: bool) -> dict:
    if not confirm:
        raise RuntimeError("quarantine requires --confirm")

    root = root.expanduser().resolve()
    quarantine_root = quarantine_root.expanduser().resolve()
    target_path = Path(target).expanduser()
    if not target_path.is_absolute():
        target_path = root / target
    target_path = target_path.resolve()

    if not is_relative_to(target_path, root):
        raise RuntimeError("target path escapes skill root")
    if not target_path.exists() or not target_path.is_dir():
        raise RuntimeError("target skill does not exist")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = quarantine_root / f"{target_path.name}-{timestamp}"
    quarantine_root.mkdir(parents=True, exist_ok=True)
    shutil.move(str(target_path), str(destination))
    metadata = {
        "schema_version": 1,
        "tool": "theangry-skills-security",
        "quarantined_at": now_iso(),
        "skill": target_path.name,
        "source_path": str(target_path),
        "quarantine_path": str(destination),
        "reason": reason,
    }
    write_json(destination / "quarantine-meta.json", metadata)
    return {
        "schema_version": 1,
        "tool": "theangry-skills-security",
        "report_type": "quarantine",
        "generated_at": now_iso(),
        "skill": target_path.name,
        "status": "quarantined",
        "source_path": str(target_path),
        "quarantine_path": str(destination),
        "reason": reason,
    }


def resolve_command(command: str) -> str | None:
    command_path = Path(command).expanduser()
    if command_path.is_absolute() or os.sep in command:
        return str(command_path.resolve()) if command_path.exists() else None
    return shutil.which(command)


def run_skillspector(skill_path: Path, report_dir: Path, command: str, timeout: int) -> dict:
    skill_path = skill_path.expanduser().resolve()
    report_dir = report_dir.expanduser().resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    deterministic_report = scanner.scan_skill(skill_path)
    command_path = resolve_command(command)
    external = {
        "available": command_path is not None,
        "used": False,
        "status": "unavailable" if command_path is None else "not_run",
        "command": command,
        "returncode": None,
        "stdout_path": None,
        "stderr_path": None,
        "note": None,
    }

    if command_path:
        stdout_path = report_dir / "skillspector.stdout.txt"
        stderr_path = report_dir / "skillspector.stderr.txt"
        try:
            result = subprocess.run(
                [command_path, str(skill_path)],
                cwd=str(skill_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
                check=False,
            )
            stdout_path.write_text(result.stdout, encoding="utf-8")
            stderr_path.write_text(result.stderr, encoding="utf-8")
            external.update({
                "used": True,
                "status": "passed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
            })
        except subprocess.TimeoutExpired as exc:
            stdout_path.write_text(exc.stdout or "", encoding="utf-8")
            stderr_path.write_text(exc.stderr or "", encoding="utf-8")
            external.update({
                "used": True,
                "status": "timeout",
                "returncode": None,
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "note": f"timed out after {timeout}s",
            })

    verdict = deterministic_report["verdict"]
    if external["used"] and external["status"] != "passed" and verdict in SAFE_VERDICTS:
        verdict = "needs_human_review"

    return {
        "schema_version": 1,
        "tool": "theangry-skills-security",
        "report_type": "skillspector_evidence",
        "generated_at": now_iso(),
        "skill": deterministic_report["skill"],
        "deterministic_verdict": deterministic_report["verdict"],
        "verdict": verdict,
        "next_action": scanner.next_action_for_verdict(verdict),
        "deterministic_report": deterministic_report,
        "skillspector": external,
    }


def positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill security admission operational helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("update-plan", help="Build a read-only staged update plan.")
    plan_parser.add_argument("--candidate-root", required=True)
    plan_parser.add_argument("--installed-root", required=True)
    plan_parser.add_argument("--skill", action="append", dest="skills", help="Limit plan to one skill name. Repeatable.")
    plan_parser.add_argument("--json", action="store_true")
    plan_parser.add_argument("--write", help="Optional path to write the JSON plan.")

    apply_parser = subparsers.add_parser("update-apply", help="Apply safe entries from a staged update plan.")
    apply_parser.add_argument("--plan", required=True)
    apply_parser.add_argument("--only-safe", action="store_true")
    apply_parser.add_argument("--confirm", action="store_true")
    apply_parser.add_argument("--json", action="store_true")

    quarantine_parser = subparsers.add_parser("quarantine", help="Move a skill to a quarantine directory.")
    quarantine_parser.add_argument("target")
    quarantine_parser.add_argument("--root", required=True)
    quarantine_parser.add_argument("--quarantine-root", required=True)
    quarantine_parser.add_argument("--reason", required=True)
    quarantine_parser.add_argument("--confirm", action="store_true")
    quarantine_parser.add_argument("--json", action="store_true")

    skillspector_parser = subparsers.add_parser("skillspector", help="Run SkillSpector as optional external evidence.")
    skillspector_parser.add_argument("skill_path")
    skillspector_parser.add_argument("--report-dir", required=True)
    skillspector_parser.add_argument("--command", dest="skillspector_command", default="skillspector")
    skillspector_parser.add_argument("--timeout", type=positive_int, default=60)
    skillspector_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    try:
        if args.command == "update-plan":
            report = build_update_plan(Path(args.candidate_root), Path(args.installed_root), args.skills)
            if args.write:
                write_json(Path(args.write).expanduser().resolve(), report)
        elif args.command == "update-apply":
            report = apply_update_plan(Path(args.plan), args.only_safe, args.confirm)
        elif args.command == "quarantine":
            report = quarantine_skill(args.target, Path(args.root), Path(args.quarantine_root), args.reason, args.confirm)
        elif args.command == "skillspector":
            report = run_skillspector(Path(args.skill_path), Path(args.report_dir), args.skillspector_command, args.timeout)
        else:
            parser.error("unknown command")
    except Exception as exc:
        error_report = {
            "schema_version": 1,
            "tool": "theangry-skills-security",
            "report_type": "error",
            "generated_at": now_iso(),
            "error": str(exc),
        }
        print(render_json_or_human(error_report, getattr(args, "json", False)))
        return 2

    print(render_json_or_human(report, getattr(args, "json", False)))
    if report.get("verdict") in BLOCKING_VERDICTS:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
