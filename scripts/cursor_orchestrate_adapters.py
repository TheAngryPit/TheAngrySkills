"""Local, non-dispatching contracts for the held ``cursor-orchestrate`` mirror.

The adapter makes the parts that can be checked in this repository explicit:
plan shape, bounded handoff aggregation, and a reviewable Work cloud request.
It never creates a task, calls a connector, reads credentials, or runs the
bundled Cursor scripts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from typing import Any


class OrchestrateAdapterError(ValueError):
    """The local plan or proof fixture is malformed."""


_ROLES = frozenset({"planner", "subplanner", "worker", "verifier"})
_STATUSES = frozenset({"PASS", "ISSUES", "BLOCKED"})
_FORBIDDEN_DATA_MARKERS = (
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
    return value.strip()


def _task_id(value: Any) -> str:
    task_id = _text(value, "task_id")
    if any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in task_id):
        raise OrchestrateAdapterError("task_id must be a simple stable identifier")
    return task_id


def prepare_local_plan(
    goal: str,
    tasks: Iterable[Mapping[str, Any]],
    *,
    max_children: int = 4,
) -> dict[str, Any]:
    """Validate a bounded plan and mark cloud execution unavailable.

    This is deliberately a plan-only operation.  ``tasks`` are copied into a
    deterministic structure; no task or artifact is created.
    """

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
    for task in normalized:
        missing = set(task["depends_on"]) - seen
        if missing:
            raise OrchestrateAdapterError(
                f"unknown dependency for {task['task_id']}: {sorted(missing)}"
            )
    dependencies = {task["task_id"]: task["depends_on"] for task in normalized}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise OrchestrateAdapterError(f"cyclic dependency involving {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in dependencies[task_id]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in dependencies:
        visit(task_id)
    if sum(task["role"] in {"worker", "subplanner", "verifier"} for task in normalized) > max_children:
        raise OrchestrateAdapterError("plan exceeds max_children")

    return {
        "status": "PLAN_ONLY",
        "goal": goal,
        "root_task": planner_id,
        "max_children": max_children,
        "tasks": tuple(normalized),
        "cloud_execution": "UNAVAILABLE",
        "dispatch_performed": False,
        "external_writes": False,
    }


def reconcile_local_handoffs(
    plan: Mapping[str, Any], handoffs: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    """Aggregate supplied handoffs while preserving missing and blocked work."""

    if plan.get("status") != "PLAN_ONLY" or plan.get("dispatch_performed"):
        raise OrchestrateAdapterError("handoffs require a non-dispatching local plan")
    tasks = plan.get("tasks")
    if not isinstance(tasks, (tuple, list)):
        raise OrchestrateAdapterError("plan tasks are missing")
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
        if status not in _STATUSES:
            raise OrchestrateAdapterError(f"unsupported handoff status for {task_id}: {status}")
        evidence = _text(raw.get("evidence"), f"evidence for {task_id}")
        artifact = raw.get("artifact")
        if status == "PASS" and not isinstance(artifact, str):
            raise OrchestrateAdapterError(f"PASS handoff needs artifact identity: {task_id}")
        if isinstance(artifact, str) and not artifact.strip():
            raise OrchestrateAdapterError(f"artifact identity is empty: {task_id}")
        received[task_id] = {
            "task_id": task_id,
            "status": status,
            "evidence": evidence,
            "artifact": artifact,
        }

    missing = tuple(task_id for task_id in expected if task_id not in received)
    blocked = tuple(
        task_id for task_id, handoff in received.items() if handoff["status"] == "BLOCKED"
    )
    issues = tuple(
        task_id for task_id, handoff in received.items() if handoff["status"] == "ISSUES"
    )
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


def build_work_cloud_approval_payload() -> dict[str, Any]:
    """Return one exact, approval-gated Work cloud proof request.

    The returned object is a payload for review.  It is never passed to a
    task-creation tool by this adapter.
    """

    synthetic_data = {"records": [{"id": 1, "value": "alpha"}, {"id": 2, "value": "beta"}]}
    prompt = (
        "Run one read-only orchestration proof using only this synthetic/public data: "
        '{"records":[{"id":1,"value":"alpha"},{"id":2,"value":"beta"}]}. '
        "Return the record count and the two values in a single structured handoff. "
        "Exercise root status, at most one child, handoff readback, artifact identity, "
        "stop/cancel, and recovery readback only when the Work surface exposes each operation. "
        "Do not access repositories, private data, credentials, secrets, connectors, or external services. "
        "Do not edit, publish, message, purchase, merge, or create artifacts outside this task."
    )
    serialized_data = json.dumps(synthetic_data, sort_keys=True).casefold()
    if any(marker in serialized_data for marker in _FORBIDDEN_DATA_MARKERS):
        raise OrchestrateAdapterError("synthetic data contains a forbidden credential or private-data marker")
    return {
        "status": "READY_FOR_EXPLICIT_APPROVAL",
        "recipient": "ChatGPT Work cloud (one user-owned task)",
        "destination": {"type": "chatgptWorkCloud"},
        "prompt": prompt,
        "synthetic_data": synthetic_data,
        "max_children": 1,
        "operations": (
            "create one root task",
            "read root status",
            "request at most one child when exposed",
            "read structured handoff and artifact identity",
            "stop or cancel the exact task when exposed",
            "recover by readback or one bounded follow-up when exposed",
        ),
        "stop_cancel_recovery": {
            "stop": "stop after the first available readback or immediately if the task exceeds the stated scope",
            "cancel": "cancel only the exact returned task identity through a documented native operation; never archive as a substitute",
            "recovery": "preserve the last confirmed status and request one bounded readback/follow-up; report unavailable cancellation or recovery as a gap",
        },
        "safety": {
            "repo_data": False,
            "private_data": False,
            "secrets": False,
            "external_publication": False,
            "connectors": False,
        },
        "dispatch_performed": False,
    }
