"""Synthetic Codex hook-payload proof; project hook registration is a separate step."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts/cursor_native_hook_adapters.py"


class CursorNativeHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cursor-native-hook-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.other = self.root / "other"
        self.other.mkdir()

    def state(self, family, data, project=None):
        project = project or self.project
        path = project / ".codex/cursor-mirror-state" / family / "state.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        return path

    def call(self, handler, event, project=None, env=None):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), handler, "--project", str(project or self.project)],
            input=json.dumps(event), text=True, capture_output=True, check=True,
            env=os.environ | (env or {}),
        )
        return json.loads(result.stdout)

    def command(self, handler, *arguments):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), handler, "--project", str(self.project),
             *arguments], text=True, capture_output=True, check=True,
        )
        return json.loads(result.stdout)

    def stop_event(self, *, turn="turn-1", session="task-1", project=None, message=None):
        return {
            "hook_event_name": "Stop", "cwd": str(project or self.project),
            "session_id": session, "turn_id": turn, "stop_hook_active": False,
            "last_assistant_message": message,
        }

    def test_ralph_continues_once_per_turn_and_stops_on_exact_promise(self):
        path = self.state("ralph", {
            "session_id": "task-1", "prompt": "Fix the flaky test", "iteration": 1,
            "max_iterations": 3, "completion_promise": "tests pass",
        })
        first = self.call("ralph-stop", self.stop_event(message="Still working"))
        self.assertEqual(first["decision"], "block")
        self.assertIn("Fix the flaky test", first["reason"])
        self.assertIn("iteration 2", first["reason"])
        self.assertEqual(json.loads(path.read_text())["iteration"], 2)
        self.assertEqual(self.call("ralph-stop", self.stop_event(message="Still working")), {})
        self.assertEqual(json.loads(path.read_text())["iteration"], 2)

        second = self.call("ralph-stop", self.stop_event(turn="turn-2", message="tests pass"))
        self.assertEqual(second["decision"], "block")
        self.assertEqual(json.loads(path.read_text())["iteration"], 3)
        done = self.call("ralph-stop", self.stop_event(
            turn="turn-3", message="Evidence checked. <promise>tests   pass</promise>"
        ))
        self.assertEqual(done, {})
        self.assertFalse(path.exists())

    def test_ralph_max_corruption_cancellation_and_session_isolation(self):
        path = self.state("ralph", {
            "session_id": "task-1", "prompt": "Check", "iteration": 2,
            "max_iterations": 2, "completion_promise": None,
        })
        self.assertEqual(self.call("ralph-stop", self.stop_event(session="other-task")), {})
        self.assertTrue(path.exists())
        self.assertEqual(self.call("ralph-stop", self.stop_event(project=self.other)), {})
        self.assertTrue(path.exists())
        self.assertEqual(self.call("ralph-stop", self.stop_event()), {})
        self.assertFalse(path.exists())
        self.assertEqual(self.call("ralph-stop", self.stop_event(turn="turn-2")), {})

        path = self.state("ralph", {
            "session_id": "task-1", "prompt": "", "iteration": -1,
            "max_iterations": 2, "completion_promise": None,
        })
        warning = self.call("ralph-stop", self.stop_event())
        self.assertIn("invalid", warning["systemMessage"])
        self.assertFalse(path.exists())

    def test_ralph_arm_cancel_and_config_are_project_scoped(self):
        prompt = self.root / "prompt.txt"
        prompt.write_text("Fix the flaky test")
        base = [sys.executable, str(SCRIPT)]
        render = subprocess.run(
            [*base, "render-ralph-config", "--project", str(self.project)],
            text=True, capture_output=True, check=True,
        )
        config = json.loads(render.stdout)
        command = config["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.assertIn("ralph-stop", command)
        self.assertIn(str(self.project), command)
        self.assertFalse((self.project / ".codex").exists())

        armed = subprocess.run(
            [*base, "ralph-start", "--project", str(self.project),
             "--session-id", "task-1", "--prompt-file", str(prompt),
             "--max-iterations", "2", "--completion-promise", "done"],
            text=True, capture_output=True, check=True,
        )
        self.assertEqual(json.loads(armed.stdout)["status"], "ARMED_HOOK_TRUST_UNVERIFIED")
        path = self.project / ".codex/cursor-mirror-state/ralph/state.json"
        self.assertEqual(json.loads(path.read_text())["iteration"], 1)
        duplicate = subprocess.run(
            [*base, "ralph-start", "--project", str(self.project),
             "--session-id", "task-2", "--prompt-file", str(prompt)],
            text=True, capture_output=True, check=True,
        )
        self.assertIn("already active", json.loads(duplicate.stdout)["systemMessage"])
        wrong = subprocess.run(
            [*base, "ralph-cancel", "--project", str(self.project), "--session-id", "task-2"],
            text=True, capture_output=True, check=True,
        )
        self.assertEqual(json.loads(wrong.stdout)["status"], "OTHER_SESSION")
        self.assertTrue(path.exists())
        cancelled = subprocess.run(
            [*base, "ralph-cancel", "--project", str(self.project), "--session-id", "task-1"],
            text=True, capture_output=True, check=True,
        )
        self.assertEqual(json.loads(cancelled.stdout), {"status": "CANCELLED", "iteration": 1})
        self.assertFalse(path.exists())

    def test_advisor_subagent_identity_and_verdict_guard_pending_state(self):
        path = self.state("advisor", {
            "session_id": "task-1", "enabled": True, "nudge": True,
            "pending": True, "consults": 0, "expected_agent_id": "advisor-42",
        })
        event = {
            "hook_event_name": "SubagentStop", "cwd": str(self.project),
            "session_id": "task-1", "turn_id": "turn-1", "agent_id": "wrong",
            "agent_type": "advisor-subagent", "last_assistant_message": "Verdict: proceed",
        }
        self.assertEqual(self.call("advisor-subagent-stop", event), {})
        self.assertTrue(json.loads(path.read_text())["pending"])
        event["agent_id"] = "advisor-42"
        self.assertEqual(self.call("advisor-subagent-stop", event | {"agent_type": "reviewer"}), {})
        self.assertTrue(json.loads(path.read_text())["pending"])
        warning = self.call("advisor-subagent-stop", event | {"last_assistant_message": "No verdict"})
        self.assertIn("lacked a verdict", warning["systemMessage"])
        self.assertTrue(json.loads(path.read_text())["pending"])
        self.assertEqual(self.call("advisor-subagent-stop", event), {})
        state = json.loads(path.read_text())
        self.assertEqual(state["consults"], 1)
        self.assertFalse(state["pending"])
        self.assertEqual(self.call("advisor-subagent-stop", event), {})
        self.assertEqual(json.loads(path.read_text())["consults"], 1)

    def test_advisor_explicit_task_binding_expectation_and_disable(self):
        missing = self.command("advisor-enable", "--session-id", "task-1")
        self.assertIn("model must be explicitly selected", missing["systemMessage"])
        self.assertFalse((self.project / ".codex/cursor-mirror-state/advisor/state.json").exists())
        enabled = self.command("advisor-enable", "--session-id", "task-1",
                               "--advisor-model", "gpt-6-astra", "--nudge", "off")
        self.assertEqual(enabled["status"], "BOUND_HOOK_TRUST_UNVERIFIED")
        self.assertEqual(enabled["model"], "gpt-6-astra")
        self.assertFalse(enabled["nudge"])
        self.assertEqual(self.command("advisor-status", "--session-id", "other"),
                         {"status": "OTHER_SESSION"})
        self.assertEqual(self.command("advisor-expect", "--session-id", "other",
                                      "--advisor-agent-id", "advisor-42"),
                         {"status": "NOT_BOUND_HERE"})
        expected = self.command("advisor-expect", "--session-id", "task-1",
                                "--advisor-agent-id", "advisor-42")
        self.assertEqual(expected["status"], "AWAITING_ADVISOR")
        path = self.project / ".codex/cursor-mirror-state/advisor/state.json"
        self.assertEqual(json.loads(path.read_text())["expected_agent_id"], "advisor-42")
        self.assertEqual(self.command("advisor-expect", "--session-id", "task-1",
                                      "--advisor-agent-id", "advisor-43"),
                         {"status": "CONSULT_ALREADY_PENDING"})
        verdict = {"hook_event_name": "SubagentStop", "cwd": str(self.project),
                   "session_id": "task-1", "turn_id": "turn-1",
                   "agent_id": "advisor-42", "agent_type": "advisor-subagent",
                   "last_assistant_message": "Verdict: proceed with changes\nFix the edge case."}
        self.assertEqual(self.call("advisor-subagent-stop", verdict), {})
        status = self.command("advisor-status", "--session-id", "task-1")
        self.assertEqual(status["consults"], 1)
        self.assertEqual(self.command("advisor-expect", "--session-id", "task-1",
                                      "--advisor-agent-id", "advisor-42")["status"],
                         "AWAITING_ADVISOR")
        self.assertEqual(self.call("advisor-subagent-stop", verdict | {"turn_id": "turn-2"}), {})
        self.assertEqual(self.command("advisor-status", "--session-id", "task-1")["consults"], 2)
        self.assertEqual(self.command("advisor-disable", "--session-id", "other"),
                         {"status": "OTHER_SESSION"})
        self.assertTrue(path.exists())
        self.assertEqual(self.command("advisor-disable", "--session-id", "task-1"),
                         {"status": "DISABLED"})
        self.assertFalse(path.exists())

    def test_advisor_rebind_preserves_selection_but_clears_old_session_state(self):
        self.state("advisor", {"enabled": True, "session_id": "old-task",
                               "model": "gpt-6-astra", "nudge": False, "consults": 4,
                               "pending": True, "expected_agent_id": "old-agent"})
        rebound = self.command("advisor-enable", "--session-id", "new-task")
        self.assertEqual(rebound["model"], "gpt-6-astra")
        self.assertFalse(rebound["nudge"])
        state = json.loads((self.project / ".codex/cursor-mirror-state/advisor/state.json").read_text())
        self.assertEqual(state["session_id"], "new-task")
        self.assertEqual(state["consults"], 0)
        self.assertFalse(state["pending"])
        self.assertIsNone(state["expected_agent_id"])
        self.assertEqual(self.command("advisor-disable", "--session-id", "old-task"),
                         {"status": "OTHER_SESSION"})

    def test_advisor_patch_event_marks_only_successful_task_edits(self):
        path = self.state("advisor", {
            "session_id": "task-1", "enabled": True, "nudge": True,
            "pending": False, "consults": 0,
        })
        event = {
            "hook_event_name": "PostToolUse", "cwd": str(self.project),
            "session_id": "task-1", "turn_id": "turn-1",
            "tool_name": "apply_patch", "tool_use_id": "patch-1",
            "tool_input": {"command": "*** Begin Patch\n..."},
            "tool_response": {"exit_code": 0},
        }
        self.assertEqual(self.call("advisor-post-tool-use", event | {"session_id": "other"}), {})
        self.assertEqual(self.call("advisor-post-tool-use", event | {"cwd": str(self.other)}), {})
        self.assertEqual(self.call("advisor-post-tool-use", event | {"tool_name": "Bash"}), {})
        self.assertEqual(self.call("advisor-post-tool-use", event | {"tool_response": {"exit_code": 1}}), {})
        self.assertFalse(json.loads(path.read_text())["pending"])
        self.assertEqual(self.call("advisor-post-tool-use", event), {})
        state = json.loads(path.read_text())
        self.assertTrue(state["pending"])
        self.assertEqual(state["last_edit_tool_use_id"], "patch-1")
        state["pending"] = False
        path.write_text(json.dumps(state))
        self.assertEqual(self.call("advisor-post-tool-use", event), {})
        self.assertFalse(json.loads(path.read_text())["pending"])
        event["tool_use_id"] = "patch-2"
        self.assertEqual(self.call("advisor-post-tool-use", event), {})
        self.assertTrue(json.loads(path.read_text())["pending"])

    def test_advisor_nudges_once_but_keeps_question_pending(self):
        path = self.state("advisor", {
            "session_id": "task-1", "enabled": True, "nudge": True,
            "pending": True, "consults": 0,
        })
        self.assertEqual(self.call("advisor-stop", self.stop_event(message="Which branch?")), {})
        self.assertTrue(json.loads(path.read_text())["pending"])
        nudge = self.call("advisor-stop", self.stop_event(turn="turn-2", message="Done."))
        self.assertEqual(nudge["decision"], "block")
        self.assertIn("advisor consult", nudge["reason"])
        self.assertFalse(json.loads(path.read_text())["pending"])
        self.assertEqual(self.call("advisor-stop", self.stop_event(turn="turn-2")), {})
        self.assertEqual(self.call("advisor-stop", self.stop_event(turn="turn-3")), {})

    def test_continual_learning_threshold_and_transcript_boundary(self):
        transcripts = self.root / "transcripts"
        transcripts.mkdir()
        transcript = transcripts / "task-1.jsonl"
        transcript.write_text("fixture only\n")
        os.utime(transcript, ns=(2_000_000_000_000_000_000,) * 2)
        path = self.state("continual-learning", {
            "session_id": "task-1", "enabled": True,
            "transcript_root": str(transcripts), "turns_since_last_run": 8,
            "last_run_at_ms": 0, "last_transcript_mtime_ms": None,
        })
        event = self.stop_event() | {"transcript_path": str(transcript)}
        self.assertEqual(self.call("continual-learning-stop", event | {"session_id": "other"}), {})
        self.assertEqual(self.call("continual-learning-stop", event | {"stop_hook_active": True}), {})
        self.assertEqual(self.call("continual-learning-stop", event), {})
        self.assertEqual(json.loads(path.read_text())["turns_since_last_run"], 9)
        self.assertEqual(self.call("continual-learning-stop", event), {})
        self.assertEqual(json.loads(path.read_text())["turns_since_last_run"], 9)

        outside = self.root / "outside.jsonl"
        outside.write_text("outside fixture\n")
        event["turn_id"] = "turn-2"
        event["transcript_path"] = None
        self.assertEqual(self.call("continual-learning-stop", event), {})
        self.assertEqual(json.loads(path.read_text())["turns_since_last_run"], 10)
        event["turn_id"] = "turn-3"
        event["transcript_path"] = str(outside)
        self.assertEqual(self.call("continual-learning-stop", event), {})
        self.assertEqual(json.loads(path.read_text())["turns_since_last_run"], 11)
        event["turn_id"] = "turn-4"
        event["transcript_path"] = str(transcript)
        ready = self.call("continual-learning-stop", event)
        self.assertEqual(ready["decision"], "block")
        self.assertIn("cursor-continual-learning", ready["reason"])
        state = json.loads(path.read_text())
        self.assertEqual(state["turns_since_last_run"], 0)
        self.assertEqual(state["last_transcript_mtime_ms"], 2_000_000_000_000)

    def test_continual_learning_trial_does_not_retrigger_on_same_mtime(self):
        transcripts = self.root / "transcripts"
        transcripts.mkdir()
        transcript = transcripts / "task-1.jsonl"
        transcript.write_text("fixture only\n")
        path = self.state("continual-learning", {
            "session_id": "task-1", "enabled": True,
            "transcript_root": str(transcripts), "turns_since_last_run": 2,
            "last_run_at_ms": 0, "last_transcript_mtime_ms": None,
            "trial": {"enabled": True},
        })
        event = self.stop_event() | {"transcript_path": str(transcript)}
        self.assertEqual(self.call("continual-learning-stop", event)["decision"], "block")
        state = json.loads(path.read_text())
        self.assertIsInstance(state["trial_started_at_ms"], int)
        state["turns_since_last_run"] = 2
        state["last_run_at_ms"] = 0
        path.write_text(json.dumps(state))
        event["turn_id"] = "turn-2"
        self.assertEqual(self.call("continual-learning-stop", event), {})
        self.assertEqual(json.loads(path.read_text())["turns_since_last_run"], 3)

    def test_continual_learning_environment_overrides_and_expired_trial(self):
        transcripts = self.root / "transcripts"
        transcripts.mkdir()
        transcript = transcripts / "task-1.jsonl"
        transcript.write_text("fixture only\n")
        path = self.state("continual-learning", {
            "session_id": "task-1", "enabled": True,
            "transcript_root": str(transcripts), "turns_since_last_run": 1,
            "last_run_at_ms": 0, "last_transcript_mtime_ms": None,
            "trial_started_at_ms": 1,
        })
        event = self.stop_event() | {"transcript_path": str(transcript)}
        env = {
            "CONTINUAL_LEARNING_TRIAL_MODE": "true",
            "CONTINUAL_LEARNING_TRIAL_DURATION_MINUTES": "1",
            "CONTINUAL_LEARNING_MIN_TURNS": "2",
            "CONTINUAL_LEARNING_MIN_MINUTES": "1",
        }
        response = self.call("continual-learning-stop", event, env=env)
        self.assertEqual(response["decision"], "block")
        self.assertEqual(json.loads(path.read_text())["turns_since_last_run"], 0)

    def test_state_directory_symlink_cannot_redirect_hook_writes(self):
        outside = self.root / "outside-state"
        outside.mkdir()
        (self.project / ".codex").symlink_to(outside, target_is_directory=True)
        event = self.stop_event()
        warning = self.call("ralph-stop", event)
        self.assertIn("must not be a symlink", warning["systemMessage"])
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
