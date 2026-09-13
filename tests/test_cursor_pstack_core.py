"""Functional and renderer-boundary proof for the three held pstack core skills."""

import json
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from cursor_functional_adapters import (  # noqa: E402
    AdapterError,
    PSTACK_PLAYBOOK_FILES,
    read_pstack_playbook_fixture,
    run_verification_fixture,
    select_verification_target,
)
_SYNC_SPEC = importlib.util.spec_from_file_location(
    "sync_cursor_plugin_skills", REPO / "scripts/sync-cursor-plugin-skills.py"
)
_SYNC = importlib.util.module_from_spec(_SYNC_SPEC)
assert _SYNC_SPEC.loader is not None
_SYNC_SPEC.loader.exec_module(_SYNC)
SOURCE = _SYNC.SOURCE
render_skill = _SYNC.render_skill


MANIFEST = REPO / "sources/cursor-plugins/manifest.json"
OVERLAYS = REPO / "sources/cursor-plugins/overlays"
CORE = (
    "cursor-poteto-mode",
    "cursor-create-verification-skill",
    "cursor-maintain-verification-skill",
)


def read_manifest():
    return json.loads(MANIFEST.read_text())


class CursorPstackCoreTests(unittest.TestCase):
    def render_core(self, name: str, staging: Path) -> Path:
        entries = {item["published_name"]: item for item in read_manifest()["skills"]}
        entry = entries[name]
        source_to_entry = {
            (SOURCE / item["path"]).resolve(): item for item in entries.values()
        }
        staging.mkdir(parents=True, exist_ok=True)
        render_skill(entry, staging, read_manifest()["upstream_commit"], source_to_entry)
        return staging / name

    def test_core_entries_are_held_and_have_native_contracts(self):
        entries = {item["published_name"]: item for item in read_manifest()["skills"]}
        for name in CORE:
            entry = entries[name]
            overlay = json.loads((OVERLAYS / f"{name}.json").read_text())
            contract = overlay["codex_contract"]
            self.assertFalse(entry["publish"], name)
            self.assertTrue(entry["declared_for_distribution"], name)
            self.assertEqual(contract["name_mapping"]["published_name"], name)
            self.assertEqual(contract["name_mapping"]["source_path"], entry["path"])
            self.assertEqual(overlay["source_path"], entry["path"])
            self.assertEqual(overlay["source_sha256"], entry["files"]["SKILL.md"])
            self.assertIn(
                "model-capability-router", contract["native_mapping"]["routing_authority"]
            )
            self.assertIn("proof-orchestrator", contract["native_mapping"]["routing_authority"])
            self.assertTrue(contract["native_mapping"]["fallback"])
            self.assertTrue(contract["permission_gates"])
            self.assertEqual(
                set(contract["behavioral_proof"]),
                {"positive", "missing_tool_or_input", "error"},
            )
            self.assertTrue(contract["promotion_status"].startswith("held_until_"))
            if name == "cursor-poteto-mode":
                self.assertEqual(
                    contract["native_mapping"]["concrete_skill_dependencies"],
                    {
                        "cleanup": "cursor-deslop",
                        "cli": "cursor-control-cli",
                        "ui": "cursor-control-ui",
                        "availability": "Check each skill before use; if absent or not applicable, record the exact capability gap and use the documented fallback.",
                    },
                )
                self.assertEqual(
                    contract["native_mapping"]["upstream_agent_dependency"]["status"],
                    "bundled_as_native_role_reference",
                )

    def test_poteto_renders_all_playbooks_with_native_markdown_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.render_core("cursor-poteto-mode", Path(temporary) / "staging")
            self.assertEqual(len(list((target / "playbooks").glob("*.md"))), 23)
            self.assertEqual(len(PSTACK_PLAYBOOK_FILES), 23)
            self.assertEqual(
                {path.stem for path in (target / "playbooks").glob("*.md")},
                set(PSTACK_PLAYBOOK_FILES),
            )
            self.assertTrue((target / "references/bugbot-triage.md").is_file())
            self.assertTrue((target / "scripts/package.json").is_file())
            self.assertTrue((target / "scripts/orch/orch.ts").is_file())
            self.assertTrue((target / "scripts/watch-pr/watch-pr").is_file())
            delegate_role = target / "references/poteto-agent.md"
            self.assertTrue(delegate_role.is_file())
            self.assertIn("cursor-poteto-mode", delegate_role.read_text())
            self.assertIn("cursor-principle-*", delegate_role.read_text())

            skill_markdown = (target / "SKILL.md").read_text()
            self.assertIn("per-turn native Codex guidance adapter", skill_markdown)
            self.assertIn("cursor-deslop", skill_markdown)
            self.assertIn("cursor-control-cli", skill_markdown)
            self.assertIn("cursor-control-ui", skill_markdown)
            self.assertIn("pstack/agents/poteto-agent.md", skill_markdown)
            self.assertIn("Cloud-capable task environments", skill_markdown)
            self.assertIn("do not claim parity", skill_markdown)
            opening = (target / "playbooks/opening-a-pr.md").read_text()
            self.assertIn("cursor-no-comments", opening)
            self.assertIn("cursor-technical-writing", opening)
            self.assertIn("cursor-unslop", opening)
            self.assertIn("cursor-interrogate", opening)
            multi_phase = (target / "playbooks/multi-phase-plan.md").read_text()
            self.assertIn("cursor-no-comments", multi_phase)
            self.assertIn("cursor-deslop", multi_phase)
            frontmatter = (target / "SKILL.md").read_text().split("---", 2)[1]
            self.assertIn("name: cursor-poteto-mode", frontmatter)
            self.assertNotIn("mode: true", frontmatter)

            read = read_pstack_playbook_fixture(target / "playbooks", "bug-fix")
            self.assertEqual(read["status"], "READ")
            self.assertEqual(read["playbook"], "bug-fix")
            self.assertTrue(read["entries"])
            self.assertEqual(read["environment"], "isolated-read-only-fixture")
            self.assertFalse(read["external_writes"])

            missing_root = Path(temporary) / "missing-playbooks"
            missing = read_pstack_playbook_fixture(missing_root, "bug-fix")
            self.assertEqual(missing["status"], "FALLBACK")
            missing_capability = read_pstack_playbook_fixture(
                target / "playbooks",
                "bug-fix",
                required_capabilities=("native bounded delegation",),
            )
            self.assertEqual(missing_capability["status"], "FALLBACK")
            self.assertEqual(missing_capability["missing"], ("native bounded delegation",))
            empty_root = Path(temporary) / "empty-playbooks"
            empty_root.mkdir()
            (empty_root / "bug-fix.md").write_text("")
            malformed = read_pstack_playbook_fixture(empty_root, "bug-fix")
            self.assertEqual(malformed["status"], "ERROR")
            with self.assertRaises(AdapterError):
                read_pstack_playbook_fixture(target / "playbooks", "not-a-playbook")

    def test_verification_mirrors_use_agents_root_and_native_harness_language(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "staging"
            create = self.render_core("cursor-create-verification-skill", root)
            maintain = self.render_core("cursor-maintain-verification-skill", root)
            create_markdown = "\n".join(path.read_text() for path in create.rglob("*.md"))
            maintain_markdown = "\n".join(path.read_text() for path in maintain.rglob("*.md"))
            self.assertIn(".agents/skills/verify-<app>/", create_markdown)
            self.assertNotIn(".cursor/skills", create_markdown)
            self.assertIn("control-notes", create_markdown)
            self.assertIn("cursor-control-ui", create_markdown)
            self.assertIn("cursor-control-cli", create_markdown)
            self.assertIn("adapt them to concrete commands", create_markdown)
            self.assertIn(".agents/skills/verify-*/", maintain_markdown)
            self.assertNotIn(".cursor/skills", maintain_markdown)
            self.assertIn("native bounded delegation", maintain_markdown)
            self.assertIn("blocked", maintain_markdown)

    def test_verification_target_selection_reports_path_state_only(self):
        self.assertEqual(
            select_verification_target([".agents/skills/verify-notes"]),
            {"status": "READY", "target": ".agents/skills/verify-notes"},
        )
        self.assertEqual(
            select_verification_target([]),
            {"status": "BLOCKED", "reason": "no verification skill target exists"},
        )
        self.assertEqual(
            select_verification_target(
                [".agents/skills/verify-a", ".agents/skills/verify-b"]
            )["status"],
            "NEEDS_INPUT",
        )
        self.assertEqual(
            select_verification_target(
                [".agents/skills/verify-a"], requested=".agents/skills/verify-missing"
            )["status"],
            "BLOCKED",
        )

    def test_verification_fixture_creates_reconciles_and_compares_fixture_observations(self):
        features = {
            "create-note": "Create a note and record the evidence.",
            "search": "Search notes and record the evidence.",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture_result = run_verification_fixture(
                root,
                "notes",
                features,
                app_available=True,
                observed_features=features,
            )
            self.assertEqual(fixture_result["status"], "FIXTURE_ONLY")
            self.assertTrue(fixture_result["created_skill"])
            self.assertEqual(fixture_result["reconciled_features"], tuple(sorted(features)))
            self.assertEqual(fixture_result["fixture_observations"], tuple(sorted(features)))
            self.assertFalse(fixture_result["product_edits"])
            self.assertTrue((root / ".agents/skills/verify-notes/SKILL.md").is_file())
            self.assertTrue((root / ".agents/skills/verify-notes/features/search.md").is_file())

        with tempfile.TemporaryDirectory() as temporary:
            blocked = run_verification_fixture(
                temporary,
                "notes",
                features,
                app_available=False,
            )
            self.assertEqual(blocked["status"], "BLOCKED")
            self.assertEqual(blocked["fixture_observations"], ())
            self.assertFalse(blocked["product_edits"])

        with tempfile.TemporaryDirectory() as temporary:
            mismatch = run_verification_fixture(
                temporary,
                "notes",
                features,
                app_available=True,
                observed_features={"create-note": "different", "search": features["search"]},
            )
            self.assertEqual(mismatch["status"], "ERROR")
            self.assertEqual(
                mismatch["reason"],
                "observed feature results do not match the reconciled map",
            )

        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(AdapterError):
                run_verification_fixture(temporary, ".", features, app_available=False)
            with self.assertRaises(AdapterError):
                run_verification_fixture(temporary, "notes", {"..": "invalid"}, app_available=False)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "outside"
            outside.mkdir()
            (root / ".agents").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(AdapterError):
                run_verification_fixture(root, "notes", features, app_available=False)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            project_alias = root / "project-alias"
            project_alias.symlink_to(project, target_is_directory=True)
            with self.assertRaises(AdapterError):
                run_verification_fixture(project_alias, "notes", features, app_available=False)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature_dir = root / ".agents/skills/verify-notes/features"
            feature_dir.mkdir(parents=True)
            outside_file = root / "outside.md"
            outside_file.write_text("outside")
            (feature_dir / "search.md").symlink_to(outside_file)
            with self.assertRaises(AdapterError):
                run_verification_fixture(root, "notes", features, app_available=False)


if __name__ == "__main__":
    unittest.main()
