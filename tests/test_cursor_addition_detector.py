"""Regression proof for separately pinned additions in scheduled detection."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("addition_detector", ROOT / "scripts/detect-upstream-updates.py")
detector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(detector)


class AdditionDetectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "ours"
        self.upstream = Path(self.temp.name) / "upstream"
        self.upstream.mkdir()
        self.paths = [f"pstack/skills/{name}/SKILL.md" for name in ["base", "in-your-own-words", "ketchup", "sharpen"]]
        records = {}
        for path in self.paths:
            file = self.upstream / path
            file.parent.mkdir(parents=True)
            file.write_text("original " + path)
            records[path] = {"sha256": hashlib.sha256(file.read_bytes()).hexdigest()}
        self.git("init", "-q")
        self.commit()
        base = self.root / "sources/cursor-plugins"
        base.mkdir(parents=True)
        self.baseline = self.git("rev-parse", "HEAD").strip()
        (base / "full-tree.json").write_text(json.dumps({"commit": self.baseline, "files": {self.paths[0]: records[self.paths[0]]}}))
        (base / "additions.json").write_text(json.dumps({"files": {path: records[path] for path in self.paths[1:]}}))
        (base / "manifest.json").write_text(json.dumps({"skills": [{"path": path} for path in self.paths]}))
        self.before = {str(p): p.read_bytes() for p in self.root.rglob("*.json")}

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.upstream), *args], text=True)

    def commit(self):
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")

    def test_unchanged_promoted_skills_are_not_new(self):
        report = detector.detect_cursor(self.upstream, self.root)
        self.assertEqual(report["new_skills"], [])
        self.assertEqual(report["changed_skills"], [])
        self.assertEqual(report["removed_skills"], [])

    def test_change_and_removal_are_reported_without_mutating_baseline(self):
        changed, removed = self.paths[1:3]
        (self.upstream / changed).write_text("changed upstream")
        (self.upstream / removed).unlink()
        self.commit()
        report = detector.detect_cursor(self.upstream, self.root)
        self.assertEqual(report["new_skills"], [])
        self.assertEqual(report["changed_skills"], [changed])
        self.assertEqual(report["removed_skills"], [str(Path(removed).parent)])
        self.assertEqual(self.before, {str(p): p.read_bytes() for p in self.root.rglob("*.json")})

    def test_addition_cannot_override_baseline(self):
        file = self.root / "sources/cursor-plugins/additions.json"
        file.write_text(json.dumps({"files": {self.paths[0]: {"sha256": "altered"}}}))
        with self.assertRaisesRegex(ValueError, "collides with preserved baseline"):
            detector.detect_cursor(self.upstream, self.root)

    def test_malformed_family_refresh_is_rejected_before_detector_uses_it(self):
        directory = self.root / "sources/cursor-plugins"
        (directory / "family-refresh.json").write_text(json.dumps({
            "family": "pstack",
            "baseline_commit": self.baseline,
            "source_commit": self.baseline,
            "files": {"other-plugin/README.md": {
                "mode": "100644", "git_blob": "0" * 40,
                "sha256": "0" * 64, "source_commit": self.baseline,
            }},
            "overrides": {},
        }))
        with self.assertRaisesRegex(ValueError, "unsafe pstack family path"):
            detector.detect_cursor(self.upstream, self.root)
