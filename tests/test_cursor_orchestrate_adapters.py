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


def _pass_handoff(task_id: str, cloud_task_id: str | None = None):
    return {
        "task_id": task_id,
        "status": "PASS",
        "evidence": "Status and diff inspected.",
        "artifact": {
            "uri": f"codex-cloud://{cloud_task_id or task_id}/attempt/1",
            "sha256": "a" * 64,
        },
        "cloud_task_id": cloud_task_id or f"task_e_{task_id}",
        "attempt": 1,
        "status_checked": True,
        "diff_checked": True,
    }


def test_plan_and_dependency_ready_batches_are_bounded():
    plan = _plan()
    assert plan["status"] == "PLAN_READY"
    assert plan["cloud_execution"] == "ENVIRONMENT_REQUIRED"
    assert plan["dispatch_performed"] is False
    assert ready_task_ids(plan) == ("root",)
    assert ready_task_ids(plan, (_pass_handoff("root"),)) == ("worker",)
    assert ready_task_ids(
        plan, (_pass_handoff("root"), _pass_handoff("worker"))
    ) == ()


def test_dispatch_requires_authorization_and_builds_shell_free_argv():
    with pytest.raises(OrchestrateAdapterError, match="out-of-band authorization"):
        build_codex_cloud_dispatch_batch(
            _plan(), environment_id="env_123", branch="codex/test"
        )
    with pytest.raises(OrchestrateAdapterError, match="content requires explicit authorization"):
        build_codex_cloud_dispatch_batch(
            _plan(), environment_id="env_123", branch="codex/test", authorization_granted=True
        )
    batch = build_codex_cloud_dispatch_batch(
        _plan(),
        environment_id="env_123",
        branch="codex/test",
        attempts=2,
        authorization_granted=True,
        content_authorization_granted=True,
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
        "2",
        "--branch",
        "codex/test",
        "Goal: Review the synthetic fixture and return a bounded handoff.\nTask: root\nRole: planner\nAcceptance: Return the plan.\nReturn a concise structured handoff with status, evidence, and artifact identity.",
    )


def test_dispatch_rejects_private_paths_credentials_and_unsafe_identifiers():
    with pytest.raises(OrchestrateAdapterError, match="private path marker"):
        prepare_local_plan(
            "Read from /tmp/.ssh material",
            [{"task_id": "root", "role": "planner", "acceptance": "Return it."}],
        )
    with pytest.raises(OrchestrateAdapterError, match="credential-shaped content"):
        prepare_local_plan(
            "Use API_KEY=sk-proj-1234567890123456",
            [{"task_id": "root", "role": "planner", "acceptance": "Return it."}],
        )
    for credential in (
        "OPENAI_API_KEY=value",
        "AWS_SECRET_ACCESS_KEY=value",
        "SLACK_BOT_TOKEN=value",
        "-----BEGIN PRIVATE KEY-----",
        "ghp_12345678901234567890",
    ):
        with pytest.raises(OrchestrateAdapterError, match="credential-shaped content"):
            prepare_local_plan(
                credential,
                [{"task_id": "root", "role": "planner", "acceptance": "Return it."}],
            )
    with pytest.raises(OrchestrateAdapterError, match="safe CLI identifier"):
        build_codex_cloud_dispatch_batch(
            _plan(),
            environment_id="env;touch-bad",
            branch="codex/test",
            authorization_granted=True,
            content_authorization_granted=True,
        )
    forged = dict(_plan())
    forged["goal"] = "Forward an API_KEY=sk-proj-1234567890123456 from an unvalidated plan."
    with pytest.raises(OrchestrateAdapterError, match="credential-shaped content"):
        build_codex_cloud_dispatch_batch(
            forged,
            environment_id="env_123",
            branch="codex/test",
            authorization_granted=True,
            content_authorization_granted=True,
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
            "cursor": "cursor_2",
        }
    )
    task = result["tasks"][0]
    assert task["id"] == "task_123"
    assert task["status_command"] == ("codex", "cloud", "status", "task_123")
    assert task["diff_command"] == ("codex", "cloud", "diff", "task_123")
    assert task["environment_label"] == "Main"
    assert result["cursor"] == "cursor_2"
    assert result["next_cursor"] == "cursor_2"
    assert parse_codex_cloud_list({"tasks": []})["tasks"] == ()


