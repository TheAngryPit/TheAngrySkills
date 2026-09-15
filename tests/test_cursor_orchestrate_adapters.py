"""Focused local proofs for the native Codex Cloud orchestrate contract."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from cursor_orchestrate_adapters import (  # noqa: E402
    OrchestrateAdapterError,
    build_apply_command,
    build_codex_cloud_dispatch_batch,
    parse_codex_cloud_list,
    prepare_local_plan,
    ready_task_ids,
    reconcile_local_handoffs,
)


def _plan():
    return prepare_local_plan(
        "Review the synthetic fixture and return a bounded handoff.",
        [
            {"task_id": "root", "role": "planner", "acceptance": "Return the plan."},
            {
                "task_id": "worker",
                "role": "worker",
                "depends_on": ("root",),
                "acceptance": "Return evidence and artifact identity.",
            },
        ],
        max_children=1,
    )


def test_plan_and_dependency_ready_batches_are_bounded():
    plan = _plan()
    assert plan["status"] == "PLAN_READY"
    assert plan["cloud_execution"] == "ENVIRONMENT_REQUIRED"
    assert plan["dispatch_performed"] is False
    assert ready_task_ids(plan) == ("root",)
    assert ready_task_ids(plan, completed=("root",)) == ("worker",)
    assert ready_task_ids(plan, completed=("root", "worker")) == ()


def test_dispatch_requires_authorization_and_builds_shell_free_argv():
    with pytest.raises(OrchestrateAdapterError, match="out-of-band authorization"):
        build_codex_cloud_dispatch_batch(
            _plan(), environment_id="env_123", branch="codex/test"
        )
    batch = build_codex_cloud_dispatch_batch(
        _plan(),
        environment_id="env_123",
        branch="codex/test",
        authorization_granted=True,
    )
    assert batch["ready_task_ids"] == ("root",)
    assert batch["dispatch_performed"] is False
    assert batch["commands"][0][:10] == (
        "codex",
        "cloud",
        "exec",
        "--env",
        "env_123",
        "--attempts",
        "1",
        "--branch",
        "codex/test",
        "Goal: Review the synthetic fixture and return a bounded handoff.\nTask: root\nRole: planner\nAcceptance: Return the plan.\nReturn a concise structured handoff with status, evidence, and artifact identity.",
    )


def test_dispatch_rejects_private_markers_and_unsafe_identifiers():
    with pytest.raises(OrchestrateAdapterError, match="private-data marker"):
        prepare_local_plan(
            "Use SECRET material",
            [{"task_id": "root", "role": "planner", "acceptance": "Return it."}],
        )
    with pytest.raises(OrchestrateAdapterError, match="safe CLI identifier"):
        build_codex_cloud_dispatch_batch(
            _plan(),
            environment_id="env;touch-bad",
            branch="codex/test",
            authorization_granted=True,
        )
    forged = dict(_plan())
    forged["goal"] = "Forward a SECRET from an unvalidated plan."
    with pytest.raises(OrchestrateAdapterError, match="private-data marker"):
        build_codex_cloud_dispatch_batch(
            forged,
            environment_id="env_123",
            branch="codex/test",
            authorization_granted=True,
        )


def test_cloud_list_parser_normalizes_documented_fields():
    result = parse_codex_cloud_list(
        {
            "tasks": [
                {
                    "id": "task_123",
                    "url": "https://chatgpt.com/codex/tasks/task_123",
                    "title": "Synthetic proof",
                    "status": "ready",
                    "updated_at": "2026-09-15T10:00:00Z",
                    "environment_id": "env_123",
                    "environment_label": "Main",
                    "summary": "Complete",
                    "is_review": False,
                    "attempt_total": 1,
                }
            ],
            "next_cursor": "cursor_2",
        }
    )
    task = result["tasks"][0]
    assert task["id"] == "task_123"
    assert task["status_command"] == ("codex", "cloud", "status", "task_123")
    assert task["diff_command"] == ("codex", "cloud", "diff", "task_123")
    assert result["next_cursor"] == "cursor_2"
    assert parse_codex_cloud_list({"tasks": []})["tasks"] == ()


def test_apply_requires_separate_authorization():
    with pytest.raises(OrchestrateAdapterError, match="separate authorization"):
        build_apply_command("task_123")
    assert build_apply_command(
        "task_123", attempt=2, authorization_granted=True
    ) == ("codex", "cloud", "apply", "task_123", "--attempt", "2")


def test_handoffs_preserve_pass_missing_and_blocked():
    passed = reconcile_local_handoffs(
        _plan(),
        [
            {"task_id": "root", "status": "PASS", "evidence": "Validated.", "artifact": "task://root"},
            {"task_id": "worker", "status": "PASS", "evidence": "Checked.", "artifact": "task://worker"},
        ],
    )
    assert passed["status"] == "PASS"
    assert passed["missing"] == ()

    missing = reconcile_local_handoffs(
        _plan(),
        [{"task_id": "root", "status": "PASS", "evidence": "Validated.", "artifact": "task://root"}],
    )
    assert missing["status"] == "BLOCKED"
    assert missing["missing"] == ("worker",)

    blocked = reconcile_local_handoffs(
        _plan(),
        [
            {"task_id": "root", "status": "PASS", "evidence": "Validated.", "artifact": "task://root"},
            {"task_id": "worker", "status": "BLOCKED", "evidence": "Environment unavailable."},
        ],
    )
    assert blocked["blocked"] == ("worker",)


def test_plan_rejects_unknown_dependencies_cycles_and_excess_children():
    with pytest.raises(OrchestrateAdapterError, match="unknown dependency"):
        prepare_local_plan(
            "goal",
            [
                {"task_id": "root", "role": "planner", "acceptance": "root"},
                {"task_id": "worker", "role": "worker", "depends_on": ("missing",), "acceptance": "worker"},
            ],
        )
    with pytest.raises(OrchestrateAdapterError, match="cyclic dependency"):
        prepare_local_plan(
            "goal",
            [
                {"task_id": "root", "role": "planner", "acceptance": "root"},
                {"task_id": "one", "role": "worker", "depends_on": ("two",), "acceptance": "one"},
                {"task_id": "two", "role": "verifier", "depends_on": ("one",), "acceptance": "two"},
            ],
        )
    with pytest.raises(OrchestrateAdapterError, match="exceeds max_children"):
        prepare_local_plan(
            "goal",
            [
                {"task_id": "root", "role": "planner", "acceptance": "root"},
                {"task_id": "one", "role": "worker", "acceptance": "one"},
                {"task_id": "two", "role": "worker", "acceptance": "two"},
            ],
            max_children=1,
        )
