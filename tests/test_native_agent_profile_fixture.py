"""Proof boundaries for native comment-sicko and poteto-agent profiles."""

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "skills/core/model-capability-router/assets/agents"
sys.path.insert(0, str(ROOT / "scripts"))
from native_agent_profile_fixture import (  # noqa: E402
    PROFILE_NAMES,
    run_native_agent_profile_fixture,
)


OBSERVED_NATIVE_SURFACE = {
    "create_thread": ("prompt", "target", "thinking", "model", "title"),
    "send_message_to_thread": ("threadId", "prompt", "thinking", "model"),
    "wait_threads": ("targets", "timeoutMs"),
}


class NativeAgentProfileFixtureTests(unittest.TestCase):
    def test_current_surface_stops_at_static_fixture_proof(self):
        with tempfile.TemporaryDirectory() as temporary:
            sentinel = Path(temporary) / "config-sentinel"
            sentinel.write_text("unchanged\n")
            result = run_native_agent_profile_fixture(
                ASSETS,
                OBSERVED_NATIVE_SURFACE,
                synthetic_input="SAFE_SYNTHETIC_PROFILE_PROBE",
            )
            self.assertEqual(result["status"], "STATIC_PROOF_ONLY")
            self.assertTrue(result["fixture_only"])
            self.assertFalse(result["writes_performed"])
            self.assertFalse(result["session_created"])
            self.assertEqual(result["discovery"]["status"], "NOT_EXPOSED")
            self.assertEqual(result["discovery"]["exposed_selectors"], ())
            self.assertEqual(result["nominal_selection"]["status"], "NOT_ATTEMPTED")
            self.assertEqual(
                {item["name"] for item in result["instructions"]},
                set(PROFILE_NAMES),
            )
            self.assertTrue(
                all(
                    item["static_toml_load"] == "PASS"
                    and item["session_instruction_load"] == "NOT_OBSERVED"
                    for item in result["instructions"]
                )
            )
            instructions = {
                item["name"]: item["skill_references"]
                for item in result["instructions"]
            }
            self.assertIn("cursor-how", instructions["comment-sicko"])
            self.assertIn("cursor-why", instructions["comment-sicko"])
            self.assertIn("cursor-poteto-mode", instructions["poteto-agent"])
            self.assertIn("cursor-principle-*", instructions["poteto-agent"])
            self.assertEqual(result["execution"]["status"], "FIXTURE_ONLY")
            self.assertEqual(
                [item["synthetic_input"] for item in result["execution"]["returns"]],
                ["SAFE_SYNTHETIC_PROFILE_PROBE"] * len(PROFILE_NAMES),
            )
            self.assertEqual(result["limits"]["skills_invoked"], ())
            self.assertEqual(result["limits"]["host"], "local fixture")
            self.assertIn("1 discovery: NOT_EXPOSED", result["report"])
            self.assertIn("2 nominal selection: NOT_ATTEMPTED", result["report"])
            self.assertIn("6 limits:", result["report"])
            self.assertEqual(sentinel.read_text(), "unchanged\n")

    def test_surface_with_selector_is_detected_but_never_invoked(self):
        surface = dict(OBSERVED_NATIVE_SURFACE)
        surface["hypothetical_native_tool"] = ("agent_type", "prompt")
        result = run_native_agent_profile_fixture(ASSETS, surface)
        self.assertEqual(result["status"], "STATIC_PROOF_ONLY")
        self.assertEqual(result["discovery"]["status"], "EXPOSED_NOT_RUN")
        self.assertEqual(result["discovery"]["exposed_selectors"], ("agent_type",))
        self.assertEqual(result["nominal_selection"]["status"], "NOT_ATTEMPTED")
        self.assertFalse(result["session_created"])

    def test_missing_profile_or_malformed_surface_is_error_without_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "comment-sicko.toml").write_text(
                "name='comment-sicko'\n"
                "description='fixture'\n"
                "developer_instructions='fixture'\n"
            )
            result = run_native_agent_profile_fixture(
                root,
                {"create_thread": "not-a-field-list"},
            )
            self.assertEqual(result["status"], "ERROR")
            self.assertTrue(result["fixture_only"])
            self.assertFalse(result["writes_performed"])
            self.assertFalse(result["session_created"])
            self.assertIn("must be iterable", result["reason"])

            malformed = run_native_agent_profile_fixture(
                root,
                OBSERVED_NATIVE_SURFACE,
            )
            self.assertEqual(malformed["status"], "ERROR")
            self.assertIn("missing or symlinked profile", malformed["reason"])


if __name__ == "__main__":
    unittest.main()