def test_cloud_list_parser_accepts_real_cli_null_environment_id():
    result = parse_codex_cloud_list(
        {
            "tasks": [
                {
                    "id": "task_e_6aa91395baf483268a13e1a5cd9db403",
                    "url": "https://chatgpt.com/codex/tasks/task_e_6aa91395baf483268a13e1a5cd9db403",
                    "title": "Perform read-only audit on repository",
                    "status": "pending",
                    "environment_id": None,
                    "environment_label": "TheAngrySkills orchestrate proof",
                    "attempt_total": 1,
                }
            ],
            "cursor": None,
        }
    )
    task = result["tasks"][0]
    assert task["environment_id"] is None
    assert task["environment_label"] == "TheAngrySkills orchestrate proof"
    assert result["cursor"] is None


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
            _pass_handoff("root"),
            _pass_handoff("worker"),
        ],
    )
    assert passed["status"] == "PASS"
    assert passed["readiness"] == "READY"
    assert passed["ready_for_follow_on"] is True
    assert passed["missing"] == ()

    missing = reconcile_local_handoffs(
        _plan(),
        [_pass_handoff("root")],
    )
    assert missing["status"] == "BLOCKED"
    assert missing["readiness"] == "NOT_READY"
    assert missing["ready_for_follow_on"] is False
    assert missing["missing"] == ("worker",)

    blocked = reconcile_local_handoffs(
        _plan(),
        [
            _pass_handoff("root"),
            {"task_id": "worker", "status": "BLOCKED", "evidence": "Environment unavailable."},
        ],
    )
    assert blocked["blocked"] == ("worker",)
    assert blocked["ready_for_follow_on"] is False


@pytest.mark.parametrize("attempts", [1, 2, 3, 4])
def test_dispatch_supports_bounded_attempts_and_optional_branch(attempts):
    batch = build_codex_cloud_dispatch_batch(
        _plan(),
        environment_id="env_123",
        attempts=attempts,
        authorization_granted=True,
        content_authorization_granted=True,
    )
    assert batch["attempts"] == attempts
    assert batch["commands"][0][6] == str(attempts)
    assert "--branch" not in batch["commands"][0]


@pytest.mark.parametrize("attempts", [0, 5, True, "1", None])
def test_dispatch_rejects_attempts_outside_native_range(attempts):
    with pytest.raises(OrchestrateAdapterError, match="1 through 4"):
        build_codex_cloud_dispatch_batch(
            _plan(), environment_id="env_123", attempts=attempts,
            authorization_granted=True, content_authorization_granted=True,
        )


def test_pass_handoff_requires_non_empty_text_artifact():
    with pytest.raises(OrchestrateAdapterError, match="artifact"):
        reconcile_local_handoffs(
            _plan(),
            [{"task_id": "root", "status": "PASS", "evidence": "ok", "artifact": ""}],
        )
    with pytest.raises(OrchestrateAdapterError, match="artifact"):
        reconcile_local_handoffs(
            _plan(),
            [{"task_id": "root", "status": "PASS", "evidence": "ok", "artifact": 12}],
        )


def test_dependency_readiness_rejects_bare_ids_and_uninspected_or_blocked_handoffs():
    with pytest.raises(OrchestrateAdapterError, match="mapping"):
        ready_task_ids(_plan(), ("root",))
    blocked = {
        "task_id": "root",
        "status": "BLOCKED",
        "evidence": "Cloud task did not pass.",
    }
    assert ready_task_ids(_plan(), (blocked,)) == ()
    uninspected = _pass_handoff("root")
    uninspected["diff_checked"] = False
    with pytest.raises(OrchestrateAdapterError, match="status and diff inspection"):
        ready_task_ids(_plan(), (uninspected,))


def test_pass_handoff_rejects_invented_text_reference_and_malformed_digest():
    with pytest.raises(OrchestrateAdapterError, match="structured artifact"):
        reconcile_local_handoffs(
            _plan(),
            [{"task_id": "root", "status": "PASS", "evidence": "ok", "artifact": "task://invented"}],
        )
    malformed = _pass_handoff("root")
    malformed["artifact"]["sha256"] = "not-a-digest"
    with pytest.raises(OrchestrateAdapterError, match="64 lowercase hex"):
        reconcile_local_handoffs(_plan(), (malformed,))


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
