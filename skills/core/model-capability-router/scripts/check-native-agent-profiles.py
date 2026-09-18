#!/usr/bin/env python3
"""Validate the public native agent-profile assets against pinned pstack roles."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tomllib
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_ROOT.parents[2]
ASSET_ROOT = SKILL_ROOT / "assets/agents"
SOURCE_ROOT = REPO_ROOT / "sources/cursor-plugins/snapshot/pstack/agents"
PINNED_SOURCE_SHA256 = {
    "comment-sicko": "c0fd0383008da45fc78cfac17b9007d62c42f87ad1c8d5c2fb658b1fd01f7c82",
    "poteto-agent": "c3850be1b97bc97cec0568ed8b26d04e7693c4e07868137c58fe546d37f288e9",
}

PROFILES = {
    "comment-sicko": {
        "source": "comment-sicko.md",
        "required": (
            "I hate comments.",
            "MUST KILL",
            "Report only.",
            "cursor-how",
            "cursor-why",
            "required adapted skill",
        ),
    },
    "poteto-agent": {
        "source": "poteto-agent.md",
        "required": (
            "full agent style",
            "cursor-poteto-mode",
            "cursor-principle-",
            "native Codex subagent delegation",
            "reuse the existing poteto-agent",
            "required adapted skill",
        ),
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned_body(source_text: str) -> str:
    if not source_text.startswith("---\n"):
        raise ValueError("pinned agent source is missing frontmatter")
    _, _, body = source_text.partition("\n---\n")
    return body.lstrip("\n")


def adapted_body(name: str, source_text: str) -> str:
    body = pinned_body(source_text)
    if name == "comment-sicko":
        body = body.replace(
            "I run `/how`, `/why`, or both from the **how** and **why** skills",
            "I run `cursor-how`, `cursor-why`, or both from the adapted **cursor-how** and **cursor-why** skills",
        )
        return body + "\nIf a required adapted skill is unavailable, report the exact missing dependency to the coordinator; do not silently substitute a different workflow.\n"
    body = body.replace("Read the `poteto-mode` skill's", "Read the `cursor-poteto-mode` skill's")
    body = body.replace("leaf `principle-*` skill", "leaf `cursor-principle-*` skill")
    return body + "\nUse native Codex subagent delegation. The coordinator should reuse the existing poteto-agent for this conversation through native follow-up tools; spawn this named agent only when no suitable instance exists. Native asynchronous delegation replaces Cursor is_background.\n\nIf a required adapted skill is unavailable, report the exact missing dependency to the coordinator; do not silently substitute a different workflow.\n"


def validate_profile(
    name: str,
    installed_root: Path | None,
    source_root: Path,
    require_source: bool,
) -> dict[str, object]:
    profile_path = ASSET_ROOT / f"{name}.toml"
    source_path = source_root / str(PROFILES[name]["source"])
    if not profile_path.is_file():
        raise ValueError(f"missing public profile asset: {profile_path}")
    if require_source and not source_path.is_file():
        raise ValueError(f"missing pinned source role: {source_path}")

    profile_text = profile_path.read_text()
    parsed = tomllib.loads(profile_text)
    if set(parsed) != {"name", "description", "developer_instructions"}:
        raise ValueError(f"{name}: unexpected TOML top-level keys: {sorted(parsed)}")
    if parsed["name"] != name:
        raise ValueError(f"{name}: TOML name does not match filename")
    if not all(isinstance(parsed[key], str) and parsed[key].strip() for key in parsed):
        raise ValueError(f"{name}: name, description and instructions must be non-empty strings")
    if "subagent_type:" in profile_text or "generalPurpose" in profile_text:
        raise ValueError(f"{name}: Cursor agent-type syntax leaked into native profile")
    for phrase in PROFILES[name]["required"]:
        if phrase not in profile_text:
            raise ValueError(f"{name}: missing adapted semantic anchor: {phrase}")
    source_available = source_path.is_file()
    observed_source_sha256 = digest(source_path) if source_available else None
    if source_available:
        source_text = source_path.read_text()
        if observed_source_sha256 != PINNED_SOURCE_SHA256[name]:
            raise ValueError(f"{name}: pinned source hash does not match the reviewed source")
        if parsed["developer_instructions"] != adapted_body(name, source_text):
            raise ValueError(f"{name}: native instructions differ from the exact reviewed adaptation")
    elif require_source:
        raise ValueError(f"missing pinned source role: {source_path}")

    installed_match: bool | None = None
    installed_path: str | None = None
    if installed_root is not None:
        if installed_root.is_symlink():
            raise ValueError(f"{installed_root}: installed directory must not be a symlink")
        if installed_root.exists() and not installed_root.is_dir():
            raise ValueError(f"{installed_root}: installed target must be a directory")
        installed = installed_root / f"{name}.toml"
        if installed.is_symlink():
            raise ValueError(f"{installed}: installed profile must not be a symlink")
        installed_path = str(installed)
        installed_match = installed.is_file() and installed.read_bytes() == profile_path.read_bytes()

    return {
        "name": name,
        "asset": str(profile_path.relative_to(SKILL_ROOT)),
        "asset_sha256": digest(profile_path),
        "pinned_source": str(source_path),
        "pinned_source_sha256": PINNED_SOURCE_SHA256[name],
        "observed_source_sha256": observed_source_sha256,
        "source_available": source_available,
        "source_comparison": "exact normalized body adaptation" if source_available else "not_observed",
        "installed_path": installed_path,
        "installed_byte_match": installed_match,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--installed-dir",
        type=Path,
        help="optional existing native-agent directory to compare byte-for-byte",
    )
    parser.add_argument(
        "--pinned-source-root",
        type=Path,
        default=SOURCE_ROOT,
        help="optional read-only root containing pinned pstack/agent Markdown files",
    )
    parser.add_argument(
        "--require-pinned-source",
        action="store_true",
        help="fail when the pinned source files are unavailable",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="copy the validated public profiles to --installed-dir",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="allow replacing an existing differing profile when installing",
    )
    args = parser.parse_args()
    if args.replace and not args.install:
        parser.error("--replace requires --install")
    if args.install and args.installed_dir is None:
        parser.error("--install requires --installed-dir")
    try:
        profiles = [
            validate_profile(
                name,
                args.installed_dir,
                args.pinned_source_root,
                args.require_pinned_source,
            )
            for name in PROFILES
        ]
        if args.install:
            args.installed_dir.mkdir(parents=True, exist_ok=True)
            for profile in profiles:
                source = SKILL_ROOT / str(profile["asset"])
                target = args.installed_dir / f"{profile['name']}.toml"
                if target.is_symlink():
                    raise ValueError(f"{target}: installed profile must not be a symlink")
                if target.exists() and target.read_bytes() != source.read_bytes() and not args.replace:
                    raise ValueError(
                        f"{target}: existing profile differs; pass --replace for an explicit replacement"
                    )
            for profile in profiles:
                source = SKILL_ROOT / str(profile["asset"])
                target = args.installed_dir / f"{profile['name']}.toml"
                if not target.exists() or target.read_bytes() != source.read_bytes():
                    shutil.copy2(source, target)
            profiles = [
                validate_profile(
                    name,
                    args.installed_dir,
                    args.pinned_source_root,
                    args.require_pinned_source,
                )
                for name in PROFILES
            ]
    except (OSError, tomllib.TOMLDecodeError, ValueError) as error:
        print(f"native agent profiles: {error}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "profiles": profiles,
                "source_root": str(args.pinned_source_root),
                "live_session_load": "not_observed",
                "native_dependencies": "availability must be checked by the host session",
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
