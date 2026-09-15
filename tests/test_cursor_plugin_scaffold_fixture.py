"""Bounded static scaffold proof for the held create-plugin skill."""

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from cursor_plugin_scaffold_fixture import (  # noqa: E402
    MARKER, MARKER_CONTENT, scaffold_cursor_plugin_fixture,
)
from cursor_plugin_submission_audit import audit_plugin_fixture  # noqa: E402


class CursorPluginScaffoldFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cursor-scaffold-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / MARKER).write_text(MARKER_CONTENT)
        self.args = {
            "description": "Example: static local plugin",
            "author": "Fixture Author",
            "license_id": "MIT",
            "license_text": "Fixture license text\n",
            "components": ("skills", "rules", "agents", "commands"),
        }

    def call(self, **overrides):
        return scaffold_cursor_plugin_fixture(
            self.root, "example-plugin", project_root=self.root.parent,
            **(self.args | overrides)
        )

    def test_static_scaffold_is_explicit_local_and_auditable(self):
        result = self.call()
        self.assertEqual(result["status"], "FIXTURE_ONLY")
        self.assertTrue(result["created"])
        self.assertFalse(result["global_install"])
        self.assertFalse(result["marketplace_wired"])
        plugin = self.root / "example-plugin"
        manifest = json.loads((plugin / ".cursor-plugin/plugin.json").read_text())
        self.assertEqual(manifest["name"], "example-plugin")
        self.assertEqual((plugin / "LICENSE").read_text(), "Fixture license text\n")
        self.assertIn('description: "Example: static local plugin"',
                      (plugin / "skills/example-plugin/SKILL.md").read_text())
        audit = audit_plugin_fixture(plugin)
        self.assertEqual(audit["status"], "STRUCTURAL_PASS")
        self.assertEqual(audit["checked_component_files"], 4)
        self.assertFalse(audit["executed_components"])

    def test_active_components_and_marketplace_stop_before_write(self):
        blocked = self.call(components=("skills", "hooks", "mcpServers"))
        self.assertEqual(blocked["status"], "REVIEW_REQUIRED")
        self.assertEqual(blocked["requested_active_surfaces"], ["hooks", "mcpServers"])
        self.assertFalse(blocked["created"])
        self.assertEqual({p.name for p in self.root.iterdir()}, {MARKER})
        marketplace = self.call(marketplace=True)
        self.assertEqual(marketplace["status"], "REVIEW_REQUIRED")
        self.assertFalse(marketplace["created"])

    def test_missing_marker_invalid_name_and_nonempty_root_stop_before_write(self):
        (self.root / MARKER).unlink()
        self.assertEqual(self.call()["status"], "BLOCKED")
        (self.root / MARKER).write_text(MARKER_CONTENT)
        bad = scaffold_cursor_plugin_fixture(
            self.root, "../bad", project_root=self.root.parent, **self.args
        )
        self.assertEqual(bad["status"], "ERROR")
        self.assertFalse(bad["created"])
        (self.root / "existing.txt").write_text("preserve me")
        self.assertEqual(self.call()["status"], "BLOCKED")
        self.assertEqual((self.root / "existing.txt").read_text(), "preserve me")

    def test_symlinked_ancestor_cannot_escape_project_boundary(self):
        with tempfile.TemporaryDirectory(prefix="cursor-scaffold-project-") as project_dir, \
                tempfile.TemporaryDirectory(prefix="cursor-scaffold-outside-") as outside_dir:
            project = Path(project_dir)
            outside = Path(outside_dir)
            fixture = outside / "fixture"
            fixture.mkdir()
            (fixture / MARKER).write_text(MARKER_CONTENT)
            (project / "escape").symlink_to(outside, target_is_directory=True)
            result = scaffold_cursor_plugin_fixture(
                project / "escape/fixture", "example-plugin",
                project_root=project, **self.args,
            )
            self.assertEqual(result["status"], "BLOCKED")
            self.assertFalse(result["created"])
            self.assertFalse((fixture / "example-plugin").exists())


if __name__ == "__main__":
    unittest.main()
