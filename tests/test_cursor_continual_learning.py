"""Renderer boundary for the proposal-only continual-learning adaptation."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "sync_cursor_plugin_skills", REPO / "scripts/sync-cursor-plugin-skills.py"
)
sync = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(sync)


class CursorContinualLearningTests(unittest.TestCase):
    def test_published_skill_excludes_mutating_upstream_role(self):
        manifest = json.loads((REPO / "sources/cursor-plugins/manifest.json").read_text())
        entries = {item["published_name"]: item for item in manifest["skills"]}
        entry = entries["cursor-continual-learning"]
        self.assertTrue(entry["publish"])
        source_to_entry = {
            (sync.SOURCE / item["path"]).resolve(): item for item in entries.values()
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sync.render_skill(entry, root, manifest["upstream_commit"], source_to_entry)
            target = root / "cursor-continual-learning"
            skill = (target / "SKILL.md").read_text()
            self.assertFalse((target / "references/agents-memory-updater.md").exists())
            self.assertIn("proposal-only briefing", skill)
            self.assertIn("return `not-run`", skill)
            self.assertIn("Do not edit `AGENTS.md`", skill)


if __name__ == "__main__":
    unittest.main()
