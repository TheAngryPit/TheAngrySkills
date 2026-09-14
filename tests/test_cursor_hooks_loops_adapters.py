"""Focused proofs for the held advisor, continual-learning, and Ralph overlays."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from cursor_hooks_loops_adapters import HooksLoopsFixture  # noqa: E402


class CursorHooksLoopsAdapterTests(unittest.TestCase):
    def project(self):
        return tempfile.TemporaryDirectory(prefix="cursor-hooks-loops-test-")

    def test_advisor_positive_lifecycle_and_one_time_nudge(self):
        with self.project() as directory:
            fixture = HooksLoopsFixture(Path(directory))
            self.assertEqual(fixture.enable_advisor()["status"], "BOUND_HOOK_TRUST_UNVERIFIED")
            self.assertEqual(fixture.mark_advisor_edit(), {})
            nudge = fixture.advisor_nudge()
            self.assertEqual(nudge["decision"], "block")
            self.assertEqual(fixture.advisor_nudge(), {})
            self.assertEqual(fixture.expect_advisor()["status"], "AWAITING_ADVISOR")
            self.assertEqual(fixture.complete_advisor(), {})

    def test_advisor_wrong_session_and_invalid_verdict_preserve_pending_state(self):
        with self.project() as directory:
            project = Path(directory)
            fixture = HooksLoopsFixture(project)
            fixture.enable_advisor()
            fixture.mark_advisor_edit()
            wrong = HooksLoopsFixture(project, "other-session")
            self.assertEqual(wrong.advisor_nudge(), {})
            self.assertEqual(fixture.expect_advisor()["status"], "AWAITING_ADVISOR")
            invalid = fixture.complete_advisor(verdict="maybe")
            self.assertIn("systemMessage", invalid)
            self.assertEqual(fixture.advisor_nudge("after-invalid")["decision"], "block")

    def test_ralph_positive_iteration_and_promise_cleanup(self):
        with self.project() as directory:
            fixture = HooksLoopsFixture(Path(directory))
            self.assertEqual(fixture.arm_ralph(max_iterations=3)["status"], "ARMED_HOOK_TRUST_UNVERIFIED")
            iteration = fixture.ralph_iteration()
            self.assertEqual(iteration["decision"], "block")
            self.assertEqual(fixture.ralph_iteration("fixture-turn-2")["decision"], "block")
            self.assertEqual(fixture.ralph_iteration("fixture-turn-3", "<promise>DONE</promise>"), {})
            self.assertEqual(fixture.cancel_ralph()["status"], "INACTIVE")

    def test_ralph_wrong_session_is_no_op_and_cancel_is_idempotent(self):
        with self.project() as directory:
            project = Path(directory)
            fixture = HooksLoopsFixture(project)
            fixture.arm_ralph(max_iterations=2)
            other = HooksLoopsFixture(project, "other-session")
            self.assertEqual(other.ralph_iteration(), {})
            self.assertEqual(other.cancel_ralph()["status"], "OTHER_SESSION")
            self.assertEqual(fixture.cancel_ralph()["status"], "CANCELLED")
            self.assertEqual(fixture.cancel_ralph()["status"], "INACTIVE")

    def test_continual_learning_positive_threshold_uses_scoped_fixture_transcript(self):
        with self.project() as directory:
            project = Path(directory)
            transcript_root = project / "transcripts"
            transcript_root.mkdir()
            transcript = transcript_root / "fixture.jsonl"
            transcript.write_text('{"role":"user","content":"fixture"}\n')
            fixture = HooksLoopsFixture(project)
            fixture.arm_continual_learning(transcript_root)
            with patch.dict(
                os.environ,
                {
                    "CONTINUAL_LEARNING_MIN_TURNS": "1",
                    "CONTINUAL_LEARNING_MIN_MINUTES": "1",
                },
                clear=False,
            ):
                result = fixture.continual_learning_stop(transcript)
            self.assertEqual(result["decision"], "block")
            self.assertIn("cursor-continual-learning", result["reason"])

    def test_continual_learning_missing_or_out_of_scope_transcript_stays_quiet(self):
        with self.project() as directory:
            project = Path(directory)
            transcript_root = project / "transcripts"
            transcript_root.mkdir()
            fixture = HooksLoopsFixture(project)
            fixture.arm_continual_learning(transcript_root)
            with patch.dict(
                os.environ,
                {
                    "CONTINUAL_LEARNING_MIN_TURNS": "1",
                    "CONTINUAL_LEARNING_MIN_MINUTES": "1",
                },
                clear=False,
            ):
                self.assertEqual(fixture.continual_learning_stop(project / "outside.jsonl"), {})
            self.assertFalse((project / "outside.jsonl").exists())

    def test_fixture_rejects_project_and_transcript_root_symlink_aliases(self):
        with self.project() as directory:
            real_project = Path(directory) / "project"
            real_project.mkdir()
            project_alias = Path(directory) / "project-alias"
            transcript_root = real_project / "transcripts"
            transcript_root.mkdir()
            transcript_alias = Path(directory) / "transcripts-alias"
            os.symlink(real_project, project_alias)
            os.symlink(transcript_root, transcript_alias)

            with self.assertRaisesRegex(ValueError, "fixture project path contains a symlink"):
                HooksLoopsFixture(project_alias)
            fixture = HooksLoopsFixture(real_project)
            with self.assertRaisesRegex(ValueError, "transcript root path contains a symlink"):
                fixture.arm_continual_learning(transcript_alias)


if __name__ == "__main__":
    unittest.main()
