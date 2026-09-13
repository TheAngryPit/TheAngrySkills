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
    PSTACK_PLAYBOOKS,
    select_pstack_playbook,
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

    def test_poteto_renders_all_playbooks_with_native_markdown_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.render_core("cursor-poteto-mode", Path(temporary) / "staging")
            self.assertEqual(len(list((target / "playbooks").glob("*.md"))), 23)
            self.assertEqual(len(PSTACK_PLAYBOOKS), 23)
            self.assertTrue((target / "references/bugbot-triage.md").is_file())
            self.assertTrue((target / "scripts/package.json").is_file())
            self.assertTrue((target / "scripts/orch/orch.ts").is_file())
            self.assertTrue((target / "scripts/watch-pr/watch-pr").is_file())

            markdown = "\n".join(
                path.read_text()
                for path in target.rglob("*.md")
                if path.name != "MIRROR.md"
            )
            for marker in (
                "Cursor",
                "cursor-team-kit",
                "AskQuestion",
                "subagent_type",
                ".cursor",
                "/loop",
                "grok-4.6-fast-xhigh",
                "claude-fable-5-1-thinking-max",
            ):
                self.assertNotIn(marker, markdown, marker)
            frontmatter = (target / "SKILL.md").read_text().split("---", 2)[1]
            self.assertIn("name: cursor-poteto-mode", frontmatter)
            self.assertNotIn("mode: true", frontmatter)
            self.assertIn("per-turn native Codex guidance adapter", (target / "SKILL.md").read_text())

    def test_verification_mirrors_use_agents_root_and_native_harness_language(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "staging"
            create = self.render_core("cursor-create-verification-skill", root)
            maintain = self.render_core("cursor-maintain-verification-skill", root)
            create_markdown = "\n".join(path.read_text() for path in create.rglob("*.md"))
            maintain_markdown = "\n".join(path.read_text() for path in maintain.rglob("*.md"))
            self.assertIn(".agents/skills/verify-<app>/", create_markdown)
            self.assertNotIn(".cursor/skills", create_markdown)
            self.assertNotIn("control-notes", create_markdown)
            self.assertIn(".agents/skills/verify-*/", maintain_markdown)
            self.assertNotIn(".cursor/skills", maintain_markdown)
            self.assertIn("native bounded delegation", maintain_markdown)
            self.assertIn("blocked", maintain_markdown)

    def test_playbook_and_verification_target_selection_is_bounded(self):
        self.assertEqual(
            select_pstack_playbook("Please investigate this regression and find the root cause"),
            {"status": "NATIVE", "playbook": "bug-fix"},
        )
        self.assertEqual(
            select_pstack_playbook(
                "Please investigate this regression", available=["investigation"]
            ),
            {
                "status": "FALLBACK",
                "playbook": "bug-fix",
                "reason": "matched playbook is unavailable; use sequential native steps",
            },
        )
        self.assertEqual(
            select_pstack_playbook("Please summarize the current state"),
            {"status": "DIRECT", "reason": "no bounded playbook trigger matched"},
        )
        with self.assertRaises(AdapterError):
            select_pstack_playbook("")
        with self.assertRaises(AdapterError):
            select_pstack_playbook("anything", explicit="not-a-playbook")

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


if __name__ == "__main__":
    unittest.main()
