"""Fixture-only proof for the cursor-setup-pstack model mapping boundary."""

import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from cursor_functional_adapters import (  # noqa: E402
    PSTACK_BUDGETS,
    PSTACK_MODEL_PANEL_ROLES,
    PSTACK_MODEL_ROLES,
    PSTACK_ROLE_PRESET_POLICY,
    run_pstack_model_mapping_fixture,
)


INVENTORY = {
    "gpt-5.6-sol": ("medium", "high"),
    "gpt-5.6-luna": ("high", "xhigh"),
    "gpt-6-astra": ("low", "medium"),
}

BUDGET_INVENTORY = {
    "gpt-5.6-sol": ("medium", "high", "xhigh"),
    "gpt-5.6-luna": ("medium", "high", "xhigh"),
    "gpt-6-astra": ("low", "medium", "high"),
    "cursor-grok-4.6-medium-fast": ("medium",),
}

PRESET_INVENTORY = {
    "gpt-6.1-sol": ("medium", "high"),
    "gpt-6-luna": ("high", "xhigh", "max"),
    "gpt-6-astra": ("low", "xhigh"),
}

EXPECTED_PSTACK_ROLES = (
    "feature, refactoring",
    "bug-fix",
    "perf-issue",
    "hillclimb",
    "judgment and prose",
    "hardest tasks",
    "how explorer",
    "how explainer",
    "why investigators",
    "why synthesizer",
    "reflect tooling",
    "reflect judgment, divergent, synthesizer",
    "arena runners",
    "arena cross-judge pool",
    "swarm workers",
    "architect runners",
    "interrogate reviewers",
)


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

    def test_new_setup_uses_default_preset_and_keeps_selection_distinct(self):
        result = run_pstack_model_mapping_fixture(
            PRESET_INVENTORY, {}, new_setup=True
        )
        self.assertEqual(result["status"], "DRY_RUN")
        self.assertIsNone(result["selected_preset"])
        self.assertEqual(result["applied_preset"], "equilibrado")
        self.assertEqual(result["default_preset"], "equilibrado")
        self.assertEqual(result["preset_source"], "default")
        self.assertEqual(PSTACK_MODEL_ROLES, EXPECTED_PSTACK_ROLES)
        self.assertEqual(set(result["mapping"]), set(PSTACK_MODEL_ROLES))
        policy = PSTACK_ROLE_PRESET_POLICY
        default = policy["presets"][policy["default_preset"]]
        for role, metadata in ((item["label"], item) for item in policy["roles"]):
            expected = default["classes"][metadata["class"]]
            selection = result["mapping"][role]["selections"][0]
            self.assertEqual(
                selection["selection"],
                {"model": expected["model"], "effort": expected["effort"]},
                role,
            )
            self.assertEqual(selection["source"], "default-preset", role)
            self.assertEqual(result["mapping"][role]["panel"], metadata["panel"])
            if metadata["panel"]:
                self.assertEqual(result["mapping"][role]["count"], 1, role)

        limited = dict(PRESET_INVENTORY)
        limited.pop("gpt-6-luna")
        blocked = run_pstack_model_mapping_fixture(
            limited, {}, new_setup=True
        )
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(
            blocked["mapping"]["bug-fix"]["selections"][0]["selection"],
            {"model": "gpt-6-luna", "effort": "xhigh"},
        )
        self.assertEqual(
            blocked["mapping"]["bug-fix"]["selections"][0]["availability"],
            "needs-choice",
        )
        self.assertFalse(blocked["writes_performed"])

        limited_effort = dict(PRESET_INVENTORY)
        limited_effort["gpt-6.1-sol"] = ("high",)
        blocked_effort = run_pstack_model_mapping_fixture(
            limited_effort, {}, preset="power"
        )
        self.assertEqual(blocked_effort["status"], "BLOCKED")
        self.assertEqual(
            blocked_effort["mapping"]["bug-fix"]["selections"][0]["selection"],
            {"model": "gpt-6.1-sol", "effort": "medium"},
        )
        self.assertEqual(
            blocked_effort["mapping"]["bug-fix"]["selections"][0]["availability"],
            "needs-choice",
        )

    def test_power_maps_workers_and_tooling_without_fallback(self):
        result = run_pstack_model_mapping_fixture(
            PRESET_INVENTORY, {}, preset="power"
        )
        self.assertEqual(result["status"], "DRY_RUN")
        self.assertEqual(result["selected_preset"], "power")
        self.assertEqual(result["applied_preset"], "power")
        self.assertEqual(result["preset_source"], "selected")
        self.assertEqual(
            result["coordinator_recommendation"],
            {
                "model": "gpt-6.1-sol",
                "effort": "high",
                "when": "demanding coordination; preserve an explicit operator selection",
            },
        )
        for role, mapping in result["mapping"].items():
            if mapping["class"] in {"execution", "exploration_tooling"}:
                self.assertEqual(
                    mapping["selections"][0]["selection"],
                    {"model": "gpt-6.1-sol", "effort": "medium"},
                    role,
                )
            else:
                self.assertEqual(
                    mapping["selections"][0]["selection"],
                    {"model": "gpt-6-astra", "effort": "low"},
                    role,
                )

        limited = dict(PRESET_INVENTORY)
        limited.pop("gpt-6.1-sol")
        blocked = run_pstack_model_mapping_fixture(
            limited, {}, preset="power"
        )
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(
            blocked["mapping"]["bug-fix"]["selections"][0]["selection"],
            {"model": "gpt-6.1-sol", "effort": "medium"},
        )
        self.assertEqual(
            blocked["mapping"]["bug-fix"]["selections"][0]["availability"],
            "needs-choice",
        )
        self.assertFalse(blocked["writes_performed"])

    def test_selected_preset_preserves_explicit_roles_and_panel_entries(self):
        choices = {
            "hardest tasks": {"model": "gpt-6-astra", "effort": "xhigh"},
            "arena runners": [
                {"model": "inherit-parent"},
                {"model": "gpt-6-luna", "effort": "max"},
            ],
        }
        result = run_pstack_model_mapping_fixture(
            PRESET_INVENTORY, choices, preset="power"
        )
        self.assertEqual(result["status"], "DRY_RUN")
        self.assertEqual(
            result["mapping"]["hardest tasks"]["selections"][0]["selection"],
            choices["hardest tasks"],
        )
        self.assertEqual(
            [
                item["selection"]
                for item in result["mapping"]["arena runners"]["selections"]
            ],
            choices["arena runners"],
        )
        self.assertEqual(result["mapping"]["arena runners"]["count"], 2)
        self.assertEqual(
            result["mapping"]["bug-fix"]["selections"][0]["source"], "preset"
        )
        self.assertEqual(
            result["mapping"]["hardest tasks"]["selections"][0]["source"],
            "preserved-override",
        )
        self.assertTrue(
            all(
                item["source"] == "preserved-override"
                for item in result["mapping"]["arena runners"]["selections"]
            )
        )
        self.assertIn("[preserved explicit override]", result["dry_run"])

    def test_partial_existing_mapping_needs_an_explicit_preset_or_new_setup(self):
        result = run_pstack_model_mapping_fixture(
            PRESET_INVENTORY, {"bug-fix": {"model": "gpt-6-luna", "effort": "high"}}
        )
        self.assertEqual(result["status"], "ERROR")
        self.assertTrue(
            any("missing roles" in item for item in result["details"])
        )
        self.assertFalse(result["writes_performed"])

    def test_preset_and_global_budget_are_mutually_exclusive(self):
        result = run_pstack_model_mapping_fixture(
            PRESET_INVENTORY, {}, preset="equilibrado", budget="small"
        )
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("not both", result["reason"])
        self.assertFalse(result["writes_performed"])

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
        self.assertIn("not-in-channel", result["dry_run"])

    def test_malformed_panel_is_an_explicit_error_without_write(self):
        choices = choices_for_all_roles()
        choices["arena runners"] = {"model": "gpt-5.6-sol", "effort": "medium"}
        result = run_pstack_model_mapping_fixture(INVENTORY, choices)
        self.assertEqual(result["status"], "ERROR")
        self.assertFalse(result["writes_performed"])
        self.assertFalse(result["configuration_changed"])
        self.assertIn("non-empty model panel list", result["reason"])
        self.assertIn("ERROR:", result["dry_run"])

    def test_alias_effort_needs_parent_model_before_validation(self):
        choices = choices_for_all_roles()
        choices["hardest tasks"] = {"model": "auto", "effort": "xhigh"}
        result = run_pstack_model_mapping_fixture(INVENTORY, choices)
        self.assertEqual(result["status"], "ERROR")
        self.assertFalse(result["writes_performed"])
        self.assertIn("without the parent model", result["reason"])

    def test_budget_maps_efforts_and_same_family_model_variants_without_write(self):
        choices = choices_for_all_roles()
        choices["bug-fix"] = "grok-4.6-fast-xhigh"
        result = run_pstack_model_mapping_fixture(
            BUDGET_INVENTORY, choices, budget="small"
        )
        self.assertEqual(result["status"], "DRY_RUN")
        self.assertEqual(result["budget"], "small")
        self.assertEqual(result["budget_label"], PSTACK_BUDGETS["small"]["label"])
        self.assertEqual(result["target_effort"], "medium")
        self.assertFalse(result["writes_performed"])
        bug_fix = result["mapping"]["bug-fix"]["selections"][0]
        self.assertEqual(
            bug_fix["selection"],
            {"model": "cursor-grok-4.6-medium-fast", "effort": "medium"},
        )
        self.assertEqual(
            bug_fix["requested_selection"], {"model": "grok-4.6-fast-xhigh"}
        )
        self.assertEqual(
            result["mapping"]["feature, refactoring"]["selections"][0]["selection"],
            {"model": "gpt-5.6-sol", "effort": "medium"},
        )
        self.assertEqual(
            result["mapping"]["judgment and prose"]["selections"][0]["selection"],
            {"model": "inherit-parent"},
        )
        self.assertIn("budget: small — medium reasoning (medium)", result["dry_run"])

        for budget, specification in PSTACK_BUDGETS.items():
            budget_choices = choices_for_all_roles()
            if budget != "unlimited":
                budget_choices["bug-fix"] = "grok-4.6-fast-xhigh"
            budget_result = run_pstack_model_mapping_fixture(
                BUDGET_INVENTORY, budget_choices, budget=budget
            )
            self.assertEqual(budget_result["status"], "DRY_RUN", budget)
            self.assertEqual(budget_result["budget_label"], specification["label"])
            self.assertEqual(
                budget_result["target_effort"], specification["target_effort"]
            )

    def test_budget_without_supported_effort_marks_roles_needing_choice(self):
        choices = choices_for_all_roles()
        unavailable_inventory = dict(BUDGET_INVENTORY)
        unavailable_inventory["gpt-5.6-luna"] = ("max",)
        result = run_pstack_model_mapping_fixture(
            unavailable_inventory, choices, budget="small"
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["writes_performed"])
        self.assertTrue(
            any("no detected model in family 'gpt-5.6-luna'" in item for item in result["unavailable"])
        )
        self.assertTrue(
            any(
                item["availability"] == "needs-choice"
                for item in result["mapping"]["how explorer"]["selections"]
            )
        )

    def test_unknown_budget_is_an_explicit_error_without_write(self):
        result = run_pstack_model_mapping_fixture(
            INVENTORY, choices_for_all_roles(), budget="tiny"
        )
        self.assertEqual(result["status"], "ERROR")
        self.assertFalse(result["writes_performed"])
        self.assertFalse(result["configuration_changed"])
        self.assertIn("budget must be one of", result["reason"])


if __name__ == "__main__":
    unittest.main()
