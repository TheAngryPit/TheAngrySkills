#!/usr/bin/env python3
"""Regression tests for operational skill security admission helpers."""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "skills" / "core" / "skill-catalog-curator" / "scripts"
PIPELINE_PATH = SCRIPTS_ROOT / "security_admission_pipeline.py"
FIXTURE_TEMPLATES = REPO_ROOT / "tests" / "fixtures" / "security-skills"


def load_pipeline():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("security_admission_pipeline", PIPELINE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load pipeline from {PIPELINE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def materialize_fixtures(target: Path) -> Path:
    fixtures = target / "security-skills"
    shutil.copytree(FIXTURE_TEMPLATES, fixtures)
    for fixture_skill in fixtures.rglob("SKILL.fixture.md"):
        fixture_skill.rename(fixture_skill.with_name("SKILL.md"))
    return fixtures


class SecurityAdmissionPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = load_pipeline()
        cls.fixture_tmp = tempfile.TemporaryDirectory()
        cls.fixtures = materialize_fixtures(Path(cls.fixture_tmp.name))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture_tmp.cleanup()

    def test_update_plan_classifies_safe_review_and_blocked_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = root / "installed"
            candidate = root / "candidate"
            installed.mkdir()
            candidate.mkdir()
            shutil.copytree(self.fixtures / "safe-basic", installed / "safe-basic")
            shutil.copytree(self.fixtures / "safe-basic", candidate / "safe-basic")
            (candidate / "safe-basic" / "assets" / "new.txt").write_text("new safe file\n", encoding="utf-8")
            shutil.copytree(self.fixtures / "script-review", candidate / "script-review")
            shutil.copytree(self.fixtures / "remote-exec", candidate / "remote-exec")

            plan = self.pipeline.build_update_plan(candidate, installed)

        entries = {entry["skill"]: entry for entry in plan["entries"]}
        self.assertEqual(plan["report_type"], "update_plan")
        self.assertEqual(entries["safe-basic"]["action"], "update")
        self.assertTrue(entries["safe-basic"]["safe_to_apply"])
        self.assertEqual(entries["script-review"]["action"], "review")
        self.assertFalse(entries["script-review"]["safe_to_apply"])
        self.assertEqual(entries["remote-exec"]["action"], "block")
        self.assertFalse(entries["remote-exec"]["safe_to_apply"])

    def test_update_apply_requires_confirm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            plan_path.write_text('{"report_type":"update_plan","entries":[],"candidate_root":"' + tmp + '","installed_root":"' + tmp + '"}', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "requires --confirm"):
                self.pipeline.apply_update_plan(plan_path, only_safe=True, confirm=False)

    def test_update_apply_only_safe_copies_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = root / "installed"
            candidate = root / "candidate"
            installed.mkdir()
            candidate.mkdir()
            shutil.copytree(self.fixtures / "safe-basic", candidate / "safe-basic")
            shutil.copytree(self.fixtures / "remote-exec", candidate / "remote-exec")
            plan = self.pipeline.build_update_plan(candidate, installed)
            plan_path = root / "plan.json"
            self.pipeline.write_json(plan_path, plan)

            report = self.pipeline.apply_update_plan(plan_path, only_safe=True, confirm=True)

            self.assertEqual(report["summary"]["applied_count"], 1)
            self.assertTrue((installed / "safe-basic" / "SKILL.md").exists())
            self.assertFalse((installed / "remote-exec").exists())

    def test_quarantine_moves_skill_and_writes_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            quarantine_root = Path(tmp) / "quarantine"
            root.mkdir()
            shutil.copytree(self.fixtures / "remote-exec", root / "remote-exec")

            report = self.pipeline.quarantine_skill(
                "remote-exec",
                root,
                quarantine_root,
                "test quarantine",
                confirm=True,
            )

            self.assertEqual(report["status"], "quarantined")
            self.assertFalse((root / "remote-exec").exists())
            quarantine_path = Path(report["quarantine_path"])
            self.assertTrue((quarantine_path / "SKILL.md").exists())
            self.assertTrue((quarantine_path / "quarantine-meta.json").exists())

    def test_skillspector_unavailable_does_not_override_deterministic_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = self.pipeline.run_skillspector(
                self.fixtures / "safe-basic",
                Path(tmp) / "reports",
                "definitely-not-installed-skillspector",
                timeout=5,
            )

        self.assertEqual(report["report_type"], "skillspector_evidence")
        self.assertFalse(report["skillspector"]["available"])
        self.assertFalse(report["skillspector"]["used"])
        self.assertEqual(report["deterministic_verdict"], "safe_to_install")
        self.assertEqual(report["verdict"], "safe_to_install")

    def test_skillspector_failure_marks_safe_candidate_for_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "fake-skillspector"
            fake.write_text("#!/usr/bin/env sh\necho nope >&2\nexit 9\n", encoding="utf-8")
            os.chmod(fake, 0o700)

            report = self.pipeline.run_skillspector(
                self.fixtures / "safe-basic",
                Path(tmp) / "reports",
                str(fake),
                timeout=5,
            )

        self.assertTrue(report["skillspector"]["available"])
        self.assertTrue(report["skillspector"]["used"])
        self.assertEqual(report["skillspector"]["status"], "failed")
        self.assertEqual(report["verdict"], "needs_human_review")


if __name__ == "__main__":
    unittest.main()
