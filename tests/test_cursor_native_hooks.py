"""Synthetic Codex hook-payload proof; project hook registration is a separate step."""

import json
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

    def call(self, handler, event, project=None):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), handler, "--project", str(project or self.project)],
            input=json.dumps(event), text=True, capture_output=True, check=True,
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
            "session_id": "task-1", "prompt": "Fix the flaky test", "iteration": 0,
            "max_iterations": 3, "completion_promise": "tests pass",
        })
        first = self.call("ralph-stop", self.stop_event(message="Still working"))
        self.assertEqual(first["decision"], "block")
        self.assertIn("Fix the flaky test", first["reason"])
        self.assertIn("iteration 1", first["reason"])
        self.assertEqual(json.loads(path.read_text())["iteration"], 1)
        self.assertEqual(self.call("ralph-stop", self.stop_event(message="Still working")), {})
        self.assertEqual(json.loads(path.read_text())["iteration"], 1)

        second = self.call("ralph-stop", self.stop_event(turn="turn-2", message="tests pass"))
        self.assertEqual(second["decision"], "block")
        self.assertEqual(json.loads(path.read_text())["iteration"], 2)
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

    def test_advisor_subagent_identity_and_verdict_guard_pending_state(self):
        path = self.state("advisor", {
            "session_id": "task-1", "enabled": True, "nudge": True,
            "pending": True, "consults": 0, "expected_agent_id": "advisor-42",
        })
        event = {
            "hook_event_name": "SubagentStop", "cwd": str(self.project),
            "session_id": "task-1", "turn_id": "turn-1", "agent_id": "wrong",
            "agent_type": "reviewer", "last_assistant_message": "Verdict: proceed",
        }
        self.assertEqual(self.call("advisor-subagent-stop", event), {})
        self.assertTrue(json.loads(path.read_text())["pending"])
        event["agent_id"] = "advisor-42"
        warning = self.call("advisor-subagent-stop", event | {"last_assistant_message": "No verdict"})
        self.assertIn("lacked a verdict", warning["systemMessage"])
        self.assertTrue(json.loads(path.read_text())["pending"])
        self.assertEqual(self.call("advisor-subagent-stop", event), {})
        state = json.loads(path.read_text())
        self.assertEqual(state["consults"], 1)
        self.assertFalse(state["pending"])
        self.assertEqual(self.call("advisor-subagent-stop", event), {})
        self.assertEqual(json.loads(path.read_text())["consults"], 1)

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


if __name__ == "__main__":
    unittest.main()
