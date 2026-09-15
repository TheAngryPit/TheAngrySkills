"""Focused local proofs for the held Cursor orchestrate contract."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from cursor_orchestrate_adapters import (  # noqa: E402
    OrchestrateAdapterError,
    build_work_cloud_approval_payload,
    prepare_local_plan,
    reconcile_local_handoffs,
)


def _plan():
    return prepare_local_plan(
        "Review the synthetic fixture and return a bounded handoff.",
        [
            {
                "task_id": "root",
                "role": "planner",
                "acceptance": "Publish one aggregate handoff.",
            },
            {
                "task_id": "worker",
                "role": "worker",
                "depends_on": ("root",),
                "acceptance": "Return evidence and artifact identity.",
            },
        ],
        max_children=1,
    )


def test_local_plan_is_bounded_and_never_dispatches():
    plan = _plan()
    assert plan["status"] == "PLAN_ONLY"
    assert plan["cloud_execution"] == "UNAVAILABLE"
    assert plan["dispatch_performed"] is False
    assert plan["external_writes"] is False
    assert plan["root_task"] == "root"


def test_local_handoff_aggregate_preserves_structured_pass():
    result = reconcile_local_handoffs(
        _plan(),
        [
            {
                "task_id": "root",
                "status": "PASS",
                "evidence": "Plan was validated locally.",
                "artifact": "fixture://root-handoff",
            },
            {
                "task_id": "worker",
                "status": "PASS",
                "evidence": "Synthetic data was read without external access.",
                "artifact": "fixture://worker-handoff",
            },
        ],
    )
    assert result["status"] == "PASS"
    assert result["missing"] == ()
    assert result["dispatch_performed"] is False


def test_local_handoff_keeps_missing_and_blocked_explicit():
    result = reconcile_local_handoffs(
        _plan(),
        [
            {
                "task_id": "root",
                "status": "PASS",
                "evidence": "Root was checked.",
                "artifact": "fixture://root-handoff",
            }
        ],
    )
    assert result["status"] == "BLOCKED"
    assert result["missing"] == ("worker",)

    blocked = reconcile_local_handoffs(
        _plan(),
        [
            {
                "task_id": "root",
                "status": "PASS",
                "evidence": "Root was checked.",
                "artifact": "fixture://root-handoff",
            },
            {
                "task_id": "worker",
                "status": "BLOCKED",
                "evidence": "No Work-compatible child surface was exposed.",
            },
        ],
    )
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked"] == ("worker",)


def test_plan_rejects_unknown_dependencies_and_unbounded_children():
    with pytest.raises(OrchestrateAdapterError, match="unknown dependency"):
        prepare_local_plan(
            "goal",
            [
                {"task_id": "root", "role": "planner", "acceptance": "root"},
                {"task_id": "worker", "role": "worker", "depends_on": ("missing",), "acceptance": "worker"},
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
    with pytest.raises(OrchestrateAdapterError, match="cyclic dependency"):
        prepare_local_plan(
            "goal",
            [
                {"task_id": "root", "role": "planner", "acceptance": "root"},
                {"task_id": "one", "role": "worker", "depends_on": ("two",), "acceptance": "one"},
                {"task_id": "two", "role": "verifier", "depends_on": ("one",), "acceptance": "two"},
            ],
        )


def test_work_cloud_payload_is_exactly_one_approval_gated_synthetic_request():
    payload = build_work_cloud_approval_payload()
    assert payload["status"] == "READY_FOR_EXPLICIT_APPROVAL"
    assert payload["recipient"] == "ChatGPT Work cloud (one user-owned task)"
    assert payload["destination"] == {"type": "chatgptWorkCloud"}
    assert payload["synthetic_data"] == {"records": [{"id": 1, "value": "alpha"}, {"id": 2, "value": "beta"}]}
    assert payload["max_children"] == 1
    assert payload["dispatch_performed"] is False
    assert all(value is False for value in payload["safety"].values())
    assert "CURSOR_API_KEY" not in payload["prompt"]
    assert "SLACK_BOT_TOKEN" not in payload["prompt"]
    assert "at most one child" in payload["prompt"]
