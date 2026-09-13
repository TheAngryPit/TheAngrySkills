"""Functional and renderer-boundary proof for the three held pstack core skills."""

import json
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import cursor_functional_adapters as adapters  # noqa: E402
from cursor_functional_adapters import (  # noqa: E402
    AdapterError,
    MissingCapability,
    PSTACK_PLAYBOOK_FILES,
    PSTACK_FIXTURE_MARKER,
    PSTACK_FIXTURE_MARKER_CONTENT,
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
elif command == "trace-search":
    query = sys.argv[2]
    notes = json.loads(store.read_text()) if store.exists() else []
    title = notes[0]["title"] if notes else ""
    matched = query in title
    print(
        f"trace:query={query};title={title};"
        f"comparison=case-sensitive;matched={str(matched).lower()}"
    )
else:
    raise SystemExit("unknown command")
"""
FIXED_NOTES_APP = BUGGY_NOTES_APP.replace(
    'query in note["title"]',
    'query.casefold() in note["title"].casefold()',
)
VALID_PLAN = """# Synthetic bug-fix plan

Short fixture plan.

## How to read this

One box is one unit of work
names the evidence
Check a box only when its evidence exists
playbooks/
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

/goal

### Spawn owners

status message

### PR mechanics

git show origin/main:

### Verdict and merge

30-minute review

### Boot recipe

fixture boot

## Fix synthetic notes app

**Depends on.** local fixture

**Files.**
- [ ] app.py

**Build.**
- [ ] Run the fixture app.

**You see.**
- [ ] Capture the observed output.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Unit evidence exists.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.6-fast-xhigh` at the PR head
- [ ] Lane 1. exercise fixture. Save `lane-1.txt`. Pass when output matches.
- [ ] Lane 2. exercise fixture. Save `lane-2.txt`. Pass when output matches.
- [ ] Lane 3. exercise fixture. Save `lane-3.txt`. Pass when output matches.
- [ ] Lane 4. exercise fixture. Save `lane-4.txt`. Pass when output matches.
- [ ] Lane 5. exercise fixture. Save `lane-5.txt`. Pass when output matches.
- [ ] Lane 6. exercise fixture. Save `lane-6.txt`. Pass when output matches.
- [ ] Lane 7. exercise fixture. Save `lane-7.txt`. Pass when output matches.
- [ ] Lane 8. exercise fixture. Save `lane-8.txt`. Pass when output matches.
- [ ] Lane 9. exercise fixture. Save `lane-9.txt`. Pass when output matches.
- [ ] Lane 10. exercise fixture. Save `lane-10.txt`. Pass when output matches.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric.
- [ ] Probe.
- [ ] Baseline.
- [ ] Rule.

**Review gate.** None.

**Merge.**
- [ ] Merge only after the fixture evidence is reviewed.

## Close the program

Close after the fixture report is written.

## Appendix Prototype evidence

The synthetic fixture is not a live product proof.
"""


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
            (root / PSTACK_FIXTURE_MARKER).write_text(PSTACK_FIXTURE_MARKER_CONTENT)
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
                {"fixture_completed": (1, 4, 5), "partial": (2, 3, 6), "unexercised": ()},
            )
            self.assertEqual(result["before"]["status"], "PASS")
            self.assertEqual(result["failure"]["status"], "FAIL")
            self.assertEqual(result["diagnosis"]["status"], "HYPOTHESIS_SUPPORTED")
            self.assertEqual(
                result["diagnosis"]["surviving_hypothesis"],
                "case-sensitive search predicate",
            )
            self.assertEqual(result["plan"]["status"], "PLAN_RECORDED")
            self.assertEqual(
                result["plan"]["review"]["status"], "DIFF_RECORDED"
            )
            self.assertEqual(result["plan"]["review"]["mode"], "structural_only")
            self.assertIn("casefold", result["plan"]["diff"])
            self.assertEqual(result["local_history"]["status"], "LOCAL_ONLY")
            self.assertEqual(
                result["local_history"]["subjects_newest_first"],
                (
                    "fix(pstack): normalize notes search",
                    "test(pstack): reproduce notes search failure",
                ),
            )
            self.assertEqual(
                result["local_history"]["pr_simulation"]["status"],
                "SIMULATED_ONLY",
            )
            self.assertFalse(result["local_history"]["pr_simulation"]["real_pr"])
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
                    "trace observable search mechanism",
                    "record hypothesis cut and review prewritten correction diff",
                    "commit reproduction before correction",
                    "write prewritten corrected fixture source and commit correction",
                    "push to temporary local bare remote as PR simulation",
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
            (root / PSTACK_FIXTURE_MARKER).write_text(PSTACK_FIXTURE_MARKER_CONTENT)
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
                {"fixture_completed": (1,), "partial": (), "unexercised": (2, 3, 4, 5, 6)},
            )
            self.assertEqual(app.read_text(), wrong_failure_app)

    def test_bug_fix_history_requires_disposable_marker_and_known_root_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staging = self.render_core("cursor-poteto-mode", root / "staging")
            app = root / "app.py"
            app.write_text(BUGGY_NOTES_APP)
            unmarked = run_bug_fix_playbook_fixture(
                staging / "playbooks",
                root,
                app,
                buggy_source=BUGGY_NOTES_APP,
                corrected_source=FIXED_NOTES_APP,
            )
            self.assertEqual(unmarked["status"], "ERROR")
            self.assertEqual(unmarked["local_history"]["status"], "BLOCKED")
            self.assertIn("marker", unmarked["local_history"]["reason"])
            self.assertEqual(app.read_text(), BUGGY_NOTES_APP)

            (root / "notes.json").unlink()
            (root / PSTACK_FIXTURE_MARKER).write_text(PSTACK_FIXTURE_MARKER_CONTENT)
            (root / "unexpected.txt").write_text("must not be touched\n")
            unexpected = run_bug_fix_playbook_fixture(
                staging / "playbooks",
                root,
                app,
                buggy_source=BUGGY_NOTES_APP,
                corrected_source=FIXED_NOTES_APP,
            )
            self.assertEqual(unexpected["status"], "ERROR")
            self.assertEqual(unexpected["local_history"]["status"], "BLOCKED")
            self.assertIn("unexpected entries", unexpected["local_history"]["reason"])
            self.assertEqual(app.read_text(), BUGGY_NOTES_APP)

    def test_local_git_timeout_is_explicitly_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            timeout = subprocess.TimeoutExpired(("git",), 5.0)
            with mock.patch.object(adapters.shutil, "which", return_value="/usr/bin/git"):
                with mock.patch.object(
                    adapters.subprocess, "run", side_effect=timeout
                ):
                    with self.assertRaisesRegex(
                        MissingCapability, "local git fixture command timed out"
                    ):
                        adapters._run_local_git(root, ("init", "--quiet"))

    def test_check_plan_safe_fixture_valid_and_invalid(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("node unavailable")
        script = (
            REPO
            / "sources/cursor-plugins/snapshot/pstack/skills/poteto-mode/scripts/check-plan.mjs"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            home.mkdir()
            valid = root / "valid.md"
            invalid = root / "invalid.md"
            valid.write_text(VALID_PLAN)
            invalid.write_text("# invalid\n")
            environment = {
                "PATH": str(Path(node).parent),
                "HOME": str(home),
                "LANG": "C",
            }
            checked = subprocess.run(
                [node, str(script), str(valid)],
                cwd=str(REPO),
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                shell=False,
                timeout=5.0,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertIn("1 PR sections, 0 problems", checked.stdout)

            rejected = subprocess.run(
                [node, str(script), str(invalid)],
                cwd=str(REPO),
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                shell=False,
                timeout=5.0,
            )
            self.assertEqual(rejected.returncode, 1)
            self.assertRegex(
                rejected.stderr,
                r'no "## How to read this" section|no "## Program checklist"',
            )

    def test_worktree_audit_safe_fixture_uses_only_mocks(self):
        script = (
            REPO
            / "sources/cursor-plugins/snapshot/pstack/skills/poteto-mode/scripts/worktree-audit.sh"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            child = repo / "child"
            repo.mkdir()
            child.mkdir()
            mock_bin = root / "mock-bin"
            mock_bin.mkdir()
            repo_text = str(repo)
            child_text = str(child)
            git = mock_bin / "git"
            git.write_text(
                f'''#!/bin/bash
if [ "$1" = "-C" ]; then
  target="$2"
  shift 2
fi
case "$1" in
  worktree)
    if [ "$2" = "list" ]; then
      printf 'worktree {repo_text}\\nHEAD 1111111111111111111111111111111111111111\\nbranch refs/heads/main\\nworktree {child_text}\\nHEAD 2222222222222222222222222222222222222222\\nbranch refs/heads/fix/mock\\n'
    fi
    ;;
  fetch) exit 0 ;;
  rev-parse) printf '2222222222222222222222222222222222222222\\n' ;;
  log) printf '1700000000\\n' ;;
  merge-base) exit 1 ;;
  status) exit 0 ;;
  symbolic-ref) printf 'refs/heads/fix/mock\\n' ;;
  show-ref) exit 1 ;;
  rev-list) printf '1\\n' ;;
  *) exit 0 ;;
esac
'''
            )
            gh = mock_bin / "gh"
            gh.write_text("#!/bin/bash\nprintf '[]\\n'\n")
            jq = mock_bin / "jq"
            jq.write_text("#!/bin/bash\nexit 0\n")
            rg = mock_bin / "rg"
            rg.write_text("#!/bin/bash\nexit 1\n")
            for executable in (git, gh, jq, rg):
                executable.chmod(0o755)

            home = root / "home"
            slug = str(repo).lstrip("/").replace("/", "-")
            transcripts = home / ".cursor/projects" / slug / "agent-transcripts"
            transcripts.mkdir(parents=True)
            environment = {
                "HOME": str(home),
                "PATH": f"{mock_bin}:/usr/bin:/bin",
                "LANG": "C",
            }
            audited = subprocess.run(
                ["/bin/bash", str(script), str(repo)],
                cwd=str(repo),
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                shell=False,
                timeout=5.0,
            )
            self.assertEqual(audited.returncode, 0, audited.stderr)
            self.assertIn("SIZE\tAGE\tMERGED\tDIRTY\tREMOTE\tPR\tLAST_CHAT\tBUCKET\tWORKTREE", audited.stdout)
            self.assertIn(str(child), audited.stdout)
            self.assertIn("no-remote", audited.stdout)

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
