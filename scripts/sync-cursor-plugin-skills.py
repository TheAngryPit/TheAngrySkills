#!/usr/bin/env python3
"""Build the reviewed Cursor skill mirror from a pinned, local source snapshot.

The committed source and per-skill overlays are the authority. Refresh compares a
new upstream checkout without accepting additions or changing published skills.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "sources" / "cursor-plugins" / "snapshot"
LEDGER = ROOT / "sources" / "cursor-plugins" / "manifest.json"
OVERLAYS = ROOT / "sources" / "cursor-plugins" / "overlays"
DEST = ROOT / "skills" / "mirrors-cursor"
STATE = ROOT / "reports" / "cursor-plugin-skills-state.json"
SKILL_PATTERN = re.compile(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n")
NAME_PATTERN = re.compile(r"^name:\s*[^\r\n]+$", re.MULTILINE)
MARKDOWN_LINK = re.compile(r"\]\(([^)]+)\)")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink())


def safe_relative(value: str) -> Path:
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError(f"unsafe path: {value}")
    return rel


def physical_skills(root: Path) -> set[str]:
    return {
        p.relative_to(root).as_posix()
        for p in root.rglob("SKILL.md")
        if "skills" in p.relative_to(root).parts and not p.is_symlink()
    }


def validate_manifest(manifest: dict) -> list[dict]:
    if manifest.get("schema_version") != 1:
        raise ValueError("unknown manifest schema")
    entries = manifest.get("skills")
    if not isinstance(entries, list) or not entries:
        raise ValueError("empty skill ledger")
    paths = [e["path"] for e in entries]
    names = [e["published_name"] for e in entries]
    if len(set(paths)) != len(paths) or len(set(names)) != len(names):
        raise ValueError("duplicate source path or published name")
    for entry in entries:
        safe_relative(entry["path"])
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", entry["published_name"]):
            raise ValueError(f"invalid published name: {entry['published_name']}")
        if not entry["path"].endswith("/SKILL.md"):
            raise ValueError(f"invalid skill path: {entry['path']}")
    return entries


def verify_snapshot(manifest: dict) -> None:
    entries = validate_manifest(manifest)
    symlinks = sorted(p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob("*") if p.is_symlink())
    if symlinks:
        raise ValueError(f"snapshot contains untracked symlinks: {symlinks}")
    actual = physical_skills(SOURCE)
    expected = {e["path"] for e in entries}
    if actual != expected:
        raise ValueError(f"snapshot inventory drift: missing={sorted(expected-actual)}, new={sorted(actual-expected)}")
    for entry in entries:
        source_dir = SOURCE / Path(entry["path"]).parent
        actual_files = {
            p.relative_to(source_dir).as_posix(): sha(p)
            for p in files(source_dir)
        }
        if actual_files != entry["files"]:
            raise ValueError(f"snapshot file drift: {entry['path']}")
        license_path = entry.get("license_path")
        if license_path and sha(SOURCE / safe_relative(license_path)) != entry["license_sha256"]:
            raise ValueError(f"license drift: {license_path}")


def replace_exact(text: str, before: str, after: str, owner: str) -> str:
    count = text.count(before)
    if count != 1:
        raise ValueError(f"overlay anchor count {count}, expected 1: {owner}: {before[:80]!r}")
    return text.replace(before, after, 1)


def rewrite_sibling_links(source_file: Path, output_file: Path, text: str,
                          source_to_entry: dict[Path, dict], staging: Path, commit: str) -> str:
    def replace(match: re.Match[str]) -> str:
        value = match.group(1)
        if ":" in value or value.startswith("/"):
            return match.group(0)
        path_value, sep, fragment = value.partition("#")
        source_target = (source_file.parent / path_value).resolve()
        sibling = source_to_entry.get(source_target)
        if not sibling:
            return match.group(0)
        if sibling["publish"]:
            output_target = staging / sibling["published_name"] / "SKILL.md"
            link = os.path.relpath(output_target, output_file.parent).replace(os.sep, "/")
        else:
            link = f"https://github.com/cursor/plugins/blob/{commit}/{sibling['path']}"
        return f"]({link}{sep}{fragment})"

    return MARKDOWN_LINK.sub(replace, text)


def render_skill(entry: dict, staging: Path, commit: str,
                 source_to_entry: dict[Path, dict]) -> dict[str, str]:
    name = entry["published_name"]
    source_dir = SOURCE / Path(entry["path"]).parent
    target = staging / name
    shutil.copytree(source_dir, target)
    overlay_path = OVERLAYS / f"{name}.json"
    overlay = load(overlay_path)
    if overlay.get("source_path") != entry["path"] or overlay.get("source_sha256") != entry["files"]["SKILL.md"]:
        raise ValueError(f"overlay source mismatch: {name}")
    skill_file = target / "SKILL.md"
    text = skill_file.read_text()
    match = SKILL_PATTERN.match(text)
    if not match:
        raise ValueError(f"missing frontmatter: {entry['path']}")
    frontmatter = match.group(1)
    if len(NAME_PATTERN.findall(frontmatter)) != 1:
        raise ValueError(f"name count invalid: {entry['path']}")
    original_name = NAME_PATTERN.search(frontmatter).group(0)
    frontmatter = replace_exact(frontmatter, original_name, f"name: {name}", name)
    text = text[:match.start(1)] + frontmatter + text[match.end(1):]
    skill_file.write_text(text)
    for op in overlay.get("replacements", []):
        relative = safe_relative(op["file"])
        target_file = target / relative
        if not target_file.is_file() or relative.as_posix() not in entry["files"]:
            raise ValueError(f"overlay target is not a source skill file: {name}/{relative}")
        contents = target_file.read_text()
        contents = replace_exact(contents, op["before"], op["after"], f"{name}/{relative}")
        target_file.write_text(contents)
    text = skill_file.read_text()
    if overlay.get("codex_note"):
        marker = SKILL_PATTERN.match(text)
        text = text[:marker.end()] + "\n" + overlay["codex_note"].rstrip() + "\n" + text[marker.end():]
    skill_file.write_text(text)
    for output_file in files(target):
        if output_file.suffix.lower() not in {".md", ".mdx"}:
            continue
        source_file = source_dir / output_file.relative_to(target)
        original = output_file.read_text()
        rewritten = rewrite_sibling_links(source_file, output_file, original, source_to_entry, staging, commit)
        if rewritten != original:
            output_file.write_text(rewritten)
    if entry.get("license_path"):
        shutil.copy2(SOURCE / entry["license_path"], target / "LICENSE.upstream")
    note = [
        "# Cursor skill mirror", "",
        f"Source: {manifest_repository()}",
        f"Commit: {commit}",
        f"Physical source path: {entry['path']}",
        f"Source SHA-256: {entry['files']['SKILL.md']}",
        f"Published name: {name}",
        f"Decision class: {entry['decision_classification']}",
        f"Availability: {entry['availability']}",
        f"License evidence: {entry.get('license_path') or 'not established at this path'}", "",
        "The raw source is in `sources/cursor-plugins/snapshot/`. This directory is",
        "generated from that source and its exact per-skill overlay. External",
        "products, connectors, credentials and automation runtimes remain external.",
        "The decision class does not establish runtime availability.", "",
    ]
    (target / "MIRROR.md").write_text("\n".join(note))
    return {p.relative_to(target).as_posix(): sha(p) for p in files(target)}


def manifest_repository() -> str:
    return load(LEDGER)["upstream_repository"]


def compare_trees(expected: Path, actual: Path) -> list[str]:
    a = {p.relative_to(expected).as_posix(): sha(p) for p in files(expected)}
    b = {p.relative_to(actual).as_posix(): sha(p) for p in files(actual)} if actual.exists() else {}
    return [k for k in sorted(a.keys() | b.keys()) if a.get(k) != b.get(k)]


def build(check: bool) -> None:
    manifest = load(LEDGER)
    verify_snapshot(manifest)
    entries = validate_manifest(manifest)
    active = [e for e in entries if e["publish"]]
    source_to_entry = {(SOURCE / e["path"]).resolve(): e for e in entries}
    previous = load(STATE) if STATE.exists() else None
    if not check and previous:
        recorded = previous.get("generated_files", {})
        actual = {p.relative_to(DEST).as_posix(): sha(p) for p in files(DEST)} if DEST.exists() else {}
        if actual != recorded:
            raise ValueError("published tree has local modifications; preserve and review them before rebuild")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cursor-mirror-build-", dir=DEST.parent) as tmp:
        staged = Path(tmp) / "mirrors-cursor"
        staged.mkdir()
        for entry in active:
            render_skill(entry, staged, manifest["upstream_commit"], source_to_entry)
        changed = compare_trees(staged, DEST)
        generated = {p.relative_to(staged).as_posix(): sha(p) for p in files(staged)}
        state = {
            "schema_version": 1,
            "upstream_commit": manifest["upstream_commit"],
            "physical_skills": len(entries),
            "published_skills": len(active),
            "source_dormant_skills": sum(not e["declared_for_distribution"] for e in entries),
            "candidate_not_published": sum(e["declared_for_distribution"] and not e["publish"] for e in entries),
            "generated_files": generated,
        }
        if check:
            if changed or not STATE.exists() or load(STATE) != state:
                raise ValueError(f"generated mirror differs: {len(changed)} files")
            print(f"mirror check passed: {len(entries)} physical, {len(active)} published, {len(generated)} output files")
            return
        backup = Path(tmp) / "prior-mirrors-cursor"
        state_file = Path(tmp) / "state.json"
        state_file.write_text(dump(state))
        STATE.parent.mkdir(parents=True, exist_ok=True)
        moved_prior = False
        try:
            if DEST.exists():
                DEST.rename(backup)
                moved_prior = True
            staged.rename(DEST)
            state_file.replace(STATE)
        except OSError:
            if DEST.exists():
                shutil.rmtree(DEST)
            if moved_prior:
                backup.rename(DEST)
            raise
        print(f"built {len(active)} skills, {len(generated)} files; changed={len(changed)}")


def refresh(upstream: Path) -> None:
    manifest = load(LEDGER)
    entries = validate_manifest(manifest)
    existing = {e["path"]: e for e in entries}
    current = physical_skills(upstream)
    pinned = set(existing)
    changed = []
    changed_licenses = []
    for path in sorted(pinned & current):
        item = existing[path]
        root = upstream / Path(path).parent
        hashes = {p.relative_to(root).as_posix(): sha(p) for p in files(root)}
        if hashes != item["files"]:
            changed.append(path)
    for license_path, expected_sha in sorted({
        (e["license_path"], e["license_sha256"]) for e in entries if e.get("license_path")
    }):
        live = upstream / license_path
        if not live.is_file() or sha(live) != expected_sha:
            changed_licenses.append(license_path)
    head = subprocess.check_output(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True).strip()
    report = {"upstream_commit": head, "pinned_commit": manifest["upstream_commit"],
              "new_skills": sorted(current-pinned), "removed_skills": sorted(pinned-current),
              "changed_skills": changed, "changed_licenses": changed_licenses}
    print(dump(report), end="")
    if report["new_skills"] or report["removed_skills"] or changed or changed_licenses:
        raise ValueError("upstream changes require explicit per-skill review and overlay rebase")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify committed build without writing")
    parser.add_argument("--compare-upstream", type=Path, help="report upstream changes; never import automatically")
    args = parser.parse_args()
    if args.compare_upstream:
        refresh(args.compare_upstream.resolve())
    else:
        build(args.check)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"cursor mirror: {error}", file=sys.stderr)
        sys.exit(1)
