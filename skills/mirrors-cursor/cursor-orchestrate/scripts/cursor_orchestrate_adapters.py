"""Bounded, non-executing contracts for native Codex Cloud orchestration.

The adapter validates a coordinator-owned dependency graph and builds reviewable
``codex cloud`` argument tuples. It never invokes the CLI, reads credentials,
creates tasks, applies diffs, or runs the bundled Cursor runtime.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


class OrchestrateAdapterError(ValueError):
    """The orchestration plan, authorization, or readback is malformed."""


_ROLES = frozenset({"planner", "subplanner", "worker", "verifier"})
_HANDOFF_STATUSES = frozenset({"PASS", "ISSUES", "BLOCKED"})
_SAFE_IDENTIFIER_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:/"
)
_FORBIDDEN_TEXT_MARKERS = (
    "/.git",
    "/.ssh",
    "api_key",
    "authorization:",
    "bearer ",
    "password",
    "secret",
    "slack_bot_token",
    "cursor_api_key",
)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OrchestrateAdapterError(f"{label} must be non-empty text")
    if any(ord(char) < 32 for char in value if char not in "\n\t"):
        raise OrchestrateAdapterError(f"{label} contains a control character")
    text = value.strip()
    folded = text.casefold()
    if any(marker in folded for marker in _FORBIDDEN_TEXT_MARKERS):
        raise OrchestrateAdapterError(f"{label} contains a forbidden private-data marker")
    return text


def _task_id(value: Any) -> str:
    task_id = _text(value, "task_id")
    if any(char not in _SAFE_IDENTIFIER_CHARS - frozenset("./:") for char in task_id):
        raise OrchestrateAdapterError("task_id must be a simple stable identifier")
    return task_id


def _cli_identifier(value: Any, label: str) -> str:
    identifier = _text(value, label)
    if any(char not in _SAFE_IDENTIFIER_CHARS for char in identifier):
        raise OrchestrateAdapterError(f"{label} must be a safe CLI identifier")
    if identifier.startswith("-"):
        raise OrchestrateAdapterError(f"{label} cannot begin with a dash")
    return identifier


def prepare_local_plan(
    goal: str,
    tasks: Iterable[Mapping[str, Any]],
    *,
    max_children: int = 4,
) -> dict[str, Any]:
    """Validate a bounded dependency graph without dispatching any task."""

    goal = _text(goal, "goal")
    if not isinstance(max_children, int) or isinstance(max_children, bool) or not 1 <= max_children <= 8:
        raise OrchestrateAdapterError("max_children must be an integer from 1 through 8")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in tasks:
        if not isinstance(raw, Mapping):
            raise OrchestrateAdapterError("each task must be a mapping")
        task_id = _task_id(raw.get("task_id"))
        if task_id in seen:
            raise OrchestrateAdapterError(f"duplicate task_id: {task_id}")
        seen.add(task_id)
        role = _text(raw.get("role"), f"role for {task_id}")
        if role not in _ROLES:
            raise OrchestrateAdapterError(f"unsupported role for {task_id}: {role}")
        acceptance = _text(raw.get("acceptance"), f"acceptance for {task_id}")
        dependencies = raw.get("depends_on", ())
        if isinstance(dependencies, (str, bytes)):
            raise OrchestrateAdapterError(f"depends_on for {task_id} must be a sequence")
        dependency_ids = tuple(_task_id(item) for item in dependencies)
        if len(set(dependency_ids)) != len(dependency_ids):
            raise OrchestrateAdapterError(f"duplicate dependency for {task_id}")
        normalized.append(
            {
                "task_id": task_id,
                "role": role,
                "depends_on": dependency_ids,
                "acceptance": acceptance,
            }
        )

    if not normalized:
        raise OrchestrateAdapterError("plan needs at least one task")
    planners = [task for task in normalized if task["role"] == "planner"]
    if len(planners) != 1:
        raise OrchestrateAdapterError("plan needs exactly one planner")
    planner_id = planners[0]["task_id"]
    if planners[0]["depends_on"]:
        raise OrchestrateAdapterError("planner cannot depend on a child task")

    dependencies_by_id = {task["task_id"]: task["depends_on"] for task in normalized}
    for task_id, dependencies in dependencies_by_id.items():
        missing = set(dependencies) - seen
        if missing:
            raise OrchestrateAdapterError(f"unknown dependency for {task_id}: {sorted(missing)}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise OrchestrateAdapterError(f"cyclic dependency involving {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in dependencies_by_id[task_id]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in dependencies_by_id:
        visit(task_id)
    child_count = sum(task["role"] != "planner" for task in normalized)
    if child_count > max_children:
        raise OrchestrateAdapterError("plan exceeds max_children")

    return {
        "status": "PLAN_READY",
        "goal": goal,
        "root_task": planner_id,
        "max_children": max_children,
        "tasks": tuple(normalized),
        "cloud_execution": "ENVIRONMENT_REQUIRED",
        "dispatch_performed": False,
        "external_writes": False,
    }


def ready_task_ids(plan: Mapping[str, Any], completed: Iterable[str] = ()) -> tuple[str, ...]:
    """Return dependency-ready task IDs in stable plan order."""

    tasks = plan.get("tasks")
    if plan.get("status") != "PLAN_READY" or not isinstance(tasks, (tuple, list)):
        raise OrchestrateAdapterError("ready tasks require a validated local plan")
    plan = prepare_local_plan(
        plan.get("goal"), tasks, max_children=plan.get("max_children", 4)
    )
    tasks = plan["tasks"]
    expected = {task["task_id"] for task in tasks}
    completed_ids = {_task_id(item) for item in completed}
    unknown = completed_ids - expected
    if unknown:
        raise OrchestrateAdapterError(f"completed task is outside the plan: {sorted(unknown)}")
    return tuple(
        task["task_id"]
        for task in tasks
        if task["task_id"] not in completed_ids
        and set(task["depends_on"]).issubset(completed_ids)
    )


def build_codex_cloud_dispatch_batch(
    plan: Mapping[str, Any],
    *,
    environment_id: str,
    branch: str,
    completed: Iterable[str] = (),
    authorization_granted: bool = False,
) -> dict[str, Any]:
    """Build shell-free ``codex cloud exec`` argv for dependency-ready tasks."""

    if authorization_granted is not True:
        raise OrchestrateAdapterError("cloud task creation requires out-of-band authorization")
    environment_id = _cli_identifier(environment_id, "environment_id")
    branch = _cli_identifier(branch, "branch")
    validated_plan = prepare_local_plan(
        plan.get("goal"), plan.get("tasks", ()), max_children=plan.get("max_children", 4)
    )
    tasks = {task["task_id"]: task for task in validated_plan["tasks"]}
    ready = ready_task_ids(validated_plan, completed)
    commands: list[tuple[str, ...]] = []
    for task_id in ready:
        task = tasks[task_id]
        prompt = (
            f"Goal: {validated_plan['goal']}\n"
            f"Task: {task_id}\n"
            f"Role: {task['role']}\n"
            f"Acceptance: {task['acceptance']}\n"
            "Return a concise structured handoff with status, evidence, and artifact identity."
        )
        commands.append(
            (
                "codex",
                "cloud",
                "exec",
                "--env",
                environment_id,
                "--attempts",
                "1",
                "--branch",
                branch,
                prompt,
            )
        )
    return {
        "status": "DISPATCH_REVIEW_READY",
        "environment_id": environment_id,
        "branch": branch,
        "ready_task_ids": ready,
        "commands": tuple(commands),
        "dispatch_performed": False,
        "external_writes": False,
    }


def parse_codex_cloud_list(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize the documented ``codex cloud list --json`` response."""

    if not isinstance(payload, Mapping):
        raise OrchestrateAdapterError("cloud list payload must be a mapping")
    raw_tasks = payload.get("tasks")
    if not isinstance(raw_tasks, Sequence) or isinstance(raw_tasks, (str, bytes)):
        raise OrchestrateAdapterError("cloud list payload needs a tasks sequence")
    normalized: list[dict[str, Any]] = []
    for raw in raw_tasks:
        if not isinstance(raw, Mapping):
            raise OrchestrateAdapterError("each cloud task must be a mapping")
        task_id = _cli_identifier(raw.get("id"), "cloud task id")
        attempt_total = raw.get("attempt_total")
        if not isinstance(attempt_total, int) or isinstance(attempt_total, bool) or attempt_total < 0:
            raise OrchestrateAdapterError("attempt_total must be a non-negative integer")
        normalized.append(
            {
                "id": task_id,
                "url": _text(raw.get("url"), f"url for {task_id}"),
                "title": _text(raw.get("title"), f"title for {task_id}"),
                "status": _text(raw.get("status"), f"status for {task_id}"),
                "environment_id": _cli_identifier(
                    raw.get("environment_id"), f"environment_id for {task_id}"
                ),
                "attempt_total": attempt_total,
                "status_command": ("codex", "cloud", "status", task_id),
                "diff_command": ("codex", "cloud", "diff", task_id),
            }
        )
    next_cursor = payload.get("next_cursor")
    if next_cursor is not None:
        next_cursor = _text(next_cursor, "next_cursor")
    return {"tasks": tuple(normalized), "next_cursor": next_cursor, "read_only": True}


