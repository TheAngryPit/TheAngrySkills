"""Bounded positive and negative proofs for held scanner overlays."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cursor_plugin_scanner_adapters import (  # noqa: E402
    PermissionDenied,
    compatibility_report,
    inspect_compatibility_fixture,
    local_plugin_compatibility_scan,
    sdk_reference_report,
    sdk_native_contract_report,
)
from cursor_plugin_scaffold_fixture import (  # noqa: E402
    MARKER,
    MARKER_CONTENT,
    scaffold_cursor_plugin_fixture,
)


class CursorPluginScannerAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="cursor-scanner-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "README.md").write_text("# Fixture\n")
        (self.root / "tests").mkdir()

    def test_compatibility_inventory_is_separate_and_withholds_score(self) -> None:
        result = inspect_compatibility_fixture(self.root)
        self.assertEqual(result["status"], "EVIDENCE_ONLY")
        self.assertEqual(result["deterministic_scanner"], "UNAVAILABLE")
        self.assertIsNone(result["agent_compatibility_score"])
        self.assertTrue(result["separate_evidence_required"])
        self.assertFalse(result["package_installed"])
        self.assertFalse(result["network_used"])
        self.assertEqual(compatibility_report(self.root)["status"], "SCANNER_UNAVAILABLE")

    def test_local_scanner_scores_real_disposable_plugin_contract(self) -> None:
        fixture_root = self.root / "disposable"
        fixture_root.mkdir()
        (fixture_root / MARKER).write_text(MARKER_CONTENT)
        created = scaffold_cursor_plugin_fixture(
            fixture_root,
            "example-plugin",
            project_root=self.root,
            description="Example: static local plugin",
            author="Fixture Author",
            license_id="MIT",
            license_text="Fixture license text\n",
            components=("skills", "rules", "agents", "commands"),
        )
        self.assertEqual(created["status"], "FIXTURE_ONLY")
        plugin = fixture_root / "example-plugin"
        result = local_plugin_compatibility_scan(plugin)
        self.assertEqual(result["status"], "LOCAL_SCANNER_PASS")
        self.assertEqual(result["local_codex_compatibility_score"], 100)
        self.assertIsNone(result["agent_compatibility_score"])
        self.assertEqual(set(result["roles"]), {
            "deterministic-scanner",
            "startup-review",
            "validation-review",
            "docs-reliability-review",
        })
        self.assertTrue(all(role["score"] == 100 for role in result["roles"].values()))
        self.assertFalse(result["runtime_executed"])
        self.assertFalse(result["components_executed"])

    def test_local_scanner_reports_missing_plugin_surfaces_without_execution(self) -> None:
        result = local_plugin_compatibility_scan(self.root)
        self.assertEqual(result["status"], "LOCAL_SCANNER_REVIEW")
        self.assertLess(result["local_codex_compatibility_score"], 100)
        self.assertIsNone(result["agent_compatibility_score"])
        self.assertTrue(result["roles"]["startup-review"]["issues"])
        self.assertFalse(result["runtime_executed"])
        self.assertFalse(result["external_writes"])

    def test_supplied_real_score_is_preserved_without_execution(self) -> None:
        result = compatibility_report(self.root, scanner_result={"score": 87, "summary": "fixture"})
        self.assertEqual(result["status"], "UNVERIFIED_SCANNER_RESULT_SUPPLIED")
        self.assertIsNone(result["agent_compatibility_score"])
        self.assertEqual(result["unverified_scanner_score"], 87)
        self.assertEqual(result["score_provenance"], "UNVERIFIED_CALLER_INPUT")
        self.assertFalse(result["external_writes"])

    def test_nan_and_out_of_range_scores_are_withheld(self) -> None:
        for score in (float("nan"), -1, 101):
            result = compatibility_report(self.root, scanner_result={"score": score})
            self.assertIsNone(result["agent_compatibility_score"])
            self.assertIsNone(result["unverified_scanner_score"])

    def test_sdk_reference_report_has_symbols_but_no_runtime_claim(self) -> None:
        source = (
            'import { Agent } from "@cursor/sdk";\n'
            'Agent.create({ local: { cwd: process.cwd() } });\n'
            'await agent.send("inspect");\n'
            'await run.wait();\n'
        )
        result = sdk_reference_report(source)
        self.assertEqual(result["status"], "REFERENCE_ONLY")
        self.assertIn("@cursor/sdk", result["symbols"])
        self.assertIn("Agent.create", result["symbols"])
        self.assertEqual(result["runtime"], "UNAVAILABLE")
        self.assertFalse(result["credentials_read"])
        self.assertFalse(result["network_used"])

    def test_sdk_credentials_and_execution_requests_fail_closed(self) -> None:
        with self.assertRaises(PermissionDenied):
            sdk_reference_report("Agent.create({});", request={"apiKey": "redacted"})
        with self.assertRaises(PermissionDenied):
            sdk_reference_report("Agent.prompt('x');", request={"execute": True})
        with self.assertRaises(PermissionDenied):
            sdk_reference_report("Agent.create({});", request={"mcpServers": {}})
        with self.assertRaises(PermissionDenied):
            sdk_reference_report(
                "Agent.create({});",
                request={"options": {"credentials": {"apiKey": "redacted"}}},
            )
        with self.assertRaises(PermissionDenied):
            sdk_reference_report(
                "Agent.create({});",
                request={"options": {"credentials": "provided by caller"}},
            )

    def test_sdk_reference_reports_full_symbol_inventory_without_runtime_claim(self) -> None:
        source = " ".join(
            (
                "@cursor/sdk",
                "Agent.create",
                "Agent.prompt",
                "Agent.resume",
                "agent.send",
                "run.stream",
                "run.wait",
                "CursorAgentError",
                "mcpServers",
            )
        )
        result = sdk_reference_report(source)
        self.assertEqual(
            result["symbols"],
            (
                "@cursor/sdk",
                "Agent.create",
                "Agent.prompt",
                "Agent.resume",
                "agent.send",
                "run.stream",
                "CursorAgentError",
                "run.wait",
                "mcpServers",
            ),
        )
        self.assertEqual(result["runtime"], "UNAVAILABLE")
        self.assertFalse(result["credentials_read"])
        self.assertFalse(result["authenticated"])

    def test_sdk_native_mapping_is_safe_and_does_not_claim_api_equivalence(self) -> None:
        result = sdk_native_contract_report()
        self.assertEqual(result["status"], "CODEX_NATIVE_MAPPING_REFERENCE_ONLY")
        self.assertEqual(set(result["mappings"]), {
            "Agent.create",
            "Agent.prompt",
            "Agent.resume",
            "agent.send",
            "run.stream",
            "run.wait",
            "CursorAgentError",
            "mcpServers",
        })
        self.assertEqual(result["equivalence"], "conceptual_only; native Codex task APIs are a different contract")
        self.assertFalse(result["cursor_sdk_imported"])
        self.assertFalse(result["cursor_sdk_executed"])
        self.assertFalse(result["credentials_read"])
        self.assertFalse(result["external_writes"])

    def test_cli_is_json_and_read_only(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/cursor_plugin_scanner_adapters.py", "sdk-reference"],
            cwd=Path(__file__).resolve().parent.parent,
            input='import { Agent } from "@cursor/sdk";\nAgent.prompt("x");\n',
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "REFERENCE_ONLY")
        self.assertFalse(result["external_writes"])

    def test_cli_runs_local_scanner_on_disposable_plugin(self) -> None:
        fixture_root = self.root / "cli-disposable"
        fixture_root.mkdir()
        (fixture_root / MARKER).write_text(MARKER_CONTENT)
        created = scaffold_cursor_plugin_fixture(
            fixture_root,
            "cli-plugin",
            project_root=self.root,
            description="CLI scanner fixture",
            author="Fixture Author",
            license_id="MIT",
            license_text="Fixture license text\n",
            components=("skills", "rules"),
        )
        self.assertEqual(created["status"], "FIXTURE_ONLY")
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/cursor_plugin_scanner_adapters.py",
                "compatibility",
                str(fixture_root / "cli-plugin"),
                "--local-scan",
            ],
            cwd=Path(__file__).resolve().parent.parent,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "LOCAL_SCANNER_RESULT")
        self.assertEqual(result["local_codex_compatibility_score"], 100)
        self.assertIsNone(result["agent_compatibility_score"])

    def test_published_bundle_runs_with_its_local_auditor(self) -> None:
        fixture_root = self.root / "published-bundle"
        fixture_root.mkdir()
        (fixture_root / MARKER).write_text(MARKER_CONTENT)
        scaffold_cursor_plugin_fixture(
            fixture_root, "published-plugin", project_root=self.root,
            description="Published bundle fixture", author="Fixture Author",
            license_id="MIT", license_text="Fixture license\n",
            components=("skills", "rules"),
        )
        script = (
            Path(__file__).resolve().parent.parent
            / "skills/mirrors-cursor/cursor-check-agent-compatibility/scripts"
            / "cursor_plugin_scanner_adapters.py"
        )
        completed = subprocess.run(
            [sys.executable, str(script), "compatibility",
             str(fixture_root / "published-plugin"), "--local-scan"],
            text=True, capture_output=True, check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "LOCAL_SCANNER_RESULT")
        self.assertEqual(result["local_codex_compatibility_score"], 100)

    def test_cli_rejects_sdk_file_path(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/cursor_plugin_scanner_adapters.py", "sdk-reference", str(self.root / "README.md")],
            cwd=Path(__file__).resolve().parent.parent,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("never reads a path", completed.stderr)


if __name__ == "__main__":
    unittest.main()
