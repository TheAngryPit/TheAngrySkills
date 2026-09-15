#!/usr/bin/env python3
"""Read-only structural fixture for the held Cursor plugin submission skill.

This does not activate a hook or MCP server, install a plugin, or submit it.
It checks manifest JSON, bounded local paths, discoverable component metadata,
and README presence. YAML validation and marketplace policy remain separate.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_FIELD = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.+)$")
COMPONENTS = {
    "skills": ("skills", "SKILL.md", ("name", "description")),
    "rules": ("rules", None, ("description",)),
    "agents": ("agents", None, ("name", "description")),
    "commands": ("commands", None, ("name", "description")),
}


def _bounded(root: Path, value: str) -> Path | None:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    current = root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            return None
    resolved = current.resolve()
    return resolved if resolved.is_relative_to(root) else None


def _frontmatter_fields(path: Path) -> set[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return set()
    if not lines or lines[0] != "---":
        return set()
    fields: set[str] = set()
    for line in lines[1:]:
        if line == "---":
            return fields
        match = FRONTMATTER_FIELD.match(line)
        if match:
            fields.add(match.group(1))
    return set()


def audit_plugin_fixture(plugin_root: str | Path) -> dict[str, object]:
    """Return local structural findings without reading outside the plugin root."""
    source = Path(plugin_root)
    if source.is_symlink() or not source.is_dir():
        return {"status": "BLOCKED", "issues": ["plugin root missing or symlinked"],
                "review_surfaces": [], "executed_components": False}
    root = source.resolve()
    issues: list[str] = []
    review_surfaces: list[str] = []
    manifest_path = _bounded(root, ".cursor-plugin/plugin.json")
    if manifest_path is None or not manifest_path.is_file():
        return {"status": "BLOCKED", "issues": ["missing bounded .cursor-plugin/plugin.json"],
                "review_surfaces": [], "executed_components": False}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"status": "ERROR", "issues": ["invalid plugin manifest JSON"],
                "review_surfaces": [], "executed_components": False}
    if not isinstance(manifest, dict):
        return {"status": "ERROR", "issues": ["plugin manifest must be an object"],
                "review_surfaces": [], "executed_components": False}
    name = manifest.get("name")
    if not isinstance(name, str) or not NAME.fullmatch(name):
        issues.append("invalid lowercase kebab-case plugin name")
    for field in ("description", "version", "license"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            issues.append(f"missing or empty {field}")
    author = manifest.get("author")
    if not (isinstance(author, str) and author.strip()) and not (
        isinstance(author, dict) and isinstance(author.get("name"), str)
        and author["name"].strip()
    ):
        issues.append("missing or empty author")
    readme = _bounded(root, "README.md")
    if readme is None or not readme.is_file():
        issues.append("missing README.md")
    logo = manifest.get("logo")
    if isinstance(logo, str):
        logo_path = _bounded(root, logo)
        if logo_path is None or not logo_path.is_file():
            issues.append("logo path missing or outside plugin")

    checked_files = 0
    for key, (default_dir, fixed_name, required) in COMPONENTS.items():
        declared = manifest.get(key, f"./{default_dir}/")
        if not isinstance(declared, str):
            issues.append(f"{key} path is not a string")
            continue
        directory = _bounded(root, declared)
        if directory is None:
            issues.append(f"{key} path escapes or links outside plugin")
            continue
        if key in manifest and not directory.is_dir():
            issues.append(f"declared {key} path missing")
            continue
        if not directory.is_dir():
            continue
        if fixed_name:
            files = sorted(directory.glob(f"*/{fixed_name}"))
        elif key == "rules":
            files = sorted((*directory.glob("*.mdc"), *directory.glob("*.md")))
        else:
            files = sorted((*directory.glob("*.md"), *directory.glob("*.txt")))
        if key in manifest and not files:
            issues.append(f"declared {key} has no discoverable files")
        for path in files:
            relative = path.relative_to(root)
            if _bounded(root, str(relative)) != path.resolve() or not path.is_file():
                issues.append(f"unsafe {key} file path: {relative}")
                continue
            checked_files += 1
            missing = set(required) - _frontmatter_fields(path)
            if missing:
                issues.append(f"{relative} missing frontmatter: {', '.join(sorted(missing))}")

    for key, path in (("hooks", "hooks/hooks.json"), ("mcp", "mcp.json")):
        candidate = _bounded(root, path)
        if candidate is None and ((root / path).exists() or (root / path).is_symlink()):
            issues.append(f"unsafe {key} path escapes or links outside plugin")
        elif candidate is not None and candidate.exists():
            review_surfaces.append(key)
    if "mcpServers" in manifest:
        review_surfaces.append("mcpServers")
    if "hooks" in manifest:
        review_surfaces.append("hooks declaration")
    return {
        "status": "ERROR" if issues else "REVIEW_REQUIRED" if review_surfaces else "STRUCTURAL_PASS",
        "plugin_name": name,
        "issues": issues,
        "review_surfaces": sorted(set(review_surfaces)),
        "checked_component_files": checked_files,
        "executed_components": False,
        "submission_recommendation": "not_assessed",
    }
