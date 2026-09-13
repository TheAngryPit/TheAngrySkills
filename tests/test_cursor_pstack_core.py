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
    run_bug_fix_playbook_fixture,
    run_local_app_fixture,
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
BUGGY_NOTES_APP = """
from pathlib import Path
import json
import sys

store = Path("notes.json")
command = sys.argv[1]
if command == "create":
    note = {"title": sys.argv[2], "body": sys.argv[3]}
    notes = json.loads(store.read_text()) if store.exists() else []
    notes.append(note)
    store.write_text(json.dumps(notes))
    print(f"created:{note['title']}")
elif command == "search":
    query = sys.argv[2]
    notes = json.loads(store.read_text()) if store.exists() else []
    matches = [note["title"] for note in notes if query in note["title"]]
    if not matches:
        print("not-found")
        raise SystemExit(1)
    print("found:" + ",".join(matches))
else:
    raise SystemExit("unknown command")
"""
FIXED_NOTES_APP = BUGGY_NOTES_APP.replace(
    'query in note["title"]',
    'query.casefold() in note["title"].casefold()',
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

    def test_local_app_fixture_collects_independent_failure_and_fix(self):
        features = {
            "create-note": "Create a note and record the evidence.",
            "search": "Search notes and record the evidence.",
        }
        buggy_app = BUGGY_NOTES_APP
        fixed_app = FIXED_NOTES_APP

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = root / "app.py"
            app.write_text(buggy_app)
            generated = run_verification_fixture(
                root,
                "notes",
                features,
                app_available=False,
            )
            self.assertEqual(generated["status"], "BLOCKED")
            self.assertEqual(generated["environment"], "isolated-project-fixture")

            created = run_local_app_fixture(
                root,
                app,
                ("create", "Release checklist", "Tag and publish"),
                expected_stdout="created:Release checklist\n",
            )
            self.assertEqual(created["status"], "PASS")
            self.assertEqual(created["environment"], "local-app-fixture-process")
            self.assertEqual(
                created["evidence_scope"], ("exit_code", "stdout", "stderr")
            )
            self.assertEqual(created["filesystem_isolation"], "not_observed")
            self.assertEqual(created["network_isolation"], "not_observed")

            failed = run_local_app_fixture(
                root,
                app,
                ("search", "release"),
                expected_stdout="found:Release checklist\n",
            )
            self.assertEqual(failed["status"], "FAIL")
            self.assertEqual(
                failed["evidence"],
                {
                    "exit_code": 1,
                    "stdout": "not-found\n",
                    "stderr": "",
                },
            )
            self.assertNotEqual(failed["evidence"], failed["expected"])

            app.write_text(fixed_app)
            repaired = run_local_app_fixture(
                root,
                app,
                ("search", "release"),
                expected_stdout="found:Release checklist\n",
            )
            self.assertEqual(repaired["status"], "PASS")
            self.assertEqual(
                repaired["evidence"],
                {
                    "exit_code": 0,
                    "stdout": "found:Release checklist\n",
                    "stderr": "",
                },
            )

    def test_bug_fix_playbook_executes_contextual_notes_steps(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staging = self.render_core("cursor-poteto-mode", root / "staging")
            app = root / "app.py"
            app.write_text(BUGGY_NOTES_APP)
            result = run_bug_fix_playbook_fixture(
                staging / "playbooks",
                root,
                app,
                buggy_source=BUGGY_NOTES_APP,
                corrected_source=FIXED_NOTES_APP,
            )

            self.assertEqual(result["status"], "FIXTURE_ONLY")
            self.assertEqual(result["playbook"], "bug-fix")
            self.assertEqual(result["playbook_read"]["status"], "READ")
            self.assertNotEqual(result["playbook_read"]["status"], "APPLIED")
            self.assertEqual(
                result["playbook_step_scope"],
                {"exercised": (1, 4), "unexercised": (2, 3, 5, 6)},
            )
            self.assertEqual(result["before"]["status"], "PASS")
            self.assertEqual(result["failure"]["status"], "FAIL")
            self.assertEqual(result["correction"]["status"], "CORRECTED")
            self.assertTrue(result["correction"]["changed"])
            self.assertEqual(result["after"]["status"], "PASS")
            self.assertEqual(
                result["failure"]["evidence"],
                {
                    "exit_code": 1,
                    "stdout": "not-found\n",
                    "stderr": "",
                },
            )
            self.assertEqual(
                result["after"]["evidence"],
                {
                    "exit_code": 0,
                    "stdout": "found:Release checklist\n",
                    "stderr": "",
                },
            )
            self.assertEqual(
                result["contextual_steps"],
                (
                    "create note",
                    "baseline exact-case search",
                    "reproduce lower-case search failure",
                    "write corrected fixture source",
                    "repeat lower-case search",
                ),
            )
            self.assertEqual(result["evidence_scope"], ("exit_code", "stdout", "stderr"))
            self.assertEqual(result["filesystem_isolation"], "not_observed")
            self.assertEqual(result["network_isolation"], "not_observed")

    def test_bug_fix_playbook_requires_bug_specific_failure_before_correction(self):
        wrong_failure_app = BUGGY_NOTES_APP.replace(
            "raise SystemExit(1)",
            "raise SystemExit(2)",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staging = self.render_core("cursor-poteto-mode", root / "staging")
            app = root / "app.py"
            app.write_text(wrong_failure_app)
            result = run_bug_fix_playbook_fixture(
                staging / "playbooks",
                root,
                app,
                buggy_source=wrong_failure_app,
                corrected_source=FIXED_NOTES_APP,
            )

            self.assertEqual(result["status"], "ERROR")
            self.assertEqual(result["failure"]["evidence"]["exit_code"], 2)
            self.assertEqual(result["correction"]["status"], "NOT_RUN")
            self.assertEqual(result["after"]["status"], "NOT_RUN")
            self.assertEqual(
                result["playbook_step_scope"],
                {"exercised": (1,), "unexercised": (2, 3, 4, 5, 6)},
            )
            self.assertEqual(app.read_text(), wrong_failure_app)

    def test_local_app_fixture_rejects_outside_or_symlinked_apps(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = root / "app.py"
            app.write_text("print('ok')\n")
            outside = root.parent / f"{root.name}-outside-app.py"
            outside.write_text("print('outside')\n")
            try:
                with self.assertRaises(AdapterError):
                    run_local_app_fixture(
                        root,
                        outside,
                        (),
                        expected_stdout="outside\n",
                    )
            finally:
                outside.unlink()
            alias = root / "alias.py"
            alias.symlink_to(app)
            with self.assertRaises(AdapterError):
                run_local_app_fixture(root, alias, (), expected_stdout="ok\n")

if __name__ == "__main__":
    unittest.main()
