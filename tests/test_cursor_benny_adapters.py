"""Focused no-write tests for the conditional Benny event gate."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from cursor_benny_adapters import (  # noqa: E402
    accept_triage_reply,
    evaluate_intake_event,
)


CONFIG = {
    "slack": {
        "source_channel_id": "C-source",
        "triage_identity_user_id": "U-triage",
    },
    "verdict_markers": {
        "bug": "[benny:bug]",
        "performance": "[benny:performance]",
        "other": "[benny:other]",
    },
}
ROOT = {"source_channel_id": "C-source", "source_thread_ts": "100.001"}


def no_write(result):
    assert result["external_writes"] is False
    assert result["scheduled"] is False
    assert result["activated"] is False
    assert result["write_actions"] == []


class BennyAdapterTests(unittest.TestCase):
    def test_top_level_event_freezes_message_as_root(self):
        result = evaluate_intake_event(
            {"source_channel_id": "C-source", "message_ts": "100.001"}, CONFIG
        )
        self.assertEqual(result["status"], "READY_FOR_TRIAGE")
        self.assertEqual(result["source_thread_ts"], "100.001")
        no_write(result)

    def test_wrong_channel_and_reply_cannot_enter(self):
        for event in (
            {"source_channel_id": "C-other", "message_ts": "100.001"},
            {"source_channel_id": "C-source", "message_ts": "100.002", "thread_ts": "100.001"},
        ):
            result = evaluate_intake_event(event, CONFIG)
            self.assertEqual(result["status"], "BLOCKED")
            no_write(result)

    def test_activation_and_schedule_requests_are_blocked(self):
        for key in ("activation_requested", "schedule_requested", "enable_requested"):
            result = evaluate_intake_event(
                {"source_channel_id": "C-source", "message_ts": "100.001", key: True}, CONFIG
            )
            self.assertEqual(result["status"], "BLOCKED")
            no_write(result)

    def test_missing_config_fails_closed(self):
        result = evaluate_intake_event(
            {"source_channel_id": "C-source", "message_ts": "100.001"}, {"slack": {}}
        )
        self.assertEqual(result["status"], "BLOCKED")
        no_write(result)

    def test_trusted_bug_reply_is_accepted(self):
        result = accept_triage_reply(
            {
                "channel_id": "C-source",
                "thread_ts": "100.001",
                "is_reply": True,
                "author_id": "U-triage",
                "text": "confirmed\n[benny:bug] tracker=https://tracker.example/1",
            },
            CONFIG,
            ROOT,
        )
        self.assertEqual(result["status"], "TRIAGE_ACCEPTED")
        self.assertEqual(result["category"], "bug")
        no_write(result)

    def test_untrusted_or_wrong_thread_reply_is_blocked(self):
        for reply in (
            {"channel_id": "C-source", "thread_ts": "100.001", "is_reply": True, "author_id": "U-other", "text": "[benny:bug]"},
            {"channel_id": "C-source", "thread_ts": "100.002", "is_reply": True, "author_id": "U-triage", "text": "[benny:bug]"},
            {"channel_id": "C-source", "thread_ts": "100.001", "is_reply": False, "author_id": "U-triage", "text": "[benny:bug]"},
            {"channel_id": "C-source", "thread_ts": "100.001", "author_id": "U-triage", "text": "[benny:bug]"},
        ):
            result = accept_triage_reply(reply, CONFIG, ROOT)
            self.assertEqual(result["status"], "BLOCKED")
            no_write(result)

    def test_missing_other_and_duplicate_markers_are_safe(self):
        base = {"channel_id": "C-source", "thread_ts": "100.001", "is_reply": True, "author_id": "U-triage"}
        for body, status in (("still checking", "WAITING_FOR_TRIAGE"), ("[benny:other]", "TRIAGE_STOPPED"), ("[benny:bug] [benny:performance]", "BLOCKED"), ("[benny:bug] [benny:bug]", "BLOCKED")):
            result = accept_triage_reply({**base, "text": body}, CONFIG, ROOT)
            self.assertEqual(result["status"], status)
            no_write(result)

    def test_cli_is_json_and_no_write(self):
        payload = {"event": {"source_channel_id": "C-source", "message_ts": "100.001"}, "config": CONFIG}
        completed = subprocess.run(
            [sys.executable, "scripts/cursor_benny_adapters.py", "intake"],
            cwd=REPO,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "READY_FOR_TRIAGE")
        no_write(result)


if __name__ == "__main__":
    unittest.main()
