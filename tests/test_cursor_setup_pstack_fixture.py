"""Fixture-only proof for the cursor-setup-pstack model mapping boundary."""

import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from cursor_functional_adapters import (  # noqa: E402
    PSTACK_MODEL_PANEL_ROLES,
    PSTACK_MODEL_ROLES,
    run_pstack_model_mapping_fixture,
)


INVENTORY = {
    "gpt-5.6-sol": ("medium", "high"),
    "gpt-5.6-luna": ("high", "xhigh"),
    "gpt-6-astra": ("low", "medium"),
}


def choices_for_all_roles():
    choices = {
        "feature, refactoring": {"model": "gpt-5.6-sol", "effort": "medium"},
        "bug-fix": {"model": "gpt-5.6-luna", "effort": "high"},
        "perf-issue": "gpt-5.6-sol",
        "hillclimb": {"model": "gpt-6-astra", "effort": "low"},
        "judgment and prose": {"model": "inherit-parent"},
        "hardest tasks": {"model": "auto"},
        "how explorer": {"model": "gpt-5.6-luna", "effort": "xhigh"},
        "how explainer": {"model": "gpt-6-astra", "effort": "medium"},
        "why investigators": {"model": "gpt-5.6-sol", "effort": "high"},
        "why synthesizer": {"model": "gpt-6-astra", "effort": "low"},
        "reflect tooling": {"model": "gpt-5.6-luna", "effort": "high"},
        "reflect judgment, divergent, synthesizer": {"model": "auto"},
        "arena runners": [
            {"model": "gpt-5.6-luna", "effort": "xhigh"},
            {"model": "inherit-parent"},
        ],
        "arena cross-judge pool": [
            {"model": "gpt-6-astra", "effort": "low"},
            {"model": "auto"},
        ],
        "swarm workers": {"model": "gpt-5.6-sol", "effort": "medium"},
        "architect runners": [
            {"model": "gpt-5.6-luna", "effort": "high"},
            {"model": "gpt-6-astra", "effort": "medium"},
        ],
        "interrogate reviewers": [
            {"model": "inherit-parent"},
            {"model": "gpt-5.6-sol", "effort": "high"},
        ],
    }
    assert set(choices) == set(PSTACK_MODEL_ROLES)
    return choices


class CursorSetupPstackFixtureTests(unittest.TestCase):
    def test_positive_mapping_covers_every_role_and_preserves_choices(self):
        choices = choices_for_all_roles()
        with tempfile.TemporaryDirectory() as temporary:
            sentinel = Path(temporary) / "config-sentinel"
            sentinel.write_text("must remain unchanged\n")
            result = run_pstack_model_mapping_fixture(INVENTORY, choices)
            self.assertEqual(result["status"], "DRY_RUN")
            self.assertTrue(result["fixture_only"])
            self.assertFalse(result["writes_performed"])
            self.assertFalse(result["configuration_changed"])
            self.assertEqual(set(result["mapping"]), set(PSTACK_MODEL_ROLES))
            self.assertEqual(
                {
                    role
                    for role in PSTACK_MODEL_PANEL_ROLES
                    if result["mapping"][role]["panel"]
                },
                set(PSTACK_MODEL_PANEL_ROLES),
            )
            for role in PSTACK_MODEL_ROLES:
                expected = choices[role]
                expected_items = expected if isinstance(expected, list) else [expected]
                expected_items = [
                    item if isinstance(item, dict) else {"model": item}
                    for item in expected_items
                ]
                actual_items = [
                    item["selection"]
                    for item in result["mapping"][role]["selections"]
                ]
                self.assertEqual(actual_items, expected_items, role)
            self.assertEqual(result["mapping"]["arena runners"]["count"], 2)
            self.assertEqual(result["mapping"]["arena cross-judge pool"]["count"], 2)
            self.assertEqual(result["mapping"]["architect runners"]["count"], 2)
            self.assertEqual(result["mapping"]["interrogate reviewers"]["count"], 2)
            for role in PSTACK_MODEL_ROLES:
                self.assertIn(role, result["dry_run"])
            self.assertEqual(sentinel.read_text(), "must remain unchanged\n")

    def test_unavailable_model_and_effort_block_without_write(self):
        choices = choices_for_all_roles()
        choices["bug-fix"] = {"model": "not-in-channel", "effort": "xhigh"}
        choices["perf-issue"] = {"model": "gpt-5.6-sol", "effort": "xhigh"}
        result = run_pstack_model_mapping_fixture(INVENTORY, choices)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["writes_performed"])
        self.assertFalse(result["configuration_changed"])
        self.assertTrue(any("unavailable model" in item for item in result["unavailable"])
        )
        self.assertTrue(any("unavailable effort" in item for item in result["unavailable"])
        )
        self.assertIn("configuration unchanged", result["dry_run"])

    def test_malformed_panel_is_an_explicit_error_without_write(self):
        choices = choices_for_all_roles()
        choices["arena runners"] = {"model": "gpt-5.6-sol", "effort": "medium"}
        result = run_pstack_model_mapping_fixture(INVENTORY, choices)
        self.assertEqual(result["status"], "ERROR")
        self.assertFalse(result["writes_performed"])
        self.assertFalse(result["configuration_changed"])
        self.assertIn("non-empty model panel list", result["reason"])
        self.assertIn("ERROR:", result["dry_run"])


if __name__ == "__main__":
    unittest.main()
