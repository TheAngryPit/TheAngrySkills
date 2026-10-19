"""Read and verify the pinned current pstack family snapshot."""

import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath


FAMILY = "pstack"
LEDGER_NAME = "family-refresh.json"
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")


def validate_path(path: str) -> None:
    value = PurePosixPath(path)
    if (not path.startswith("pstack/") or "\\" in path or value.is_absolute()
            or any(part in ("", ".", "..") for part in value.parts)
            or value.as_posix() != path):
        raise ValueError(f"unsafe pstack family path: {path}")


def same_content(left: dict | None, right: dict | None) -> bool:
    if left is None or right is None:
        return left is right
    return all(left.get(key) == right.get(key) for key in ("mode", "git_blob", "sha256"))


def record(path: Path, mode: str) -> dict[str, str]:
    data = path.read_bytes()
    return {
        "mode": mode,
        "git_blob": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def load(base: Path) -> dict:
    ledger_path = base / LEDGER_NAME
    if not ledger_path.is_file():
        return {}
    ledger = json.loads(ledger_path.read_text())
    if (ledger.get("family") != FAMILY
            or not isinstance(ledger.get("baseline_commit"), str)
            or not COMMIT.fullmatch(ledger["baseline_commit"])
            or not isinstance(ledger.get("source_commit"), str)
            or not COMMIT.fullmatch(ledger["source_commit"])):
        raise ValueError("invalid pstack family refresh header")
    files = ledger.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("pstack family refresh inventory is empty")
    for path, record_data in files.items():
        validate_path(path)
        if record_data.get("source_commit") != ledger["source_commit"]:
            raise ValueError(f"pstack family source commit mismatch: {path}")
        if (record_data.get("mode") not in ("100644", "100755")
                or not isinstance(record_data.get("git_blob"), str)
                or not re.fullmatch(r"[0-9a-f]{40}", record_data["git_blob"])
                or not isinstance(record_data.get("sha256"), str)
                or not HASH.fullmatch(record_data["sha256"])):
            raise ValueError(f"invalid pstack family file record: {path}")
    return ledger


def current_inventory(upstream: Path, revision: str = "HEAD") -> dict[str, dict[str, str]]:
    rows = subprocess.check_output(
        ["git", "-C", str(upstream), "ls-tree", "-r", revision], text=True
    ).splitlines()
    result = {}
    for row in rows:
        metadata, name = row.split("\t", 1)
        mode, kind, blob = metadata.split()
        if not name.startswith("pstack/"):
            continue
        validate_path(name)
        if kind != "blob" or mode not in ("100644", "100755"):
            raise ValueError(f"unsupported upstream pstack object: {name}")
        data = subprocess.check_output(["git", "-C", str(upstream), "show", f"{revision}:{name}"])
        record_data = record_from_bytes(data, mode)
        if record_data["git_blob"] != blob:
            raise ValueError(f"pstack Git blob mismatch: {name}")
        result[name] = record_data
    return result


def record_from_bytes(data: bytes, mode: str) -> dict[str, str]:
    return {
        "mode": mode,
        "git_blob": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def merged_inventory(base: Path) -> dict[str, dict[str, str]]:
    full = json.loads((base / "full-tree.json").read_text())
    ledger = load(base)
    if ledger and ledger["baseline_commit"] != full["commit"]:
        raise ValueError("pstack family baseline differs from full-tree pin")
    files = {path: record.copy() for path, record in full["files"].items() if not path.startswith("pstack/")}
    files.update(ledger.get("files", {}))
    return files


def verify(base: Path, upstream: Path | None = None) -> dict:
    full = json.loads((base / "full-tree.json").read_text())
    ledger = load(base)
    if ledger["baseline_commit"] != full["commit"]:
        raise ValueError("pstack family baseline differs from full-tree pin")
    baseline = full["files"]
    current = ledger["files"]
    baseline_family = {path: record for path, record in baseline.items() if path.startswith("pstack/")}
    expected_overrides = {}
    for path in set(baseline_family) | set(current):
        validate_path(path)
        before = baseline_family.get(path)
        after = current.get(path)
        if not same_content(before, after):
            expected_overrides[path] = {
                "baseline": ({**before, "source_commit": ledger["baseline_commit"]} if before else None),
                "current": after,
            }
    if ledger.get("overrides") != expected_overrides:
        raise ValueError("pstack family override ledger does not match the historical baseline")
    tree = base / "upstream-tree" / "pstack"
    if tree.is_symlink():
        raise ValueError("pstack source directory is a symlink")
    actual = {f"pstack/{p.relative_to(tree).as_posix()}": p for p in tree.rglob("*") if p.is_file() or p.is_symlink()}
    if set(actual) != set(current):
        raise ValueError("pstack family inventory drift")
    for name, record_data in current.items():
        path = actual[name]
        if path.is_symlink():
            raise ValueError(f"unsupported pstack snapshot symlink: {name}")
        data = path.read_bytes()
        observed = record_from_bytes(data, record_data["mode"])
        if any(observed.get(key) != record_data.get(key) for key in ("mode", "git_blob", "sha256")):
            raise ValueError(f"pstack family content drift: {name}")
    if upstream is not None:
        head = subprocess.check_output(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True).strip()
        if head != ledger["source_commit"]:
            raise ValueError("upstream commit differs from pstack family pin")
        observed = current_inventory(upstream)
        observed = {path: {**record_data, "source_commit": ledger["source_commit"]} for path, record_data in observed.items()}
        if observed != current:
            raise ValueError("upstream pstack inventory differs from family snapshot")
    return {"files": len(current), "overrides": len(expected_overrides), "source_commit": ledger["source_commit"]}
