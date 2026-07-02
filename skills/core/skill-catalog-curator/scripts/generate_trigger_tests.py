#!/usr/bin/env python3
"""Generate Waza-style trigger test fixtures from a skill's frontmatter."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_frontmatter(text: str) -> tuple[dict[str, str], str | None]:
    if not text.startswith("---\n"):
        return {}, "missing opening frontmatter delimiter"
    end = text.find("\n---", 4)
    if end == -1:
        return {}, "missing closing frontmatter delimiter"
    raw = text[4:end]
    data: dict[str, str] = {}
    current_key: str | None = None
    current_value: list[str] = []
    for line in raw.splitlines():
        key_match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if key_match:
            if current_key:
                data[current_key] = "\n".join(current_value).strip().strip("\"'").replace('\\"', '"')
            current_key = key_match.group(1)
            raw_value = key_match.group(2).strip()
            current_value = [] if raw_value in {"|", ">"} else [raw_value]
        elif current_key and (line.startswith("  ") or line.startswith("\t")):
            current_value.append(line.strip())
    if current_key:
        data[current_key] = "\n".join(current_value).strip().strip("\"'").replace('\\"', '"')
    return data, None


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def split_phrases(raw: str) -> list[str]:
    cleaned = raw.strip().strip(".")
    quoted = re.findall(r'"([^"]+)"|`([^`]+)`', cleaned)
    phrases = [a or b for a, b in quoted if (a or b)]
    if phrases:
        return unique(phrases)
    parts = re.split(r"\s*(?:,|;|\band\b|\bor\b)\s*", cleaned, flags=re.IGNORECASE)
    return unique([part.strip(" .") for part in parts if 2 <= len(part.strip(" .")) <= 90])


def extract_after_marker(description: str, markers: list[str]) -> list[str]:
    escaped = "|".join(re.escape(marker) for marker in markers)
    match = re.search(rf"\b(?:{escaped})\s*:?\s*(.+)", description, re.IGNORECASE)
    if not match:
        return []
    tail = re.split(r"\b(?:DO NOT USE FOR|INVOKES|FOR SINGLE OPERATIONS|WHEN NOT)\s*:?", match.group(1), maxsplit=1, flags=re.IGNORECASE)[0]
    return split_phrases(tail)


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        normalized = re.sub(r"\s+", " ", value).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            out.append(normalized)
    return out


def fallback_trigger_phrases(name: str, description: str) -> list[str]:
    base = description
    base = re.sub(r"\bUse when\b|\bUse this skill when\b|\bwhen the user\b", "", base, flags=re.IGNORECASE)
    base = re.sub(r"\b(do not use for|invokes|for single operations)\b.*", "", base, flags=re.IGNORECASE)
    clauses = re.split(r"\.|\bwhen\b|\bor\b|\band\b", base, flags=re.IGNORECASE)
    candidates = [name.replace("-", " ")]
    candidates.extend(clause.strip(" :;.") for clause in clauses if 12 <= len(clause.strip(" :;.")) <= 90)
    return unique(candidates)[:6]


def trigger_variants(phrase: str) -> list[str]:
    lower = phrase[:1].lower() + phrase[1:]
    upper = phrase[:1].upper() + phrase[1:]
    return unique([
        phrase,
        f"How do I {lower}?",
        f"Please {lower}",
        f"{upper} for this project",
    ])


def anti_trigger_variants(phrase: str) -> list[str]:
    lower = phrase[:1].lower() + phrase[1:]
    return unique([
        phrase,
        f"Help me {lower}",
        f"I only need to {lower}",
    ])


def generate(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise SystemExit(f"missing SKILL.md: {skill_dir}")
    text = skill_md.read_text(encoding="utf-8")
    frontmatter, error = parse_frontmatter(text)
    if error:
        raise SystemExit(error)

    name = frontmatter.get("name") or skill_dir.name
    description = frontmatter.get("description", "")
    trigger_phrases = extract_after_marker(description, ["WHEN", "USE FOR"])
    if not trigger_phrases:
        trigger_phrases = fallback_trigger_phrases(name, description)
    anti_phrases = extract_after_marker(description, ["DO NOT USE FOR", "WHEN NOT"])

    should_trigger: list[str] = []
    for phrase in trigger_phrases:
        should_trigger.extend(trigger_variants(phrase))
    should_trigger = unique(should_trigger)[:16]

    should_not: list[str] = []
    for phrase in anti_phrases:
        should_not.extend(anti_trigger_variants(phrase))
    should_not.extend([
        "What is the weather today?",
        "Write a short poem",
        "Summarize this unrelated news article",
        "Install a new package without asking",
        "Delete this folder now",
    ])
    should_not = unique(should_not)[:16]

    lines = [
        f"name: {name}-triggers",
        f"skill: {name}",
        "",
        "shouldTriggerPrompts:",
    ]
    lines.extend(f"  - {yaml_quote(prompt)}" for prompt in should_trigger)
    lines.extend(["", "shouldNotTriggerPrompts:"])
    lines.extend(f"  - {yaml_quote(prompt)}" for prompt in should_not)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Waza-style trigger_tests.yaml for a skill.")
    parser.add_argument("skill_path", help="Skill directory containing SKILL.md.")
    parser.add_argument("--write", nargs="?", const="tests", help="Write to <dir>/<skill-name>/trigger_tests.yaml. Defaults to tests when no value is given.")
    args = parser.parse_args()

    skill_dir = Path(args.skill_path).expanduser().resolve()
    yaml_text = generate(skill_dir)
    if args.write:
        target_root = Path(args.write).expanduser()
        target = target_root / skill_dir.name / "trigger_tests.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(yaml_text, encoding="utf-8")
        print(f"wrote_trigger_tests: {target}")
    else:
        print(yaml_text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
