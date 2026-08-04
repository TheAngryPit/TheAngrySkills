import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).parents[1]
SCRIPT = ROOT / "skills/engineering/continuity-handoff/scripts/recall-codex-history.mjs"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_snapshot(root):
    return {
        str(path.relative_to(root)): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


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
            before = tree_snapshot(codex_home)

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
            self.assertEqual(before, tree_snapshot(codex_home))
            self.assertFalse((codex_home / "state_5.sqlite-wal").exists())
            self.assertFalse((codex_home / "state_5.sqlite-shm").exists())

    def test_secrets_are_redacted_from_all_returned_context(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory) / "codex"
            codex_home.mkdir()
            rollout = codex_home / "rollout.jsonl"
            thread_id = "019f-test-redaction"
            secrets = [
                "first-cookie-must-not-leak",
                "second-cookie-must-not-leak",
                "basic-auth-must-not-leak",
                "json-token-must-not-leak",
                "github_pat_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "-----BEGIN OPENSSH PRIVATE KEY-----\nprivate-key-body-must-not-leak\n-----END OPENSSH PRIVATE KEY-----",
            ]
            rows = [
                {"type": "session_meta", "payload": {"id": thread_id}},
                {"timestamp": "2026-08-04T10:00:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": f"Cookie: session={secrets[0]}; csrftoken={secrets[1]}\nAuthorization: Basic {secrets[2]}"}]}},
                {"timestamp": "2026-08-04T10:01:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "find the accepted continuity decision"}]}},
                {"timestamp": "2026-08-04T10:02:00Z", "type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": f'Context follows {{"access_token":"{secrets[3]}"}} and {secrets[4]}\n{secrets[5]}'}]}},
            ]
            rollout.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(codex_home / "state_5.sqlite"))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                {json.dumps(thread_id)}, "Continuity", "/repo", {json.dumps(str(rollout))}, 0
              );
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)
            before = tree_snapshot(codex_home)

            completed = subprocess.run(
                [
                    "node", str(SCRIPT),
                    "--codex-home", str(codex_home),
                    "--thread-id", thread_id,
                    "--query", "accepted continuity decision",
                    "--before", "1",
                    "--after", "1",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            for secret in secrets:
                self.assertNotIn(secret, completed.stdout)
            self.assertGreaterEqual(completed.stdout.count("[REDACTED"), 4)
            self.assertEqual(before, tree_snapshot(codex_home))

    def test_secrets_are_redacted_from_returned_identity_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory) / "codex"
            codex_home.mkdir()
            metadata_secret = "github_pat_BBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
            rollout = codex_home / f"rollout-{metadata_secret}.jsonl"
            thread_id = "019f-test-metadata"
            rollout.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"id": thread_id}}),
                json.dumps({"timestamp": "2026-08-04T10:01:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "safe metadata lookup"}]}}),
            ]) + "\n")
            (codex_home / "session_index.jsonl").write_text(
                json.dumps({"id": thread_id, "thread_name": f"Task {metadata_secret}"}) + "\n"
            )
            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(codex_home / "state_5.sqlite"))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                {json.dumps(thread_id)}, "fallback", {json.dumps(f'/repo/{metadata_secret}')}, {json.dumps(str(rollout))}, 0
              );
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)

            completed = subprocess.run(
                ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", thread_id, "--query", "safe metadata lookup"],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertNotIn(metadata_secret, completed.stdout)
            self.assertIn("[REDACTED_TOKEN]", completed.stdout)

    def test_matching_uses_full_redacted_text_before_evidence_truncation(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory) / "codex"
            codex_home.mkdir()
            rollout = codex_home / "rollout.jsonl"
            thread_id = "019f-test-long-message"
            literal = "decision-after-evidence-limit"
            long_text = f"{'x' * 3000}{literal}"
            rollout.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"id": thread_id}}),
                json.dumps({"timestamp": "2026-08-04T10:01:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": long_text}]}}),
            ]) + "\n")
            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(codex_home / "state_5.sqlite"))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                {json.dumps(thread_id)}, "Long message", "/repo", {json.dumps(str(rollout))}, 0
              );
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)

            completed = subprocess.run(
                ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", thread_id, "--query", literal, "--max-message-chars", "2400"],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)

            self.assertEqual(result["scope"]["matched_windows"], 1)
            evidence = result["evidence"][0]["messages"][0]["text"]
            self.assertIn(literal, evidence)
            self.assertTrue(evidence.startswith("[TRUNCATED PREFIX]"))

    def test_live_wal_database_is_recalled_while_writer_remains_open(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            codex_home = root / "codex"
            codex_home.mkdir()
            database = codex_home / "state_5.sqlite"
            rollout = codex_home / "rollout.jsonl"
            thread_id = "019f-test-live-wal"
            rollout.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"id": thread_id}}),
                json.dumps({"timestamp": "2026-08-04T11:00:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "live continuity lookup"}]}}),
            ]) + "\n")
            writer_source = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(database))});
              db.exec("PRAGMA journal_mode=WAL");
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                {json.dumps(thread_id)}, "Live task", "/repo", {json.dumps(str(rollout))}, 0
              );
              process.stdout.write("ready\\n");
              setInterval(() => {{}}, 1000);
            '''
            writer = subprocess.Popen(
                ["node", "-e", writer_source],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                self.assertEqual(writer.stdout.readline().strip(), "ready")
                self.assertTrue((codex_home / "state_5.sqlite-wal").exists())
                self.assertTrue((codex_home / "state_5.sqlite-shm").exists())
                before = tree_snapshot(codex_home)

                completed = subprocess.run(
                    ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", thread_id, "--query", "live continuity lookup"],
                    check=True,
                    capture_output=True,
                    text=True,
                    env={**os.environ, "TMPDIR": str(root)},
                )
                result = json.loads(completed.stdout)
                after = tree_snapshot(codex_home)

                self.assertEqual(result["identity"]["title"], "Live task")
                self.assertEqual(result["scope"]["matched_windows"], 1)
                self.assertIsNone(writer.poll())
                self.assertEqual(set(before), set(after))
                for name in ["rollout.jsonl", "state_5.sqlite", "state_5.sqlite-wal"]:
                    self.assertEqual(before[name], after[name])
                self.assertFalse(any(root.glob("continuity-recall-*")))
            finally:
                writer.terminate()
                writer.wait(timeout=5)
                writer.stdout.close()
                writer.stderr.close()

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
