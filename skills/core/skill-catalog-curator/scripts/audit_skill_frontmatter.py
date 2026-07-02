#!/usr/bin/env python3
"""Audit Codex skill frontmatter, routing, and skill-body quality without mutating files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover - fallback keeps the auditor usable without PyYAML.
    yaml = None


NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$")
KNOWN_CATEGORY_DIRS = {
    "core",
    "engineering",
    "design",
    "knowledge",
    "documentation-skills",
    "mirrors-openclaw",
    "mirrors-mattpocock",
    "mirrors-taste",
    "mirrors-vercel-skills",
    "mirrors-vercel-agent-skills",
    "mirrors-cursor",
    "mirrors-marketing",
    "mirrors-dot-skills",
    "mirrors-looper",
    "mirrors-effective-html",
    "review",
    "archive",
}
TRIGGER_RE = re.compile(
    r"(\bWHEN:|\bUSE FOR:|\buse when\b|\buse this skill when\b|\bwhen the user\b|\bwhen codex\b|\basks? to\b|\basks? for\b|\bsays?\b)",
    re.IGNORECASE,
)
LOCAL_PATH_RE = re.compile(r"(/Users/[^\s)`]+|~/(?:Documents|Library)[^\s)`]*)")
NO_OP_PATTERNS = [
    re.compile(r"\b(be|stay|remain)\s+(very\s+)?(thorough|careful|clear|concise|helpful|pragmatic|honest|specific|accurate|complete|robust|secure|clean|readable|maintainable|efficient)\b", re.IGNORECASE),
    re.compile(r"\b(make|keep|ensure)\b.{0,90}\b(easy to read|clear|concise|detailed|simple|robust|reliable|maintainable|high[- ]quality|well[- ]structured|well[- ]organized)\b", re.IGNORECASE),
    re.compile(r"\b(follow|use|apply)\s+(good|solid|standard|common|best)\s+practices\b", re.IGNORECASE),
    re.compile(r"\b(write|produce|create|provide)\b.{0,90}\b(very\s+)?(detailed|clear|concise|helpful|good|high[- ]quality)\b", re.IGNORECASE),
    re.compile(r"\b(handle errors gracefully|make it user[- ]friendly|make it intuitive|do a good job)\b", re.IGNORECASE),
]
NO_OP_SKIP_RE = re.compile(
    r"(`[^`]+`|\b(no-op|no op|anti-pattern|example|bad:|good:)\b|\b(must include|must contain|required fields?|exactly|at least|at most|no more than|under \d+|before|after|until|unless|if)\b)",
    re.IGNORECASE,
)


@dataclass
class Finding:
    severity: str
    code: str
    message: str


def parse_frontmatter(text: str) -> tuple[dict[str, object], str | None]:
    if not text.startswith("---\n"):
        return {}, "missing opening frontmatter delimiter"
    end = text.find("\n---", 4)
    if end == -1:
        return {}, "missing closing frontmatter delimiter"
    raw = text[4:end]

    if yaml is not None:
        try:
            parsed = yaml.safe_load(raw) or {}
        except Exception as exc:
            return {}, f"invalid YAML frontmatter: {exc}"
        if not isinstance(parsed, dict):
            return {}, "frontmatter must be a YAML mapping"
        return {str(key): value for key, value in parsed.items()}, None

    data: dict[str, object] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            return data, f"invalid frontmatter line: {line}"
        key, value = stripped.split(":", 1)
        raw_value = value.strip()
        if raw_value and raw_value[0] not in {"\"", "'"} and re.search(r":\s", raw_value):
            return data, f"invalid unquoted YAML value with colon-space: {line}"
        data[key.strip()] = raw_value.strip("\"'")
    return data, None


def grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def body_lines_without_code_or_frontmatter(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    in_frontmatter = text.startswith("---\n")
    in_code_fence = False
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if line_number == 1 and in_frontmatter:
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        lines.append((line_number, raw_line))
    return lines


def normalize_instruction_line(raw_line: str) -> str:
    cleaned = raw_line.strip()
    cleaned = re.sub(r"^>\s*", "", cleaned)
    cleaned = re.sub(r"^[-*+]\s+", "", cleaned)
    cleaned = re.sub(r"^\d+\.\s+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def collect_no_op_candidates(text: str) -> list[dict[str, str | int]]:
    candidates: list[dict[str, str | int]] = []
    for line_number, raw_line in body_lines_without_code_or_frontmatter(text):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue
        cleaned = normalize_instruction_line(raw_line)
        if len(cleaned) < 8:
            continue
        if '"' in cleaned or "'" in cleaned or NO_OP_SKIP_RE.search(cleaned):
            continue
        if any(pattern.search(cleaned) for pattern in NO_OP_PATTERNS):
            candidates.append({"line": line_number, "text": cleaned})
    return candidates


def is_grouped_pack_skill(skill_dir: Path) -> bool:
    parts = skill_dir.resolve().parts
    try:
        skills_index = max(index for index, part in enumerate(parts) if part == "skills")
    except ValueError:
        return False

    relative_parts = parts[skills_index + 1 :]
    if len(relative_parts) < 2:
        return False

    if relative_parts[0] in KNOWN_CATEGORY_DIRS:
        return len(relative_parts) >= 3

    return True


def audit_skill(skill_dir: Path, profile: str) -> dict:
    skill_md = skill_dir / "SKILL.md"
    findings: list[Finding] = []
    if not skill_md.exists():
        return {
            "path": str(skill_dir),
            "score": 0,
            "grade": "F",
            "findings": [asdict(Finding("error", "missing-skill-md", "SKILL.md not found"))],
        }

    text = skill_md.read_text(encoding="utf-8")
    frontmatter, fm_error = parse_frontmatter(text)
    if fm_error:
        findings.append(Finding("error", "frontmatter-parse", fm_error))

    name = str(frontmatter.get("name", "") or "")
    description = str(frontmatter.get("description", "") or "")
    body = text.split("\n---", 1)[-1] if "\n---" in text else text

    if not name:
        findings.append(Finding("error", "missing-name", "frontmatter is missing name"))
    elif not NAME_RE.match(name):
        findings.append(Finding("error", "invalid-name", f'name "{name}" is not lowercase hyphen-case'))
    elif name != skill_dir.name and not is_grouped_pack_skill(skill_dir):
        findings.append(Finding("error", "directory-name-mismatch", f'directory "{skill_dir.name}" does not match name "{name}"'))

    if not description:
        findings.append(Finding("error", "missing-description", "frontmatter is missing description"))
    else:
        if len(description) < 150:
            findings.append(Finding("warning", "short-description", f"description is short ({len(description)} chars); routing may be weak"))
        if len(description) > 1024:
            findings.append(Finding("error", "description-too-long", f"description exceeds 1024 chars ({len(description)})"))
        if len(description.split()) > 70:
            findings.append(Finding("warning", "wordy-description", f"description has {len(description.split())} words; keep trigger text tight"))
        if not TRIGGER_RE.search(description):
            findings.append(Finding("warning", "missing-trigger-language", "description does not include clear trigger language such as 'Use when' or 'when the user'"))

    allowed_keys = {
        "codex": {"name", "description"},
        "shared": {"name", "description", "metadata", "license", "version", "compatibility"},
        "agentskills": {"name", "description", "metadata", "license", "version", "compatibility"},
    }[profile]

    extra_keys = sorted(set(frontmatter) - allowed_keys)
    if extra_keys:
        findings.append(Finding("info", "extra-frontmatter", f"extra frontmatter keys present: {', '.join(extra_keys)}"))

    if profile == "agentskills":
        if "license" not in frontmatter:
            findings.append(Finding("info", "missing-license", "license field is recommended for agentskills-style publication"))
        if "version" not in frontmatter and "metadata" not in frontmatter:
            findings.append(Finding("info", "missing-version", "version or metadata.version is recommended for agentskills-style publication"))
        if description and not re.search(r"(\bWHEN:|\bUSE FOR:|\bUse when\b|\bUse this skill when\b)", description):
            findings.append(Finding("warning", "agentskills-trigger-format", "agentskills-style routing prefers explicit WHEN: or USE FOR: trigger text"))

    line_count = len(text.splitlines())
    if line_count > 500:
        findings.append(Finding("warning", "oversized-skill-md", f"SKILL.md has {line_count} lines; move bulky material into references/"))
    elif line_count > 220 and not (skill_dir / "references").exists():
        findings.append(Finding("info", "consider-references", f"SKILL.md has {line_count} lines and no references/ directory"))

    agents_yaml = skill_dir / "agents" / "openai.yaml"
    if not agents_yaml.exists():
        findings.append(Finding("info", "missing-openai-yaml", "agents/openai.yaml is absent; useful for UI display metadata"))

    scanned_files = [skill_md]
    if (skill_dir / "references").exists():
        scanned_files.extend(p for p in (skill_dir / "references").rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".txt", ".yaml", ".yml", ".json"})

    leaks: list[str] = []
    for file_path in scanned_files:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if LOCAL_PATH_RE.search(content):
            leaks.append(str(file_path.relative_to(skill_dir)))
    if leaks:
        findings.append(Finding("warning", "local-path-leak", f"local filesystem paths found in: {', '.join(sorted(set(leaks)))}"))

    no_op_candidates = collect_no_op_candidates(text)
    if no_op_candidates:
        preview_items = [f"L{item['line']}: {item['text']}" for item in no_op_candidates[:5]]
        remainder = len(no_op_candidates) - len(preview_items)
        suffix = f"; +{remainder} more" if remainder > 0 else ""
        findings.append(
            Finding(
                "info",
                "possible-no-op-instructions",
                f"possible no-op instruction lines in SKILL.md: {'; '.join(preview_items)}{suffix}",
            )
        )

    score = 100
    for finding in findings:
        if finding.severity == "error":
            score -= 20
        elif finding.severity == "warning":
            score -= 7
        else:
            score -= 1
    score = max(score, 0)

    counts = {
        "error": sum(1 for f in findings if f.severity == "error"),
        "warning": sum(1 for f in findings if f.severity == "warning"),
        "info": sum(1 for f in findings if f.severity == "info"),
    }

    return {
        "path": str(skill_dir),
        "name": name,
        "profile": profile,
        "score": score,
        "grade": grade(score),
        "lineCount": line_count,
        "descriptionChars": len(description),
        "descriptionWords": len(description.split()) if description else 0,
        "noOpCandidateCount": len(no_op_candidates),
        "noOpCandidates": no_op_candidates,
        "counts": counts,
        "findings": [asdict(f) for f in findings],
    }


def find_skill_dirs(root: Path) -> list[Path]:
    if (root / "SKILL.md").exists():
        return [root]
    return sorted({p.parent for p in root.rglob("SKILL.md")})


def display_path(raw_path: str) -> str:
    path = Path(raw_path)
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def render_markdown(results: list[dict], profile: str) -> str:
    lines = ["# Skill frontmatter audit", ""]
    total = len(results)
    errors = sum(r["counts"]["error"] for r in results)
    warnings = sum(r["counts"]["warning"] for r in results)
    lines.append(f"Profile: `{profile}`")
    lines.append(f"Scope: {total} skill(s)")
    lines.append(f"Findings: {errors} error(s), {warnings} warning(s)")
    lines.append("")
    for result in results:
        lines.append(f"## {result.get('name') or Path(result['path']).name}")
        lines.append("")
        lines.append(f"- Score: {result['score']}/100 ({result['grade']})")
        lines.append(f"- Path: `{display_path(result['path'])}`")
        lines.append(f"- SKILL.md: {result.get('lineCount', 0)} lines")
        lines.append(f"- Description: {result.get('descriptionChars', 0)} chars, {result.get('descriptionWords', 0)} words")
        if result.get("noOpCandidateCount", 0):
            lines.append(f"- No-op candidates: {result.get('noOpCandidateCount', 0)}")
        lines.append("")
        if result["findings"]:
            for finding in result["findings"]:
                lines.append(f"- **{finding['severity']} / {finding['code']}**: {finding['message']}")
        else:
            lines.append("- No findings.")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Codex skill frontmatter and routing quality.")
    parser.add_argument("paths", nargs="+", help="Skill directory or root containing skills.")
    parser.add_argument(
        "--profile",
        choices=["shared", "codex", "agentskills"],
        default="shared",
        help="Audit profile. shared is the team default; codex is Codex strict; agentskills follows agentskills/Sensei-style publication hints.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    args = parser.parse_args()

    skill_dirs: list[Path] = []
    for raw in args.paths:
        skill_dirs.extend(find_skill_dirs(Path(raw).expanduser().resolve()))

    results = [audit_skill(skill_dir, args.profile) for skill_dir in sorted(set(skill_dirs))]
    if args.json:
        print(json.dumps({"profile": args.profile, "results": results}, indent=2))
    else:
        print(render_markdown(results, args.profile))

    return 1 if any(r["counts"]["error"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
