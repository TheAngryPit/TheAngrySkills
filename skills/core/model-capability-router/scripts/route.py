#!/usr/bin/env python3
"""Validate topology-first routing presets and resolve one Codex execution lane."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_ROUTES = {
    "single",
    "direct_subagent",
    "direct_fleet",
    "field_coordinator",
    "field_fleet",
    "delegated_subtask",
    "parallel_task",
    "max_single",
    "ultra_auto",
}
EFFORTS = {"minimal", "low", "medium", "high", "xhigh", "max", "ultra"}
OPERATOR_ONLY_EFFORTS = {"max", "ultra"}
PROTECTED_COMPUTE_ROLES = {"planner", "reviewer", "auditor", "release-checker"}
EXECUTION_CHANNELS = {
    "current_task": "current_task",
    "native_subagent": "spawn_agent",
    "native_task": "create_thread",
}
SELECTION_MODES = {"pinned", "profile", "role", "vanilla"}
TASK_RELATIONSHIPS = {"delegated_subtask", "independent_parallel_task"}
WORKFLOW_OWNERS = {"native", "gstack"}
GSTACK_PHASE_TOPOLOGIES = {
    "shape": {"single", "direct_subagent"},
    "plan": {"single", "direct_subagent"},
    "implementation": {
        "single",
        "direct_subagent",
        "direct_fleet",
        "field_coordinator",
        "field_fleet",
        "delegated_subtask",
    },
    "review": {"direct_subagent"},
    "qa": {"single", "direct_subagent", "field_coordinator", "delegated_subtask"},
    "ship": {"single"},
    "context": {"single"},
}
GSTACK_PHASE_ROLES = {
    "shape": {"planner", "explorer"},
    "plan": {"planner"},
    "implementation": {
        "explorer",
        "general-worker",
        "coder",
        "debugger",
        "mechanical-debugger",
        "hard-coder",
    },
    "review": {"reviewer", "auditor"},
    "qa": {
        "explorer",
        "general-worker",
        "debugger",
        "mechanical-debugger",
        "reviewer",
        "auditor",
    },
}
GSTACK_FLEET_ROLES = {
    "explorer",
    "general-worker",
    "coder",
    "mechanical-debugger",
    "hard-coder",
}
GSTACK_CONTEXT_REQUIREMENTS = {
    "shape": {"repo_root"},
    "plan": {"repo_root", "plan_path"},
    "implementation": {"repo_root", "plan_path", "branch", "revision", "owned_scope"},
    "review": {"repo_root", "branch", "revision", "diff_scope", "test_evidence"},
    "qa": {"repo_root", "target", "test_evidence"},
    "ship": {"repo_root", "branch", "revision", "review_verdict", "test_evidence"},
    "context": {"repo_root", "branch", "revision"},
}
SUBAGENT_CONTROL_TOOLS = {
    "spawn_agent",
    "followup_task",
    "send_message",
    "wait_agent",
    "list_agents",
    "interrupt_agent",
}


def load_preset(path: str) -> dict:
    with Path(path).open("rb") as handle:
        return tomllib.load(handle)


def selection_spec_errors(name: str, spec: dict) -> list[str]:
    errors = [
        f"{name} is missing {key}"
        for key in ("role", "model", "effort", "proof", "stop_condition")
        if not spec.get(key)
    ]
    if spec.get("effort") not in EFFORTS:
        errors.append(f"{name} has invalid effort")
    return errors


def route_errors(name: str, route: dict, preset: dict) -> list[str]:
    errors: list[str] = []
    for key in ("execution_kind", "channel", "selection_mode"):
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
    elif selection_mode == "pinned":
        errors.extend(selection_spec_errors(name, route))
    elif selection_mode == "profile":
        profile = route.get("profile")
        if not profile:
            errors.append(f"{name} profile selection is missing profile")
        elif profile not in preset.get("profiles", {}):
            errors.append(f"{name} references unknown profile: {profile}")
    elif selection_mode == "role":
        role = route.get("default_role")
        if not role:
            errors.append(f"{name} role selection is missing default_role")
        elif role not in preset.get("roles", {}):
            errors.append(f"{name} references unknown default role: {role}")
    elif any(route.get(key) for key in ("role", "model", "effort", "profile", "default_role")):
        errors.append(f"{name} vanilla selection must not pin a role, model, effort, or profile")

    fleet_profile = route.get("fleet_profile")
    if fleet_profile and fleet_profile not in preset.get("profiles", {}):
        errors.append(f"{name} references unknown fleet profile: {fleet_profile}")
    if name in {"direct_fleet", "field_fleet"} and not fleet_profile:
        errors.append(f"{name} must define fleet_profile")
    if name not in {"direct_fleet", "field_fleet"} and fleet_profile:
        errors.append(f"{name} must not define fleet_profile")
    if name == "field_fleet" and route.get("existing_task_required") is not True:
        errors.append("field_fleet must require an existing verified coordinator")

    errors.extend(lifecycle_errors(name, route, execution_kind))
    if route.get("effort") in OPERATOR_ONLY_EFFORTS and not route.get(
        "operator_authorization_required"
    ):
        errors.append(f"{name} uses max or ultra without operator authorization requirement")
    return errors


def lifecycle_errors(name: str, route: dict, execution_kind: str | None) -> list[str]:
    errors: list[str] = []
    task_only_keys = {
        "lifecycle",
        "reuse_scope",
        "native_relationship",
        "logical_relationship",
        "logical_parent",
        "user_nomenclature",
    }
    if execution_kind != "native_task":
        if any(route.get(key) for key in task_only_keys):
            errors.append(f"{name} task lifecycle and relationship fields require native_task")
        return errors

    if route.get("lifecycle") not in {"ephemeral", "reusable"}:
        errors.append(f"{name} native task must define ephemeral or reusable lifecycle")
    if route.get("lifecycle") == "reusable" and not route.get("reuse_scope"):
        errors.append(f"{name} reusable native task must define reuse_scope")
    if route.get("creation_requires_user_authorization") is not True:
        errors.append(f"{name} native task must require user authorization")
    if route.get("native_relationship") != "peer_user_owned_task":
        errors.append(f"{name} native task must declare peer_user_owned_task")

    relationship = route.get("logical_relationship")
    if relationship not in TASK_RELATIONSHIPS:
        errors.append(f"{name} native task has invalid logical_relationship")
    elif relationship == "delegated_subtask" and not route.get("logical_parent"):
        errors.append(f"{name} delegated subtask must define logical_parent")
    elif relationship == "independent_parallel_task" and route.get("logical_parent"):
        errors.append(f"{name} independent parallel task must not define logical_parent")
    return errors


def errors_for(preset: dict) -> list[str]:
    errors: list[str] = []
    if preset.get("schema_version") != 3:
        errors.append("schema_version must be 3; schemas 1 and 2 are obsolete")

    for name, spec in preset.get("profiles", {}).items():
        errors.extend(selection_spec_errors(f"profiles.{name}", spec))
    for name, spec in preset.get("roles", {}).items():
        errors.extend(
            selection_spec_errors(f"roles.{name}", {**spec, "role": name})
        )
        if (
            name in PROTECTED_COMPUTE_ROLES
            and spec.get("compute_override_allowed") is not False
        ):
            errors.append(f"roles.{name} must prohibit compute overrides")

    routes = preset.get("routes", {})
    missing = sorted(REQUIRED_ROUTES - set(routes))
    if missing:
        errors.append("missing required routes: " + ", ".join(missing))
    for name, route in routes.items():
        errors.extend(route_errors(name, route, preset))

    policy = preset.get("policy", {})
    if not policy.get("max_operator_only") or not policy.get("ultra_operator_only"):
        errors.append("max and ultra must remain operator-only")
    cap = policy.get("max_concurrent_threads_per_session")
    initial = policy.get("fleet_initial_fanout")
    if not isinstance(cap, int) or not 1 <= cap <= 8:
        errors.append("max_concurrent_threads_per_session must be between 1 and 8")
    if not isinstance(initial, int) or not isinstance(cap, int) or not 1 <= initial <= cap:
        errors.append("fleet_initial_fanout must be between 1 and the concurrency cap")
    receipt_age = policy.get("coordinator_receipt_max_age_seconds")
    if not isinstance(receipt_age, int) or not 30 <= receipt_age <= 900:
        errors.append("coordinator receipt maximum age must be between 30 and 900 seconds")
    if policy.get("delegation_depth") != "direct_children_only":
        errors.append("delegation must remain direct-children-only")
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


def parse_role_rejections(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("role rejections must use ROLE=DETAIL")
        role, detail = value.split("=", 1)
        if not role or not detail:
            raise ValueError("role rejection role and detail must not be empty")
        result[role] = detail
    return result


def parse_context_artifacts(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("context artifacts must use KEY=VALUE")
        key, artifact = value.split("=", 1)
        if not key or not artifact:
            raise ValueError("context artifact key and value must not be empty")
        result[key] = artifact
    return result


def load_json_receipt(path: str | None) -> tuple[dict | None, dict | None]:
    if not path:
        return None, None
    receipt_path = Path(path).expanduser().resolve()
    payload = receipt_path.read_bytes()
    receipt = json.loads(payload)
    if not isinstance(receipt, dict):
        raise ValueError("coordinator receipt must be a JSON object")
    evidence = {
        "path": str(receipt_path),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "observed_at": receipt.get("observed_at"),
    }
    return receipt, evidence


def receipt_age_seconds(value: object) -> float:
    if not isinstance(value, str) or not value:
        raise ValueError("coordinator receipt requires observed_at")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    observed = datetime.fromisoformat(normalized)
    if observed.tzinfo is None:
        raise ValueError("coordinator receipt observed_at must include a timezone")
    return (datetime.now(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds()


def canonical_tool_name(value: str) -> str:
    if "__" in value:
        return value.rsplit("__", 1)[1]
    if "." in value:
        return value.rsplit(".", 1)[1]
    return value


def selected_spec(preset: dict, route: dict, args: argparse.Namespace) -> dict:
    if args.vanilla:
        if route["execution_kind"] != "native_subagent":
            raise ValueError("vanilla override is only valid for direct native subagents")
        if args.role or args.model or args.effort:
            raise ValueError("vanilla override cannot be combined with role, model, or effort")
        return {"mode": "vanilla"}
    mode = route["selection_mode"]
    if mode != "role" and (args.role or args.model or args.effort):
        raise ValueError(
            "role, model, and effort overrides require a role-selected route"
        )
    if mode == "vanilla":
        return {"mode": "vanilla"}
    if mode == "pinned":
        spec = dict(route)
    elif mode == "profile":
        spec = dict(preset["profiles"][route["profile"]])
    else:
        role = args.role or route["default_role"]
        if role not in preset.get("roles", {}):
            raise ValueError(f"unknown role profile: {role}")
        spec = dict(preset["roles"][role])
        spec["role"] = role
    if (args.model or args.effort) and spec.get("compute_override_allowed") is False:
        raise ValueError(f"compute override is prohibited for protected role: {spec['role']}")
    if args.model:
        spec["model"] = args.model
    if args.effort:
        spec["effort"] = args.effort
    if spec.get("effort") not in EFFORTS:
        raise ValueError(f"invalid effort: {spec.get('effort')}")
    spec["mode"] = mode
    return spec


def fleet_spec(
    preset: dict,
    route: dict,
    args: argparse.Namespace,
    coordinator_receipt: dict | None,
) -> dict | None:
    profile_name = route.get("fleet_profile")
    if not profile_name:
        if any(
            value is not None
            for value in (
                args.worker_role,
                args.worker_model,
                args.worker_effort,
                args.fanout,
                args.runtime_capacity,
                args.active_subagents,
            )
        ):
            raise ValueError("worker, fanout, and capacity arguments require a Fleet route")
        return None
    if route.get("existing_task_required") and coordinator_receipt is None:
        raise ValueError("field Fleet requires a structured coordinator receipt")
    if coordinator_receipt is not None and (
        args.runtime_capacity is not None or args.active_subagents is not None
    ):
        raise ValueError(
            "field Fleet capacity must come from the coordinator receipt"
        )
    spec = dict(preset["profiles"][profile_name])
    if args.worker_role:
        if args.worker_role not in preset.get("roles", {}):
            raise ValueError(f"unknown worker role profile: {args.worker_role}")
        spec = dict(preset["roles"][args.worker_role])
        spec["role"] = args.worker_role
    if (args.worker_model or args.worker_effort) and spec.get(
        "compute_override_allowed"
    ) is False:
        raise ValueError(
            f"worker compute override is prohibited for protected role: {spec['role']}"
        )
    if args.worker_model:
        spec["model"] = args.worker_model
    if args.worker_effort:
        spec["effort"] = args.worker_effort
    if spec.get("effort") not in EFFORTS:
        raise ValueError(f"invalid worker effort: {spec.get('effort')}")
    policy = preset["policy"]
    requested_fanout = (
        args.fanout
        if args.fanout is not None
        else policy["fleet_initial_fanout"]
    )
    policy_cap = policy["max_concurrent_threads_per_session"]
    if not 1 <= requested_fanout <= policy_cap:
        raise ValueError(f"fanout must be between 1 and {policy_cap}")
    if coordinator_receipt is not None:
        runtime_capacity = coordinator_receipt.get("runtime_capacity")
        active_subagents = coordinator_receipt.get("active_subagents")
    else:
        runtime_capacity = args.runtime_capacity
        active_subagents = args.active_subagents
    if runtime_capacity is None or active_subagents is None:
        raise ValueError(
            "Fleet routing requires runtime capacity and active-subagent evidence"
        )
    if not isinstance(runtime_capacity, int) or runtime_capacity < 1:
        raise ValueError("runtime capacity must be at least 1")
    if not isinstance(active_subagents, int) or active_subagents < 0:
        raise ValueError("active subagents must not be negative")
    free_slots = max(runtime_capacity - active_subagents, 0)
    effective_fanout = min(requested_fanout, policy_cap, free_slots)
    if effective_fanout < 1:
        raise ValueError("Fleet has no free runtime slots")
    spec.update(
        {
            "channel": "spawn_agent",
            "requested_fanout": requested_fanout,
            "fanout": effective_fanout,
            "max_fanout": policy_cap,
            "runtime_capacity": runtime_capacity,
            "active_subagents": active_subagents,
            "free_slots": free_slots,
            "capacity_limited": effective_fanout < requested_fanout,
            "context_inheritance": "none_or_bounded",
            "delegation_depth": "direct_children_only",
        }
    )
    spec["proof_requirement"] = spec.pop("proof")
    return spec


def binding_error(role: str | None, model: str, effort: str, agents: dict[str, dict]) -> str | None:
    if not role:
        return "selection has no agent role"
    agent = agents.get(role)
    if not agent:
        return f"configured agent role is unavailable: {role}"
    pinned_model = agent.get("model")
    pinned_effort = agent.get("model_reasoning_effort")
    if pinned_model and pinned_model != model:
        return f"agent role pins a conflicting model: {role}"
    if pinned_effort and pinned_effort != effort:
        return f"agent role pins a conflicting effort: {role}"
    return None


def runtime_rejection(role: str | None, rejections: dict[str, str]) -> str | None:
    if role in rejections:
        return f"runtime rejected configured agent role: {role} ({rejections[role]})"
    return None


def effective_task_lifecycle(route: dict, args: argparse.Namespace) -> str | None:
    if args.task_lifecycle:
        if route["execution_kind"] != "native_task" or route["selection_mode"] != "role":
            raise ValueError(
                "task lifecycle override requires a role-selected native task route"
            )
        return args.task_lifecycle
    return route.get("lifecycle")


def task_contract_problems(
    route_name: str, route: dict, lifecycle: str | None, args: argparse.Namespace
) -> list[str]:
    if route["execution_kind"] != "native_task":
        if args.existing_task_id or args.reuse_verified or args.logical_parent_id:
            return ["task reuse and logical-parent evidence require a native task route"]
        return []
    problems: list[str] = []
    if route_name == "field_fleet" and not args.existing_task_id:
        problems.append(
            "field Fleet requires an existing live-reconciled field coordinator; resolve field_coordinator first"
        )
    relationship = route["logical_relationship"]
    if relationship == "delegated_subtask" and not args.logical_parent_id:
        problems.append("delegated subtask requires the verified logical parent task ID")
    if relationship == "independent_parallel_task" and args.logical_parent_id:
        problems.append("independent parallel task must not receive a logical parent task ID")
    if args.existing_task_id:
        if lifecycle != "reusable":
            problems.append("ephemeral task routes cannot reuse an existing task")
        if not args.reuse_verified:
            problems.append(
                "existing task reuse requires fresh project, purpose, ownership, relationship, and lifecycle verification"
            )
    elif args.reuse_verified:
        problems.append("reuse verification requires an existing task ID")
    return problems


def coordinator_receipt_problems(
    receipt: dict | None,
    preset: dict,
    selection: dict,
    fleet: dict | None,
    args: argparse.Namespace,
) -> list[str]:
    if args.route != "field_fleet":
        return []
    if receipt is None:
        return ["field Fleet requires a structured coordinator receipt"]
    problems: list[str] = []
    if receipt.get("schema_version") != 1:
        problems.append("coordinator receipt schema_version must be 1")
    try:
        policy_max_age = preset["policy"]["coordinator_receipt_max_age_seconds"]
        if (
            args.max_receipt_age_seconds is not None
            and not 1 <= args.max_receipt_age_seconds <= policy_max_age
        ):
            problems.append(
                "requested receipt freshness window exceeds the preset policy"
            )
        effective_max_age = min(
            args.max_receipt_age_seconds
            if args.max_receipt_age_seconds is not None
            else policy_max_age,
            policy_max_age,
        )
        age = receipt_age_seconds(receipt.get("observed_at"))
        if age < -30 or age > effective_max_age:
            problems.append("coordinator receipt is outside the allowed freshness window")
    except (TypeError, ValueError) as error:
        problems.append(str(error))
    expected = {
        "task_id": args.existing_task_id,
        "logical_parent_id": args.logical_parent_id,
        "role": selection.get("role"),
        "model": selection.get("model"),
        "effort": selection.get("effort"),
        "logical_relationship": "delegated_subtask",
        "lifecycle": "reusable",
    }
    if fleet:
        expected.update(
            {
                "worker_role": fleet.get("role"),
                "worker_model": fleet.get("model"),
                "worker_effort": fleet.get("effort"),
            }
        )
    for key, value in expected.items():
        if receipt.get(key) != value:
            problems.append(f"coordinator receipt {key} does not match the route")
    for key in ("project_verified", "purpose_verified", "ownership_verified"):
        if receipt.get(key) is not True:
            problems.append(f"coordinator receipt requires {key}=true")
    if receipt.get("role_binding") != "matched":
        problems.append("coordinator receipt does not prove its loaded role binding")
    if receipt.get("worker_role_binding") != "matched":
        problems.append("coordinator receipt does not prove the worker role binding")
    if receipt.get("verification_method") != "list_threads+read_thread+coordinator_readback":
        problems.append("coordinator receipt has an unsupported verification method")
    receipt_rejections = receipt.get("runtime_role_rejections")
    if not isinstance(receipt_rejections, dict):
        problems.append("coordinator receipt requires runtime_role_rejections object")
    else:
        for role in (selection.get("role"), fleet.get("role") if fleet else None):
            if role in receipt_rejections:
                problems.append(
                    f"coordinator runtime rejected configured role: {role} ({receipt_rejections[role]})"
                )
    return problems


def workflow_problems(
    route_name: str,
    selection: dict,
    fleet: dict | None,
    args: argparse.Namespace,
    context_artifacts: dict[str, str],
) -> tuple[list[str], list[str]]:
    if args.workflow_owner == "native":
        if args.workflow_phase or context_artifacts:
            return ["workflow phase and context artifacts require the gstack overlay"], []
        return [], []
    if not args.workflow_phase:
        return ["gstack overlay requires workflow_phase"], ["gstack"]
    phase = args.workflow_phase
    allowed_topologies = GSTACK_PHASE_TOPOLOGIES[phase]
    problems: list[str] = []
    if route_name not in allowed_topologies:
        problems.append(f"{route_name} is not allowed during gstack {phase}")
    allowed_roles = GSTACK_PHASE_ROLES.get(phase)
    if allowed_roles and route_name in {"direct_subagent", "delegated_subtask"}:
        if selection.get("role") not in allowed_roles:
            problems.append(
                f"role {selection.get('role')} is not allowed during gstack {phase}"
            )
    if fleet and fleet.get("role") not in GSTACK_FLEET_ROLES:
        problems.append(
            f"role {fleet.get('role')} is not an implementation Fleet role under gstack"
        )
    required_context = GSTACK_CONTEXT_REQUIREMENTS[phase]
    missing_context = sorted(required_context - set(context_artifacts))
    if missing_context:
        problems.append(
            "gstack phase is missing context artifacts: " + ", ".join(missing_context)
        )
    return problems, ["gstack"]


def task_resolution(
    status: str,
    route: dict,
    lifecycle: str | None,
    args: argparse.Namespace,
) -> tuple[str, str | None]:
    if status != "preflight_ready" or route["execution_kind"] != "native_task":
        return status, None
    if args.existing_task_id:
        if lifecycle != "reusable":
            return "blocked", None
        return "preflight_ready", "reuse"
    if args.task_creation_authorized:
        return "preflight_ready", "create"
    return "needs_authorization", "create"


def role_kind(route: dict, selection: dict) -> str:
    if selection["mode"] == "vanilla":
        return "runtime_selected"
    return {
        "native_task": "logical_task_role",
        "native_subagent": "custom_agent_role",
        "current_task": "current_task_role",
    }[route["execution_kind"]]


def public_selection(spec: dict | None) -> dict | None:
    if spec is None:
        return None
    if spec.get("mode") == "vanilla":
        return {"mode": "vanilla"}
    return {
        "mode": spec["mode"],
        "model": spec["model"],
        "effort": spec["effort"],
    }


def cmd_validate(args: argparse.Namespace) -> int:
    errors = errors_for(load_preset(args.preset))
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


def cmd_inventory(args: argparse.Namespace) -> int:
    print(json.dumps({"skills": sorted(skill_names(args.skill_root))}, indent=2))
    return 0


def cmd_migration_preflight(args: argparse.Namespace) -> int:
    legacy_path = Path(args.legacy_preset).expanduser().resolve()
    target_path = Path(args.target_preset).expanduser().resolve()
    legacy_bytes = legacy_path.read_bytes()
    target_bytes = target_path.read_bytes()
    legacy = tomllib.loads(legacy_bytes.decode("utf-8"))
    target = tomllib.loads(target_bytes.decode("utf-8"))
    problems: list[str] = []
    if legacy.get("schema_version") != 2:
        problems.append("legacy preset must use schema_version 2")
    target_errors = errors_for(target)
    if target_errors:
        problems.extend(f"target: {error}" for error in target_errors)
    if legacy.get("name") != target.get("name"):
        problems.append("legacy and target preset names must match")
    result = {
        "status": "preflight_ready" if not problems else "blocked",
        "migration": "schema_2_to_schema_3_coordinated_bundle",
        "legacy": {
            "path": str(legacy_path),
            "version": legacy.get("version"),
            "sha256": hashlib.sha256(legacy_bytes).hexdigest(),
        },
        "target": {
            "path": str(target_path),
            "version": target.get("version"),
            "sha256": hashlib.sha256(target_bytes).hexdigest(),
        },
        "required_release_unit": [
            "router_directory",
            "bundled_schema_3_preset",
            "role_assets",
            "routing_caller",
            "external_preset_mirror",
        ],
        "proof_state": "not_started",
        "problems": problems,
    }
    print(json.dumps(result, indent=2))
    return 0 if not problems else 1


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
    if args.route != "field_fleet" and args.coordinator_receipt:
        raise ValueError(
            "field-coordinator capability evidence is only valid for field_fleet"
        )

    coordinator_receipt, coordinator_receipt_evidence = load_json_receipt(
        args.coordinator_receipt
    )
    selection = selected_spec(preset, route, args)
    fleet = fleet_spec(preset, route, args, coordinator_receipt)
    lifecycle = effective_task_lifecycle(route, args)
    selected_role = selection.get("role")
    restricted_efforts = {selection.get("effort"), fleet.get("effort") if fleet else None}
    if restricted_efforts & OPERATOR_ONLY_EFFORTS and not args.operator_authorized:
        result = {
            "status": "needs_authorization",
            "route": args.route,
            "authorization": "operator_authorization_required",
            "proof_requirement": selection.get("proof"),
            "proof_state": "not_started",
        }
        print(json.dumps(result, indent=2))
        return 1

    channel_models = parse_channel_models(args.channel_model)
    coordinator_channel_models = {
        channel: set(models)
        for channel, models in (coordinator_receipt or {}).get(
            "channel_models", {}
        ).items()
        if isinstance(models, list)
    }
    role_rejections = parse_role_rejections(args.rejected_role)
    context_artifacts = parse_context_artifacts(args.context_artifact)
    raw_available_tools = set(args.available_tool)
    available_tools = {canonical_tool_name(value) for value in raw_available_tools}
    raw_coordinator_tools = set(
        (coordinator_receipt or {}).get("available_tools", [])
    )
    coordinator_tools = {
        canonical_tool_name(value) for value in raw_coordinator_tools
    }
    required_tools = route.get("required_tools", [])
    missing_tools = sorted(set(required_tools) - available_tools)
    agents = agent_configs(args.agent_root)

    problems: list[str] = []
    main_binding: str | None = None
    if selection["mode"] != "vanilla":
        if (
            args.route != "field_fleet"
            and selection["model"] not in channel_models.get(route["channel"], set())
        ):
            problems.append("selected model is unavailable on the required channel")
        rejection = (
            None
            if args.route == "field_fleet"
            else runtime_rejection(selected_role, role_rejections)
        )
        if rejection:
            problems.append(rejection)
        if route["execution_kind"] == "native_subagent":
            main_binding = binding_error(
                selected_role, selection["model"], selection["effort"], agents
            )
            if main_binding:
                problems.append(main_binding)

    fleet_binding: str | None = None
    if fleet:
        fleet_channel_models = (
            coordinator_channel_models
            if args.route == "field_fleet"
            else channel_models
        )
        if fleet["model"] not in fleet_channel_models.get("spawn_agent", set()):
            location = "field coordinator" if args.route == "field_fleet" else "current task"
            problems.append(
                f"fleet worker model is unavailable on {location} spawn_agent"
            )
        if args.route == "field_fleet":
            missing_coordinator_tools = sorted(
                SUBAGENT_CONTROL_TOOLS - coordinator_tools
            )
            if missing_coordinator_tools:
                problems.append(
                    "field coordinator is missing native subagent controls: "
                    + ", ".join(missing_coordinator_tools)
                )
        rejection = (
            None
            if args.route == "field_fleet"
            else runtime_rejection(fleet["role"], role_rejections)
        )
        if rejection:
            problems.append(rejection)
        if args.route == "field_fleet":
            fleet_binding = (
                None
                if (coordinator_receipt or {}).get("worker_role_binding") == "matched"
                else "coordinator receipt does not prove the worker role binding"
            )
        else:
            fleet_binding = binding_error(
                fleet["role"], fleet["model"], fleet["effort"], agents
            )
            if fleet_binding:
                problems.append(fleet_binding)

    problems.extend(task_contract_problems(args.route, route, lifecycle, args))
    problems.extend(
        coordinator_receipt_problems(
            coordinator_receipt, preset, selection, fleet, args
        )
    )

    workflow_errors, workflow_skills = workflow_problems(
        args.route, selection, fleet, args, context_artifacts
    )
    problems.extend(workflow_errors)

    installed = skill_names(args.skill_root)
    capability = preset.get("capabilities", {}).get(args.capability, {}) if args.capability else {}
    required_skills = sorted(set(capability.get("skills", [])) | set(workflow_skills))
    missing_skills = sorted(set(required_skills) - installed)
    status = (
        "preflight_ready"
        if not problems and not missing_skills and not missing_tools
        else "blocked"
    )
    status, task_action = task_resolution(status, route, lifecycle, args)

    result = {
        "status": status,
        "preset": {"name": preset.get("name"), "version": preset.get("version")},
        "route": args.route,
        "execution": {
            "kind": route["execution_kind"],
            "channel": route["channel"],
            "role": selected_role,
            "role_kind": role_kind(route, selection),
        },
        "selection": public_selection(selection),
        "fleet": fleet,
        "workflow": {
            "owner": args.workflow_owner,
            "phase": args.workflow_phase,
            "context_artifacts": context_artifacts,
            "gstack_workflow_authority": args.workflow_owner == "gstack",
            "context_evidence": (
                "caller_supplied_unverified_references"
                if context_artifacts
                else "not_applicable"
            ),
        },
        "proof_requirement": selection.get("proof"),
        "proof_state": "not_started",
        "stop_condition": selection.get("stop_condition"),
        "escalation_trigger": selection.get("escalation_trigger"),
        "capability": args.capability,
        "required_skills": required_skills,
        "missing_skills": missing_skills,
        "required_tools": required_tools,
        "missing_tools": missing_tools,
        "availability_evidence": {
            "channel_models": {
                channel: sorted(models) for channel, models in sorted(channel_models.items())
            },
            "coordinator_channel_models": {
                channel: sorted(models)
                for channel, models in sorted(coordinator_channel_models.items())
            },
            "available_tools": sorted(available_tools),
            "raw_available_tools": sorted(raw_available_tools),
            "coordinator_available_tools": sorted(coordinator_tools),
            "raw_coordinator_available_tools": sorted(raw_coordinator_tools),
            "agent_roots": args.agent_root,
            "agent_config_roots": args.agent_root,
            "skill_roots": args.skill_root,
            "runtime_role_rejections": role_rejections,
            "coordinator_receipt": coordinator_receipt_evidence,
        },
        "binding_evidence": {
            "main": (
                "receipt_claimed_match"
                if args.route == "field_fleet"
                and (coordinator_receipt or {}).get("role_binding") == "matched"
                else "matched"
                if main_binding is None and route["execution_kind"] == "native_subagent"
                else "not_applicable_or_unmatched"
            ),
            "fleet": "matched" if fleet and fleet_binding is None else "not_applicable_or_unmatched",
            "runtime": "rejected" if any(
                role in role_rejections for role in (selected_role, fleet.get("role") if fleet else None)
            ) else "not_observed",
        },
        "gate": capability.get("gate"),
        "lifecycle": lifecycle,
        "reuse_scope": route.get("reuse_scope") if lifecycle == "reusable" else None,
        "native_relationship": route.get("native_relationship"),
        "logical_relationship": route.get("logical_relationship"),
        "logical_parent": route.get("logical_parent"),
        "logical_parent_id": args.logical_parent_id,
        "user_nomenclature": route.get("user_nomenclature"),
        "lifecycle_tools": route.get("lifecycle_tools", []),
        "task_action": task_action,
        "existing_task_id": args.existing_task_id,
        "reuse_evidence": (
            "caller_supplied_structured_coordinator_attestation"
            if args.route == "field_fleet" and coordinator_receipt
            else "caller_attested_preflight"
            if args.existing_task_id and args.reuse_verified
            else "not_applicable"
        ),
        "creation_requires_user_authorization": route.get(
            "creation_requires_user_authorization", False
        ),
        "excluded_operations": ["fork_thread", "handoff_thread"],
    }
    if problems:
        result["error"] = "; ".join(dict.fromkeys(problems))
    elif missing_tools:
        result["error"] = "required native tools are unavailable"
    elif missing_skills:
        result["error"] = "required skills are unavailable"
    elif status == "needs_authorization":
        result["authorization"] = "explicit current user request to create a task"
    print(json.dumps(result, indent=2))
    return 0 if status == "preflight_ready" else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--preset", required=True)
    validate.set_defaults(func=cmd_validate)
    inventory = sub.add_parser("inventory")
    inventory.add_argument("--skill-root", action="append", default=[])
    inventory.set_defaults(func=cmd_inventory)
    migration = sub.add_parser("migration-preflight")
    migration.add_argument("--legacy-preset", required=True)
    migration.add_argument("--target-preset", required=True)
    migration.set_defaults(func=cmd_migration_preflight)
    resolve = sub.add_parser("resolve")
    resolve.add_argument("--preset", required=True)
    resolve.add_argument("--route", required=True)
    resolve.add_argument("--vanilla", action="store_true")
    resolve.add_argument("--role")
    resolve.add_argument("--model")
    resolve.add_argument("--effort")
    resolve.add_argument("--worker-role")
    resolve.add_argument("--worker-model")
    resolve.add_argument("--worker-effort")
    resolve.add_argument("--fanout", type=int)
    resolve.add_argument("--runtime-capacity", type=int)
    resolve.add_argument("--active-subagents", type=int)
    resolve.add_argument(
        "--workflow-owner", choices=sorted(WORKFLOW_OWNERS), default="native"
    )
    resolve.add_argument(
        "--workflow-phase", choices=sorted(GSTACK_PHASE_TOPOLOGIES)
    )
    resolve.add_argument("--context-artifact", action="append", default=[])
    resolve.add_argument(
        "--channel-model",
        action="append",
        default=[],
        help="Fresh channel capability in CHANNEL=MODEL form.",
    )
    resolve.add_argument("--available-tool", action="append", default=[])
    resolve.add_argument("--coordinator-receipt")
    resolve.add_argument("--max-receipt-age-seconds", type=int)
    resolve.add_argument("--skill-root", action="append", default=[])
    resolve.add_argument("--agent-root", action="append", default=[])
    resolve.add_argument(
        "--rejected-role",
        action="append",
        default=[],
        help="Observed runtime rejection in ROLE=DETAIL form.",
    )
    resolve.add_argument("--capability")
    resolve.add_argument(
        "--operator-authorized",
        action="store_true",
        help="Confirm explicit current-task operator authorization for max or ultra.",
    )
    resolve.add_argument("--task-creation-authorized", action="store_true")
    resolve.add_argument("--task-lifecycle", choices=("ephemeral", "reusable"))
    resolve.add_argument("--existing-task-id")
    resolve.add_argument("--reuse-verified", action="store_true")
    resolve.add_argument("--logical-parent-id")
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
