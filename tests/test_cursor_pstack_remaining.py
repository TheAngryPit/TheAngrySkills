"""Bounded proof cases for the remaining history/procedure pstack adapters."""

import tempfile
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from cursor_functional_adapters import (  # noqa: E402
    AdapterError,
    run_automate_me_fixture,
    run_recall_fixture,
)


class CursorPstackRemainingTests(unittest.TestCase):
    def test_automate_me_writes_only_corroborated_project_local_preferences(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_automate_me_fixture(
                Path(temporary),
                {
                    "task-a": ("preserve exact evidence", "use bounded scope"),
                    "task-b": ("preserve exact evidence", "use bounded scope"),
                    "task-c": ("preserve exact evidence",),
                },
                ("preserve exact evidence", "one-off preference"),
                unslop_available=True,
                draft_approved=True,
            )
            self.assertEqual(result["status"], "FIXTURE_ONLY")
            self.assertTrue(result["writes_performed"])
            self.assertFalse(result["global_write"])
            self.assertEqual(result["confirmed"], ("preserve exact evidence",))
            self.assertEqual(result["omitted"], ("one-off preference",))
            destination = Path(result["destination"])
            self.assertTrue(destination.is_file())
            content = destination.read_text()
            self.assertIn("Keep explicit evidence", content)
            self.assertIn("preserve exact evidence", content)
            self.assertNotIn("one-off preference", content)

    def test_automate_me_preserves_existing_skill_when_history_or_unslop_is_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / ".agents/skills/fixture-mode/fixture-mode-mode/SKILL.md"
            destination.parent.mkdir(parents=True)
            destination.write_text("existing\n")
            partial = run_automate_me_fixture(
                root,
                {"only": ("preserve exact evidence",)},
                ("preserve exact evidence",),
                unslop_available=True,
                draft_approved=True,
            )
            self.assertEqual(partial["status"], "PARTIAL")
            self.assertEqual(destination.read_text(), "existing\n")
            blocked = run_automate_me_fixture(
                root,
                {"a": ("preserve exact evidence",), "b": ("preserve exact evidence",)},
                ("preserve exact evidence",),
                unslop_available=False,
                draft_approved=True,
            )
            self.assertEqual(blocked["status"], "PARTIAL")
            self.assertEqual(destination.read_text(), "existing\n")

            unapproved = run_automate_me_fixture(
                root,
                {"a": ("preserve exact evidence",), "b": ("preserve exact evidence",)},
                ("preserve exact evidence",),
                unslop_available=True,
                draft_approved=False,
            )
            self.assertEqual(unapproved["status"], "PARTIAL")
            self.assertEqual(destination.read_text(), "existing\n")

    def test_automate_me_rejects_symlink_components_and_control_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "outside"
            outside.mkdir()
            (outside / "fixture-mode-mode").mkdir()
            (root / ".agents").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(AdapterError, "symlink component"):
                run_automate_me_fixture(
                    root,
                    {"a": ("preserve exact evidence",), "b": ("preserve exact evidence",)},
                    ("preserve exact evidence",),
                    unslop_available=True,
                    draft_approved=True,
                )
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(AdapterError, "control characters"):
                run_automate_me_fixture(
                    Path(temporary),
                    {"a": ("bad\npreference",), "b": ("bad\npreference",)},
                    ("bad\npreference",),
                    unslop_available=True,
                    draft_approved=True,
                )

    def test_recall_reconciles_exact_scope_without_writes(self):
        result = run_recall_fixture(
            [
                {"thread_id": "current", "workspace": "/repo", "title": "pstack recall", "updated_at": 3},
                {"thread_id": "prior", "workspace": "/repo", "title": "pstack closure", "updated_at": 2},
                {"thread_id": "other", "workspace": "/other", "title": "pstack closure", "updated_at": 1},
            ],
            topic="pstack",
            workspace="/repo",
            live_state={"workspace": "/repo", "branch": "codex/test", "status": "clean"},
            shared_record={
                "record_id": "ledger-1",
                "workspace": "/repo",
                "topic": "pstack",
                "summary": "bounded closure evidence",
            },
            current_thread_id="current",
        )
        self.assertEqual(result["status"], "FIXTURE_ONLY")
        self.assertEqual(result["selected_history"], ("prior",))
        self.assertFalse(result["writes_performed"])
        self.assertEqual(result["brief"]["live_state"]["branch"], "codex/test")

    def test_recall_marks_missing_or_mismatched_records_partial(self):
        records = [{"thread_id": "prior", "workspace": "/repo", "title": "pstack closure"}]
        missing = run_recall_fixture(
            records,
            topic="pstack",
            workspace="/repo",
            live_state={"workspace": "/repo"},
            shared_record=None,
        )
        self.assertEqual(missing["status"], "PARTIAL")
        self.assertTrue(missing["missing_export"])
        mismatch = run_recall_fixture(
            records,
            topic="pstack",
            workspace="/repo",
            live_state={"workspace": "/repo"},
            shared_record={"record_id": "wrong", "workspace": "/other", "topic": "other"},
        )
        self.assertEqual(mismatch["status"], "PARTIAL")
        self.assertFalse(mismatch["writes_performed"])
        with self.assertRaisesRegex(AdapterError, "topic and workspace"):
            run_recall_fixture(records, topic="", workspace="/repo", live_state={}, shared_record=None)


if __name__ == "__main__":
    unittest.main()
