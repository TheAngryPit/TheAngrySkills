#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "route.py"
PRESET = ROOT / "assets" / "vitor-opinionated.toml"
AGENT_ASSETS = ROOT / "assets" / "agents"
SUBAGENT_TOOLS = [
    "spawn_agent",
    "followup_task",
    "send_message",
    "wait_agent",
    "list_agents",
    "interrupt_agent",
]
TASK_TOOLS = [
    "create_thread",
    "list_threads",
    "read_thread",
    "send_message_to_thread",
    "wait_threads",
]
FLEET_CAPACITY_ARGS = [
    "--runtime-capacity",
    "6",
    "--active-subagents",
    "0",
]


class RouteTests(unittest.TestCase):
    def run_cli(self, *args: str, expected: int = 0):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        return json.loads(result.stdout or result.stderr)

    def write_temp_preset(self, content: str) -> str:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".toml", encoding="utf-8", delete=False
        ) as handle:
            handle.write(content)
            path = handle.name
        self.addCleanup(Path(path).unlink, missing_ok=True)
        return path

    def write_coordinator_receipt(self, **overrides: object) -> str:
        receipt = {
            "schema_version": 1,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "task_id": "field-coordinator-thread",
            "logical_parent_id": "master-thread",
            "role": "field-coordinator",
            "model": "gpt-5.6-terra",
            "effort": "medium",
            "logical_relationship": "delegated_subtask",
            "lifecycle": "reusable",
            "project_verified": True,
            "purpose_verified": True,
            "ownership_verified": True,
            "role_binding": "matched",
            "worker_role": "general-worker",
            "worker_model": "gpt-5.6-luna",
            "worker_effort": "medium",
            "worker_role_binding": "matched",
            "runtime_role_rejections": {},
            "verification_method": "list_threads+read_thread+coordinator_readback",
            "channel_models": {"spawn_agent": ["gpt-5.6-luna"]},
            "available_tools": SUBAGENT_TOOLS,
            "runtime_capacity": 8,
            "active_subagents": 0,
        }
        receipt.update(overrides)
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", encoding="utf-8", delete=False
        ) as handle:
            json.dump(receipt, handle)
            path = handle.name
        self.addCleanup(Path(path).unlink, missing_ok=True)
        return path

    @staticmethod
    def tool_args(tools: list[str]) -> list[str]:
        result: list[str] = []
        for tool in tools:
            result.extend(["--available-tool", tool])
        return result

    @staticmethod
    def write_agent(
        directory: str,
        name: str,
        model: str | None = None,
        effort: str | None = None,
    ) -> None:
        lines = [f'name = "{name}"']
        if model:
            lines.append(f'model = "{model}"')
        if effort:
            lines.append(f'model_reasoning_effort = "{effort}"')
        Path(directory, f"{name}.toml").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

    @staticmethod
    def write_skill(directory: str, name: str) -> None:
        skill = Path(directory, name)
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\n---\n", encoding="utf-8"
        )

    def test_windows_launcher_uses_python_launcher(self):
        launcher = ROOT / "scripts" / "route.cmd"
        self.assertIn('py -3 "%~dp0route.py" %*', launcher.read_text())

    def test_schema_three_presets_validate(self):
        self.assertTrue(self.run_cli("validate", "--preset", str(PRESET))["valid"])
        neutral = (
            ROOT.parent
            / "model-routing-preset-builder"
            / "assets"
            / "neutral-balanced.toml"
        )
        self.assertTrue(self.run_cli("validate", "--preset", str(neutral))["valid"])

    def test_schema_two_is_rejected(self):
        path = self.write_temp_preset("schema_version = 2\n")
        result = self.run_cli("validate", "--preset", path, expected=1)
        self.assertIn("schema_version must be 3", result["errors"][0])

    def test_schema_two_to_three_migration_preflight_binds_exact_hashes(self):
        legacy = self.write_temp_preset(
            'schema_version = 2\nname = "vitor-opinionated"\n'
            'version = "legacy"\n'
        )
        result = self.run_cli(
            "migration-preflight",
            "--legacy-preset",
            legacy,
            "--target-preset",
            str(PRESET),
        )
        self.assertEqual(result["status"], "preflight_ready")
        self.assertEqual(result["migration"], "schema_2_to_schema_3_coordinated_bundle")
        self.assertEqual(result["proof_state"], "not_started")
        self.assertEqual(len(result["legacy"]["sha256"]), 64)
        self.assertIn("external_preset_mirror", result["required_release_unit"])

    def test_public_example_matches_builder_source(self):
        builder = (
            ROOT.parent
            / "model-routing-preset-builder"
            / "assets"
            / "vitor-opinionated.toml"
        )
        self.assertEqual(PRESET.read_bytes(), builder.read_bytes())

    def test_role_assets_do_not_pin_compute(self):
        import tomllib

        for path in AGENT_ASSETS.glob("*.toml"):
            config = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("model", config, path.name)
            self.assertNotIn("model_reasoning_effort", config, path.name)

    def test_fleet_policy_is_adaptive_with_operator_ceiling_six(self):
        import tomllib

        preset = tomllib.loads(PRESET.read_text(encoding="utf-8"))
        self.assertEqual(preset["policy"]["fleet_initial_fanout"], 3)
        self.assertEqual(
            preset["policy"]["max_concurrent_threads_per_session"], 6
        )

    def test_concurrency_above_eight_is_rejected(self):
        preset = PRESET.read_text(encoding="utf-8").replace(
            "max_concurrent_threads_per_session = 6",
            "max_concurrent_threads_per_session = 9",
            1,
        )
        path = self.write_temp_preset(preset)
        result = self.run_cli("validate", "--preset", path, expected=1)
        self.assertIn(
            "max_concurrent_threads_per_session must be between 1 and 8",
            result["errors"],
        )

    def test_single_is_sol_medium_master(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "single",
            "--channel-model",
            "current_task=gpt-5.6-sol",
        )
        self.assertEqual(result["execution"]["kind"], "current_task")
        self.assertEqual(
            result["selection"],
            {"mode": "profile", "model": "gpt-5.6-sol", "effort": "medium"},
        )

    def test_planner_is_sol_high_direct_subagent(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_subagent",
            "--role",
            "planner",
            "--channel-model",
            "spawn_agent=gpt-5.6-sol",
            "--agent-root",
            str(AGENT_ASSETS),
            *self.tool_args(SUBAGENT_TOOLS),
        )
        self.assertEqual(result["execution"]["role"], "planner")
        self.assertEqual(result["selection"]["effort"], "high")
        self.assertEqual(result["proof_requirement"], "reviewable_plan")
        self.assertEqual(result["proof_state"], "not_started")
        self.assertEqual(result["binding_evidence"]["main"], "matched")

    def test_protected_planner_cannot_be_downgraded(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_subagent",
            "--role",
            "planner",
            "--model",
            "gpt-5.6-luna",
            "--effort",
            "low",
            expected=2,
        )
        self.assertIn("protected role: planner", result["error"])

    def test_direct_subagent_accepts_explicit_supported_compute_override(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_subagent",
            "--role",
            "coder",
            "--model",
            "gpt-5.6-luna",
            "--effort",
            "high",
            "--channel-model",
            "spawn_agent=gpt-5.6-luna",
            "--agent-root",
            str(AGENT_ASSETS),
            *self.tool_args(SUBAGENT_TOOLS),
        )
        self.assertEqual(result["selection"]["model"], "gpt-5.6-luna")
        self.assertEqual(result["selection"]["effort"], "high")

    def test_master_and_coordinator_profiles_cannot_be_overridden(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "single",
            "--model",
            "gpt-5.6-luna",
            expected=2,
        )
        self.assertIn("require a role-selected route", result["error"])

    def test_worker_overrides_require_a_fleet_route(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_subagent",
            "--worker-effort",
            "high",
            expected=2,
        )
        self.assertIn("require a Fleet route", result["error"])

    def test_pinned_role_file_blocks_conflicting_override(self):
        with tempfile.TemporaryDirectory() as agents:
            self.write_agent(agents, "coder", "gpt-5.6-sol", "medium")
            result = self.run_cli(
                "resolve",
                "--preset",
                str(PRESET),
                "--route",
                "direct_subagent",
                "--role",
                "coder",
                "--model",
                "gpt-5.6-luna",
                "--channel-model",
                "spawn_agent=gpt-5.6-luna",
                "--agent-root",
                agents,
                *self.tool_args(SUBAGENT_TOOLS),
                expected=1,
            )
        self.assertIn("pins a conflicting model", result["error"])

    def test_vanilla_direct_subagent_avoids_pinning(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_subagent",
            "--vanilla",
            *self.tool_args(SUBAGENT_TOOLS),
        )
        self.assertEqual(result["selection"], {"mode": "vanilla"})
        self.assertIsNone(result["execution"]["role"])

    def test_runtime_rejection_outranks_flexible_role_config(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_subagent",
            "--role",
            "planner",
            "--channel-model",
            "spawn_agent=gpt-5.6-sol",
            "--agent-root",
            str(AGENT_ASSETS),
            "--rejected-role",
            "planner=runtime refused role",
            *self.tool_args(SUBAGENT_TOOLS),
            expected=1,
        )
        self.assertIn("runtime rejected configured agent role", result["error"])
        self.assertEqual(result["binding_evidence"]["runtime"], "rejected")

    def test_direct_fleet_defaults_to_three_luna_medium_workers(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_fleet",
            "--channel-model",
            "current_task=gpt-5.6-sol",
            "--channel-model",
            "spawn_agent=gpt-5.6-luna",
            "--agent-root",
            str(AGENT_ASSETS),
            *FLEET_CAPACITY_ARGS,
            *self.tool_args(SUBAGENT_TOOLS),
        )
        self.assertEqual(result["status"], "preflight_ready")
        self.assertEqual(result["fleet"]["model"], "gpt-5.6-luna")
        self.assertEqual(result["fleet"]["effort"], "medium")
        self.assertEqual(result["fleet"]["fanout"], 3)
        self.assertEqual(result["fleet"]["max_fanout"], 6)
        self.assertEqual(result["fleet"]["delegation_depth"], "direct_children_only")
        self.assertEqual(result["workflow"]["owner"], "native")
        self.assertNotIn("gstack", result["required_skills"])

    def test_direct_fleet_accepts_all_normal_luna_efforts(self):
        for effort in ("low", "medium", "high", "xhigh"):
            with self.subTest(effort=effort):
                result = self.run_cli(
                    "resolve",
                    "--preset",
                    str(PRESET),
                    "--route",
                    "direct_fleet",
                    "--worker-effort",
                    effort,
                    "--channel-model",
                    "current_task=gpt-5.6-sol",
                    "--channel-model",
                    "spawn_agent=gpt-5.6-luna",
                    "--agent-root",
                    str(AGENT_ASSETS),
                    *FLEET_CAPACITY_ARGS,
                    *self.tool_args(SUBAGENT_TOOLS),
                )
                self.assertEqual(result["fleet"]["effort"], effort)

    def test_fleet_allows_six_and_rejects_above_operator_ceiling(self):
        base = [
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_fleet",
            "--channel-model",
            "current_task=gpt-5.6-sol",
            "--channel-model",
            "spawn_agent=gpt-5.6-luna",
            "--agent-root",
            str(AGENT_ASSETS),
            *FLEET_CAPACITY_ARGS,
            *self.tool_args(SUBAGENT_TOOLS),
        ]
        self.assertEqual(self.run_cli(*base, "--fanout", "6")["fleet"]["fanout"], 6)
        result = self.run_cli(*base, "--fanout", "7", expected=2)
        self.assertIn("between 1 and 6", result["error"])
        result = self.run_cli(*base, "--fanout", "0", expected=2)
        self.assertIn("between 1 and 6", result["error"])

    def test_fleet_effective_fanout_uses_live_free_slots(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_fleet",
            "--fanout",
            "6",
            "--runtime-capacity",
            "6",
            "--active-subagents",
            "3",
            "--channel-model",
            "current_task=gpt-5.6-sol",
            "--channel-model",
            "spawn_agent=gpt-5.6-luna",
            "--agent-root",
            str(AGENT_ASSETS),
            *self.tool_args(SUBAGENT_TOOLS),
        )
        self.assertEqual(result["fleet"]["requested_fanout"], 6)
        self.assertEqual(result["fleet"]["fanout"], 3)
        self.assertEqual(result["fleet"]["free_slots"], 3)
        self.assertTrue(result["fleet"]["capacity_limited"])

    def test_fleet_requires_capacity_evidence_and_a_free_slot(self):
        common = [
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_fleet",
            "--channel-model",
            "current_task=gpt-5.6-sol",
            "--channel-model",
            "spawn_agent=gpt-5.6-luna",
            "--agent-root",
            str(AGENT_ASSETS),
            *self.tool_args(SUBAGENT_TOOLS),
        ]
        missing = self.run_cli(*common, expected=2)
        self.assertIn("runtime capacity", missing["error"])
        full = self.run_cli(
            *common,
            "--runtime-capacity",
            "8",
            "--active-subagents",
            "8",
            expected=2,
        )
        self.assertIn("no free runtime slots", full["error"])

    def test_fleet_reviewer_uses_reviewer_compute_profile(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_fleet",
            "--worker-role",
            "reviewer",
            "--channel-model",
            "current_task=gpt-5.6-sol",
            "--channel-model",
            "spawn_agent=gpt-5.6-sol",
            "--agent-root",
            str(AGENT_ASSETS),
            *FLEET_CAPACITY_ARGS,
            *self.tool_args(SUBAGENT_TOOLS),
        )
        self.assertEqual(result["fleet"]["role"], "reviewer")
        self.assertEqual(result["fleet"]["model"], "gpt-5.6-sol")
        self.assertEqual(result["fleet"]["effort"], "high")
        self.assertEqual(result["fleet"]["proof_requirement"], "independent_review")

    def test_protected_fleet_reviewer_cannot_be_downgraded(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_fleet",
            "--worker-role",
            "reviewer",
            "--worker-model",
            "gpt-5.6-luna",
            "--worker-effort",
            "low",
            expected=2,
        )
        self.assertIn("protected role: reviewer", result["error"])

    def test_gstack_is_an_optional_enforced_overlay(self):
        with tempfile.TemporaryDirectory() as skills:
            self.write_skill(skills, "gstack")
            context = [
                "repo_root=/repo",
                "plan_path=/repo/plan.md",
                "branch=feature",
                "revision=abc123",
                "owned_scope=src/a.py",
            ]
            args = [
                "resolve",
                "--preset",
                str(PRESET),
                "--route",
                "direct_fleet",
                "--workflow-owner",
                "gstack",
                "--workflow-phase",
                "implementation",
                "--channel-model",
                "current_task=gpt-5.6-sol",
                "--channel-model",
                "spawn_agent=gpt-5.6-luna",
                "--agent-root",
                str(AGENT_ASSETS),
                "--skill-root",
                skills,
                *FLEET_CAPACITY_ARGS,
                *self.tool_args(SUBAGENT_TOOLS),
            ]
            for item in context:
                args.extend(["--context-artifact", item])
            result = self.run_cli(*args)
        self.assertEqual(result["workflow"]["owner"], "gstack")
        self.assertTrue(result["workflow"]["gstack_workflow_authority"])
        self.assertIn("gstack", result["required_skills"])

    def test_gstack_overlay_blocks_when_gstack_is_missing(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "single",
            "--workflow-owner",
            "gstack",
            "--workflow-phase",
            "shape",
            "--context-artifact",
            "repo_root=/repo",
            "--channel-model",
            "current_task=gpt-5.6-sol",
            expected=1,
        )
        self.assertIn("gstack", result["missing_skills"])

    def test_gstack_review_requires_fresh_review_topology_and_context(self):
        with tempfile.TemporaryDirectory() as skills:
            self.write_skill(skills, "gstack")
            common = [
                "--workflow-owner",
                "gstack",
                "--workflow-phase",
                "review",
                "--skill-root",
                skills,
                "--context-artifact",
                "repo_root=/repo",
                "--context-artifact",
                "branch=feature",
                "--context-artifact",
                "revision=abc123",
                "--context-artifact",
                "diff_scope=src",
                "--context-artifact",
                "test_evidence=31-tests-pass",
            ]
            ready = self.run_cli(
                "resolve",
                "--preset",
                str(PRESET),
                "--route",
                "direct_subagent",
                "--role",
                "reviewer",
                "--channel-model",
                "spawn_agent=gpt-5.6-sol",
                "--agent-root",
                str(AGENT_ASSETS),
                *common,
                *self.tool_args(SUBAGENT_TOOLS),
            )
            blocked = self.run_cli(
                "resolve",
                "--preset",
                str(PRESET),
                "--route",
                "direct_fleet",
                "--channel-model",
                "current_task=gpt-5.6-sol",
                "--channel-model",
                "spawn_agent=gpt-5.6-luna",
                "--agent-root",
                str(AGENT_ASSETS),
                *FLEET_CAPACITY_ARGS,
                *common,
                *self.tool_args(SUBAGENT_TOOLS),
                expected=1,
            )
        self.assertEqual(ready["status"], "preflight_ready")
        self.assertEqual(
            ready["workflow"]["context_evidence"],
            "caller_supplied_unverified_references",
        )
        self.assertIn("not allowed during gstack review", blocked["error"])

    def test_gstack_implementation_rejects_review_roles(self):
        with tempfile.TemporaryDirectory() as skills:
            self.write_skill(skills, "gstack")
            result = self.run_cli(
                "resolve",
                "--preset",
                str(PRESET),
                "--route",
                "direct_subagent",
                "--role",
                "reviewer",
                "--workflow-owner",
                "gstack",
                "--workflow-phase",
                "implementation",
                "--skill-root",
                skills,
                "--context-artifact",
                "repo_root=/repo",
                "--context-artifact",
                "plan_path=/repo/plan.md",
                "--context-artifact",
                "branch=feature",
                "--context-artifact",
                "revision=abc123",
                "--context-artifact",
                "owned_scope=src/a.py",
                "--channel-model",
                "spawn_agent=gpt-5.6-sol",
                "--agent-root",
                str(AGENT_ASSETS),
                *self.tool_args(SUBAGENT_TOOLS),
                expected=1,
            )
        self.assertIn("not allowed during gstack implementation", result["error"])

    def test_field_fleet_reuses_a_verified_coordinator_with_own_capability_evidence(self):
        receipt = self.write_coordinator_receipt()
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "field_fleet",
            "--agent-root",
            str(AGENT_ASSETS),
            "--coordinator-receipt",
            receipt,
            "--existing-task-id",
            "field-coordinator-thread",
            "--reuse-verified",
            "--logical-parent-id",
            "master-thread",
            *self.tool_args(TASK_TOOLS[1:]),
        )
        self.assertEqual(result["task_action"], "reuse")
        self.assertEqual(result["status"], "preflight_ready")
        self.assertEqual(
            result["reuse_evidence"],
            "caller_supplied_structured_coordinator_attestation",
        )
        self.assertEqual(
            result["binding_evidence"]["main"],
            "receipt_claimed_match",
        )
        self.assertEqual(result["native_relationship"], "peer_user_owned_task")
        self.assertEqual(result["logical_relationship"], "delegated_subtask")
        self.assertEqual(result["logical_parent"], "master-orchestrator")
        self.assertEqual(result["fleet"]["max_fanout"], 6)

    def test_field_fleet_cannot_claim_unproven_coordinator_capability(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "field_fleet",
            "--agent-root",
            str(AGENT_ASSETS),
            "--existing-task-id",
            "field-coordinator-thread",
            "--reuse-verified",
            "--logical-parent-id",
            "master-thread",
            *self.tool_args(TASK_TOOLS[1:]),
            expected=2,
        )
        self.assertIn("structured coordinator receipt", result["error"])

    def test_field_fleet_rejects_mismatched_or_stale_coordinator_receipt(self):
        receipt = self.write_coordinator_receipt(
            task_id="different-task",
            observed_at="2020-01-01T00:00:00+00:00",
            worker_role_binding="missing",
        )
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "field_fleet",
            "--agent-root",
            str(AGENT_ASSETS),
            "--coordinator-receipt",
            receipt,
            "--existing-task-id",
            "field-coordinator-thread",
            "--reuse-verified",
            "--logical-parent-id",
            "master-thread",
            *self.tool_args(TASK_TOOLS[1:]),
            expected=1,
        )
        self.assertIn("outside the allowed freshness window", result["error"])
        self.assertIn("task_id does not match", result["error"])
        self.assertIn("worker role binding", result["error"])

    def test_field_fleet_receipt_freshness_window_cannot_exceed_policy(self):
        receipt = self.write_coordinator_receipt(
            observed_at="2020-01-01T00:00:00+00:00"
        )
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "field_fleet",
            "--agent-root",
            str(AGENT_ASSETS),
            "--coordinator-receipt",
            receipt,
            "--max-receipt-age-seconds",
            "999999999",
            "--existing-task-id",
            "field-coordinator-thread",
            "--reuse-verified",
            "--logical-parent-id",
            "master-thread",
            *self.tool_args(TASK_TOOLS[1:]),
            expected=1,
        )
        self.assertIn("exceeds the preset policy", result["error"])
        self.assertIn("outside the allowed freshness window", result["error"])

    def test_field_fleet_ignores_master_role_rejections_but_honors_coordinator_rejections(self):
        common = [
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "field_fleet",
            "--agent-root",
            str(AGENT_ASSETS),
            "--existing-task-id",
            "field-coordinator-thread",
            "--reuse-verified",
            "--logical-parent-id",
            "master-thread",
            *self.tool_args(TASK_TOOLS[1:]),
        ]
        valid_receipt = self.write_coordinator_receipt()
        ready = self.run_cli(
            *common,
            "--coordinator-receipt",
            valid_receipt,
            "--rejected-role",
            "general-worker=master-side rejection",
        )
        self.assertEqual(ready["status"], "preflight_ready")

        rejected_receipt = self.write_coordinator_receipt(
            runtime_role_rejections={"general-worker": "coordinator rejected role"}
        )
        blocked = self.run_cli(
            *common,
            "--coordinator-receipt",
            rejected_receipt,
            expected=1,
        )
        self.assertIn("coordinator runtime rejected", blocked["error"])

    def test_field_coordinator_requires_task_creation_authorization(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "field_coordinator",
            "--channel-model",
            "create_thread=gpt-5.6-terra",
            "--logical-parent-id",
            "master-thread",
            *self.tool_args(TASK_TOOLS),
            expected=1,
        )
        self.assertEqual(result["status"], "needs_authorization")
        self.assertEqual(result["task_action"], "create")

    def test_delegated_subtask_and_parallel_task_remain_distinct(self):
        common = [
            "resolve",
            "--preset",
            str(PRESET),
            "--channel-model",
            "create_thread=gpt-5.6-luna",
            "--task-creation-authorized",
            *self.tool_args(TASK_TOOLS),
        ]
        delegated = self.run_cli(
            *common,
            "--route",
            "delegated_subtask",
            "--logical-parent-id",
            "coordinator-thread",
        )
        parallel = self.run_cli(*common, "--route", "parallel_task")
        self.assertEqual(delegated["user_nomenclature"], "subtask")
        self.assertEqual(delegated["logical_relationship"], "delegated_subtask")
        self.assertIsNotNone(delegated["logical_parent"])
        self.assertEqual(parallel["user_nomenclature"], "task")
        self.assertEqual(parallel["logical_relationship"], "independent_parallel_task")
        self.assertIsNone(parallel["logical_parent"])

    def test_reusable_task_can_be_reused_without_creation_gate(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "delegated_subtask",
            "--channel-model",
            "create_thread=gpt-5.6-luna",
            "--existing-task-id",
            "verified-task",
            "--reuse-verified",
            "--logical-parent-id",
            "coordinator-thread",
            *self.tool_args(TASK_TOOLS),
        )
        self.assertEqual(result["status"], "preflight_ready")
        self.assertEqual(result["reuse_evidence"], "caller_attested_preflight")
        self.assertEqual(result["task_action"], "reuse")

    def test_existing_task_id_is_not_self_verifying(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "parallel_task",
            "--channel-model",
            "create_thread=gpt-5.6-luna",
            "--existing-task-id",
            "arbitrary-task",
            *self.tool_args(TASK_TOOLS),
            expected=1,
        )
        self.assertIn("requires fresh project", result["error"])

    def test_delegated_subtask_can_be_ephemeral(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "delegated_subtask",
            "--task-lifecycle",
            "ephemeral",
            "--logical-parent-id",
            "coordinator-thread",
            "--channel-model",
            "create_thread=gpt-5.6-luna",
            "--task-creation-authorized",
            *self.tool_args(TASK_TOOLS),
        )
        self.assertEqual(result["lifecycle"], "ephemeral")
        self.assertIsNone(result["reuse_scope"])

    def test_namespaced_task_tools_are_normalized(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "parallel_task",
            "--channel-model",
            "create_thread=gpt-5.6-luna",
            "--task-creation-authorized",
            *self.tool_args([f"codex_app__{name}" for name in TASK_TOOLS]),
        )
        self.assertEqual(result["missing_tools"], [])

    def test_max_and_ultra_remain_operator_authorized(self):
        for route in ("max_single", "ultra_auto"):
            with self.subTest(route=route):
                blocked = self.run_cli(
                    "resolve",
                    "--preset",
                    str(PRESET),
                    "--route",
                    route,
                    "--channel-model",
                    "current_task=gpt-5.6-sol",
                    expected=1,
                )
                self.assertEqual(
                    blocked["authorization"], "operator_authorization_required"
                )
                ready = self.run_cli(
                    "resolve",
                    "--preset",
                    str(PRESET),
                    "--route",
                    route,
                    "--channel-model",
                    "current_task=gpt-5.6-sol",
                    "--operator-authorized",
                )
                self.assertEqual(ready["status"], "preflight_ready")

    def test_missing_native_tool_blocks(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "direct_subagent",
            "--role",
            "planner",
            "--channel-model",
            "spawn_agent=gpt-5.6-sol",
            "--agent-root",
            str(AGENT_ASSETS),
            "--available-tool",
            "spawn_agent",
            expected=1,
        )
        self.assertIn("wait_agent", result["missing_tools"])

    def test_missing_capability_blocks(self):
        with tempfile.TemporaryDirectory() as skills:
            result = self.run_cli(
                "resolve",
                "--preset",
                str(PRESET),
                "--route",
                "direct_subagent",
                "--role",
                "reviewer",
                "--channel-model",
                "spawn_agent=gpt-5.6-sol",
                "--capability",
                "security_review",
                "--skill-root",
                skills,
                "--agent-root",
                str(AGENT_ASSETS),
                *self.tool_args(SUBAGENT_TOOLS),
                expected=1,
            )
        self.assertIn("security-scan", result["missing_skills"])

    def test_inventory_uses_frontmatter_name(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "different-folder"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: canonical-name\n---\n", encoding="utf-8"
            )
            result = self.run_cli("inventory", "--skill-root", directory)
        self.assertEqual(result["skills"], ["canonical-name"])

    def test_fork_and_handoff_are_excluded(self):
        result = self.run_cli(
            "resolve",
            "--preset",
            str(PRESET),
            "--route",
            "single",
            "--channel-model",
            "current_task=gpt-5.6-sol",
        )
        self.assertEqual(
            result["excluded_operations"], ["fork_thread", "handoff_thread"]
        )

    def test_gstack_compatibility_preserves_workflow_authority(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT / "references" / "gstack-compatibility.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("gstack-compatibility.md", skill)
        self.assertIn("gstack owns workflow order", contract)
        self.assertIn("A worker must not approve its own changes", contract)
        self.assertIn("same-family Fleet is throughput,\nnot model diversity", contract)
        self.assertIn("Ship/deploy", contract)

    def test_broad_router_uses_schema_three_topology_vocabulary(self):
        broad_router_path = ROOT.parent / "ask-theangrypit" / "SKILL.md"
        if not broad_router_path.exists():
            self.skipTest("ask-theangrypit is not part of this install surface")
        broad_router = broad_router_path.read_text(encoding="utf-8")
        self.assertIn("direct\n   Fleet", broad_router)
        self.assertIn("second-stage field Fleet", broad_router)
        self.assertNotIn("bounded_worker", broad_router)
        self.assertNotIn("micro-check", broad_router)


if __name__ == "__main__":
    unittest.main()
