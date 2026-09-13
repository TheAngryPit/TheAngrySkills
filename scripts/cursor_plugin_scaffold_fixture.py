#!/usr/bin/env python3
"""Inactive, explicit-destination Cursor plugin scaffold fixture for Codex.

This preserves the source plugin layout in a disposable local fixture. It does
not install into ~/.cursor, register a marketplace entry, or activate hooks or
MCP servers. Native Codex plugin authoring is a separate contract.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable


NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKER = ".cursor-scaffold-disposable-fixture"
MARKER_CONTENT = "cursor-scaffold-fixture-v1\n"
STATIC_COMPONENTS = {"skills", "rules", "agents", "commands"}
ACTIVE_COMPONENTS = {"hooks", "mcpServers"}


def scaffold_cursor_plugin_fixture(
    fixture_root: str | Path,
    name: str,
    *,
    description: str,
    author: str,
    license_id: str,
    license_text: str,
    components: Iterable[str],
    marketplace: bool = False,
) -> dict[str, object]:
    """Create only static source-format files under a marked empty fixture."""
    root_path = Path(fixture_root)
    if root_path.is_symlink() or not root_path.is_dir():
        return {"status": "BLOCKED", "reason": "fixture root missing or symlinked",
                "created": False}
    root = root_path.resolve()
    marker = root / MARKER
    if marker.is_symlink() or not marker.is_file() or marker.read_text() != MARKER_CONTENT:
        return {"status": "BLOCKED", "reason": "explicit disposable fixture marker missing",
                "created": False}
    if {entry.name for entry in root.iterdir()} != {MARKER}:
        return {"status": "BLOCKED", "reason": "fixture root is not empty",
                "created": False}
    if not isinstance(name, str) or not NAME.fullmatch(name):
        return {"status": "ERROR", "reason": "invalid lowercase kebab-case plugin name",
                "created": False}
    for label, value in (("description", description), ("author", author),
                         ("license_id", license_id), ("license_text", license_text)):
        if not isinstance(value, str) or not value.strip():
            return {"status": "ERROR", "reason": f"missing {label}", "created": False}
    if isinstance(components, (str, bytes)):
        return {"status": "ERROR", "reason": "components must be a sequence", "created": False}
    chosen = tuple(components)
    if not chosen or any(not isinstance(item, str) for item in chosen):
        return {"status": "ERROR", "reason": "components must be nonempty strings",
                "created": False}
    unsupported = sorted(set(chosen) - STATIC_COMPONENTS - ACTIVE_COMPONENTS)
    if unsupported:
        return {"status": "ERROR", "reason": "unsupported components: " + ", ".join(unsupported),
                "created": False}
    active = sorted(set(chosen) & ACTIVE_COMPONENTS)
    if active or marketplace:
        return {"status": "REVIEW_REQUIRED",
                "reason": "hooks, MCP, and marketplace wiring are outside static fixture scope",
                "requested_active_surfaces": active + (["marketplace"] if marketplace else []),
                "created": False}

    destination = root / name
    destination.mkdir()
    manifest_dir = destination / ".cursor-plugin"
    manifest_dir.mkdir()
    manifest = {
        "name": name, "version": "0.1.0", "description": description,
        "author": author, "license": license_id,
    }
    for component in sorted(set(chosen)):
        manifest[component] = f"./{component}/"
    (manifest_dir / "plugin.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (destination / "README.md").write_text(
        f"# {name}\n\n{description.strip()}\n\n"
        "Local fixture only; installation and publication are not assessed.\n\n"
        "Components: " + ", ".join(sorted(set(chosen))) + "\n",
        encoding="utf-8",
    )
    (destination / "LICENSE").write_text(license_text, encoding="utf-8")
    for component in sorted(set(chosen)):
        directory = destination / component
        directory.mkdir()
        if component == "skills":
            skill = directory / name
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                f"---\nname: {name}\n"
                f"description: {json.dumps(description.strip(), ensure_ascii=False)}\n"
                "---\n\n"
                f"# {name}\n\nStatic fixture instructions.\n", encoding="utf-8"
            )
        elif component == "rules":
            (directory / "quality.mdc").write_text(
                "---\ndescription: Static fixture quality guidance\n"
                "alwaysApply: false\n---\n\n# Quality\n",
                encoding="utf-8",
            )
        elif component == "agents":
            (directory / "reviewer.md").write_text(
                "---\nname: reviewer\ndescription: Static fixture reviewer\n"
                "---\n\n# Reviewer\n", encoding="utf-8"
            )
        else:
            (directory / "check.md").write_text(
                "---\nname: check\ndescription: Static fixture command\n"
                "---\n\n# Check\n", encoding="utf-8"
            )
    return {"status": "FIXTURE_ONLY", "created": True,
            "destination": str(destination), "components": tuple(sorted(set(chosen))),
            "active_surfaces": [], "marketplace_wired": False,
            "global_install": False}
