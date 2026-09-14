"""Static checks for a disposable project skill fixture, not Codex runtime proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable


FRONTMATTER_FIELD = re.compile(r"^(name|description):\s*(.+?)\s*$")
POLICY_FIELD = re.compile(
    r"^\s*allow_implicit_invocation:\s*(true|false)\s*$", re.MULTILINE
)
FRONTMATTER_END = "---"


def _clean_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _read_frontmatter(skill_path: Path) -> tuple[dict[str, str], int]:
    with skill_path.open(encoding="utf-8") as stream:
        first = stream.readline().rstrip("\n")
        if first != FRONTMATTER_END:
            raise ValueError(f"missing frontmatter opener: {skill_path}")
        fields: dict[str, str] = {}
        for line_number, line in enumerate(stream, start=2):
            stripped = line.rstrip("\n")
            if stripped == FRONTMATTER_END:
                if set(fields) != {"name", "description"}:
                    raise ValueError(f"invalid frontmatter fields: {skill_path}")
                return fields, line_number
            match = FRONTMATTER_FIELD.match(stripped)
            if match:
                fields[match.group(1)] = _clean_yaml_scalar(match.group(2))
    raise ValueError(f"unterminated frontmatter: {skill_path}")


def _implicit_policy(skill_dir: Path) -> bool:
    policy_path = skill_dir / "agents" / "openai.yaml"
    if not policy_path.exists():
        return True
    policy = policy_path.read_text(encoding="utf-8")
    match = POLICY_FIELD.search(policy)
    return True if match is None else match.group(1) == "true"


def _catalogue_entry(skill_dir: Path) -> dict[str, object]:
    skill_path = skill_dir / "SKILL.md"
    fields, frontmatter_end_line = _read_frontmatter(skill_path)
    return {
        "name": fields["name"],
        "description": fields["description"],
        "path": str(skill_path),
        "frontmatter_end_line": frontmatter_end_line,
        "allow_implicit_invocation": _implicit_policy(skill_dir),
        "catalogue_read": True,
        "full_skill_read": False,
    }


def _full_skill_read(skill_dir: Path, entry: dict[str, object]) -> dict[str, object]:
    skill_path = skill_dir / "SKILL.md"
    body = skill_path.read_text(encoding="utf-8")
    full = dict(entry)
    full.update(
        {
            "full_skill_read": True,
            "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
            "body_chars": len(body),
        }
    )
    return full


def scan_skill_catalogue(
    fixture_root: str | Path,
    *,
    full_read_names: Iterable[str] = (),
) -> dict[str, object]:
    """Separate catalogue discovery from selected full ``SKILL.md`` reads."""

    root = Path(fixture_root)
    skills_root = root / ".agents" / "skills"
    if not skills_root.is_dir():
        raise ValueError(f"missing project skill root: {skills_root}")

    requested = set(full_read_names)
    catalogue: list[dict[str, object]] = []
    full_reads: list[dict[str, object]] = []
    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        if not (skill_dir / "SKILL.md").is_file():
            continue
        entry = _catalogue_entry(skill_dir)
        catalogue.append(entry)
        if str(entry["name"]) in requested:
            full_reads.append(_full_skill_read(skill_dir, entry))

    names = {str(entry["name"]) for entry in catalogue}
    missing = sorted(requested - names)
    if missing:
        raise ValueError(f"requested full reads are not in catalogue: {missing}")
    return {
        "fixture_root": str(root),
        "skill_root": str(skills_root),
        "catalogue": catalogue,
        "catalogue_names": tuple(sorted(names)),
        "full_skill_reads": full_reads,
        "full_skill_read_names": tuple(
            sorted(str(entry["name"]) for entry in full_reads)
        ),
    }


def classify_activation_request(
    catalogue: dict[str, object],
    *,
    skill_name: str,
    prompt: str,
    implicit_trigger: str | None = None,
) -> dict[str, object]:
    """Classify what the fixture can establish without running a model."""

    entries = {
        str(entry["name"]): entry for entry in catalogue["catalogue"]  # type: ignore[index]
    }
    entry = entries.get(skill_name)
    if entry is None:
        return {"status": "NOT_IN_CATALOGUE", "skill_name": skill_name}

    explicit_token = f"${skill_name}"
    explicit = re.search(rf"{re.escape(explicit_token)}(?![\w-])", prompt) is not None
    has_path = "/" in prompt or str(catalogue["fixture_root"]) in prompt
    implicit_triggered = bool(implicit_trigger and implicit_trigger in prompt)
    allow_implicit = bool(entry["allow_implicit_invocation"])

    if explicit:
        status = "EXPLICIT_TOKEN_PRESENT_NOT_OBSERVED"
    elif implicit_triggered and allow_implicit:
        status = "IMPLICIT_ELIGIBLE_NOT_OBSERVED"
    elif implicit_triggered and not allow_implicit:
        status = "IMPLICIT_BLOCKED_BY_POLICY"
    else:
        status = "NOT_SELECTED"

    return {
        "status": status,
        "skill_name": skill_name,
        "catalogue_discovered": True,
        "explicit_token_present": explicit,
        "implicit_trigger_present": implicit_triggered,
        "allow_implicit_invocation": allow_implicit,
        "prompt_contains_path": has_path,
        "full_skill_read": skill_name in catalogue["full_skill_read_names"],  # type: ignore[operator]
    }


def verify_exact_copy(source: str | Path, candidate: str | Path) -> dict[str, object]:
    """Verify a project skill is an exact byte-for-byte source copy."""

    source_path = Path(source)
    candidate_path = Path(candidate)
    source_bytes = source_path.read_bytes()
    candidate_bytes = candidate_path.read_bytes()
    return {
        "source": str(source_path),
        "candidate": str(candidate_path),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "byte_match": source_bytes == candidate_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture_root", type=Path)
    parser.add_argument("--full-read", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = scan_skill_catalogue(args.fixture_root, full_read_names=args.full_read)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("catalogue: " + ", ".join(result["catalogue_names"]))
        print("full SKILL.md reads: " + ", ".join(result["full_skill_read_names"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
