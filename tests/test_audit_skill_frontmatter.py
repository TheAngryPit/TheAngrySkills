#!/usr/bin/env python3
"""Regression tests for skill frontmatter auditing."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDITOR_PATH = REPO_ROOT / "skills" / "core" / "skill-catalog-curator" / "scripts" / "audit_skill_frontmatter.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_skill_frontmatter", AUDITOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load auditor from {AUDITOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SkillFrontmatterAuditTests(unittest.TestCase):
    def write_skill(self, skill_dir: Path, name: str) -> None:
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            textwrap.dedent(
                f"""\
                ---
                name: {name}
                description: Use when validating grouped skill folder audit behavior and directory naming invariants for TheAngrySkills.
                ---

                # {name}
                """
            ),
            encoding="utf-8",
        )

    def test_unquoted_colon_in_description_is_rejected(self) -> None:
        auditor = load_auditor()
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "bad-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                textwrap.dedent(
                    """\
                    ---
                    name: bad-skill
                    description: Use when broken. USE FOR: "bad trigger".
                    ---

                    # Bad Skill
                    """
                ),
                encoding="utf-8",
            )

            result = auditor.audit_skill(skill_dir, "shared")

        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("frontmatter-parse", codes)
        self.assertGreater(result["counts"]["error"], 0)

    def test_quoted_colon_in_description_is_accepted(self) -> None:
        auditor = load_auditor()
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "good-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                textwrap.dedent(
                    """\
                    ---
                    name: good-skill
                    description: 'Use when broken. USE FOR: "good trigger".'
                    ---

                    # Good Skill
                    """
                ),
                encoding="utf-8",
            )

            result = auditor.audit_skill(skill_dir, "shared")

        codes = {finding["code"] for finding in result["findings"]}
        self.assertNotIn("frontmatter-parse", codes)

    def test_flat_skill_directory_must_match_frontmatter_name(self) -> None:
        auditor = load_auditor()
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "writing-ticks"
            self.write_skill(skill_dir, "writing-ticks")

            result = auditor.audit_skill(skill_dir, "shared")

        codes = {finding["code"] for finding in result["findings"]}
        self.assertNotIn("directory-name-mismatch", codes)

    def test_flat_skill_directory_rejects_name_mismatch(self) -> None:
        auditor = load_auditor()
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "skills" / "loop-router"
            self.write_skill(skill_dir, "themindshift-loop-router")

            result = auditor.audit_skill(skill_dir, "shared")

        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("directory-name-mismatch", codes)
        self.assertGreater(result["counts"]["error"], 0)

    def test_grouped_skill_pack_allows_nested_matching_leaf_directory(self) -> None:
        auditor = load_auditor()
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "skills" / "themindshift-editorial" / "themindshift-loop-router"
            self.write_skill(skill_dir, "themindshift-loop-router")

            result = auditor.audit_skill(skill_dir, "shared")

        codes = {finding["code"] for finding in result["findings"]}
        self.assertNotIn("directory-name-mismatch", codes)

    def test_grouped_skill_pack_allows_organizational_leaf_directory(self) -> None:
        auditor = load_auditor()
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "skills" / "themindshift-editorial" / "loop-router"
            self.write_skill(skill_dir, "themindshift-loop-router")

            result = auditor.audit_skill(skill_dir, "shared")

        codes = {finding["code"] for finding in result["findings"]}
        self.assertNotIn("directory-name-mismatch", codes)

    def test_categorized_pack_allows_organizational_leaf_directory(self) -> None:
        auditor = load_auditor()
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "skills" / "knowledge" / "themindshift" / "loop-router"
            self.write_skill(skill_dir, "themindshift-loop-router")

            result = auditor.audit_skill(skill_dir, "shared")

        codes = {finding["code"] for finding in result["findings"]}
        self.assertNotIn("directory-name-mismatch", codes)

    def test_category_direct_skill_still_rejects_name_mismatch(self) -> None:
        auditor = load_auditor()
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "skills" / "core" / "loop-router"
            self.write_skill(skill_dir, "themindshift-loop-router")

            result = auditor.audit_skill(skill_dir, "shared")

        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("directory-name-mismatch", codes)

    def test_find_skill_dirs_discovers_nested_grouped_pack_skills(self) -> None:
        auditor = load_auditor()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            flat_skill = root / "writing-ticks"
            grouped_skill = root / "echo-ingest-knowledge" / "echo-ingest-source-intake"
            self.write_skill(flat_skill, "writing-ticks")
            self.write_skill(grouped_skill, "echo-ingest-source-intake")
            project_skill = root / "TheMindShift" / "loop-router"
            self.write_skill(project_skill, "themindshift-loop-router")

            discovered = auditor.find_skill_dirs(root)

        self.assertEqual(
            sorted(str(path.relative_to(root)) for path in discovered),
            ["TheMindShift/loop-router", "echo-ingest-knowledge/echo-ingest-source-intake", "writing-ticks"],
        )


if __name__ == "__main__":
    unittest.main()
