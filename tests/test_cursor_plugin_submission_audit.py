"""Read-only structural proof for the held Cursor plugin submission auditor."""

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from cursor_plugin_submission_audit import audit_plugin_fixture  # noqa: E402


class PluginSubmissionAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cursor-plugin-audit-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".cursor-plugin").mkdir()
        (self.root / "skills/example").mkdir(parents=True)
        (self.root / "README.md").write_text("# Example\n\nPurpose and installation.\n")
        (self.root / "skills/example/SKILL.md").write_text(
            "---\nname: example\ndescription: Example skill\n---\n\n# Example\n"
        )
        self.manifest = {
            "name": "example-plugin", "description": "Example plugin",
            "version": "1.0.0", "author": {"name": "Example"}, "license": "MIT",
            "skills": "./skills/",
        }
        self.write_manifest()

    def write_manifest(self):
        (self.root / ".cursor-plugin/plugin.json").write_text(json.dumps(self.manifest))

    def test_valid_local_plugin_has_structural_pass_without_execution(self):
        result = audit_plugin_fixture(self.root)
        self.assertEqual(result["status"], "STRUCTURAL_PASS")
        self.assertEqual(result["checked_component_files"], 1)
        self.assertEqual(result["issues"], [])
        self.assertFalse(result["executed_components"])
        self.assertEqual(result["submission_recommendation"], "not_assessed")

    def test_missing_metadata_and_broken_component_are_reported(self):
        self.manifest["name"] = "Bad Plugin"
        self.manifest["skills"] = "./missing/"
        self.write_manifest()
        result = audit_plugin_fixture(self.root)
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("invalid lowercase kebab-case plugin name", result["issues"])
        self.assertIn("declared skills path missing", result["issues"])
        self.assertFalse(result["executed_components"])

    def test_missing_frontmatter_is_reported_without_opening_component(self):
        (self.root / "skills/example/SKILL.md").write_text("# Missing metadata\n")
        result = audit_plugin_fixture(self.root)
        self.assertEqual(result["status"], "ERROR")
        self.assertIn(
            "skills/example/SKILL.md missing frontmatter: description, name",
            result["issues"],
        )
        self.assertFalse(result["executed_components"])

    def test_hook_mcp_and_unsafe_path_remain_review_only(self):
        (self.root / "hooks").mkdir()
        (self.root / "hooks/hooks.json").write_text('{"danger":"never run"}')
        (self.root / "mcp.json").write_text('{"mcpServers":{"x":{"command":"touch outside"}}}')
        self.manifest["mcpServers"] = {"x": {"command": "touch outside"}}
        self.write_manifest()
        result = audit_plugin_fixture(self.root)
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertEqual(result["review_surfaces"], ["hooks", "mcp", "mcpServers"])
        self.assertFalse(result["executed_components"])
        self.assertFalse((self.root.parent / "outside").exists())

        self.manifest["skills"] = "../outside/"
        self.write_manifest()
        escaped = audit_plugin_fixture(self.root)
        self.assertEqual(escaped["status"], "ERROR")
        self.assertIn("skills path escapes or links outside plugin", escaped["issues"])

    def test_symlinked_hook_config_is_reported_as_unsafe(self):
        (self.root / "hooks").mkdir()
        outside = self.root.parent / f"{self.root.name}-outside-hook.json"
        outside.write_text('{"command":"never execute"}')
        try:
            (self.root / "hooks/hooks.json").symlink_to(outside)
            result = audit_plugin_fixture(self.root)
            self.assertEqual(result["status"], "ERROR")
            self.assertIn("unsafe hooks path escapes or links outside plugin", result["issues"])
            self.assertFalse(result["executed_components"])
        finally:
            outside.unlink()


if __name__ == "__main__":
    unittest.main()
