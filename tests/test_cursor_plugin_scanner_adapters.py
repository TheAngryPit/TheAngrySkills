"""Bounded positive and negative proofs for held scanner overlays."""

from __future__ import annotations

import json
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
    sdk_reference_report,
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

    def test_supplied_real_score_is_preserved_without_execution(self) -> None:
        result = compatibility_report(self.root, scanner_result={"score": 87, "summary": "fixture"})
        self.assertEqual(result["status"], "REAL_SCANNER_RESULT_SUPPLIED")
        self.assertEqual(result["agent_compatibility_score"], 87)
        self.assertEqual(result["scanner_result"]["summary"], "fixture")
        self.assertFalse(result["external_writes"])

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

    def test_cli_is_json_and_read_only(self) -> None:
        source = self.root / "sdk.ts"
        source.write_text('import { Agent } from "@cursor/sdk";\nAgent.prompt("x");\n')
        completed = subprocess.run(
            [sys.executable, "scripts/cursor_plugin_scanner_adapters.py", "sdk-reference", str(source)],
            cwd=Path(__file__).resolve().parent.parent,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "REFERENCE_ONLY")
        self.assertFalse(result["external_writes"])


if __name__ == "__main__":
    unittest.main()
