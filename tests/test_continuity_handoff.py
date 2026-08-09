import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
import unittest


ROOT = pathlib.Path(__file__).parents[1]
SCRIPT = ROOT / "skills/engineering/continuity-handoff/scripts/recall-codex-history.mjs"
WRITER = ROOT / "skills/engineering/continuity-handoff/scripts/write-continuity-packet.mjs"
VALIDATOR = ROOT / "skills/engineering/continuity-handoff/scripts/validate-handoff-acceptance.mjs"
SKILL = ROOT / "skills/engineering/continuity-handoff/SKILL.md"


def run_git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def init_git_repo(repo):
    repo.mkdir()
    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.email", "continuity@example.invalid")
    run_git(repo, "config", "user.name", "Continuity Test")
    (repo / "README.md").write_text("fixture\n")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-q", "-m", "fixture")


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
    def test_rollout_hashing_streams_instead_of_loading_the_file(self):
        source = SCRIPT.read_text()
        self.assertIn("fs.createReadStream(filePath)", source)
        self.assertNotIn("fs.readFileSync(filePath)", source)

    def test_create_writes_durable_versionable_packet_without_committing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            repo = root / "repo"
            init_git_repo(repo)
            packet = root / "draft.md"
            packet.write_text("# Work\n\nPortable continuity fixture.\n")
            before_head = run_git(repo, "rev-parse", "HEAD")

            completed = subprocess.run(
                [
                    "node", str(WRITER),
                    "--packet-file", str(packet),
                    "--project-root", str(repo),
                    "--work-slug", "portable-handoff",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)
            output = repo / ".traverse/continuity/portable-handoff.md"
            expected_contents = packet.read_text()
            packet.unlink()

            self.assertEqual(output.read_text(), expected_contents)
            self.assertEqual(pathlib.Path(result["path"]).resolve(), output.resolve())
            self.assertEqual(result["git_state"], "visible_in_git_status")
            self.assertFalse(result["auto_committed"])
            self.assertFalse(result["source_thread_mutated"])
            self.assertIn("?? .traverse/continuity/portable-handoff.md", run_git(repo, "status", "--porcelain=v1", "--untracked-files=all"))
            self.assertEqual(run_git(repo, "rev-parse", "HEAD"), before_head)
            self.assertEqual(list((repo / ".traverse/continuity").glob("*.md")), [output])
            self.assertNotIn("/private/tmp", str(output))

    def test_secret_blocks_packet_write_without_redaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            repo = root / "repo"
            init_git_repo(repo)
            secret = "github_pat_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            packet = root / "draft.md"
            packet.write_text(f"# Work\n\nCredential: {secret}\n")

            completed = subprocess.run(
                [
                    "node", str(WRITER),
                    "--packet-file", str(packet),
                    "--project-root", str(repo),
                    "--work-slug", "blocked-handoff",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("packet_secret_detected", completed.stderr)
            self.assertNotIn(secret, completed.stderr)
            self.assertFalse((repo / ".traverse/continuity/blocked-handoff.md").exists())
            self.assertEqual(packet.read_text(), f"# Work\n\nCredential: {secret}\n")

    def test_ignored_default_destination_is_rejected_without_gitignore_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            repo = root / "repo"
            init_git_repo(repo)
            ignore = repo / ".gitignore"
            ignore.write_text(".traverse/\n")
            packet = root / "draft.md"
            packet.write_text("# Work\n\nSafe fixture.\n")

            completed = subprocess.run(
                [
                    "node", str(WRITER),
                    "--packet-file", str(packet),
                    "--project-root", str(repo),
                    "--work-slug", "ignored-handoff",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("packet_path_ignored", completed.stderr)
            self.assertEqual(ignore.read_text(), ".traverse/\n")
            self.assertFalse((repo / ".traverse/continuity/ignored-handoff.md").exists())

    def test_symlinked_continuity_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            repo = root / "repo"
            outside = root / "outside"
            init_git_repo(repo)
            outside.mkdir()
            (repo / ".traverse").symlink_to(outside, target_is_directory=True)
            packet = root / "draft.md"
            packet.write_text("# Work\n\nSafe fixture.\n")

            completed = subprocess.run(
                [
                    "node", str(WRITER),
                    "--packet-file", str(packet),
                    "--project-root", str(repo),
                    "--work-slug", "symlink-handoff",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("packet_symlink_boundary", completed.stderr)
            self.assertFalse((outside / "continuity/symlink-handoff.md").exists())

    def test_symlinked_packet_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            repo = root / "repo"
            outside = root / "outside.md"
            init_git_repo(repo)
            destination = repo / ".traverse/continuity/symlink-handoff.md"
            destination.parent.mkdir(parents=True)
            outside.write_text("outside\n")
            destination.symlink_to(outside)
            packet = root / "draft.md"
            packet.write_text("# Work\n\nSafe fixture.\n")

            completed = subprocess.run(
                [
                    "node", str(WRITER),
                    "--packet-file", str(packet),
                    "--project-root", str(repo),
                    "--work-slug", "symlink-handoff",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("packet_symlink_boundary", completed.stderr)
            self.assertEqual(outside.read_text(), "outside\n")

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
                    "--rollout-path", str(rollout),
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

            self.assertEqual(result["output_schema_version"], 2)
            self.assertEqual(result["legacy_snapshot_flags_migration"], "schema_v2_false_means_no_snapshot_was_created")
            self.assertEqual(result["identity"]["title"], "Traverse Origin")
            self.assertEqual(result["scope"]["matched_windows"], 1)
            self.assertEqual(result["evidence"][0]["match_line"], 4)
            self.assertIn("session_index.thread_name", result["evidence"][0]["messages"][1]["text"])
            self.assertNotIn("internal instruction", completed.stdout)
            self.assertFalse(result["logical_codex_state_mutated"])
            self.assertFalse(result["live_sqlite_snapshot_used"])
            self.assertFalse(result["temporary_snapshot_removed"])
            self.assertEqual(result["sqlite_read"]["method"], "bounded_read_only_wal_aware_query")
            self.assertTrue(result["sqlite_read"]["read_only"])
            self.assertTrue(result["sqlite_read"]["query_only"])
            self.assertFalse(result["sqlite_read"]["wal_present"])
            self.assertFalse(result["sqlite_read"]["shm_present"])
            self.assertTrue(result["sqlite_read"]["shm_is_coordination_state"])
            self.assertEqual(before, tree_snapshot(codex_home))
            self.assertFalse((codex_home / "state_5.sqlite-wal").exists())
            self.assertFalse((codex_home / "state_5.sqlite-shm").exists())

    def test_selected_historical_window_is_returned_verbatim(self):
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
                    "--rollout-path", str(rollout),
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
                self.assertIn(value, returned_text)
            self.assertNotIn("[REDACTED", completed.stdout)
            self.assertEqual(before, tree_snapshot(codex_home))

    def test_identity_metadata_is_returned_verbatim(self):
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
                ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", thread_id, "--rollout-path", str(rollout), "--query", "safe metadata lookup"],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn(metadata_secret, completed.stdout)
            self.assertNotIn("[REDACTED", completed.stdout)

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
                ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", thread_id, "--rollout-path", str(rollout), "--query", literal, "--max-message-chars", "2400"],
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
                    ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", thread_id, "--rollout-path", str(rollout), "--query", "live continuity lookup"],
                    check=True,
                    capture_output=True,
                    text=True,
                    env={**os.environ, "TMPDIR": str(root)},
                )
                result = json.loads(completed.stdout)
                after = tree_snapshot(codex_home)

                self.assertEqual(result["identity"]["title"], "Live task")
                self.assertEqual(result["scope"]["matched_windows"], 1)
                self.assertTrue(result["sqlite_read"]["wal_present"])
                self.assertTrue(result["sqlite_read"]["shm_present"])
                self.assertTrue(result["sqlite_read"]["shm_is_coordination_state"])
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

    def test_live_wal_database_is_recalled_while_another_connection_keeps_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            codex_home = root / "codex"
            codex_home.mkdir()
            database = codex_home / "state_5.sqlite"
            rollout = codex_home / "rollout.jsonl"
            thread_id = "019f-test-live-wal-writes"
            rollout.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"id": thread_id}}),
                json.dumps({"timestamp": "2026-08-09T12:00:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "continuous WAL continuity lookup"}]}}),
            ]) + "\n")
            writer_source = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(database))});
              db.exec("PRAGMA journal_mode=WAL");
              db.exec("PRAGMA wal_autocheckpoint=0");
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.exec("CREATE TABLE churn (value INTEGER NOT NULL)");
              db.exec("INSERT INTO churn VALUES (0)");
              db.exec("CREATE TABLE padding (payload BLOB NOT NULL)");
              db.exec("WITH RECURSIVE counter(x) AS (VALUES(1) UNION ALL SELECT x + 1 FROM counter WHERE x < 4096) INSERT INTO padding SELECT randomblob(4096) FROM counter");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                {json.dumps(thread_id)}, "Live writing task", "/repo", {json.dumps(str(rollout))}, 0
              );
              const update = db.prepare("UPDATE churn SET value = value + 1");
              process.stdout.write("ready\\n");
              setInterval(() => update.run(), 0);
            '''
            writer = subprocess.Popen(
                ["node", "-e", writer_source],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                self.assertEqual(writer.stdout.readline().strip(), "ready")
                before = tree_snapshot(codex_home)

                completed = subprocess.run(
                    ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", thread_id, "--rollout-path", str(rollout), "--query", "continuous WAL continuity lookup"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=8,
                    env={**os.environ, "TMPDIR": str(root)},
                )
                result = json.loads(completed.stdout)
                after = tree_snapshot(codex_home)

                self.assertEqual(result["identity"]["title"], "Live writing task")
                self.assertEqual(result["scope"]["matched_windows"], 1)
                self.assertTrue(result["sqlite_read"]["wal_present"])
                self.assertTrue(result["sqlite_read"]["shm_present"])
                self.assertEqual(result["sqlite_read"]["watchdog"], "child_process_sigkill")
                self.assertLessEqual(result["sqlite_read"]["deadline_ms"], 750)
                self.assertTrue(result["sqlite_read"]["observed_file_set_equality"]["first_query_boundaries_equal"])
                self.assertTrue(result["sqlite_read"]["observed_file_set_equality"]["between_queries_equal"])
                self.assertTrue(result["sqlite_read"]["observed_file_set_equality"]["second_query_boundaries_equal"])
                self.assertTrue(result["sqlite_read"]["database_and_wal_bytes_may_change_due_to_external_writer"])
                self.assertEqual(result["source_proof"]["scope"], "exact_thread_row_and_rollout")
                self.assertFalse(result["source_proof"]["sqlite_database_bytes_immutable_claimed"])
                self.assertTrue(result["source_proof"]["unchanged"])
                self.assertIsNone(writer.poll())
                self.assertEqual(set(before), set(after))
                self.assertEqual(before["rollout.jsonl"], after["rollout.jsonl"])
                self.assertFalse(any(root.glob("continuity-recall-*")))
            finally:
                writer.terminate()
                writer.wait(timeout=5)
                writer.stdout.close()
                writer.stderr.close()

    def test_incomplete_wal_sidecars_fail_closed_without_opening_the_database(self):
        for sidecar in ["-wal", "-shm"]:
            with self.subTest(sidecar=sidecar), tempfile.TemporaryDirectory() as directory:
                codex_home = pathlib.Path(directory)
                database = codex_home / "state_5.sqlite"
                rollout = codex_home / "rollout.jsonl"
                rollout.write_text("")
                setup = f'''
                  const {{ DatabaseSync }} = require("node:sqlite");
                  const db = new DatabaseSync({json.dumps(str(database))});
                  db.exec("PRAGMA journal_mode=WAL");
                  db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT)");
                  db.close();
                '''
                subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)
                self.assertEqual(database.read_bytes()[18:20], b"\x02\x02")
                pathlib.Path(f"{database}{sidecar}").write_bytes(b"sidecar")
                before = tree_snapshot(codex_home)

                completed = subprocess.run(
                    ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", "exact-thread", "--rollout-path", str(rollout), "--query", "bounded"],
                    capture_output=True,
                    text=True,
                )

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("recall_source_unavailable: WAL-mode recorded state database requires existing readable -wal and -shm sidecars", completed.stderr)
                self.assertEqual(before, tree_snapshot(codex_home))

    def test_quiescent_wal_without_sidecars_fails_without_creating_them(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory)
            database = codex_home / "state_5.sqlite"
            rollout = codex_home / "rollout.jsonl"
            rollout.write_text("")
            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(database))});
              db.exec("PRAGMA journal_mode=WAL");
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT)");
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)
            self.assertEqual(database.read_bytes()[18:20], b"\x02\x02")
            self.assertFalse(pathlib.Path(f"{database}-wal").exists())
            self.assertFalse(pathlib.Path(f"{database}-shm").exists())
            before = tree_snapshot(codex_home)

            completed = subprocess.run(
                ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", "exact-thread", "--rollout-path", str(rollout), "--query", "bounded"],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("recall_source_unavailable: WAL-mode recorded state database requires existing readable -wal and -shm sidecars", completed.stderr)
            self.assertEqual(before, tree_snapshot(codex_home))
            self.assertFalse(pathlib.Path(f"{database}-wal").exists())
            self.assertFalse(pathlib.Path(f"{database}-shm").exists())

    def test_missing_exact_thread_row_fails_closed_without_source_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory)
            database = codex_home / "state_5.sqlite"
            rollout = codex_home / "rollout.jsonl"
            rollout.write_text("")
            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(database))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT)");
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)
            before = tree_snapshot(codex_home)

            completed = subprocess.run(
                ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", "missing-exact-thread", "--rollout-path", str(rollout), "--query", "bounded"],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("recall_source_unavailable: No exact thread row for missing-exact-thread", completed.stderr)
            self.assertEqual(before, tree_snapshot(codex_home))

    def test_locked_database_is_terminated_within_the_watchdog_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory)
            database = codex_home / "state_5.sqlite"
            rollout = codex_home / "rollout.jsonl"
            rollout.write_text("")
            writer_source = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(database))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT)");
              db.exec("BEGIN EXCLUSIVE");
              process.stdout.write("locked\\n");
              setInterval(() => {{}}, 1000);
            '''
            writer = subprocess.Popen(
                ["node", "-e", writer_source],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                self.assertEqual(writer.stdout.readline().strip(), "locked")
                before = tree_snapshot(codex_home)
                started_at = time.monotonic()

                completed = subprocess.run(
                    ["node", str(SCRIPT), "--codex-home", str(codex_home), "--thread-id", "exact-thread", "--rollout-path", str(rollout), "--query", "bounded"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )

                self.assertLess(time.monotonic() - started_at, 1.5)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("recall_source_unavailable: Timed out reading recorded state database", completed.stderr)
                self.assertNotIn("database is locked", completed.stderr)
                self.assertEqual(before, tree_snapshot(codex_home))
                self.assertIsNone(writer.poll())
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
                ["node", str(SCRIPT), "--thread-id", "x", "--query", "safe", "--codex-home", directory, "--rollout-path", str(pathlib.Path(directory) / "rollout.jsonl"), "--max-message-chars", "0"],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--max-message-chars must be at least 256", completed.stderr)

    def test_primary_target_can_recall_exact_secondary_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            primary_home = root / "primary"
            secondary_home = root / "secondary"
            primary_home.mkdir()
            secondary_home.mkdir()
            rollout = secondary_home / "rollout.jsonl"
            thread_id = "019f-secondary-source"
            rollout.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"id": thread_id}}),
                json.dumps({"timestamp": "2026-08-06T10:00:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "exact secondary evidence"}]}}),
            ]) + "\n")
            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(secondary_home / "state_5.sqlite"))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                {json.dumps(thread_id)}, "Secondary source", "/repo", {json.dumps(str(rollout))}, 0
              );
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)

            completed = subprocess.run(
                [
                    "node", str(SCRIPT),
                    "--codex-home", str(secondary_home),
                    "--thread-id", thread_id,
                    "--rollout-path", str(rollout),
                    "--work", "portable-continuity",
                    "--profile", "secondary",
                    "--device", "macbook-pro",
                    "--project", "TheAngrySkills",
                    "--query", "exact secondary evidence",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={**os.environ, "CODEX_HOME": str(primary_home)},
            )
            result = json.loads(completed.stdout)

            self.assertEqual(result["identity"]["work"], "portable-continuity")
            self.assertEqual(result["identity"]["profile"], "secondary")
            self.assertEqual(result["identity"]["device"], "macbook-pro")
            self.assertEqual(result["identity"]["project"], "TheAngrySkills")
            self.assertEqual(result["device_observation"]["codex_home"], str(secondary_home))
            self.assertEqual(result["scope"]["matched_windows"], 1)
            self.assertTrue(result["source_proof"]["unchanged"])

    def test_missing_recorded_source_fails_without_database_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            recorded = root / "recorded-secondary"
            nearby = root / "nearby-primary"
            recorded.mkdir()
            nearby.mkdir()
            (nearby / "state_5.sqlite").write_text("not the recorded source")

            completed = subprocess.run(
                [
                    "node", str(SCRIPT),
                    "--codex-home", str(recorded),
                    "--thread-id", "missing-thread",
                    "--rollout-path", str(recorded / "missing-rollout.jsonl"),
                    "--query", "do not discover",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("recall_source_unavailable", completed.stderr)
            self.assertIn(str(recorded / "state_5.sqlite"), completed.stderr)
            self.assertNotIn(str(nearby), completed.stderr)

    def test_corrupt_recorded_database_is_source_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory)
            rollout = codex_home / "rollout.jsonl"
            (codex_home / "state_5.sqlite").write_text("not sqlite")
            rollout.write_text(json.dumps({"type": "session_meta", "payload": {"id": "source"}}) + "\n")

            completed = subprocess.run(
                [
                    "node", str(SCRIPT),
                    "--codex-home", str(codex_home),
                    "--thread-id", "source",
                    "--rollout-path", str(rollout),
                    "--query", "anything",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("recall_source_unavailable", completed.stderr)
            self.assertNotIn("file is not a database", completed.stderr)

    def test_recall_without_exact_evidence_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory)
            rollout = codex_home / "rollout.jsonl"
            thread_id = "source-without-match"
            rollout.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"id": thread_id}}),
                json.dumps({"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "different evidence"}]}}),
            ]) + "\n")
            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(codex_home / "state_5.sqlite"))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                {json.dumps(thread_id)}, "No match", "/repo", {json.dumps(str(rollout))}, 0
              );
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)

            completed = subprocess.run(
                [
                    "node", str(SCRIPT),
                    "--codex-home", str(codex_home),
                    "--thread-id", thread_id,
                    "--rollout-path", str(rollout),
                    "--query", "missing exact evidence",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("recall_evidence_not_found", completed.stderr)

    def test_recorded_rollout_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = pathlib.Path(directory) / "secondary"
            codex_home.mkdir()
            exact_rollout = codex_home / "exact.jsonl"
            wrong_rollout = codex_home / "wrong.jsonl"
            thread_id = "019f-exact-rollout"
            exact_rollout.write_text(json.dumps({"type": "session_meta", "payload": {"id": thread_id}}) + "\n")
            wrong_rollout.write_text(json.dumps({"type": "session_meta", "payload": {"id": thread_id}}) + "\n")
            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(codex_home / "state_5.sqlite"))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                {json.dumps(thread_id)}, "Exact", "/repo", {json.dumps(str(exact_rollout))}, 0
              );
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)

            completed = subprocess.run(
                [
                    "node", str(SCRIPT),
                    "--codex-home", str(codex_home),
                    "--thread-id", thread_id,
                    "--rollout-path", str(wrong_rollout),
                    "--query", "anything",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("recall_source_unavailable", completed.stderr)
            self.assertIn("Recorded rollout mismatch", completed.stderr)

    def test_cross_profile_acceptance_requires_new_target_identity_and_source_proof(self):
        contract = " ".join(SKILL.read_text().split())
        required_fragments = [
            "Target Thread with a new Thread ID",
            "Target Thread ID is present and differs from the Source Thread ID",
            "one real bounded Recall query succeeds",
            "validates its Project Binding",
            "before/after evidence shows the Source Thread database row and rollout",
            "Never archive, delete, commit, rename, or otherwise mutate the Source Thread",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, contract)

        with tempfile.TemporaryDirectory() as directory:
            evidence = pathlib.Path(directory)
            acknowledgement = evidence / "ack.json"
            binding = evidence / "binding.json"
            project_root = evidence / "project"
            repo_root = project_root / "repo" / "TheAngrySkills"
            operational_cwd = repo_root / "skills"
            operational_cwd.mkdir(parents=True)
            (repo_root / ".git").mkdir()
            codex_home = evidence / "source-codex-home"
            codex_home.mkdir()
            rollout = codex_home / "rollout.jsonl"
            rollout.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"id": "source-id"}}),
                json.dumps({"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "real acceptance evidence"}]}}),
            ]) + "\n")
            setup = f'''
              const {{ DatabaseSync }} = require("node:sqlite");
              const db = new DatabaseSync({json.dumps(str(codex_home / "state_5.sqlite"))});
              db.exec("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT, archived INTEGER)");
              db.prepare("INSERT INTO threads VALUES (?, ?, ?, ?, ?)").run(
                "source-id", "Source", "/repo", {json.dumps(str(rollout))}, 0
              );
              db.close();
            '''
            subprocess.run(["node", "-e", setup], check=True, capture_output=True, text=True)
            acknowledgement.write_text(json.dumps({"acknowledged": True, "target_thread_id": "target-id"}))
            binding.write_text(json.dumps({
                "valid": True,
                "target_thread_id": "target-id",
                "project_binding": "TheAngrySkills",
                "binding_model": "project-root-with-nested-repo",
                "codex_project_root": str(project_root),
                "canonical_repo_root": str(repo_root),
                "operational_cwd": str(operational_cwd),
            }))

            common = [
                "--ack-file", str(acknowledgement),
                "--project-binding-file", str(binding),
                "--codex-home", str(codex_home),
                "--rollout-path", str(rollout),
                "--query", "real acceptance evidence",
            ]
            equal_ids = subprocess.run(
                [
                    "node", str(VALIDATOR),
                    "--source-thread-id", "same-id",
                    "--target-thread-id", "same-id",
                    *common,
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(equal_ids.returncode, 0)
            self.assertIn("target_thread_not_fresh", equal_ids.stderr)

            distinct_ids = subprocess.run(
                [
                    "node", str(VALIDATOR),
                    "--source-thread-id", "source-id",
                    "--target-thread-id", "target-id",
                    *common,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(distinct_ids.stdout)
            self.assertTrue(result["target_identity_is_fresh"])
            self.assertEqual(result["status"], "handoff_accepted")
            self.assertEqual(result["project_binding"]["binding_model"], "project-root-with-nested-repo")
            self.assertEqual(result["project_binding"]["canonical_repo_root"], str(repo_root))

            binding.write_text(json.dumps({
                "valid": True,
                "target_thread_id": "target-id",
                "project_binding": "TheAngrySkills",
                "binding_model": "project-root-with-nested-repo",
                "codex_project_root": str(repo_root),
                "canonical_repo_root": str(project_root),
                "operational_cwd": str(operational_cwd),
            }))
            invalid_roots = subprocess.run(
                [
                    "node", str(VALIDATOR),
                    "--source-thread-id", "source-id",
                    "--target-thread-id", "target-id",
                    *common,
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(invalid_roots.returncode, 0)
            self.assertIn("project_binding_valid", invalid_roots.stderr)

            binding.write_text(json.dumps({
                "valid": True,
                "target_thread_id": "target-id",
                "project_binding": "TheAngrySkills",
                "binding_model": "project-root-with-nested-repo",
                "codex_project_root": str(project_root),
                "canonical_repo_root": str(repo_root),
                "operational_cwd": str(operational_cwd),
            }))

            acknowledgement.write_text(json.dumps({"acknowledged": True, "target_thread_id": "invented-id"}))
            self_attested = subprocess.run(
                [
                    "node", str(VALIDATOR),
                    "--source-thread-id", "source-id",
                    "--target-thread-id", "target-id",
                    *common,
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(self_attested.returncode, 0)
            self.assertIn("acknowledged", self_attested.stderr)


if __name__ == "__main__":
    unittest.main()
