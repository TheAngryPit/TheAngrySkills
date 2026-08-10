#!/usr/bin/env python3

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "route.py"
PRESET = ROOT / "assets" / "vitor-opinionated.toml"
SUBAGENT_TOOLS = [
    "spawn_agent", "followup_task", "send_message",
    "wait_agent", "list_agents", "interrupt_agent",
]
TASK_TOOLS = [
    "create_thread", "list_threads", "read_thread",
    "send_message_to_thread", "wait_threads",
]


class RouteTests(unittest.TestCase):
    def run_cli(self, *args: str, expected: int = 0):
        result = subprocess.run(
            ["python3", str(SCRIPT), *args],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        return json.loads(result.stdout)

    @staticmethod
    def tool_args(tools: list[str]) -> list[str]:
        result: list[str] = []
        for tool in tools:
            result.extend(["--available-tool", tool])
        return result

    @staticmethod
    def write_agent(directory: str, name: str, model: str, effort: str) -> None:
        Path(directory, f"{name}.toml").write_text(
            f'name = "{name}"\nmodel = "{model}"\n'
            f'model_reasoning_effort = "{effort}"\n',
            encoding="utf-8",
        )

    def test_preset_validates(self):
        self.assertTrue(self.run_cli("validate", "--preset", str(PRESET))["valid"])

    def test_fork_and_handoff_are_excluded_from_routing(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET),
            "--route", "master_orchestration",
            "--channel-model", "current_task=gpt-5.6-sol",
        )
        self.assertEqual(
            result["excluded_operations"], ["fork_thread", "handoff_thread"]
        )

    def test_public_example_matches_builder_source(self):
        builder = (
            ROOT.parent
            / "model-routing-preset-builder"
            / "assets"
            / "vitor-opinionated.toml"
        )
        self.assertEqual(PRESET.read_bytes(), builder.read_bytes())

    def test_native_subagent_routes_match_bundled_agent_assets(self):
        import tomllib

        preset = tomllib.loads(PRESET.read_text(encoding="utf-8"))
        agent_root = ROOT / "assets" / "agents"
        for name, route in preset["routes"].items():
            if route["execution_kind"] != "native_subagent":
                continue
            if route["selection_mode"] == "vanilla":
                continue
            agent = tomllib.loads(
                (agent_root / f'{route["role"]}.toml').read_text(encoding="utf-8")
            )
            self.assertEqual(agent["name"], route["role"], name)
            self.assertEqual(agent["model"], route["model"], name)
            self.assertEqual(agent["model_reasoning_effort"], route["effort"], name)

    def test_schema_one_is_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".toml") as handle:
            handle.write("schema_version = 1\n")
            handle.flush()
            result = self.run_cli(
                "validate", "--preset", handle.name, expected=1
            )
        self.assertIn("schema_version must be 2", result["errors"][0])

    def test_reusable_native_task_requires_reuse_scope(self):
        preset = PRESET.read_text(encoding="utf-8").replace(
            'reuse_scope = "project_ticket_or_small_bundle"\n', "", 1
        )
        with tempfile.NamedTemporaryFile("w", suffix=".toml") as handle:
            handle.write(preset)
            handle.flush()
            result = self.run_cli(
                "validate", "--preset", handle.name, expected=1
            )
        self.assertTrue(
            any("coordination reusable native task" in item for item in result["errors"])
        )

    def test_master_is_sol_medium_current_task(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET),
            "--route", "master_orchestration",
            "--channel-model", "current_task=gpt-5.6-sol",
        )
        self.assertEqual(result["execution"]["kind"], "current_task")
        self.assertEqual(
            result["selection"],
            {"mode": "pinned", "model": "gpt-5.6-sol", "effort": "medium"},
        )

    def test_planner_is_sol_high_native_subagent(self):
        with tempfile.TemporaryDirectory() as agents:
            self.write_agent(agents, "planner", "gpt-5.6-sol", "high")
            result = self.run_cli(
                "resolve", "--preset", str(PRESET), "--route", "planning",
                "--channel-model", "spawn_agent=gpt-5.6-sol",
                "--agent-root", agents,
                *self.tool_args(SUBAGENT_TOOLS),
            )
        self.assertEqual(result["execution"]["role"], "planner")
        self.assertEqual(result["execution"]["role_kind"], "custom_agent_role")
        self.assertEqual(result["selection"]["effort"], "high")
        self.assertEqual(
            result["stop_condition"],
            "reviewable_plan_with_gates_and_proof_steps_returned",
        )
        self.assertEqual(
            result["availability_evidence"]["channel_models"],
            {"spawn_agent": ["gpt-5.6-sol"]},
        )

    def test_planner_does_not_fall_back_to_luna(self):
        with tempfile.TemporaryDirectory() as agents:
            self.write_agent(agents, "planner", "gpt-5.6-sol", "high")
            result = self.run_cli(
                "resolve", "--preset", str(PRESET), "--route", "planning",
                "--channel-model", "spawn_agent=gpt-5.6-luna",
                "--agent-root", agents,
                *self.tool_args(SUBAGENT_TOOLS),
                expected=1,
            )
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["selection"])

    def test_vanilla_subagent_avoids_pinning(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET),
            "--route", "vanilla_subagent",
            *self.tool_args(SUBAGENT_TOOLS),
        )
        self.assertEqual(result["selection"], {"mode": "vanilla"})
        self.assertIsNone(result["execution"]["role"])

    def test_field_coordinator_needs_creation_authorization(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET), "--route", "coordination",
            "--channel-model", "create_thread=gpt-5.6-terra",
            *self.tool_args(TASK_TOOLS),
            expected=1,
        )
        self.assertEqual(result["status"], "needs_authorization")
        self.assertEqual(result["task_action"], "create")

    def test_field_coordinator_can_be_created_when_authorized(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET), "--route", "coordination",
            "--channel-model", "create_thread=gpt-5.6-terra",
            "--task-creation-authorized",
            *self.tool_args(TASK_TOOLS),
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["task_action"], "create")
        self.assertEqual(result["execution"]["role"], "field-coordinator")
        self.assertEqual(result["execution"]["role_kind"], "logical_task_role")
        self.assertEqual(result["reuse_scope"], "project_ticket_or_small_bundle")

    def test_namespaced_task_tools_are_normalized(self):
        namespaced_tools = [f"codex_app__{name}" for name in TASK_TOOLS]
        result = self.run_cli(
            "resolve", "--preset", str(PRESET), "--route", "coordination",
            "--channel-model", "create_thread=gpt-5.6-terra",
            "--task-creation-authorized",
            *self.tool_args(namespaced_tools),
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["missing_tools"], [])
        self.assertIn(
            "codex_app__create_thread",
            result["availability_evidence"]["raw_available_tools"],
        )

    def test_field_coordinator_reuses_verified_task_without_creation_gate(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET), "--route", "coordination",
            "--channel-model", "create_thread=gpt-5.6-terra",
            "--existing-task-id", "thread-verified",
            *self.tool_args(TASK_TOOLS),
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["task_action"], "reuse")

    def test_luna_is_not_reachable_through_spawn_agent_inventory(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET), "--route", "luna_subtask",
            "--channel-model", "spawn_agent=gpt-5.6-luna",
            "--task-creation-authorized",
            *self.tool_args(TASK_TOOLS),
            expected=1,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["selection"])

    def test_ephemeral_luna_task_cannot_reuse_existing_task(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET), "--route", "luna_subtask",
            "--channel-model", "create_thread=gpt-5.6-luna",
            "--existing-task-id", "old-task",
            *self.tool_args(TASK_TOOLS),
            expected=1,
        )
        self.assertIn("cannot reuse", result["error"])

    def test_exceptional_luna_batch_needs_operator_authorization(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET),
            "--route", "exceptional_coding_batch",
            "--channel-model", "create_thread=gpt-5.6-luna",
            "--task-creation-authorized",
            *self.tool_args(TASK_TOOLS),
            expected=1,
        )
        self.assertEqual(
            result["authorization"], "operator_authorization_required"
        )

    def test_exceptional_luna_batch_resolves_with_both_authorizations(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET),
            "--route", "exceptional_coding_batch",
            "--channel-model", "create_thread=gpt-5.6-luna",
            "--operator-authorized",
            "--task-creation-authorized",
            *self.tool_args(TASK_TOOLS),
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["selection"]["effort"], "max")

    def test_operator_only_effort_requires_guard_in_preset(self):
        preset = PRESET.read_text(encoding="utf-8").replace(
            "operator_authorization_required = true",
            "operator_authorization_required = false",
            1,
        )
        with tempfile.NamedTemporaryFile("w", suffix=".toml") as handle:
            handle.write(preset)
            handle.flush()
            result = self.run_cli("validate", "--preset", handle.name, expected=1)
        self.assertIn(
            "exceptional_coding_batch uses max or ultra without operator authorization requirement",
            result["errors"],
        )

    def test_missing_native_tool_blocks(self):
        with tempfile.TemporaryDirectory() as agents:
            self.write_agent(agents, "reviewer", "gpt-5.6-sol", "high")
            result = self.run_cli(
                "resolve", "--preset", str(PRESET), "--route", "review",
                "--channel-model", "spawn_agent=gpt-5.6-sol",
                "--agent-root", agents,
                "--available-tool", "spawn_agent",
                expected=1,
            )
        self.assertIn("wait_agent", result["missing_tools"])

    def test_mismatched_agent_blocks(self):
        with tempfile.TemporaryDirectory() as agents:
            self.write_agent(agents, "planner", "gpt-5.6-sol", "medium")
            result = self.run_cli(
                "resolve", "--preset", str(PRESET), "--route", "planning",
                "--channel-model", "spawn_agent=gpt-5.6-sol",
                "--agent-root", agents,
                *self.tool_args(SUBAGENT_TOOLS),
                expected=1,
            )
        self.assertIn("does not match", result["error"])

    def test_missing_capability_blocks(self):
        with (
            tempfile.TemporaryDirectory() as skills,
            tempfile.TemporaryDirectory() as agents,
        ):
            self.write_agent(agents, "reviewer", "gpt-5.6-sol", "high")
            result = self.run_cli(
                "resolve", "--preset", str(PRESET), "--route", "review",
                "--channel-model", "spawn_agent=gpt-5.6-sol",
                "--capability", "security_review",
                "--skill-root", skills,
                "--agent-root", agents,
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


if __name__ == "__main__":
    unittest.main()
