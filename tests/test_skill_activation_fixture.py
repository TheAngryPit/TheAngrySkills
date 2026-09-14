"""Static fixture checks; live Codex discovery and activation need runtime proof."""

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


ROUTER_SOURCE = ROOT / "skills/core/model-capability-router/SKILL.md"


class SkillActivationFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.fixture_root = Path(self.temporary.name)
        skills = self.fixture_root / ".agents" / "skills"
        explicit = skills / "fixture-explicit-only"
        implicit = skills / "fixture-implicit-eligible"
        router = skills / "model-capability-router"
        for skill in (explicit, implicit, router):
            skill.mkdir(parents=True)
        (explicit / "SKILL.md").write_text(
            "---\nname: fixture-explicit-only\ndescription: Synthetic explicit test\n---\n\nEXPLICIT_MARKER\n",
            encoding="utf-8",
        )
        (explicit / "agents").mkdir()
        (explicit / "agents" / "openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: false\n", encoding="utf-8"
        )
        (implicit / "SKILL.md").write_text(
            "---\nname: fixture-implicit-eligible\ndescription: Synthetic implicit test\n---\n\nIMPLICIT_MARKER\n",
            encoding="utf-8",
        )
        self.router_fixture = router / "SKILL.md"
        self.router_fixture.write_bytes(ROUTER_SOURCE.read_bytes())

    def test_catalogue_is_separate_from_selected_full_skill_reads(self):
        result = scan_skill_catalogue(
            self.fixture_root,
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
            self.fixture_root,
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
        self.assertEqual(explicit["status"], "EXPLICIT_TOKEN_PRESENT_NOT_OBSERVED")
        self.assertFalse(explicit["prompt_contains_path"])
        self.assertTrue(explicit["full_skill_read"])

        unmentioned = classify_activation_request(
            scan_skill_catalogue(self.fixture_root),
            skill_name="fixture-explicit-only",
            prompt="Answer the unrelated synthetic question.",
            implicit_trigger="synthetic implicit activation trigger check",
        )
        self.assertEqual(unmentioned["status"], "NOT_SELECTED")
        self.assertFalse(unmentioned["full_skill_read"])

    def test_implicit_probe_is_eligible_but_runtime_result_is_not_invented(self):
        result = scan_skill_catalogue(self.fixture_root)
        implicit = classify_activation_request(
            result,
            skill_name="fixture-implicit-eligible",
            prompt="Run a synthetic implicit activation trigger check now.",
            implicit_trigger="synthetic implicit activation trigger check",
        )
        self.assertEqual(implicit["status"], "IMPLICIT_ELIGIBLE_NOT_OBSERVED")
        self.assertFalse(implicit["full_skill_read"])

    def test_router_is_exact_copy_and_name_only_catalogue_check_stops_before_body(self):
        result = scan_skill_catalogue(self.fixture_root)
        router = classify_activation_request(
            result,
            skill_name="model-capability-router",
            prompt="Check whether the model-capability-router skill is in the catalogue by name only.",
        )
        self.assertEqual(router["status"], "NOT_SELECTED")
        self.assertTrue(router["catalogue_discovered"])
        self.assertFalse(router["full_skill_read"])
        copy_result = verify_exact_copy(ROUTER_SOURCE, self.router_fixture)
        self.assertTrue(copy_result["byte_match"])
        self.assertEqual(copy_result["source_sha256"], copy_result["candidate_sha256"])

    def test_missing_fixture_is_read_only_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "missing project skill root"):
                scan_skill_catalogue(temporary)


if __name__ == "__main__":
    unittest.main()
