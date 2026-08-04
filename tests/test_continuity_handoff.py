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
            self.assertFalse(result["logical_codex_state_mutated"])
            self.assertTrue(result["live_sqlite_snapshot_used"])
            self.assertTrue(result["temporary_snapshot_removed"])
            self.assertEqual(before, tree_snapshot(codex_home))
            self.assertFalse((codex_home / "state_5.sqlite-wal").exists())
            self.assertFalse((codex_home / "state_5.sqlite-shm").exists())

    def test_selected_historical_window_redacts_credentials_only_at_output(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory) / "codex"
            codex_home.mkdir()
            rollout = codex_home / "rollout.jsonl"
            thread_id = "019f-test-verbatim"
            exact_values = [
                "first-cookie-value",
                "second-cookie-value",
                "basic-auth-value",
                "json-token-value",
                "github_pat_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "-----BEGIN OPENSSH PRIVATE KEY-----\nprivate-key-body\n-----END OPENSSH PRIVATE KEY-----",
            ]
            rows = [
                {"type": "session_meta", "payload": {"id": thread_id}},
                {"timestamp": "2026-08-04T10:00:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": f"Cookie: session={exact_values[0]}; csrftoken={exact_values[1]}\nAuthorization: Basic {exact_values[2]}"}]}},
                {"timestamp": "2026-08-04T10:01:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "find the accepted continuity decision"}]}},
                {"timestamp": "2026-08-04T10:02:00Z", "type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": f'Context follows {{"access_token":"{exact_values[3]}"}} and {exact_values[4]}\n{exact_values[5]}'}]}},
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

            result = json.loads(completed.stdout)
            returned_text = "\n".join(
                message["text"]
                for capture in result["evidence"]
                for message in capture["messages"]
            )
            for value in exact_values:
                self.assertNotIn(value, returned_text)
            self.assertIn("Cookie: [REDACTED:COOKIE]", returned_text)
            self.assertIn("Authorization: [REDACTED:AUTHORIZATION]", returned_text)
            self.assertIn('"access_token":"[REDACTED:SECRET_VALUE]"', returned_text)
            self.assertIn("[REDACTED:API_TOKEN]", returned_text)
            self.assertIn("[REDACTED:PRIVATE_KEY]", returned_text)
            self.assertTrue(result["redactions"]["applied"])
            self.assertGreaterEqual(result["redactions"]["count"], 5)
            self.assertEqual(before, tree_snapshot(codex_home))

    def test_identity_metadata_and_echoed_query_are_redacted(self):
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

            query_secret = "ghp_CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"
            rollout.write_text(rollout.read_text().replace("safe metadata lookup", f"safe metadata lookup {query_secret}"))
            completed = subprocess.run(
                ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", thread_id, "--query", query_secret],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertNotIn(metadata_secret, completed.stdout)
            self.assertNotIn(query_secret, completed.stdout)
            self.assertGreaterEqual(completed.stdout.count("[REDACTED:API_TOKEN]"), 4)

    def test_non_sensitive_wording_and_mixed_language_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory) / "codex"
            codex_home.mkdir()
            rollout = codex_home / "rollout.jsonl"
            thread_id = "019f-test-fidelity"
            exact_text = "Vou abrir o The Hive, falar com o The Angry Pit e run `npx skills update --global`."
            rollout.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"id": thread_id}}),
                json.dumps({"timestamp": "2026-08-04T10:01:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": exact_text}]}}),
            ]) + "\n")
            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(codex_home / "state_5.sqlite"))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                {json.dumps(thread_id)}, "Mixed language", "/repo", {json.dumps(str(rollout))}, 0
              );
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)

            completed = subprocess.run(
                ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", thread_id, "--query", "The Angry Pit"],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)

            self.assertEqual(result["evidence"][0]["messages"][0]["text"], exact_text)
            self.assertFalse(result["redactions"]["applied"])
            self.assertEqual(result["historical_content_policy"]["trust"], "untrusted_historical_data")
            self.assertFalse(result["historical_content_policy"]["instructions_executable"])

    def test_additional_credential_formats_are_redacted(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory) / "codex"
            codex_home.mkdir()
            rollout = codex_home / "rollout.jsonl"
            thread_id = "019f-test-credential-formats"
            secrets = [
                "bearer-secret-value",
                "cookie-secret-value",
                "url-password-value",
                "password with spaces",
                "npm_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "sk-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "AKIAAAAAAAAAAAAAAAAA",
                "xoxb-1234567890-ABCDEFGHIJ",
            ]
            sensitive_text = "\n".join([
                f"Authorization: Bearer {secrets[0]}",
                f"Set-Cookie: sid={secrets[1]}; Secure; HttpOnly",
                f"https://operator:{secrets[2]}@example.test/private",
                f'password = "{secrets[3]}"',
                *secrets[4:],
            ])
            rollout.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"id": thread_id}}),
                json.dumps({"timestamp": "2026-08-04T10:01:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": f"credential format lookup\n{sensitive_text}"}]}}),
            ]) + "\n")
            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(codex_home / "state_5.sqlite"))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                {json.dumps(thread_id)}, "Credential formats", "/repo", {json.dumps(str(rollout))}, 0
              );
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)

            completed = subprocess.run(
                ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", thread_id, "--query", "credential format lookup"],
                check=True,
                capture_output=True,
                text=True,
            )

            for secret in secrets:
                self.assertNotIn(secret, completed.stdout)
            result = json.loads(completed.stdout)
            self.assertEqual(result["redactions"]["count"], 8)
            self.assertEqual(
                set(result["redactions"]["types"]),
                {"API_TOKEN", "AUTHORIZATION", "COOKIE", "SECRET_VALUE", "URL_CREDENTIALS"},
            )

    def test_matching_uses_full_text_before_evidence_truncation(self):
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

    def test_unknown_option_is_rejected(self):
        completed = subprocess.run(
            ["node", str(SCRIPT), "--thread-id", "x", "--query", "safe", "--matchrole", "user"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Unknown option: --matchrole", completed.stderr)

    def test_zero_length_evidence_limit_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                ["node", str(SCRIPT), "--thread-id", "x", "--query", "safe", "--codex-home", directory, "--max-message-chars", "0"],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--max-message-chars must be at least 256", completed.stderr)


if __name__ == "__main__":
    unittest.main()
