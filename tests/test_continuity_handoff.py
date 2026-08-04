import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).parents[1]
SCRIPT = ROOT / "skills/engineering/continuity-handoff/scripts/recall-codex-history.mjs"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@unittest.skipIf(shutil.which("node") is None, "node is required")
class ContinuityHandoffTests(unittest.TestCase):
    def test_bounded_recall_is_read_only_and_evidence_located(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory) / "codex"
            codex_home.mkdir()
            rollout = codex_home / "sessions" / "rollout.jsonl"
            rollout.parent.mkdir()
            thread_id = "019f-test-continuity"
            rows = [
                {"type": "session_meta", "payload": {"id": thread_id}},
                {"timestamp": "2026-07-16T07:01:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "unrelated orientation"}]}},
                {"timestamp": "2026-07-16T07:01:30Z", "type": "response_item", "payload": {"type": "message", "role": "developer", "content": [{"type": "input_text", "text": "internal instruction that must not be returned"}]}},
                {"timestamp": "2026-07-16T07:02:21Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "apply_pending_macbook_profile_grafts.sh changed the visible title"}]}},
                {"timestamp": "2026-07-16T07:05:05Z", "type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Preserve the human session_index.thread_name and never promote threads.title."}]}},
                {"timestamp": "2026-07-16T07:09:00Z", "type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "bounded validation complete"}]}},
            ]
            rollout.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
            index = codex_home / "session_index.jsonl"
            index.write_text(json.dumps({"id": thread_id, "thread_name": "Traverse Origin"}) + "\n")

            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(codex_home / "state_5.sqlite"))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                {json.dumps(thread_id)}, "technical title", "/repo", {json.dumps(str(rollout))}, 0
              );
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)
            protected = [rollout, codex_home / "state_5.sqlite", index]
            before = {file: digest(file) for file in protected}

            completed = subprocess.run(
                [
                    "node", str(SCRIPT),
                    "--codex-home", str(codex_home),
                    "--thread-id", thread_id,
                    "--query", "apply_pending_macbook_profile_grafts.sh",
                    "--date", "2026-07-16",
                    "--match-role", "user",
                    "--before", "0",
                    "--after", "2",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)

            self.assertEqual(result["identity"]["title"], "Traverse Origin")
            self.assertEqual(result["scope"]["matched_windows"], 1)
            self.assertEqual(result["evidence"][0]["match_line"], 4)
            self.assertIn("session_index.thread_name", result["evidence"][0]["messages"][1]["text"])
            self.assertNotIn("internal instruction", completed.stdout)
            self.assertFalse(result["mutation_performed"])
            self.assertEqual(before, {file: digest(file) for file in protected})

    def test_sensitive_history_query_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                ["node", str(SCRIPT), "--thread-id", "x", "--query", "find password", "--codex-home", directory],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Sensitive-history queries are not allowed", completed.stderr)

    def test_unknown_option_is_rejected(self):
        completed = subprocess.run(
            ["node", str(SCRIPT), "--thread-id", "x", "--query", "safe", "--matchrole", "user"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Unknown option: --matchrole", completed.stderr)


if __name__ == "__main__":
    unittest.main()
