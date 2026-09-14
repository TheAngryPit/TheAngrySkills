"""Proof boundaries for local Codex skill discovery and activation."""

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from skill_activation_fixture import (  # noqa: E402
    classify_activation_request,
    scan_skill_catalogue,
    verify_exact_copy,
)


FIXTURE_ROOT = Path("/private/tmp/skill-activation-luna.0xFjUr")
ROUTER_SOURCE = ROOT / "skills/core/model-capability-router/SKILL.md"
ROUTER_FIXTURE = FIXTURE_ROOT / ".agents/skills/model-capability-router/SKILL.md"


class SkillActivationFixtureTests(unittest.TestCase):
    def test_catalogue_is_separate_from_selected_full_skill_reads(self):
        result = scan_skill_catalogue(
            FIXTURE_ROOT,
            full_read_names=("fixture-explicit-only",),
        )
        self.assertEqual(
            result["catalogue_names"],
            (
                "fixture-explicit-only",
                "fixture-implicit-eligible",
                "model-capability-router",
            ),
        )
        self.assertEqual(result["full_skill_read_names"], ("fixture-explicit-only",))
        entries = {entry["name"]: entry for entry in result["catalogue"]}
        self.assertFalse(entries["fixture-explicit-only"]["allow_implicit_invocation"])
        self.assertTrue(entries["fixture-implicit-eligible"]["allow_implicit_invocation"])
        self.assertFalse(entries["model-capability-router"]["full_skill_read"])

    def test_explicit_only_requires_name_and_no_path(self):
        result = scan_skill_catalogue(
            FIXTURE_ROOT,
            full_read_names=("fixture-explicit-only",),
        )
        explicit_prompt = (
            "Use $fixture-explicit-only and return its exact activation marker."
        )
        explicit = classify_activation_request(
            result,
            skill_name="fixture-explicit-only",
            prompt=explicit_prompt,
            implicit_trigger="synthetic implicit activation trigger check",
        )
        self.assertEqual(explicit["status"], "EXPLICIT_NAME_RESOLVED")
        self.assertFalse(explicit["prompt_contains_path"])
        self.assertTrue(explicit["full_skill_read"])

        unmentioned = classify_activation_request(
            scan_skill_catalogue(FIXTURE_ROOT),
            skill_name="fixture-explicit-only",
            prompt="Answer the unrelated synthetic question.",
            implicit_trigger="synthetic implicit activation trigger check",
        )
        self.assertEqual(unmentioned["status"], "NOT_SELECTED")
        self.assertFalse(unmentioned["full_skill_read"])

    def test_implicit_probe_is_eligible_but_runtime_result_is_not_invented(self):
        result = scan_skill_catalogue(FIXTURE_ROOT)
        implicit = classify_activation_request(
            result,
            skill_name="fixture-implicit-eligible",
            prompt="Run a synthetic implicit activation trigger check now.",
            implicit_trigger="synthetic implicit activation trigger check",
        )
        self.assertEqual(implicit["status"], "IMPLICIT_ELIGIBLE_NOT_OBSERVED")
        self.assertFalse(implicit["full_skill_read"])

    def test_router_is_exact_copy_and_name_only_catalogue_check_stops_before_body(self):
        result = scan_skill_catalogue(FIXTURE_ROOT)
        router = classify_activation_request(
            result,
            skill_name="model-capability-router",
            prompt="Check whether the model-capability-router skill is in the catalogue by name only.",
        )
        self.assertEqual(router["status"], "NOT_SELECTED")
        self.assertTrue(router["catalogue_discovered"])
        self.assertFalse(router["full_skill_read"])
        copy_result = verify_exact_copy(ROUTER_SOURCE, ROUTER_FIXTURE)
        self.assertTrue(copy_result["byte_match"])
        self.assertEqual(copy_result["source_sha256"], copy_result["candidate_sha256"])

    def test_missing_fixture_is_read_only_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "missing project skill root"):
                scan_skill_catalogue(temporary)


if __name__ == "__main__":
    unittest.main()
