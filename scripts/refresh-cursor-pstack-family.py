#!/usr/bin/env python3
"""Refresh only the pstack source family and record its historical overrides."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from cursor_pstack_family import current_inventory, same_content


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "sources/cursor-plugins"
MANIFEST_PATH = BASE / "manifest.json"


def git(upstream: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(upstream), *args], text=True).strip()


def digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def refresh(upstream: Path, base: Path = BASE, root: Path = ROOT) -> dict:
    source_commit = git(upstream, "rev-parse", "HEAD")
    full = json.loads((base / "full-tree.json").read_text())
    baseline_commit = full["commit"]
    current = current_inventory(upstream)
    current = {path: {**record, "source_commit": source_commit} for path, record in current.items()}
    baseline_family = {path: value for path, value in full["files"].items() if path.startswith("pstack/")}
    overrides = {
        path: {
            "baseline": ({**baseline_family[path], "source_commit": baseline_commit} if path in baseline_family else None),
            "current": current.get(path),
        }
        for path in sorted(set(baseline_family) | set(current))
        if not same_content(baseline_family.get(path), current.get(path))
    }

    tree = base / "upstream-tree" / "pstack"
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir(parents=True)
    for name, record in current.items():
        source = upstream / name
        target = base / "upstream-tree" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o755 if record["mode"] == "100755" else 0o644)

    snapshot = base / "snapshot" / "pstack"
    if snapshot.exists():
        shutil.rmtree(snapshot)
    shutil.copytree(tree, snapshot)
    ledger = {
        "schema_version": 1,
        "family": "pstack",
        "baseline_commit": baseline_commit,
        "source_commit": source_commit,
        "files": current,
        "overrides": overrides,
    }
    write_json(base / "family-refresh.json", ledger)

    manifest = json.loads(MANIFEST_PATH.read_text())
    entries = [entry for entry in manifest["skills"] if entry.get("family") == "pstack"]
    source_refresh_note = "0.15.28 source refresh; prior runtime and fixture evidence predates this refresh. "
    for entry in entries:
        path = entry["path"]
        if path not in current:
            raise ValueError(f"pstack manifest skill is missing upstream: {path}")
        directory = upstream / Path(path).parent
        entry["files"] = {
            file.relative_to(directory).as_posix(): digest(file)
            for file in sorted(directory.rglob("*"))
            if file.is_file() and not file.is_symlink()
        }
        for relative in entry["files"]:
            source = directory / relative
            if not source.is_file():
                raise ValueError(f"pstack manifest support file is missing upstream: {source.relative_to(upstream)}")
            entry["files"][relative] = digest(source)
        entry["source_commit"] = source_commit
        if path not in {
            "pstack/skills/create-formal-verification-skill/SKILL.md",
            "pstack/skills/maintain-formal-verification-skill/SKILL.md",
        } and not entry.get("availability", "").startswith(source_refresh_note):
            entry["availability"] = source_refresh_note + entry.get("availability", "")
        license_path = entry.get("license_path")
        if license_path:
            license_source = upstream / license_path
            if not license_source.is_file():
                raise ValueError(f"pstack license is missing upstream: {license_path}")
            entry["license_sha256"] = digest(license_source)
        for profile in entry.get("native_agent_profiles", []):
            source = current.get(profile["pinned_source_path"])
            if source is None:
                raise ValueError(f"pstack native profile source is missing: {profile['pinned_source_path']}")
            profile["pinned_source_sha256"] = source["sha256"]
            profile["pinned_source_commit"] = source_commit

    documents = manifest.setdefault("documentation_files", {})
    prior_documents = documents.copy()
    documents.clear()
    doc_paths = {"pstack/README.md"} | {path for path in current if path.startswith("pstack/docs/")}
    for path in sorted(doc_paths):
        if path not in current:
            continue
        metadata = prior_documents.get(path, {})
        documents[path] = {
            **metadata,
            "sha256": current[path]["sha256"],
            "source_commit": source_commit,
            "relationship": metadata.get("relationship", "upstream Pstack reference; not native runtime instructions"),
        }
        if path.startswith("pstack/docs/guide/"):
            documents[path]["related_skills"] = ["cursor-poteto-help"]

    for path, record in manifest.get("support_files", {}).items():
        if path.startswith("pstack/") and path in current:
            record["sha256"] = current[path]["sha256"]
            record["source_commit"] = source_commit
    manifest["pstack_upstream_commit"] = source_commit
    write_json(MANIFEST_PATH, manifest)

    additions_path = base / "additions.json"
    if additions_path.exists():
        additions = json.loads(additions_path.read_text())
        for path, record in additions["files"].items():
            if path.startswith("pstack/"):
                if path not in current:
                    raise ValueError(f"selected pstack addition is missing upstream: {path}")
                record.update(current[path])
                record["source_commit"] = source_commit
        write_json(additions_path, additions)

    coverage_path = base / "agent-coverage.json"
    coverage = json.loads(coverage_path.read_text())
    for path, record in coverage["agents"].items():
        if path.startswith("pstack/"):
            if path not in current:
                raise ValueError(f"pstack agent source is missing upstream: {path}")
            record["source_sha256"] = current[path]["sha256"]
            record["source_commit"] = source_commit
            asset = root / record["asset_path"]
            checker_spec = __import__("importlib.util").util.spec_from_file_location(
                "native_agent_profile_check", root / "scripts/check-native-agent-profiles.py"
            )
            checker = __import__("importlib.util").util.module_from_spec(checker_spec)
            checker_spec.loader.exec_module(checker)
            name = asset.stem
            native_descriptions = {
                "poteto-agent": "Native Codex delegate for code-writing and helper tasks during a `cursor-poteto-mode` run. Use as a delegate, not as the playbook runner. The parent owns scope and every subagent spawn.",
                "comment-sicko": "A deranged comment-hater that savors deletion and condemns workaround code.",
            }
            instructions = checker.adapted_body(name, (upstream / path).read_text())
            asset.write_text(
                f'name = {json.dumps(name)}\n'
                f'description = {json.dumps(native_descriptions[name])}\n'
                f'developer_instructions = {json.dumps(instructions, ensure_ascii=False)}\n'
            )
            record["asset_sha256"] = digest(asset)
    write_json(coverage_path, coverage)

    return {"source_commit": source_commit, "files": len(current), "overrides": len(overrides), "skills": sum(path.endswith("/SKILL.md") for path in current)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(refresh(args.upstream.resolve()), indent=2))
