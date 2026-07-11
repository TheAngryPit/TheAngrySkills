#!/usr/bin/env python3
"""Validate routing presets, inventory skill roots, and resolve one route."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path


REQUIRED_ROUTES = {
    "micro", "exploration", "bounded_worker", "coordination", "debugging",
    "planning", "hard_implementation", "review", "audit", "release",
    "memory_worker", "memory_curator",
}
EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}


def load_preset(path: str) -> dict:
    with Path(path).open("rb") as handle:
        return tomllib.load(handle)


def errors_for(preset: dict) -> list[str]:
    errors: list[str] = []
    if preset.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    routes = preset.get("routes", {})
    missing = sorted(REQUIRED_ROUTES - set(routes))
    if missing:
        errors.append("missing required routes: " + ", ".join(missing))
    for name, route in routes.items():
        for key in ("role", "model", "effort", "proof"):
            if not route.get(key):
                errors.append(f"{name} is missing {key}")
        if route.get("effort") not in EFFORTS:
            errors.append(f"{name} has invalid effort")
        if bool(route.get("fallback_model")) != bool(route.get("fallback_effort")):
            errors.append(f"{name} fallback model and effort must be paired")
    policy = preset.get("policy", {})
    if not policy.get("max_operator_only") or not policy.get("ultra_operator_only"):
        errors.append("max and ultra must remain operator-only")
    return errors


def skill_names(roots: list[str]) -> set[str]:
    names: set[str] = set()
    for value in roots:
        root = Path(value).expanduser().resolve()
        if not root.is_dir():
            continue
        for skill in root.rglob("SKILL.md"):
            name = skill.parent.name
            for line in skill.read_text(encoding="utf-8", errors="replace").splitlines()[:30]:
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip("'\"")
                    break
            names.add(name)
    return names


def cmd_validate(args: argparse.Namespace) -> int:
    errors = errors_for(load_preset(args.preset))
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


def cmd_inventory(args: argparse.Namespace) -> int:
    print(json.dumps({"skills": sorted(skill_names(args.skill_root))}, indent=2))
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    preset = load_preset(args.preset)
    errors = errors_for(preset)
    if errors:
        print(json.dumps({"status": "blocked", "errors": errors}, indent=2))
        return 1
    route = preset["routes"].get(args.route)
    if not route:
        print(json.dumps({"status": "blocked", "errors": ["unknown route"]}, indent=2))
        return 1
    available_models = set(args.available_model)
    selected = None
    fallback_used = False
    if route["model"] in available_models:
        selected = {"model": route["model"], "effort": route["effort"]}
    elif route.get("fallback_model") in available_models:
        selected = {"model": route["fallback_model"], "effort": route["fallback_effort"]}
        fallback_used = True
    installed = skill_names(args.skill_root)
    capability = preset.get("capabilities", {}).get(args.capability, {}) if args.capability else {}
    required_skills = capability.get("skills", [])
    missing_skills = sorted(set(required_skills) - installed)
    status = "ready" if selected and not missing_skills else "blocked"
    result = {
        "status": status,
        "preset": {"name": preset.get("name"), "version": preset.get("version")},
        "route": args.route,
        "role": route["role"],
        "selection": selected,
        "fallback_used": fallback_used,
        "proof": route["proof"],
        "capability": args.capability,
        "required_skills": required_skills,
        "missing_skills": missing_skills,
        "gate": capability.get("gate"),
    }
    if not selected:
        result["error"] = "no listed model is available"
    print(json.dumps(result, indent=2))
    return 0 if status == "ready" else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--preset", required=True)
    validate.set_defaults(func=cmd_validate)
    inventory = sub.add_parser("inventory")
    inventory.add_argument("--skill-root", action="append", default=[])
    inventory.set_defaults(func=cmd_inventory)
    resolve = sub.add_parser("resolve")
    resolve.add_argument("--preset", required=True)
    resolve.add_argument("--route", required=True)
    resolve.add_argument("--available-model", action="append", default=[])
    resolve.add_argument("--skill-root", action="append", default=[])
    resolve.add_argument("--capability")
    resolve.set_defaults(func=cmd_resolve)
    return root


def main() -> int:
    try:
        args = parser().parse_args()
        return args.func(args)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