def build_apply_command(
    task_id: str,
    *,
    attempt: int = 1,
    authorization_granted: bool = False,
) -> tuple[str, ...]:
    """Build an apply argv only after separate out-of-band authorization."""

    if authorization_granted is not True:
        raise OrchestrateAdapterError("applying a cloud diff requires separate authorization")
    task_id = _cli_identifier(task_id, "cloud task id")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise OrchestrateAdapterError("attempt must be a positive integer")
    return ("codex", "cloud", "apply", task_id, "--attempt", str(attempt))


def reconcile_local_handoffs(
    plan: Mapping[str, Any], handoffs: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    """Aggregate supplied handoffs while preserving missing and blocked work."""

    if plan.get("status") != "PLAN_READY" or plan.get("dispatch_performed"):
        raise OrchestrateAdapterError("handoffs require a validated non-dispatching plan")
    tasks = plan.get("tasks")
    if not isinstance(tasks, (tuple, list)):
        raise OrchestrateAdapterError("plan tasks are missing")
    plan = prepare_local_plan(
        plan.get("goal"), tasks, max_children=plan.get("max_children", 4)
    )
    tasks = plan["tasks"]
    expected = tuple(task["task_id"] for task in tasks)
    received: dict[str, dict[str, Any]] = {}
    for raw in handoffs:
        if not isinstance(raw, Mapping):
            raise OrchestrateAdapterError("each handoff must be a mapping")
        task_id = _task_id(raw.get("task_id"))
        if task_id not in expected:
            raise OrchestrateAdapterError(f"handoff is outside the plan: {task_id}")
        if task_id in received:
            raise OrchestrateAdapterError(f"duplicate handoff: {task_id}")
        status = _text(raw.get("status"), f"status for {task_id}")
        if status not in _HANDOFF_STATUSES:
            raise OrchestrateAdapterError(f"unsupported handoff status for {task_id}: {status}")
        evidence = _text(raw.get("evidence"), f"evidence for {task_id}")
        artifact = raw.get("artifact")
        if status == "PASS" and not isinstance(artifact, str):
            raise OrchestrateAdapterError(f"PASS handoff needs artifact identity: {task_id}")
        if isinstance(artifact, str):
            artifact = _text(artifact, f"artifact for {task_id}")
        received[task_id] = {
            "task_id": task_id,
            "status": status,
            "evidence": evidence,
            "artifact": artifact,
        }

    missing = tuple(task_id for task_id in expected if task_id not in received)
    blocked = tuple(task_id for task_id, item in received.items() if item["status"] == "BLOCKED")
    issues = tuple(task_id for task_id, item in received.items() if item["status"] == "ISSUES")
    aggregate = "BLOCKED" if missing or blocked else ("ISSUES" if issues else "PASS")
    return {
        "status": aggregate,
        "handoffs": tuple(received[task_id] for task_id in expected if task_id in received),
        "missing": missing,
        "blocked": blocked,
        "issues": issues,
        "dispatch_performed": False,
        "external_writes": False,
    }
