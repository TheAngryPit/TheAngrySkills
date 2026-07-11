#!/usr/bin/env python3

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "route.py"
PRESET = ROOT / "assets" / "vitor-opinionated.toml"


class RouteTests(unittest.TestCase):
    def run_cli(self, *args: str, expected: int = 0):
        result = subprocess.run(["python3", str(SCRIPT), *args], text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_preset_validates(self):
        self.assertTrue(self.run_cli("validate", "--preset", str(PRESET))["valid"])

    def test_public_example_matches_builder_source(self):
        builder = ROOT.parent / "model-routing-preset-builder" / "assets" / "vitor-opinionated.toml"
        if builder.is_file():
            self.assertEqual(PRESET.read_bytes(), builder.read_bytes())

    def test_spark_falls_back_to_luna_light(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET), "--route", "micro",
            "--available-model", "gpt-5.6-luna",
        )
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["selection"], {"model": "gpt-5.6-luna", "effort": "low"})

    def test_unknown_availability_blocks(self):
        result = self.run_cli(
            "resolve", "--preset", str(PRESET), "--route", "coordination",
            expected=1,
        )
        self.assertEqual(result["status"], "blocked")

    def test_missing_capability_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli(
                "resolve", "--preset", str(PRESET), "--route", "review",
                "--available-model", "gpt-5.6-sol", "--capability", "security_review",
                "--skill-root", directory, expected=1,
            )
            self.assertIn("security-scan", result["missing_skills"])

    def test_inventory_uses_frontmatter_name(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "different-folder"
            skill.mkdir()
            (skill / "SKILL.md").write_text("---\nname: canonical-name\n---\n", encoding="utf-8")
            result = self.run_cli("inventory", "--skill-root", directory)
            self.assertEqual(result["skills"], ["canonical-name"])


if __name__ == "__main__":
    unittest.main()
