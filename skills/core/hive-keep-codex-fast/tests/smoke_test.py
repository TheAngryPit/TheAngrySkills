#!/usr/bin/env python3
"""Smoke tests for keep-codex-fast using a fake Codex home."""

from __future__ import annotations

import argparse
import contextlib
import io
import importlib.util
import json
import os
import runpy
import sqlite3
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "keep_codex_fast.py"


def load_module(*, patch_runtime: bool = True):
    spec = importlib.util.spec_from_file_location("keep_codex_fast", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["keep_codex_fast"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    if patch_runtime:
        module.codex_processes_running = lambda _codex_home=None: []
        module.title_apply_active_state_probe = lambda _codex_home: module.ActiveStateProbe(True, [], "")
        module.top_node_processes = lambda details=False: module.report("top_node_processes skipped_in_smoke")
    return module


def make_fake_home(root: Path) -> dict[str, Path]:
    codex_home = root / ".codex"
    sessions = codex_home / "sessions" / "2026" / "01" / "01"
    sessions.mkdir(parents=True)
    rollout = sessions / "rollout-2026-01-01T00-00-00-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.jsonl"
    rollout.write_text('{"type":"test"}\n', encoding="utf-8")
    old_time = time.time() - 30 * 86400
    os.utime(rollout, (old_time, old_time))

    (codex_home / ".codex-global-state.json").write_text('{"pinned-thread-ids":[]}', encoding="utf-8")
    session_index_entries = [
        {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "thread_name": "Codex Metadata Repair",
            "updated_at": "2026-06-18T00:00:00Z",
        },
        {
            "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "thread_name": "Handyman Manual",
            "updated_at": "2026-06-18T00:00:00Z",
        },
    ]
    (codex_home / "session_index.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in session_index_entries),
        encoding="utf-8",
    )
    (codex_home / "config.toml").write_text(
        '[projects."C:\\\\DefinitelyMissingKeepCodexFast"]\ntrust_level = "trusted"\n',
        encoding="utf-8",
    )

    worktree = codex_home / "worktrees" / "oldtree"
    worktree.mkdir(parents=True)
    (worktree / "file.txt").write_text("x", encoding="utf-8")
    os.utime(worktree, (old_time, old_time))

    log_file = codex_home / "logs_2.sqlite"
    log_file.write_text("log", encoding="utf-8")

    state_db = codex_home / "state_5.sqlite"
    conn = sqlite3.connect(state_db)
    conn.execute(
        """
        create table threads (
            id text primary key,
            title text,
            first_user_message text,
            rollout_path text,
            cwd text,
            updated_at integer,
            archived_at integer,
            archived integer
        )
        """
    )
    long_preview = "Please repair Codex thread metadata bloat without touching manual names " + ("y" * 600)
    long_title = long_preview
    conn.execute(
        "insert into threads values (?,?,?,?,?,?,?,?)",
        (
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            long_title,
            long_preview,
            str(rollout),
            r"\\?\C:\DefinitelyMissingKeepCodexFast",
            int(old_time),
            None,
            0,
        ),
    )
    manual_title = "Handyman " + ("m" * 220)
    manual_preview = "Please keep this manual title untouched while compacting display metadata " + ("p" * 600)
    conn.execute(
        "insert into threads values (?,?,?,?,?,?,?,?)",
        (
            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            manual_title,
            manual_preview,
            None,
            str(root / "ManualProject"),
            int(old_time),
            None,
            0,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "codex_home": codex_home,
        "rollout": rollout,
        "worktree": worktree,
        "log_file": log_file,
        "state_db": state_db,
    }


def make_title_repair_home(root: Path) -> dict[str, Path]:
    codex_home = root / ".codex"
    codex_home.mkdir(parents=True)
    sessions = codex_home / "sessions" / "2026" / "06" / "20"
    sessions.mkdir(parents=True)
    transcript = sessions / "rollout-2026-06-20T00-00-00-title-repair.jsonl"
    transcript.write_text('{"type":"fixture","message":"title repair transcript"}\n', encoding="utf-8")
    session_index_entries = [
        {
            "id": "22222222-2222-4222-8222-222222222222",
            "thread_name": "Safe Existing Name",
            "title": "Ignored Title Fallback",
        },
        {
            "id": "33333333-3333-4333-8333-333333333333",
            "title": "Unsafe Fallback Name",
        },
        {
            "id": "44444444-4444-4444-8444-444444444444",
            "thread_name": "Archived Safe Name",
        },
        {
            "id": "55555555-5555-4555-8555-555555555555",
            "thread_name": "Subagent Safe Name",
        },
    ]
    (codex_home / "session_index.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in session_index_entries),
        encoding="utf-8",
    )
    (codex_home / "config.toml").write_text("", encoding="utf-8")
    (codex_home / ".codex-global-state.json").write_text('{"pinned-thread-ids":[]}', encoding="utf-8")

    state_db = codex_home / "state_5.sqlite"
    conn = sqlite3.connect(state_db)
    conn.execute(
        """
        create table threads (
            id text primary key,
            title text,
            first_user_message text,
            preview text,
            source text,
            updated_at integer,
            archived_at integer,
            archived integer
        )
        """
    )
    oversized_prompt = "Use this workspace to implement the title repair dry run classifier " + ("x" * 180)
    cases = [
        (
            "11111111-1111-4111-8111-111111111111",
            "Manual Project Name",
            "Please keep the manual title because it differs from the prompt",
            "manual preview",
            "user",
            500,
            None,
            0,
        ),
        (
            "22222222-2222-4222-8222-222222222222",
            oversized_prompt,
            oversized_prompt,
            "safe candidate preview",
            "user",
            400,
            None,
            0,
        ),
        (
            "33333333-3333-4333-8333-333333333333",
            oversized_prompt + " human",
            oversized_prompt + " human",
            "human candidate preview",
            "user",
            300,
            None,
            0,
        ),
        (
            "44444444-4444-4444-8444-444444444444",
            oversized_prompt + " archived",
            oversized_prompt + " archived",
            "archived candidate preview",
            "user",
            200,
            12345,
            0,
        ),
        (
            "55555555-5555-4555-8555-555555555555",
            oversized_prompt + " subagent",
            oversized_prompt + " subagent",
            "subagent preview",
            "subagent",
            100,
            None,
            0,
        ),
    ]
    conn.executemany("insert into threads values (?,?,?,?,?,?,?,?)", cases)
    conn.commit()
    conn.close()
    return {"codex_home": codex_home, "state_db": state_db, "transcript": transcript}


def snapshot_text_file(path: Path) -> tuple[str, int]:
    return path.read_text(encoding="utf-8"), path.stat().st_mtime_ns


def assert_text_file_unchanged(path: Path, snapshot: tuple[str, int]) -> None:
    before_text, before_mtime = snapshot
    assert path.read_text(encoding="utf-8") == before_text
    assert path.stat().st_mtime_ns == before_mtime


def snapshot_file_tree(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        str(item.relative_to(root)): (item.read_bytes(), item.stat().st_mtime_ns)
        for item in sorted(root.rglob("*"))
        if item.is_file()
    }


def snapshot_sqlite_dump(path: Path) -> list[str]:
    conn = sqlite3.connect(path)
    try:
        return list(conn.iterdump())
    finally:
        conn.close()


def title_repair_rows(state_db: Path) -> dict[str, dict[str, object]]:
    conn = sqlite3.connect(state_db)
    conn.row_factory = sqlite3.Row
    try:
        columns = [row[1] for row in conn.execute('pragma table_info("threads")').fetchall()]
        return {
            str(row["id"]): {column: row[column] for column in columns}
            for row in conn.execute("select * from threads order by id").fetchall()
        }
    finally:
        conn.close()


def assert_only_expected_thread_titles_changed(
    before: dict[str, dict[str, object]],
    after: dict[str, dict[str, object]],
    expected_title_changes: dict[str, str],
) -> None:
    assert set(after) == set(before)
    for thread_id, before_row in before.items():
        after_row = after[thread_id]
        assert set(after_row) == set(before_row)
        for column, before_value in before_row.items():
            if column == "title" and thread_id in expected_title_changes:
                assert after_row[column] == expected_title_changes[thread_id]
            else:
                assert after_row[column] == before_value, f"{thread_id}.{column} changed unexpectedly"


def assert_process_detection_uses_sqlite_holders() -> None:
    module = load_module(patch_runtime=False)
    original_system = module.platform.system
    original_check_output = module.subprocess.check_output
    with tempfile.TemporaryDirectory() as td:
        codex_home = Path(td) / ".codex"
        codex_home.mkdir()
        (codex_home / "state_5.sqlite").write_text("", encoding="utf-8")
        try:
            module.platform.system = lambda: "Darwin"

            def fake_check_output(command, **kwargs):
                assert command[0] == "lsof"
                return (
                    "COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME\n"
                    "codex 123 user 14u REG 1,18 1 1 state_5.sqlite\n"
                    "codex 123 user 15u REG 1,18 1 1 state_5.sqlite-wal\n"
                )

            module.subprocess.check_output = fake_check_output
            hits = module.codex_processes_running(codex_home)
        finally:
            module.platform.system = original_system
            module.subprocess.check_output = original_check_output
    assert hits == ["codex 123 user 14u REG 1,18 1 1 state_5.sqlite"]


def assert_wait_for_codex_exit_times_out() -> None:
    module = load_module(patch_runtime=False)
    module.codex_processes_running = lambda _codex_home=None: ["codex 123 state_5.sqlite"]
    start = time.time()
    hits = module.wait_for_codex_exit(Path("/tmp/missing-codex-home"), timeout_seconds=0)
    assert hits == ["codex 123 state_5.sqlite"]
    assert time.time() - start < 1


def assert_title_apply_probe_falls_back_when_lsof_missing() -> None:
    module = load_module(patch_runtime=False)
    original_system = module.platform.system
    original_check_output = module.subprocess.check_output
    with tempfile.TemporaryDirectory() as td:
        codex_home = Path(td) / ".codex"
        codex_home.mkdir()
        (codex_home / "state_5.sqlite").write_text("", encoding="utf-8")
        commands: list[str] = []
        try:
            module.platform.system = lambda: "Darwin"

            def fake_check_output(command, **kwargs):
                commands.append(command[0])
                if command[0] == "lsof":
                    raise FileNotFoundError("lsof")
                if command[0] == "ps":
                    return " 999 zsh zsh\n"
                raise AssertionError(command)

            module.subprocess.check_output = fake_check_output
            probe = module.title_apply_active_state_probe(codex_home)
        finally:
            module.platform.system = original_system
            module.subprocess.check_output = original_check_output
    assert probe.reliable is True
    assert probe.blocking_processes == []
    assert commands == ["lsof", "ps"]


def assert_title_apply_probe_lsof_missing_detects_ps_codex() -> None:
    module = load_module(patch_runtime=False)
    original_system = module.platform.system
    original_check_output = module.subprocess.check_output
    with tempfile.TemporaryDirectory() as td:
        codex_home = Path(td) / ".codex"
        codex_home.mkdir()
        (codex_home / "state_5.sqlite").write_text("", encoding="utf-8")
        try:
            module.platform.system = lambda: "Darwin"

            def fake_check_output(command, **kwargs):
                if command[0] == "lsof":
                    raise FileNotFoundError("lsof")
                if command[0] == "ps":
                    return " 123 codex codex\n"
                raise AssertionError(command)

            module.subprocess.check_output = fake_check_output
            probe = module.title_apply_active_state_probe(codex_home)
        finally:
            module.platform.system = original_system
            module.subprocess.check_output = original_check_output
    assert probe.reliable is True
    assert probe.blocking_processes == ["123 codex codex"]


def assert_title_apply_probe_lsof_missing_detects_node_app_server() -> None:
    module = load_module(patch_runtime=False)
    original_system = module.platform.system
    original_check_output = module.subprocess.check_output
    with tempfile.TemporaryDirectory() as td:
        codex_home = Path(td) / ".codex"
        codex_home.mkdir()
        (codex_home / "state_5.sqlite").write_text("", encoding="utf-8")
        try:
            module.platform.system = lambda: "Darwin"

            def fake_check_output(command, **kwargs):
                if command[0] == "lsof":
                    raise FileNotFoundError("lsof")
                if command[0] == "ps":
                    return (
                        " 123 node node "
                        "/Applications/Codex.app/Contents/Resources/app-server "
                        "--codex-home /tmp/codex-home\n"
                    )
                raise AssertionError(command)

            module.subprocess.check_output = fake_check_output
            probe = module.title_apply_active_state_probe(codex_home)
        finally:
            module.platform.system = original_system
            module.subprocess.check_output = original_check_output
    assert probe.reliable is True
    assert probe.blocking_processes == [
        "123 node node /Applications/Codex.app/Contents/Resources/app-server --codex-home /tmp/codex-home"
    ]


def assert_help_distinguishes_legacy_repair(module) -> None:
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            module.parse_args(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("--help must exit")

    text = " ".join(output.getvalue().lower().replace("-\n", "-").split())
    assert "--repair-thread-metadata-only" in text
    assert "legacy combined repair flag" in text
    assert "title-only repair is separate" in text
    assert "--repair-thread-titles-dry-run" in text
    assert "--repair-thread-titles-apply" in text


def assert_title_dry_run_mode(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-dry-run-backup"
        before_tree = snapshot_file_tree(paths["codex_home"])
        before_db = snapshot_sqlite_dump(paths["state_db"])
        args = module.parse_args(
            [
                "--repair-thread-titles-dry-run",
                "--codex-home",
                str(paths["codex_home"]),
                "--backup-root",
                str(backup),
            ]
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert module.run(args) == 0
        text = output.getvalue()

        assert snapshot_file_tree(paths["codex_home"]) == before_tree
        assert snapshot_sqlite_dump(paths["state_db"]) == before_db
        assert not backup.exists(), "title dry-run must not create backup artifacts"
        assert "thread_title_dry_run_scanned 5" in text
        assert "thread_title_dry_run_active_real 3" in text
        assert "thread_title_dry_run_archived_real 1" in text
        assert "thread_title_dry_run_manual_keep 1" in text
        assert "thread_title_dry_run_auto_repair_candidate 3" in text
        assert "thread_title_dry_run_safe_name_available 2" in text
        assert "thread_title_dry_run_needs_human 1" in text
        assert "thread_title_dry_run_excluded_subagent 1" in text
        assert "classification=manual_keep" in text
        assert "classification=safe_name_available" in text
        assert "classification=needs_human" in text
        assert "classification=excluded_subagent" in text
        assert "location=archived classification=safe_name_available" in text
        assert "would_repair_from_session_index_thread_name" in text
        assert "request_manual_title" in text
        assert "thread_title_dry_run_writes false" in text
        assert "11111111-1111-4111-8111-111111111111" not in text
        assert "22222222-2222-4222-8222-222222222222" not in text
        assert "Manual Project Name" not in text
        assert "Use this workspace" not in text
        assert "Safe Existing Name" not in text
        assert "Unsafe Fallback Name" not in text


def assert_title_dry_run_details_mode(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        before_tree = snapshot_file_tree(paths["codex_home"])
        before_db = snapshot_sqlite_dump(paths["state_db"])
        args = module.parse_args(
            [
                "--repair-thread-titles-dry-run",
                "--details",
                "--codex-home",
                str(paths["codex_home"]),
            ]
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert module.run(args) == 0
        text = output.getvalue()

        assert snapshot_file_tree(paths["codex_home"]) == before_tree
        assert snapshot_sqlite_dump(paths["state_db"]) == before_db
        assert "22222222-2222-4222-8222-222222222222" in text
        assert "Safe Existing Name" in text
        assert "Use this workspace" in text
        assert "Unsafe Fallback Name" not in text


def assert_title_dry_run_title_limit_without_preview_limit(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        args = module.parse_args(
            [
                "--repair-thread-titles-dry-run",
                "--thread-title-limit",
                "300",
                "--codex-home",
                str(paths["codex_home"]),
            ]
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert module.run(args) == 0
        text = output.getvalue()

        assert "thread_title_dry_run_scanned 5" in text
        assert "thread_title_dry_run_writes false" in text


def assert_title_dry_run_wal_target_files_unchanged(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        writer = sqlite3.connect(paths["state_db"])
        try:
            assert writer.execute("pragma journal_mode=wal").fetchone()[0].lower() == "wal"
            writer.execute("pragma wal_autocheckpoint=0")
            writer.execute(
                "update threads set preview=? where id=?",
                ("wal-mode preview remains outside title dry-run scope", "11111111-1111-4111-8111-111111111111"),
            )
            writer.commit()
            assert Path(str(paths["state_db"]) + "-wal").exists()
            assert Path(str(paths["state_db"]) + "-shm").exists()

            before_tree = snapshot_file_tree(Path(td))
            args = module.parse_args(
                [
                    "--repair-thread-titles-dry-run",
                    "--codex-home",
                    str(paths["codex_home"]),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 3
            text = output.getvalue()

            assert snapshot_file_tree(Path(td)) == before_tree
            assert "thread_title_dry_run_blocked non_empty_wal_requires_checkpoint" in text
            assert "thread_title_dry_run_writes false" in text
            assert "thread_title_dry_run_scanned" not in text
            assert "thread_title_dry_run_item" not in text
            assert "classification=" not in text
        finally:
            writer.close()


def assert_title_apply_requires_confirmation(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-backup"
        before_tree = snapshot_file_tree(paths["codex_home"])
        before_db = snapshot_sqlite_dump(paths["state_db"])
        args = module.parse_args(
            [
                "--repair-thread-titles-apply",
                "--codex-home",
                str(paths["codex_home"]),
                "--backup-root",
                str(backup),
            ]
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert module.run(args) == 2
        text = output.getvalue()

        assert snapshot_file_tree(paths["codex_home"]) == before_tree
        assert snapshot_sqlite_dump(paths["state_db"]) == before_db
        assert not backup.exists(), "unconfirmed title apply must not create backup artifacts"
        assert "thread_title_apply_refused confirmation_required" in text
        assert "thread_title_apply_confirmation_phrase APPLY_THREAD_TITLE_REPAIR" in text


def assert_title_apply_blocks_when_codex_running(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-running-backup"
        before_tree = snapshot_file_tree(paths["codex_home"])
        before_db = snapshot_sqlite_dump(paths["state_db"])
        original_probe = module.title_apply_active_state_probe
        module.title_apply_active_state_probe = lambda _codex_home: module.ActiveStateProbe(
            True,
            ["codex 123 state_5.sqlite"],
            "",
        )
        try:
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 3
        finally:
            module.title_apply_active_state_probe = original_probe
        text = output.getvalue()

        assert snapshot_file_tree(paths["codex_home"]) == before_tree
        assert snapshot_sqlite_dump(paths["state_db"]) == before_db
        assert not backup.exists(), "blocked title apply must not create backup artifacts"
        assert "thread_title_apply_skipped_codex_running" in text
        assert "blocking_process codex_process_001" in text
        assert "codex 123 state_5.sqlite" not in text


def assert_title_apply_blocks_when_process_probe_unreliable(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-unreliable-probe-backup"
        before_tree = snapshot_file_tree(paths["codex_home"])
        before_db = snapshot_sqlite_dump(paths["state_db"])
        original_probe = module.title_apply_active_state_probe
        module.title_apply_active_state_probe = lambda _codex_home: module.ActiveStateProbe(
            False,
            [],
            "process_probe_unreliable",
        )
        try:
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 3
        finally:
            module.title_apply_active_state_probe = original_probe
        text = output.getvalue()

        assert snapshot_file_tree(paths["codex_home"]) == before_tree
        assert snapshot_sqlite_dump(paths["state_db"]) == before_db
        assert not backup.exists(), "unreliable process probe must block before backup artifacts"
        assert "thread_title_apply_blocked process_probe_unreliable" in text
        assert "thread_title_apply_scanned" not in text
        assert "thread_title_apply_item" not in text


def assert_title_apply_rechecks_active_state_after_backup(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-post-backup-running"
        before_rows = title_repair_rows(paths["state_db"])
        original_probe = module.title_apply_active_state_probe
        probe_calls = []

        def staged_probe(_codex_home):
            probe_calls.append("probe")
            if len(probe_calls) == 1:
                return module.ActiveStateProbe(True, [], "")
            return module.ActiveStateProbe(True, ["codex 123 state_5.sqlite"], "")

        module.title_apply_active_state_probe = staged_probe
        try:
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 3
        finally:
            module.title_apply_active_state_probe = original_probe
        text = output.getvalue()
        after_rows = title_repair_rows(paths["state_db"])

        assert len(probe_calls) == 2
        assert_only_expected_thread_titles_changed(before_rows, after_rows, {})
        assert (backup / "state_5.sqlite").exists()
        assert not (backup / "thread-title-repairs.jsonl").exists()
        assert not (backup / "restore-thread-titles.py").exists()
        assert "thread_title_apply_skipped_post_backup_codex_running" in text
        assert "thread_title_apply_scanned" not in text
        assert "thread_title_apply_item" not in text


def assert_title_apply_lsof_missing_ps_safe_allows_apply() -> None:
    module = load_module(patch_runtime=False)
    original_system = module.platform.system
    original_check_output = module.subprocess.check_output
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-lsof-missing-backup"
        before_rows = title_repair_rows(paths["state_db"])
        try:
            module.platform.system = lambda: "Darwin"

            def fake_check_output(command, **kwargs):
                if command[0] == "lsof":
                    raise FileNotFoundError("lsof")
                if command[0] == "ps":
                    return " 999 zsh zsh\n"
                raise AssertionError(command)

            module.subprocess.check_output = fake_check_output
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 0
        finally:
            module.platform.system = original_system
            module.subprocess.check_output = original_check_output
        text = output.getvalue()
        after_rows = title_repair_rows(paths["state_db"])

        assert_only_expected_thread_titles_changed(
            before_rows,
            after_rows,
            {
                "22222222-2222-4222-8222-222222222222": "Safe Existing Name",
                "44444444-4444-4444-8444-444444444444": "Archived Safe Name",
            },
        )
        assert (backup / "state_5.sqlite").exists()
        assert (backup / "thread-title-repairs.jsonl").exists()
        assert "thread_title_apply_blocked process_probe_unreliable" not in text
        assert "thread_title_apply_applied 2" in text


def assert_title_apply_wal_target_files_unchanged(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-wal-backup"
        writer = sqlite3.connect(paths["state_db"])
        try:
            assert writer.execute("pragma journal_mode=wal").fetchone()[0].lower() == "wal"
            writer.execute("pragma wal_autocheckpoint=0")
            writer.execute(
                "update threads set preview=? where id=?",
                ("wal-mode preview remains outside title apply scope", "11111111-1111-4111-8111-111111111111"),
            )
            writer.commit()
            assert Path(str(paths["state_db"]) + "-wal").exists()
            assert Path(str(paths["state_db"]) + "-shm").exists()

            before_tree = snapshot_file_tree(Path(td))
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 3
            text = output.getvalue()

            assert snapshot_file_tree(Path(td)) == before_tree
            assert not backup.exists(), "WAL-blocked title apply must not create backup artifacts"
            assert "thread_title_apply_blocked non_empty_wal_requires_checkpoint" in text
            assert "thread_title_apply_scanned" not in text
            assert "thread_title_apply_item" not in text
        finally:
            writer.close()


def assert_title_apply_mode(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-backup"
        session_index = paths["codex_home"] / "session_index.jsonl"
        session_index_snapshot = snapshot_text_file(session_index)
        transcript_snapshot = snapshot_text_file(paths["transcript"])
        before_rows = title_repair_rows(paths["state_db"])
        backup_observed_pre_mutation = []
        original_backup_metadata = module.backup_metadata

        def audited_backup_metadata(codex_home: Path, backup_root: Path) -> None:
            backup_observed_pre_mutation.append(title_repair_rows(paths["state_db"]))
            original_backup_metadata(codex_home, backup_root)

        module.backup_metadata = audited_backup_metadata
        try:
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 0
        finally:
            module.backup_metadata = original_backup_metadata
        text = output.getvalue()
        after_rows = title_repair_rows(paths["state_db"])

        assert backup_observed_pre_mutation == [before_rows], "backup must run before title mutation"
        assert_only_expected_thread_titles_changed(
            before_rows,
            after_rows,
            {
                "22222222-2222-4222-8222-222222222222": "Safe Existing Name",
                "44444444-4444-4444-8444-444444444444": "Archived Safe Name",
            },
        )
        assert_text_file_unchanged(session_index, session_index_snapshot)
        assert_text_file_unchanged(paths["transcript"], transcript_snapshot)
        assert (backup / "state_5.sqlite").exists()
        assert (backup / "session_index.jsonl").exists()
        assert (backup / "thread-title-repairs.jsonl").exists()
        assert (backup / "restore-thread-titles.py").exists()
        assert not (backup / "thread-metadata-repairs.jsonl").exists()
        assert not (backup / "restore-thread-metadata.py").exists()
        manifest = [
            json.loads(line)
            for line in (backup / "thread-title-repairs.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert {item["thread_id"] for item in manifest} == {
            "22222222-2222-4222-8222-222222222222",
            "44444444-4444-4444-8444-444444444444",
        }
        for item in manifest:
            assert set(item) == {
                "thread_id",
                "original_title",
                "original_first_user_message",
                "chosen_replacement",
                "safe_source",
                "location",
                "initial_verification_status",
                "verification_status",
                "safe_source_verification_status",
                "apply_rowcount",
                "restore_status",
            }
            assert item["original_first_user_message"] == before_rows[item["thread_id"]]["first_user_message"]
            assert item["safe_source"] == "session_index.thread_name"
            assert item["initial_verification_status"] == "pending"
            assert item["verification_status"] == "verified"
            assert item["safe_source_verification_status"] == "verified"
            assert item["apply_rowcount"] == 1
            assert item["restore_status"] == "not_needed"
        restore_text = (backup / "restore-thread-titles.py").read_text(encoding="utf-8")
        assert "update threads set title=?" in restore_text
        assert "first_user_message" not in restore_text
        assert "thread_title_apply_scanned 5" in text
        assert "thread_title_apply_eligible 2" in text
        assert "thread_title_apply_needs_human 1" in text
        assert "thread_title_apply_excluded_subagent 1" in text
        assert "thread_title_apply_applied 2" in text
        assert "thread_title_apply_verification_mismatches 0" in text
        assert "thread_title_apply_restore_required 0" in text
        assert "thread_title_apply_restore_attempted 0" in text
        assert "thread_title_apply_restore_succeeded 0" in text
        assert "Safe Existing Name" not in text
        assert "Use this workspace" not in text
        assert "22222222-2222-4222-8222-222222222222" not in text


def assert_title_apply_no_eligible_repairs_reports_zero_restore(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-no-eligible-backup"
        session_index = paths["codex_home"] / "session_index.jsonl"
        session_index.write_text("", encoding="utf-8")
        session_index_snapshot = snapshot_text_file(session_index)
        before_rows = title_repair_rows(paths["state_db"])
        args = module.parse_args(
            [
                "--repair-thread-titles-apply",
                "--confirm-thread-title-repair",
                "APPLY_THREAD_TITLE_REPAIR",
                "--codex-home",
                str(paths["codex_home"]),
                "--backup-root",
                str(backup),
            ]
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert module.run(args) == 0
        text = output.getvalue()

        assert title_repair_rows(paths["state_db"]) == before_rows
        assert_text_file_unchanged(session_index, session_index_snapshot)
        assert (backup / "state_5.sqlite").exists()
        assert (backup / "session_index.jsonl").exists()
        assert not (backup / "thread-title-repairs.jsonl").exists()
        assert not (backup / "restore-thread-titles.py").exists()
        assert "thread_title_apply_scanned 5" in text
        assert "thread_title_apply_manual_keep 1" in text
        assert "thread_title_apply_eligible 0" in text
        assert "thread_title_apply_needs_human 3" in text
        assert "thread_title_apply_excluded_subagent 1" in text
        assert "thread_title_apply_applied 0" in text
        assert "thread_title_apply_verification_mismatches 0" in text
        assert "thread_title_apply_restore_required 0" in text
        assert "thread_title_apply_restore_attempted 0" in text
        assert "thread_title_apply_restore_succeeded 0" in text
        assert "Safe Existing Name" not in text
        assert "Use this workspace" not in text


def assert_title_apply_manifest_records_rowcounts_before_commit(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-manifest-before-commit"
        before_rows = title_repair_rows(paths["state_db"])
        observed_precommit_rowcounts: list[dict[str, object]] = []
        original_writer = module.write_thread_title_manifest

        def audited_manifest_writer(manifest: Path, records: list[dict[str, object]]) -> None:
            rowcounts = {str(record["thread_id"]): record.get("apply_rowcount") for record in records}
            if any(count == 1 for count in rowcounts.values()):
                current_rows = title_repair_rows(paths["state_db"])
                if current_rows == before_rows:
                    observed_precommit_rowcounts.append(dict(rowcounts))
            original_writer(manifest, records)

        module.write_thread_title_manifest = audited_manifest_writer
        try:
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 0
        finally:
            module.write_thread_title_manifest = original_writer

        assert observed_precommit_rowcounts == [
            {
                "22222222-2222-4222-8222-222222222222": 1,
                "44444444-4444-4444-8444-444444444444": 1,
            }
        ]
        manifest = [
            json.loads(line)
            for line in (backup / "thread-title-repairs.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert all(item["apply_rowcount"] == 1 for item in manifest)
        assert "thread_title_apply_applied 2" in output.getvalue()


def assert_title_apply_does_not_optimize_state_db(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-no-optimize"
        executed_sql: list[str] = []
        original_sqlite_connect = module.sqlite_connect

        class RecordingConnection:
            def __init__(self, conn):
                object.__setattr__(self, "_conn", conn)

            def execute(self, sql, *args, **kwargs):
                executed_sql.append(str(sql).strip().lower())
                return self._conn.execute(sql, *args, **kwargs)

            def __getattr__(self, name):
                return getattr(self._conn, name)

            def __setattr__(self, name, value):
                if name == "_conn":
                    object.__setattr__(self, name, value)
                else:
                    setattr(self._conn, name, value)

        def audited_sqlite_connect(path: Path, *, readonly: bool):
            conn = original_sqlite_connect(path, readonly=readonly)
            if Path(path).resolve() == paths["state_db"].resolve() and not readonly:
                return RecordingConnection(conn)
            return conn

        module.sqlite_connect = audited_sqlite_connect
        try:
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 0
        finally:
            module.sqlite_connect = original_sqlite_connect

        assert executed_sql, "title apply writable connection was not observed"
        assert "pragma wal_checkpoint(truncate)" in executed_sql, executed_sql
        assert "pragma optimize" not in executed_sql, executed_sql
        conn = sqlite3.connect(paths["state_db"])
        try:
            stat_tables = [
                row[0]
                for row in conn.execute(
                    "select name from sqlite_schema where name like 'sqlite_stat%' order by name"
                ).fetchall()
            ]
        finally:
            conn.close()
        assert stat_tables == []
        assert "sqlite_optimize_skipped" not in output.getvalue()


def assert_title_apply_restores_failed_verification(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-restore-backup"
        conn = sqlite3.connect(paths["state_db"])
        conn.execute(
            """
            create trigger title_apply_corrupt_after_write
            after update of title on threads
            when new.id = '22222222-2222-4222-8222-222222222222'
             and new.title = 'Safe Existing Name'
            begin
                update threads
                set title = 'Concurrent Rewrite'
                where id = new.id;
            end
            """
        )
        conn.commit()
        conn.close()

        session_index = paths["codex_home"] / "session_index.jsonl"
        session_index_snapshot = snapshot_text_file(session_index)
        transcript_snapshot = snapshot_text_file(paths["transcript"])
        before_rows = title_repair_rows(paths["state_db"])
        args = module.parse_args(
            [
                "--repair-thread-titles-apply",
                "--confirm-thread-title-repair",
                "APPLY_THREAD_TITLE_REPAIR",
                "--codex-home",
                str(paths["codex_home"]),
                "--backup-root",
                str(backup),
            ]
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert module.run(args) == 4
        text = output.getvalue()
        after_rows = title_repair_rows(paths["state_db"])

        assert_only_expected_thread_titles_changed(
            before_rows,
            after_rows,
            {
                "22222222-2222-4222-8222-222222222222": "Concurrent Rewrite",
                "44444444-4444-4444-8444-444444444444": "Archived Safe Name",
            },
        )
        assert_text_file_unchanged(session_index, session_index_snapshot)
        assert_text_file_unchanged(paths["transcript"], transcript_snapshot)
        manifest = [
            json.loads(line)
            for line in (backup / "thread-title-repairs.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        by_thread = {item["thread_id"]: item for item in manifest}
        assert by_thread["22222222-2222-4222-8222-222222222222"]["verification_status"] == (
            "mismatch_before_restore"
        )
        assert by_thread["22222222-2222-4222-8222-222222222222"]["original_first_user_message"] == before_rows[
            "22222222-2222-4222-8222-222222222222"
        ]["first_user_message"]
        assert by_thread["22222222-2222-4222-8222-222222222222"]["safe_source_verification_status"] == "verified"
        assert by_thread["22222222-2222-4222-8222-222222222222"]["apply_rowcount"] == 1
        assert by_thread["22222222-2222-4222-8222-222222222222"]["restore_status"] == (
            "restore_skipped_current_title_changed"
        )
        assert by_thread["44444444-4444-4444-8444-444444444444"]["verification_status"] == "verified"
        assert by_thread["44444444-4444-4444-8444-444444444444"]["safe_source_verification_status"] == "verified"
        assert by_thread["44444444-4444-4444-8444-444444444444"]["restore_status"] == "not_needed"
        assert "thread_title_apply_verification_mismatches 1" in text
        assert "thread_title_apply_restore_required 1" in text
        assert "thread_title_apply_restore_attempted 1" in text
        assert "thread_title_apply_restore_succeeded 0" in text
        assert "Concurrent Rewrite" not in text
        assert "Safe Existing Name" not in text


def assert_title_apply_restores_session_index_drift(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-source-drift-backup"
        session_index = paths["codex_home"] / "session_index.jsonl"
        transcript_snapshot = snapshot_text_file(paths["transcript"])
        before_rows = title_repair_rows(paths["state_db"])
        original_restore_writer = module.write_thread_title_restore_script

        def drift_session_index_after_restore_script(manifest: Path, state_db: Path, backup_root: Path) -> None:
            original_restore_writer(manifest, state_db, backup_root)
            session_index.write_text("", encoding="utf-8")

        module.write_thread_title_restore_script = drift_session_index_after_restore_script
        try:
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 4
        finally:
            module.write_thread_title_restore_script = original_restore_writer
        text = output.getvalue()
        after_rows = title_repair_rows(paths["state_db"])

        assert_only_expected_thread_titles_changed(before_rows, after_rows, {})
        assert session_index.read_text(encoding="utf-8") == ""
        assert_text_file_unchanged(paths["transcript"], transcript_snapshot)
        manifest = [
            json.loads(line)
            for line in (backup / "thread-title-repairs.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert {item["thread_id"] for item in manifest} == {
            "22222222-2222-4222-8222-222222222222",
            "44444444-4444-4444-8444-444444444444",
        }
        for item in manifest:
            assert item["original_first_user_message"] == before_rows[item["thread_id"]]["first_user_message"]
            assert item["verification_status"] == "safe_source_mismatch_before_restore_restored"
            assert item["safe_source_verification_status"] == "mismatch"
            assert item["apply_rowcount"] == 1
            assert item["restore_status"] == "restored_original_title"
        assert "thread_title_apply_verification_mismatches 2" in text
        assert "thread_title_apply_restore_required 2" in text
        assert "thread_title_apply_restore_attempted 2" in text
        assert "thread_title_apply_restore_succeeded 2" in text
        assert "Safe Existing Name" not in text
        assert "Archived Safe Name" not in text


def assert_title_apply_does_not_restore_unowned_rowcount_zero(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-unowned-restore-backup"
        session_index = paths["codex_home"] / "session_index.jsonl"
        session_index_snapshot = snapshot_text_file(session_index)
        transcript_snapshot = snapshot_text_file(paths["transcript"])
        before_rows = title_repair_rows(paths["state_db"])
        original_classifier = module.title_dry_run_classifications

        def drift_after_classification(conn, codex_home: Path, *, title_limit: int):
            classifications = original_classifier(conn, codex_home, title_limit=title_limit)
            conn.execute(
                "update threads set title=? where id=?",
                ("Concurrent Manual Title", "22222222-2222-4222-8222-222222222222"),
            )
            conn.commit()
            return classifications

        module.title_dry_run_classifications = drift_after_classification
        try:
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 4
        finally:
            module.title_dry_run_classifications = original_classifier
        text = output.getvalue()
        after_rows = title_repair_rows(paths["state_db"])

        assert_only_expected_thread_titles_changed(
            before_rows,
            after_rows,
            {
                "22222222-2222-4222-8222-222222222222": "Concurrent Manual Title",
                "44444444-4444-4444-8444-444444444444": "Archived Safe Name",
            },
        )
        assert_text_file_unchanged(session_index, session_index_snapshot)
        assert_text_file_unchanged(paths["transcript"], transcript_snapshot)
        manifest = [
            json.loads(line)
            for line in (backup / "thread-title-repairs.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        by_thread = {item["thread_id"]: item for item in manifest}
        assert by_thread["22222222-2222-4222-8222-222222222222"]["verification_status"] == (
            "mismatch_before_restore"
        )
        assert by_thread["22222222-2222-4222-8222-222222222222"]["apply_rowcount"] == 0
        assert by_thread["22222222-2222-4222-8222-222222222222"]["restore_status"] == (
            "restore_skipped_not_owned"
        )
        assert by_thread["44444444-4444-4444-8444-444444444444"]["verification_status"] == "verified"
        assert by_thread["44444444-4444-4444-8444-444444444444"]["apply_rowcount"] == 1
        assert by_thread["44444444-4444-4444-8444-444444444444"]["restore_status"] == "not_needed"
        assert "thread_title_apply_applied 1" in text
        assert "thread_title_apply_verification_mismatches 1" in text
        assert "thread_title_apply_restore_required 1" in text
        assert "thread_title_apply_restore_attempted 1" in text
        assert "thread_title_apply_restore_succeeded 0" in text
        assert "Concurrent Manual Title" not in text

        conn = sqlite3.connect(paths["state_db"])
        conn.execute(
            "update threads set title=? where id=?",
            ("Archived Safe Name", "44444444-4444-4444-8444-444444444444"),
        )
        conn.commit()
        conn.close()
        restore_output = io.StringIO()
        with contextlib.redirect_stdout(restore_output):
            runpy.run_path(str(backup / "restore-thread-titles.py"), run_name="__main__")
        restored_rows = title_repair_rows(paths["state_db"])
        assert restored_rows["22222222-2222-4222-8222-222222222222"]["title"] == "Concurrent Manual Title"
        assert restored_rows["44444444-4444-4444-8444-444444444444"]["title"] == before_rows[
            "44444444-4444-4444-8444-444444444444"
        ]["title"]
        restore_text = restore_output.getvalue()
        assert "restore_skipped_not_owned 22222222-2222-4222-8222-222222222222" in restore_text
        assert "restore_attempted 1" in restore_text
        assert "restore_restored 1" in restore_text
        assert "restore_skipped 1" in restore_text


def assert_title_apply_does_not_restore_unowned_same_replacement_source_drift(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-unowned-same-replacement-backup"
        session_index = paths["codex_home"] / "session_index.jsonl"
        transcript_snapshot = snapshot_text_file(paths["transcript"])
        before_rows = title_repair_rows(paths["state_db"])
        original_classifier = module.title_dry_run_classifications

        def drift_after_classification(conn, codex_home: Path, *, title_limit: int):
            classifications = original_classifier(conn, codex_home, title_limit=title_limit)
            conn.execute(
                "update threads set title=? where id=?",
                ("Safe Existing Name", "22222222-2222-4222-8222-222222222222"),
            )
            conn.commit()
            session_index.write_text("", encoding="utf-8")
            return classifications

        module.title_dry_run_classifications = drift_after_classification
        try:
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 4
        finally:
            module.title_dry_run_classifications = original_classifier
        text = output.getvalue()
        after_rows = title_repair_rows(paths["state_db"])

        assert_only_expected_thread_titles_changed(
            before_rows,
            after_rows,
            {
                "22222222-2222-4222-8222-222222222222": "Safe Existing Name",
            },
        )
        assert session_index.read_text(encoding="utf-8") == ""
        assert_text_file_unchanged(paths["transcript"], transcript_snapshot)
        manifest = [
            json.loads(line)
            for line in (backup / "thread-title-repairs.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        by_thread = {item["thread_id"]: item for item in manifest}
        assert by_thread["22222222-2222-4222-8222-222222222222"]["verification_status"] == (
            "safe_source_mismatch_before_restore"
        )
        assert by_thread["22222222-2222-4222-8222-222222222222"]["apply_rowcount"] == 0
        assert by_thread["22222222-2222-4222-8222-222222222222"]["safe_source_verification_status"] == "mismatch"
        assert by_thread["22222222-2222-4222-8222-222222222222"]["restore_status"] == (
            "restore_skipped_not_owned"
        )
        assert by_thread["44444444-4444-4444-8444-444444444444"]["verification_status"] == (
            "safe_source_mismatch_before_restore_restored"
        )
        assert by_thread["44444444-4444-4444-8444-444444444444"]["apply_rowcount"] == 1
        assert by_thread["44444444-4444-4444-8444-444444444444"]["restore_status"] == (
            "restored_original_title"
        )
        assert "thread_title_apply_applied 1" in text
        assert "thread_title_apply_verification_mismatches 2" in text
        assert "thread_title_apply_restore_required 2" in text
        assert "thread_title_apply_restore_attempted 2" in text
        assert "thread_title_apply_restore_succeeded 1" in text
        assert "Safe Existing Name" not in text


def assert_title_apply_requires_ownership_for_verified_same_replacement(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_title_repair_home(Path(td))
        backup = Path(td) / "title-apply-unowned-same-replacement-verified-source"
        session_index = paths["codex_home"] / "session_index.jsonl"
        session_index_snapshot = snapshot_text_file(session_index)
        transcript_snapshot = snapshot_text_file(paths["transcript"])
        before_rows = title_repair_rows(paths["state_db"])
        original_classifier = module.title_dry_run_classifications

        def drift_after_classification(conn, codex_home: Path, *, title_limit: int):
            classifications = original_classifier(conn, codex_home, title_limit=title_limit)
            conn.execute(
                "update threads set title=? where id=?",
                ("Safe Existing Name", "22222222-2222-4222-8222-222222222222"),
            )
            conn.commit()
            return classifications

        module.title_dry_run_classifications = drift_after_classification
        try:
            args = module.parse_args(
                [
                    "--repair-thread-titles-apply",
                    "--confirm-thread-title-repair",
                    "APPLY_THREAD_TITLE_REPAIR",
                    "--codex-home",
                    str(paths["codex_home"]),
                    "--backup-root",
                    str(backup),
                ]
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert module.run(args) == 4
        finally:
            module.title_dry_run_classifications = original_classifier
        text = output.getvalue()
        after_rows = title_repair_rows(paths["state_db"])

        assert_only_expected_thread_titles_changed(
            before_rows,
            after_rows,
            {
                "22222222-2222-4222-8222-222222222222": "Safe Existing Name",
                "44444444-4444-4444-8444-444444444444": "Archived Safe Name",
            },
        )
        assert_text_file_unchanged(session_index, session_index_snapshot)
        assert_text_file_unchanged(paths["transcript"], transcript_snapshot)
        manifest = [
            json.loads(line)
            for line in (backup / "thread-title-repairs.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        by_thread = {item["thread_id"]: item for item in manifest}
        assert by_thread["22222222-2222-4222-8222-222222222222"]["verification_status"] == (
            "mismatch_before_restore"
        )
        assert by_thread["22222222-2222-4222-8222-222222222222"]["apply_rowcount"] == 0
        assert by_thread["22222222-2222-4222-8222-222222222222"]["safe_source_verification_status"] == "verified"
        assert by_thread["22222222-2222-4222-8222-222222222222"]["restore_status"] == (
            "restore_skipped_not_owned"
        )
        assert by_thread["44444444-4444-4444-8444-444444444444"]["verification_status"] == "verified"
        assert by_thread["44444444-4444-4444-8444-444444444444"]["apply_rowcount"] == 1
        assert by_thread["44444444-4444-4444-8444-444444444444"]["restore_status"] == "not_needed"
        assert "thread_title_apply_applied 1" in text
        assert "thread_title_apply_verification_mismatches 1" in text
        assert "thread_title_apply_restore_required 1" in text
        assert "thread_title_apply_restore_attempted 1" in text
        assert "thread_title_apply_restore_succeeded 0" in text
        assert "Safe Existing Name" not in text


def assert_report_mode(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_fake_home(Path(td))
        backup = Path(td) / "backup-report"
        args = argparse.Namespace(
            apply=False,
            backup_only=False,
            details=False,
            wait_for_codex_exit=False,
            codex_home=str(paths["codex_home"]),
            backup_root=str(backup),
            archive_older_than_days=10,
            worktree_older_than_days=7,
            rotate_logs_above_mb=0,
            thread_title_limit=120,
            thread_preview_limit=240,
            repair_thread_metadata_bloat=False,
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert module.run(args) == 0
        text = output.getvalue()
        assert paths["rollout"].exists(), "report mode must not move sessions"
        assert paths["worktree"].exists(), "report mode must not move worktrees"
        assert paths["log_file"].exists(), "report mode must not rotate logs"
        assert not backup.exists(), "report mode must not create backup artifacts"
        assert "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" not in text
        assert str(paths["codex_home"]) not in text
        conn = sqlite3.connect(paths["state_db"])
        title, preview = conn.execute(
            "select title, first_user_message from threads where id=?",
            ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",),
        ).fetchone()
        conn.close()
        assert len(title) > 120, "report mode must not trim titles"
        assert len(preview) > 240, "report mode must not trim previews"


def assert_backup_only_mode(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_fake_home(Path(td))
        backup = Path(td) / "backup-only"
        args = argparse.Namespace(
            apply=False,
            backup_only=True,
            details=False,
            wait_for_codex_exit=False,
            codex_home=str(paths["codex_home"]),
            backup_root=str(backup),
            archive_older_than_days=10,
            worktree_older_than_days=7,
            rotate_logs_above_mb=0,
            thread_title_limit=120,
            thread_preview_limit=240,
            repair_thread_metadata_bloat=False,
        )
        assert module.run(args) == 0
        assert paths["rollout"].exists(), "backup-only mode must not move sessions"
        assert paths["worktree"].exists(), "backup-only mode must not move worktrees"
        assert paths["log_file"].exists(), "backup-only mode must not rotate logs"
        assert (backup / "state_5.sqlite").exists()
        assert (backup / "config.toml").exists()
        assert not (backup / "moved-sessions.jsonl").exists()
        conn = sqlite3.connect(paths["state_db"])
        title, preview = conn.execute(
            "select title, first_user_message from threads where id=?",
            ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",),
        ).fetchone()
        conn.close()
        assert len(title) > 120, "backup-only mode must not trim titles"
        assert len(preview) > 240, "backup-only mode must not trim previews"


def assert_session_alias_detection(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        real_root = root / "real"
        alias_root = root / "alias"
        real_root.mkdir()
        try:
            alias_root.symlink_to(real_root, target_is_directory=True)
        except OSError:
            return

        paths = make_fake_home(real_root)
        alias_home = alias_root / ".codex"
        conn = module.sqlite_connect(alias_home / "state_5.sqlite", readonly=True)
        try:
            candidates = module.active_session_candidates(conn, alias_home, 10)
        finally:
            conn.close()
        assert len(candidates) == 1


def assert_apply_mode(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_fake_home(Path(td))
        rollout = paths["rollout"]
        rollout_snapshot = snapshot_text_file(rollout)
        session_index = paths["codex_home"] / "session_index.jsonl"
        session_index_snapshot = snapshot_text_file(session_index)
        backup = Path(td) / "backup-apply"
        args = argparse.Namespace(
            apply=True,
            backup_only=False,
            details=False,
            wait_for_codex_exit=False,
            codex_home=str(paths["codex_home"]),
            backup_root=str(backup),
            archive_older_than_days=10,
            worktree_older_than_days=7,
            rotate_logs_above_mb=0,
            thread_title_limit=120,
            thread_preview_limit=240,
            repair_thread_metadata_bloat=True,
        )
        assert module.run(args) == 0

        conn = sqlite3.connect(paths["state_db"])
        archived, archived_at, rollout_path, cwd, title, preview = conn.execute(
            "select archived, archived_at, rollout_path, cwd, title, first_user_message from threads where id=?",
            ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",),
        ).fetchone()
        conn.close()

        assert archived == 1
        assert archived_at is not None
        assert "archived_sessions" in rollout_path
        assert cwd == r"C:\DefinitelyMissingKeepCodexFast"
        assert len(title) <= 120
        assert title == "Codex Metadata Repair"
        assert len(preview) <= 240
        conn = sqlite3.connect(paths["state_db"])
        manual_title, manual_preview = conn.execute(
            "select title, first_user_message from threads where id=?",
            ("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",),
        ).fetchone()
        conn.close()
        assert manual_title.startswith("Handyman "), "manual titles must be preserved"
        assert len(manual_title) > 120, "manual title may remain long if operator-owned"
        assert len(manual_preview) <= 240, "preview metadata can be compacted independently"
        assert not paths["rollout"].exists()
        assert not paths["worktree"].exists()
        assert not paths["log_file"].exists()
        assert "DefinitelyMissingKeepCodexFast" not in (paths["codex_home"] / "config.toml").read_text(
            encoding="utf-8"
        )
        assert (backup / "restore-sessions.py").exists()
        assert (backup / "restore-thread-metadata.py").exists()
        assert (backup / "moved-sessions.jsonl").exists()
        assert (backup / "thread-metadata-repairs.jsonl").exists()
        assert (backup / "moved-worktrees.jsonl").exists()
        moved_sessions = [
            json.loads(line)
            for line in (backup / "moved-sessions.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        archived_rollout = next(item for item in moved_sessions if item["from"] == str(rollout))
        assert_text_file_unchanged(Path(archived_rollout["to"]), rollout_snapshot)
        assert_text_file_unchanged(session_index, session_index_snapshot)
        assert "Codex Metadata Repair" in session_index.read_text(encoding="utf-8")


def assert_normal_apply_does_not_repair_thread_metadata(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_fake_home(Path(td))
        session_index = paths["codex_home"] / "session_index.jsonl"
        session_index_snapshot = snapshot_text_file(session_index)
        backup = Path(td) / "backup-normal-apply"
        args = argparse.Namespace(
            apply=True,
            backup_only=False,
            details=False,
            wait_for_codex_exit=False,
            codex_home=str(paths["codex_home"]),
            backup_root=str(backup),
            archive_older_than_days=10,
            worktree_older_than_days=7,
            rotate_logs_above_mb=64,
            thread_title_limit=120,
            thread_preview_limit=240,
            repair_thread_metadata_bloat=False,
        )
        assert module.run(args) == 0

        conn = sqlite3.connect(paths["state_db"])
        title, preview = conn.execute(
            "select title, first_user_message from threads where id=?",
            ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",),
        ).fetchone()
        conn.close()

        assert len(title) > 120, "normal apply must not trim titles without explicit repair flag"
        assert len(preview) > 240, "normal apply must not trim previews without explicit repair flag"
        assert not (backup / "thread-metadata-repairs.jsonl").exists()
        assert not (backup / "restore-thread-metadata.py").exists()
        assert_text_file_unchanged(session_index, session_index_snapshot)


def assert_runbook_mode(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_fake_home(Path(td))
        backup = Path(td) / "backup-runbook"
        before = {
            item.relative_to(paths["codex_home"]): (item.stat().st_size, item.stat().st_mtime_ns)
            for item in paths["codex_home"].rglob("*")
            if item.is_file()
        }
        args = module.parse_args(
            [
                "--runbook",
                "--codex-home",
                str(paths["codex_home"]),
                "--backup-root",
                str(backup),
            ]
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert module.run(args) == 0
        after = {
            item.relative_to(paths["codex_home"]): (item.stat().st_size, item.stat().st_mtime_ns)
            for item in paths["codex_home"].rglob("*")
            if item.is_file()
        }
        text = output.getvalue()
        assert before == after, "runbook mode must not mutate Codex fixture"
        assert not backup.exists(), "runbook mode must not create backups"
        assert "--backup-only" in text
        assert "--apply" in text
        assert "--repair-thread-metadata-only" in text
        assert "legacy metadata repair" in text
        assert "Quit Codex" in text


def assert_legacy_metadata_repair_only_mode(module) -> None:
    with tempfile.TemporaryDirectory() as td:
        paths = make_fake_home(Path(td))
        session_index = paths["codex_home"] / "session_index.jsonl"
        session_index_snapshot = snapshot_text_file(session_index)
        rollout_snapshot = snapshot_text_file(paths["rollout"])
        backup = Path(td) / "backup-repair-only"
        args = module.parse_args(
            [
                "--repair-thread-metadata-only",
                "--codex-home",
                str(paths["codex_home"]),
                "--backup-root",
                str(backup),
            ]
        )
        assert module.run(args) == 0

        conn = sqlite3.connect(paths["state_db"])
        archived, archived_at, title, preview = conn.execute(
            "select archived, archived_at, title, first_user_message from threads where id=?",
            ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",),
        ).fetchone()
        conn.close()

        assert archived == 0, "metadata-only repair must not archive sessions"
        assert archived_at is None, "metadata-only repair must not mark sessions archived"
        assert len(title) <= 120
        assert title == "Codex Metadata Repair"
        assert len(preview) <= 240
        conn = sqlite3.connect(paths["state_db"])
        manual_title, manual_preview = conn.execute(
            "select title, first_user_message from threads where id=?",
            ("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",),
        ).fetchone()
        conn.close()
        assert manual_title.startswith("Handyman "), "metadata-only repair must preserve manual titles"
        assert len(manual_title) > 120
        assert len(manual_preview) <= 240
        assert_text_file_unchanged(session_index, session_index_snapshot)
        assert_text_file_unchanged(paths["rollout"], rollout_snapshot)
        assert paths["rollout"].exists(), "metadata-only repair must not move sessions"
        assert paths["worktree"].exists(), "metadata-only repair must not move worktrees"
        assert paths["log_file"].exists(), "metadata-only repair must not rotate logs"
        assert "DefinitelyMissingKeepCodexFast" in (paths["codex_home"] / "config.toml").read_text(
            encoding="utf-8"
        )
        assert (backup / "thread-metadata-repairs.jsonl").exists()
        assert (backup / "restore-thread-metadata.py").exists()
        assert not (backup / "moved-sessions.jsonl").exists()
        assert not (backup / "moved-worktrees.jsonl").exists()
        assert "Codex Metadata Repair" in (paths["codex_home"] / "session_index.jsonl").read_text(
            encoding="utf-8"
        )


def main() -> int:
    assert_process_detection_uses_sqlite_holders()
    assert_wait_for_codex_exit_times_out()
    assert_title_apply_probe_falls_back_when_lsof_missing()
    assert_title_apply_probe_lsof_missing_detects_ps_codex()
    assert_title_apply_probe_lsof_missing_detects_node_app_server()
    module = load_module()
    assert_help_distinguishes_legacy_repair(module)
    assert_title_dry_run_mode(module)
    assert_title_dry_run_details_mode(module)
    assert_title_dry_run_title_limit_without_preview_limit(module)
    assert_title_dry_run_wal_target_files_unchanged(module)
    assert_title_apply_requires_confirmation(module)
    assert_title_apply_blocks_when_codex_running(module)
    assert_title_apply_blocks_when_process_probe_unreliable(module)
    assert_title_apply_rechecks_active_state_after_backup(module)
    assert_title_apply_lsof_missing_ps_safe_allows_apply()
    assert_title_apply_wal_target_files_unchanged(module)
    assert_title_apply_mode(module)
    assert_title_apply_no_eligible_repairs_reports_zero_restore(module)
    assert_title_apply_manifest_records_rowcounts_before_commit(module)
    assert_title_apply_does_not_optimize_state_db(module)
    assert_title_apply_restores_failed_verification(module)
    assert_title_apply_restores_session_index_drift(module)
    assert_title_apply_does_not_restore_unowned_rowcount_zero(module)
    assert_title_apply_does_not_restore_unowned_same_replacement_source_drift(module)
    assert_title_apply_requires_ownership_for_verified_same_replacement(module)
    assert_report_mode(module)
    assert_runbook_mode(module)
    assert_backup_only_mode(module)
    assert_session_alias_detection(module)
    assert_normal_apply_does_not_repair_thread_metadata(module)
    assert_legacy_metadata_repair_only_mode(module)
    assert_apply_mode(module)
    print("smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
