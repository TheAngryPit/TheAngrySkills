#!/usr/bin/env python3
"""Validate channel-aware routing presets and resolve one execution lane."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path


REQUIRED_ROUTES = {
    "master_orchestration",
    "micro",
    "vanilla_subagent",
    "exploration",
    "bounded_worker",
    "bounded_coding",
    "deep_batch_worker",
    "exceptional_coding_batch",
    "coordination",
    "debugging",
    "mechanical_debugging",
    "planning",
    "hard_implementation",
    "review",
    "audit",
    "release",
    "luna_subtask",
    "luna_worker",
    "memory_worker",
    "memory_curator",
}
EFFORTS = {"minimal", "low", "medium", "high", "xhigh", "max", "ultra"}
OPERATOR_ONLY_EFFORTS = {"max", "ultra"}
EXECUTION_CHANNELS = {
    "current_task": "current_task",
    "native_subagent": "spawn_agent",
    "native_task": "create_thread",
}
SELECTION_MODES = {"pinned", "vanilla"}


def load_preset(path: str) -> dict:
    with Path(path).open("rb") as handle:
        return tomllib.load(handle)


def route_errors(name: str, route: dict) -> list[str]:
    errors: list[str] = []
    for key in ("execution_kind", "channel", "selection_mode", "proof", "stop_condition"):
        if not route.get(key):
            errors.append(f"{name} is missing {key}")
    execution_kind = route.get("execution_kind")
    expected_channel = EXECUTION_CHANNELS.get(execution_kind)
    if not expected_channel:
        errors.append(f"{name} has invalid execution_kind")
    elif route.get("channel") != expected_channel:
        errors.append(f"{name} channel must be {expected_channel} for {execution_kind}")
    selection_mode = route.get("selection_mode")
    if selection_mode not in SELECTION_MODES:
        errors.append(f"{name} has invalid selection_mode")
    if selection_mode == "pinned":
        errors.extend(pinned_selection_errors(name, route))
    elif any(route.get(key) for key in ("role", "model", "effort")):
        errors.append(f"{name} vanilla selection must not pin role, model, or effort")
    errors.extend(fallback_errors(name, route, selection_mode))
    errors.extend(lifecycle_errors(name, route, execution_kind))
    return errors


def pinned_selection_errors(name: str, route: dict) -> list[str]:
    errors = [f"{name} is missing {key}" for key in ("role", "model", "effort") if not route.get(key)]
    if route.get("effort") not in EFFORTS:
        errors.append(f"{name} has invalid effort")
    return errors


def fallback_errors(name: str, route: dict, selection_mode: str | None) -> list[str]:
    errors: list[str] = []
    fallback_keys = ("fallback_role", "fallback_model", "fallback_effort")
    if selection_mode == "vanilla" and any(route.get(key) for key in fallback_keys):
        errors.append(f"{name} vanilla selection must not define a pinned fallback")
    if bool(route.get("fallback_model")) != bool(route.get("fallback_effort")):
        errors.append(f"{name} fallback model and effort must be paired")
    if route.get("fallback_model") and not route.get("fallback_role"):
        errors.append(f"{name} fallback route must name fallback_role")
    if route.get("fallback_effort") and route.get("fallback_effort") not in EFFORTS:
        errors.append(f"{name} has invalid fallback effort")
    route_efforts = {route.get("effort"), route.get("fallback_effort")}
    if route_efforts & OPERATOR_ONLY_EFFORTS and not route.get("operator_authorization_required"):
        errors.append(f"{name} uses max or ultra without operator authorization requirement")
    return errors


def lifecycle_errors(name: str, route: dict, execution_kind: str | None) -> list[str]:
    errors: list[str] = []
    if execution_kind != "native_task":
        if route.get("lifecycle"):
            errors.append(f"{name} lifecycle is only valid for native tasks")
        return errors
    if route.get("lifecycle") not in {"ephemeral", "reusable"}:
        errors.append(f"{name} native task must define ephemeral or reusable lifecycle")
    if route.get("lifecycle") == "reusable" and not route.get("reuse_scope"):
        errors.append(f"{name} reusable native task must define reuse_scope")
    if route.get("creation_requires_user_authorization") is not True:
        errors.append(f"{name} native task must require user authorization")
    return errors


def errors_for(preset: dict) -> list[str]:
    errors: list[str] = []
    if preset.get("schema_version") != 2:
        errors.append("schema_version must be 2; schema 1 is obsolete")
    routes = preset.get("routes", {})
    missing = sorted(REQUIRED_ROUTES - set(routes))
    if missing:
        errors.append("missing required routes: " + ", ".join(missing))
    for name, route in routes.items():
        errors.extend(route_errors(name, route))
    policy = preset.get("policy", {})
    if not policy.get("max_operator_only") or not policy.get("ultra_operator_only"):
        errors.append("max and ultra must remain operator-only")
    if policy.get("visual_badges_authoritative") is not False:
        errors.append("visual badges must remain non-authoritative")
    if policy.get("fork_thread_allowed") is not False:
        errors.append("fork_thread must be excluded from model routing")
    if policy.get("handoff_thread_routing_allowed") is not False:
        errors.append("handoff_thread must remain outside model routing")
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


def agent_configs(roots: list[str]) -> dict[str, dict]:
    agents: dict[str, dict] = {}
    for value in roots:
        root = Path(value).expanduser().resolve()
        if not root.is_dir():
            continue
        for agent_file in root.glob("*.toml"):
            if agent_file.name.startswith("."):
                continue
            config = tomllib.loads(agent_file.read_text(encoding="utf-8"))
            name = config.get("name")
            if name:
                agents[name] = config
    return agents


def parse_channel_models(values: list[str]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("channel models must use CHANNEL=MODEL")
        channel, model = value.split("=", 1)
        if channel not in set(EXECUTION_CHANNELS.values()):
            raise ValueError(f"unknown model channel: {channel}")
        if not model:
            raise ValueError("channel model must not be empty")
        result.setdefault(channel, set()).add(model)
    return result


def canonical_tool_name(value: str) -> str:
    """Normalize runtime namespaces while retaining canonical native tool names."""
    if "__" in value:
        return value.rsplit("__", 1)[1]
    if "." in value:
        return value.rsplit(".", 1)[1]
    return value


def binding_error(route: dict, agents: dict[str, dict], *, fallback: bool = False) -> str | None:
    if route.get("execution_kind") != "native_subagent":
        return None
    prefix = "fallback_" if fallback else ""
    role = route.get(f"{prefix}role")
    model = route.get(f"{prefix}model")
    effort = route.get(f"{prefix}effort")
    if not role:
        return "fallback route is not configured" if fallback else "route has no agent role"
    agent = agents.get(role)
    if not agent:
        return f"configured agent role is unavailable: {role}"
    if (agent.get("model"), agent.get("model_reasoning_effort")) != (model, effort):
        return f"agent role does not match route model/effort: {role}"
    return None


def select_route(
    route: dict, channel_models: dict[str, set[str]], agents: dict[str, dict]
) -> tuple[dict | None, str | None, bool, str | None]:
    selected_role = route.get("role")
    if route["selection_mode"] == "vanilla":
        return {"mode": "vanilla"}, selected_role, False, None
    binding = binding_error(route, agents)
    available_models = channel_models.get(route["channel"], set())
    if not binding and route["model"] in available_models:
        selected = {
            "mode": "pinned",
            "model": route["model"],
            "effort": route["effort"],
        }
        return selected, selected_role, False, None
    fallback_binding = None
    if route.get("fallback_model"):
        fallback_binding = binding_error(route, agents, fallback=True)
    if route.get("fallback_model") in available_models and not fallback_binding:
        selected = {
            "mode": "pinned",
            "model": route["fallback_model"],
            "effort": route["fallback_effort"],
        }
        return selected, route["fallback_role"], True, None
    return None, selected_role, False, binding or fallback_binding


def task_resolution(
    status: str, route: dict, args: argparse.Namespace
) -> tuple[str, str | None]:
    if status != "ready" or route["execution_kind"] != "native_task":
        return status, None
    if args.existing_task_id:
        if route["lifecycle"] == "reusable":
            return "ready", "reuse"
        return "blocked", None
    if args.task_creation_authorized:
        return "ready", "create"
    return "needs_authorization", "create"


def role_kind(route: dict) -> str:
    if route["selection_mode"] == "vanilla":
        return "runtime_selected"
    return {
        "native_task": "logical_task_role",
        "native_subagent": "custom_agent_role",
        "current_task": "current_task_role",
    }[route["execution_kind"]]


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
    if route.get("operator_authorization_required") and not args.operator_authorized:
        result = {
            "status": "needs_authorization",
            "route": args.route,
            "authorization": "operator_authorization_required",
            "proof": route["proof"],
        }
        print(json.dumps(result, indent=2))
        return 1

    channel_models = parse_channel_models(args.channel_model)
    raw_available_tools = set(args.available_tool)
    available_tools = {canonical_tool_name(value) for value in raw_available_tools}
    required_tools = route.get("required_tools", [])
    missing_tools = sorted(set(required_tools) - available_tools)
    agents = agent_configs(args.agent_root)
    selected, selected_role, fallback_used, binding = select_route(
        route, channel_models, agents
    )
    installed = skill_names(args.skill_root)
    capability = preset.get("capabilities", {}).get(args.capability, {}) if args.capability else {}
    required_skills = capability.get("skills", [])
    missing_skills = sorted(set(required_skills) - installed)
    status = "ready" if selected and not missing_skills and not missing_tools else "blocked"
    status, task_action = task_resolution(status, route, args)
    result = {
        "status": status,
        "preset": {"name": preset.get("name"), "version": preset.get("version")},
        "route": args.route,
        "execution": {
            "kind": route["execution_kind"],
            "channel": route["channel"],
            "role": selected_role,
            "role_kind": role_kind(route),
        },
        "selection": selected,
        "fallback_used": fallback_used,
        "proof": route["proof"],
        "stop_condition": route.get("stop_condition"),
        "escalation_trigger": route.get("escalation_trigger"),
        "capability": args.capability,
        "required_skills": required_skills,
        "missing_skills": missing_skills,
        "required_tools": required_tools,
        "missing_tools": missing_tools,
        "availability_evidence": {
            "channel_models": {
                channel: sorted(models)
                for channel, models in sorted(channel_models.items())
            },
            "available_tools": sorted(available_tools),
            "raw_available_tools": sorted(raw_available_tools),
            "agent_roots": args.agent_root,
            "skill_roots": args.skill_root,
        },
        "gate": capability.get("gate"),
        "lifecycle": route.get("lifecycle"),
        "reuse_scope": route.get("reuse_scope"),
        "lifecycle_tools": route.get("lifecycle_tools", []),
        "task_action": task_action,
        "existing_task_id": args.existing_task_id,
        "creation_requires_user_authorization": route.get(
            "creation_requires_user_authorization", False
        ),
        "excluded_operations": ["fork_thread", "handoff_thread"],
    }
    if not selected:
        result["error"] = binding or "no model is available on the required channel"
    elif missing_tools:
        result["error"] = "required native tools are unavailable"
    elif route["execution_kind"] == "native_task" and args.existing_task_id and route["lifecycle"] != "reusable":
        result["error"] = "ephemeral task routes cannot reuse an existing task"
    elif status == "needs_authorization":
        result["authorization"] = "explicit current user request to create a task"
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
    resolve.add_argument(
        "--channel-model",
        action="append",
        default=[],
        help="Fresh channel capability in CHANNEL=MODEL form.",
    )
    resolve.add_argument("--available-tool", action="append", default=[])
    resolve.add_argument("--skill-root", action="append", default=[])
    resolve.add_argument("--agent-root", action="append", default=[])
    resolve.add_argument("--capability")
    resolve.add_argument(
        "--operator-authorized",
        action="store_true",
        help="Confirm explicit current-task operator authorization for a max or ultra route.",
    )
    resolve.add_argument("--task-creation-authorized", action="store_true")
    resolve.add_argument("--existing-task-id")
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
