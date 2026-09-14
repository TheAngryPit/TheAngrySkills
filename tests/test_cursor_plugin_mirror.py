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


def published_count(root: Path = REPO) -> int:
    manifest = json.loads((root / "sources/cursor-plugins/manifest.json").read_text())
    return sum(entry["publish"] for entry in manifest["skills"])


class CursorMirrorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cursor-mirror-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in (
            "scripts/sync-cursor-plugin-skills.py",
            "scripts/cursor_native_hook_adapters.py",
            "scripts/cursor_plugin_submission_audit.py",
            "scripts/cursor_plugin_scaffold_fixture.py",
            "scripts/cursor_bot_ui_adapters.py",
            "sources/cursor-plugins",
            "skills/mirrors-cursor",
            "skills/core/model-capability-router/assets/agents",
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
        self.assertIn(f"91 physical, {published_count()} published", result.stdout)

    def test_cursor_explicit_only_policy_is_native_and_complete(self):
        manifest = json.loads((REPO / "sources/cursor-plugins/manifest.json").read_text())
        for entry in manifest["skills"]:
            if not entry["publish"]:
                continue
            source = (REPO / "sources/cursor-plugins/snapshot" / entry["path"]).read_text()
            name = entry["published_name"]
            output = REPO / "skills/mirrors-cursor" / name
            explicit = bool(re.search(r"^disable-model-invocation:[ \t]*true[ \t]*$", source, re.MULTILINE))
            overlay = json.loads((REPO / "sources/cursor-plugins/overlays" / f"{name}.json").read_text())
            adapted_explicit = overlay.get("codex_contract", {}).get("invocation_policy") == "explicit_only"
            if adapted_explicit:
                self.assertTrue(
                    any("disable-model-invocation: true" in op["after"] for op in overlay.get("replacements", [])),
                    name,
                )
            policy = output / "agents/openai.yaml"
            frontmatter = re.match(r"\A---\n(.*?)\n---", (output / "SKILL.md").read_text(), re.DOTALL)
            self.assertIsNotNone(frontmatter, name)
            self.assertNotIn("disable-model-invocation:", frontmatter.group(1), name)
            if explicit or adapted_explicit:
                self.assertEqual(policy.read_text(), "policy:\n  allow_implicit_invocation: false\n", name)
            else:
                self.assertFalse(policy.exists(), name)

    def test_held_preview_preserves_explicit_only_policy(self):
        preview = self.root / "native-preview"
        result = self.run_build("--preview-candidates", str(preview))
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((REPO / "sources/cursor-plugins/manifest.json").read_text())
        for entry in manifest["skills"]:
            if not entry["declared_for_distribution"] or entry["publish"] or entry.get("excluded_from_mirror"):
                continue
            source = (REPO / "sources/cursor-plugins/snapshot" / entry["path"]).read_text()
            if not re.search(r"^disable-model-invocation:[ \t]*true[ \t]*$", source, re.MULTILINE):
                continue
            output = preview / entry["published_name"]
            self.assertEqual(
                (output / "agents/openai.yaml").read_text(),
                "policy:\n  allow_implicit_invocation: false\n",
            )
            frontmatter = re.match(r"\A---\n(.*?)\n---", (output / "SKILL.md").read_text(), re.DOTALL)
            self.assertIsNotNone(frontmatter, entry["published_name"])
            self.assertNotIn("disable-model-invocation:", frontmatter.group(1))

    def test_operator_exclusion_is_not_rendered_or_promotable(self):
        manifest_path = self.root / "sources/cursor-plugins/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        excluded = next(e for e in manifest["skills"] if e["published_name"] == "cursor-make-bot-ui")
        self.assertTrue(excluded["excluded_from_mirror"])
        self.assertFalse(excluded["publish"])
        self.assertTrue((self.root / "sources/cursor-plugins/snapshot" / excluded["path"]).is_file())
        state = json.loads((self.root / "reports/cursor-plugin-skills-state.json").read_text())
        self.assertEqual(state["candidate_not_published"], 16)
        self.assertEqual(state["operator_excluded_skills"], 1)
        preview = self.root / "native-preview"
        result = self.run_build("--preview-candidates", str(preview))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((preview / "cursor-make-bot-ui").exists())
        self.assertFalse((self.root / "skills/mirrors-cursor/cursor-make-bot-ui").exists())
        excluded["publish"] = True
        manifest_path.write_text(json.dumps(manifest))
        rejected = self.run_build("--check")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("excluded source cannot be published", rejected.stderr)

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

    def test_plugin_level_agent_is_pinned_and_transitively_mapped(self):
        manifest = json.loads((self.root / "sources/cursor-plugins/manifest.json").read_text())
        support = manifest["support_files"]
        self.assertEqual(len(support), 27)
        self.assertIn(
            "cursor-no-comments",
            support["pstack/agents/comment-sicko.md"]["related_skills"],
        )
        self.assertIn(
            "cursor-poteto-mode",
            support["pstack/agents/poteto-agent.md"]["related_skills"],
        )
        self.assertIn(
            "cursor-continual-learning",
            support["continual-learning/hooks/continual-learning-stop.ts"]["related_skills"],
        )

    def test_plugin_level_support_drift_is_rejected(self):
        agent = self.root / "sources/cursor-plugins/snapshot/pstack/agents/comment-sicko.md"
        agent.write_text(agent.read_text() + "\nChanged outside a skill directory.\n")
        result = self.run_build("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("plugin-level support inventory or hash drift", result.stderr)

    def test_compatibility_preview_repairs_frontmatter_and_bundles_four_roles(self):
        preview = self.root / "native-preview"
        result = self.run_build("--preview-candidates", str(preview))
        self.assertEqual(result.returncode, 0, result.stderr)
        candidate = preview / "cursor-check-agent-compatibility"
        skill = (candidate / "SKILL.md").read_text()
        self.assertIn('description: "Run the full repository compatibility pass:', skill)
        self.assertIn("package version, installation effects, and egress", skill)
        for name in ("compatibility-scan-review", "startup-review",
                     "validation-review", "docs-reliability-review"):
            role = (candidate / "references" / f"{name}.md").read_text()
            self.assertIn(f"name: {name}", role)
            self.assertNotIn("model: fast", role)
            self.assertNotIn("readonly: true", role)

    def test_submission_auditor_is_pinned_only_in_held_preview(self):
        preview = self.root / "native-preview"
        result = self.run_build("--preview-candidates", str(preview))
        self.assertEqual(result.returncode, 0, result.stderr)
        source = self.root / "scripts/cursor_plugin_submission_audit.py"
        bundled = preview / "cursor-review-plugin-submission/scripts/cursor_plugin_submission_audit.py"
        self.assertEqual(bundled.read_bytes(), source.read_bytes())
        self.assertFalse(
            (self.root / "skills/mirrors-cursor/cursor-review-plugin-submission").exists()
        )

    def test_scaffold_fixture_and_role_references_remain_held(self):
        preview = self.root / "native-preview"
        result = self.run_build("--preview-candidates", str(preview))
        self.assertEqual(result.returncode, 0, result.stderr)
        candidate = preview / "cursor-create-plugin-scaffold"
        source = self.root / "scripts/cursor_plugin_scaffold_fixture.py"
        bundled = candidate / "scripts/cursor_plugin_scaffold_fixture.py"
        self.assertEqual(bundled.read_bytes(), source.read_bytes())
        role = (candidate / "references/plugin-architect.md").read_text()
        rule = (candidate / "references/plugin-quality-gates.md").read_text()
        self.assertNotIn("model: inherit", role)
        self.assertNotIn("readonly: true", role)
        self.assertNotIn("alwaysApply: true", rule)
        self.assertIn("explicit disposable project-local destination", role)
        self.assertIn("explicit disposable project-local destination", rule)
        self.assertFalse((self.root / "skills/mirrors-cursor/cursor-create-plugin-scaffold").exists())

    def test_native_adapter_is_pinned_and_bundled_only_for_related_skills(self):
        preview = self.root / "native-preview"
        result = self.run_build("--preview-candidates", str(preview))
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("cursor-ralph-loop", "cursor-cancel-ralph", "cursor-advisor",
                     "cursor-continual-learning"):
            bundled = preview / name / "scripts/cursor_native_hook_adapters.py"
            self.assertEqual(
                bundled.read_bytes(),
                (self.root / "scripts/cursor_native_hook_adapters.py").read_bytes(),
            )
        ralph = (preview / "cursor-ralph-loop/SKILL.md").read_text()
        cancel = (preview / "cursor-cancel-ralph/SKILL.md").read_text()
        self.assertIn("ARMED_HOOK_TRUST_UNVERIFIED", ralph)
        self.assertIn("live Stop event", ralph)
        self.assertNotIn(".cursor/ralph/", ralph)
        self.assertNotIn("rm -rf", cancel)
        self.assertIn("`iteration` returned", cancel)
        advisor_role = (preview / "cursor-advisor/references/advisor-subagent.md").read_text()
        self.assertIn("authorized current-task transcript", advisor_role)
        self.assertNotIn("model: grok", advisor_role)
        self.assertNotIn("readonly: true", advisor_role)
        self.assertFalse((preview / "cursor-no-comments/scripts/cursor_native_hook_adapters.py").exists())

        adapter = self.root / "scripts/cursor_native_hook_adapters.py"
        adapter.write_text(adapter.read_text() + "\nUnexpected local edit.\n")
        drift = self.run_build("--check")
        self.assertNotEqual(drift.returncode, 0)
        self.assertIn("native support file drift", drift.stderr)

    def test_technical_writing_requires_published_unslop(self):
        skill = (
            self.root / "skills/mirrors-cursor/cursor-technical-writing/SKILL.md"
        ).read_text()
        self.assertIn("requires `cursor-unslop` for every document", skill)
        self.assertIn("Apply the **cursor-unslop** skill to every doc", skill)
        self.assertIn("`cursor-unslop`'s abstract-metaphor rule", skill)
        self.assertNotIn("optional unslop/style reference", skill)
        self.assertTrue(
            (self.root / "skills/mirrors-cursor/cursor-unslop/SKILL.md").is_file()
        )

    def test_typescript_references_published_principles_and_patterns(self):
        root = self.root / "skills/mirrors-cursor/cursor-typescript-best-practices"
        skill = (root / "SKILL.md").read_text()
        self.assertIn("cursor-principle-type-system-discipline", skill)
        self.assertIn("cursor-principle-boundary-discipline", skill)
        self.assertIn("references/patterns.md", skill)
        self.assertTrue((root / "references/patterns.md").is_file())
        for name in (
            "cursor-principle-type-system-discipline",
            "cursor-principle-boundary-discipline",
        ):
            self.assertTrue((self.root / "skills/mirrors-cursor" / name / "SKILL.md").is_file())

    def test_named_agent_uses_native_profile_without_workbench_copy(self):
        preview = self.root / "candidate-preview"
        result = self.run_build("--preview-candidates", str(preview))
        self.assertEqual(result.returncode, 0, result.stderr)
        skill = (preview / "cursor-no-comments/SKILL.md").read_text()
        self.assertIn('agent_type: "comment-sicko"', skill)
        self.assertFalse(
            (preview / "cursor-no-comments/references/comment-sicko-agent.md").exists()
        )
        agent = (
            self.root
            / "skills/core/model-capability-router/assets/agents/comment-sicko.toml"
        ).read_text()
        self.assertIn("cursor-how", agent)
        self.assertNotIn("`Task`", skill)
        self.assertIn('agent_type: "comment-sicko"', skill)
        self.assertIn("collaboration.spawn_agent", skill)
        self.assertIn("coordinator inspects the reviewer diff", skill)

        poteto = (preview / "cursor-poteto-mode/SKILL.md").read_text()
        plan = (preview / "cursor-poteto-mode/playbooks/multi-phase-plan.md").read_text()
        self.assertIn('agent_type: "poteto-agent"', poteto)
        self.assertIn("collaboration.followup_task", poteto)
        self.assertIn('agent_type: "poteto-agent"', plan)
        self.assertIn("collaboration.followup_task", plan)
        self.assertIn("Routed workflow skills keep their own role-specific", poteto)

    def test_thermos_bundles_two_distinct_review_lenses(self):
        preview = self.root / "thermos-preview"
        result = self.run_build("--preview-candidates", str(preview))
        self.assertEqual(result.returncode, 0, result.stderr)
        root = preview / "cursor-thermos"
        skill = (root / "SKILL.md").read_text()
        bug = (root / "references/bug-security-reviewer.md").read_text()
        quality = (root / "references/code-quality-reviewer.md").read_text()
        self.assertIn("bug/security role", skill)
        self.assertIn("code-quality role", skill)
        self.assertIn("cursor-thermo-nuclear-review", bug)
        self.assertIn("cursor-thermos-thermo-nuclear-code-quality-review", quality)
        self.assertIn("only added/modified code", bug)
        self.assertIn("code-judo / 1k-line / spaghetti rules", quality)

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
        self.assertEqual(len(cursor_family["skills"]), published_count() - 1)
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
        self.assertEqual(len(results), published_count())
        for item in results:
            self.assertEqual(item["counts"]["error"], 0, item)

    def test_all_active_candidates_preview_without_publishing(self):
        marketplace = self.root / ".claude-plugin/marketplace.json"
        before = marketplace.read_bytes()
        preview = self.root / "candidate-preview"
        result = self.run_build("--preview-candidates", str(preview))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(list(preview.glob("*/SKILL.md"))), 87)
        self.assertFalse((preview / "cursor-setup-benny").exists())
        self.assertFalse((preview / "cursor-make-bot-ui").exists())
        self.assertEqual(marketplace.read_bytes(), before)
        self.assertEqual(self.run_build("--check").returncode, 0)
        auditor = REPO / "skills/core/skill-catalog-curator/scripts/audit_skill_frontmatter.py"
        audit = subprocess.run(
            [sys.executable, "-S", str(auditor), str(preview),
             "--profile", "shared", "--json"],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(audit.returncode, 0, audit.stderr)
        results = json.loads(audit.stdout)["results"]
        self.assertEqual(len(results), 87)
        self.assertTrue(all(item["counts"]["error"] == 0 for item in results))
        missing = []
        for file in preview.rglob("*.md"):
            for match in re.finditer(r"\]\(([^)]+)\)", file.read_text()):
                target = match.group(1).split("#", 1)[0]
                if not target or ":" in target or target.startswith("/"):
                    continue
                if target == "url" and file.name == "synthesizer-prompt.md":
                    continue  # Upstream prompt placeholder, not a file link.
                if not (file.parent / target).exists():
                    missing.append((str(file.relative_to(preview)), target))
        self.assertEqual(missing, [])
        repeated = self.run_build("--preview-candidates", str(preview))
        self.assertNotEqual(repeated.returncode, 0)
        self.assertIn("already exists", repeated.stderr)

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
