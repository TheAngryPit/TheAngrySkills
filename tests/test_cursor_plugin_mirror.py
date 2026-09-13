"""Behavioral guards for the pinned Cursor skill mirror build."""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent


class CursorMirrorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cursor-mirror-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in (
            "scripts/sync-cursor-plugin-skills.py",
            "sources/cursor-plugins",
            "skills/mirrors-cursor",
            "reports/cursor-plugin-skills-state.json",
            ".claude-plugin/marketplace.json",
        ):
            source = REPO / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)

    def run_build(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts/sync-cursor-plugin-skills.py"), *args],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_committed_tree_is_reproducible(self):
        result = self.run_build("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("91 physical, 53 published", result.stdout)

    def test_local_skill_edit_is_preserved_on_rebuild(self):
        skill = self.root / "skills/mirrors-cursor/cursor-cli-for-agents/SKILL.md"
        skill.write_text(skill.read_text() + "\nLocal operator change.\n")
        result = self.run_build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("local modifications", result.stderr)
        self.assertIn("Local operator change.", skill.read_text())

    def test_source_edit_requires_explicit_review(self):
        skill = self.root / "sources/cursor-plugins/snapshot/cli-for-agent/skills/cli-for-agents/SKILL.md"
        skill.write_text(skill.read_text() + "\nChanged upstream.\n")
        result = self.run_build("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("snapshot file drift", result.stderr)

    def test_untracked_snapshot_symlink_is_rejected(self):
        skill_dir = self.root / "sources/cursor-plugins/snapshot/cli-for-agent/skills/cli-for-agents"
        (skill_dir / "external").symlink_to(self.root, target_is_directory=True)
        result = self.run_build("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("untracked symlinks", result.stderr)

    def test_missing_cursor_marketplace_entry_is_rejected(self):
        marketplace = self.root / ".claude-plugin/marketplace.json"
        data = json.loads(marketplace.read_text())
        data["plugins"] = [plugin for plugin in data["plugins"] if plugin["name"] != "mirrors-cursor"]
        marketplace.write_text(json.dumps(data, indent=2) + "\n")
        result = self.run_build("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("generated mirror differs", result.stderr)

    def test_marketplace_follows_reviewed_promotion_set(self):
        manifest = self.root / "sources/cursor-plugins/manifest.json"
        data = json.loads(manifest.read_text())
        entry = next(item for item in data["skills"] if item["published_name"] == "cursor-cli-for-agents")
        entry["publish"] = False
        manifest.write_text(json.dumps(data, indent=2) + "\n")
        result = self.run_build()
        self.assertEqual(result.returncode, 0, result.stderr)
        marketplace = json.loads((self.root / ".claude-plugin/marketplace.json").read_text())
        cursor_family = next(plugin for plugin in marketplace["plugins"] if plugin["name"] == "mirrors-cursor")
        self.assertEqual(len(cursor_family["skills"]), 52)
        self.assertNotIn("./skills/mirrors-cursor/cursor-cli-for-agents", cursor_family["skills"])

    def test_published_relative_markdown_links_resolve(self):
        root = self.root / "skills/mirrors-cursor"
        links = 0
        for file in root.rglob("*.md"):
            for match in re.finditer(r"\]\(([^)]+)\)", file.read_text()):
                target = match.group(1).split("#", 1)[0]
                if not target or "://" in target or target.startswith(("/", "mailto:")):
                    continue
                links += 1
                self.assertTrue((file.parent / target).exists(), (file, target))
        self.assertGreater(links, 0)

    def test_published_frontmatter_parses_without_pyyaml(self):
        auditor = REPO / "skills/core/skill-catalog-curator/scripts/audit_skill_frontmatter.py"
        result = subprocess.run(
            [sys.executable, "-S", str(auditor),
             str(self.root / "skills/mirrors-cursor"), "--profile", "shared", "--json"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        results = json.loads(result.stdout)["results"]
        self.assertEqual(len(results), 53)
        for item in results:
            self.assertEqual(item["counts"]["error"], 0, item)

    def test_published_skills_do_not_reference_repo_only_proof_harness(self):
        root = self.root / "skills/mirrors-cursor"
        for skill in root.glob("*/SKILL.md"):
            self.assertNotIn("scripts/cursor_functional_adapters.py", skill.read_text(), skill)

    def test_new_upstream_skill_is_reported_without_import(self):
        upstream = self.root / "sources/cursor-plugins/snapshot"
        subprocess.run(["git", "init", "-q", str(upstream)], check=True)
        subprocess.run(["git", "-C", str(upstream), "-c", "user.name=Test",
                        "-c", "user.email=test@example.invalid", "commit", "--allow-empty",
                        "-qm", "fixture"], check=True)
        candidate = upstream / "new-family/skills/new-skill/SKILL.md"
        candidate.parent.mkdir(parents=True)
        candidate.write_text("---\nname: new-skill\ndescription: Fixture\n---\n")
        result = self.run_build("--compare-upstream", str(upstream))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("new-family/skills/new-skill/SKILL.md", result.stdout)
        self.assertFalse((self.root / "skills/mirrors-cursor/cursor-new-skill").exists())


if __name__ == "__main__":
    unittest.main()
