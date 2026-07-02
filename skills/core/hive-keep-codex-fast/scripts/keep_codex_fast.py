#!/usr/bin/env python3
"""Backup-first Codex local-state maintenance.

Default mode is a read-only, privacy-safe report. Mutating modes are explicit:
backup-only, apply/archive maintenance, or metadata-only repair.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


THREAD_ID_RE = re.compile(
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.I,
)
PROJECT_HEADER_RE = re.compile(r"^\[projects\.([\"'])(.+)\1\]\s*$")
TEMP_PROJECT_RE = re.compile(
    r"(\\AppData\\Local\\Temp\\|/AppData/Local/Temp/|\\Temp\\codex-|/Temp/codex-|\\Temp\\spark-|/Temp/spark-)",
    re.I,
)
DEFAULT_TITLE_LIMIT = 120
DEFAULT_PREVIEW_LIMIT = 240
PROMPTISH_TITLE_PATTERNS = [
    "/Users/",
    "<image",
    "[Image",
    "[user",
    " user:",
    "assistant:",
    "tool call",
    "The following is the Codex agent history",
    "You are about to work on",
    "We are starting a new clean thread",
    "Read every textual file under",
    "Use this workspace to implement",
    "Deep-read review task",
]


@dataclass
class SessionCandidate:
    size: int
    thread_id: str
    title: str
    source: Path
    relative: Path
    updated_at: int | None


@dataclass
class ThreadMetadataRepair:
    thread_id: str
    old_title: str
    new_title: str
    old_preview: str
    new_preview: str
    title_repair_kind: str


@dataclass
class TitleDryRunClassification:
    thread_id: str
    title: str
    first_user_message: str
    classification: str
    proposed_action: str
    reason: str
    location: str
    safe_name: str


TITLE_REPAIR_CONFIRM_PHRASE = "APPLY_THREAD_TITLE_REPAIR"


@dataclass
class ThreadTitleApplyRepair:
    thread_id: str
    original_title: str
    original_first_user_message: str
    replacement_title: str
    safe_source: str
    location: str


@dataclass
class ActiveStateProbe:
    reliable: bool
    blocking_processes: list[str]
    blocked_reason: str


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def codex_home_from_args(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    override = os.environ.get("CODEX_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".codex"


def documents_backup_root() -> Path:
    docs = Path.home() / "Documents" / "Codex" / "codex-backups"
    if docs.parent.exists() or platform.system() == "Windows":
        return docs
    return Path.home() / ".codex" / "backups"


def size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                pass
    return total


def gb(value: int) -> str:
    return f"{value / 1024 / 1024 / 1024:.3f}"


def mb(value: int) -> str:
    return f"{value / 1024 / 1024:.1f}"


def report(line: str) -> None:
    print(line)


def sqlite_connect(path: Path, *, readonly: bool) -> sqlite3.Connection:
    if readonly:
        return sqlite3.connect(f"{canonical_path(path).as_uri()}?mode=ro", uri=True)
    return sqlite3.connect(path)


def sqlite_connect_immutable(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{canonical_path(path).as_uri()}?mode=ro&immutable=1", uri=True)


def sqlite_wal_may_have_uncheckpointed_content(path: Path) -> bool:
    wal = Path(str(path) + "-wal")
    try:
        return wal.exists() and wal.stat().st_size > 0
    except OSError:
        return False


def canonical_path(path: Path) -> Path:
    try:
        return path.resolve(strict=False)
    except OSError:
        return path.absolute()


def sqlite_state_holders(codex_home: Path) -> tuple[bool, list[str]]:
    targets = [
        codex_home / "state_5.sqlite",
        codex_home / "state_5.sqlite-wal",
        codex_home / "state_5.sqlite-shm",
    ]
    existing = [str(path) for path in targets if path.exists()]
    if not existing:
        return True, []
    try:
        output = subprocess.check_output(
            ["lsof", *existing],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return False, []
    except subprocess.CalledProcessError as exc:
        output = exc.output or ""
        if not output.strip():
            return True, []

    current_pid = str(os.getpid())
    hits: list[str] = []
    seen_pids: set[str] = set()
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2 or parts[1] == current_pid:
            continue
        if parts[1] in seen_pids:
            continue
        seen_pids.add(parts[1])
        hits.append(line.strip())
    return True, hits


def codex_processes_running(codex_home: Path | None = None) -> list[str]:
    system = platform.system()
    try:
        if codex_home is not None and system != "Windows":
            probed, holders = sqlite_state_holders(codex_home)
            if probed:
                return holders
        if system == "Windows":
            output = subprocess.check_output(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    (
                        "Get-CimInstance Win32_Process | "
                        "Select-Object Name,ProcessId,CommandLine | "
                        "ConvertTo-Json -Compress"
                    ),
                ],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            if not output.strip():
                return []
            data = json.loads(output)
            rows = data if isinstance(data, list) else [data]
            hits = []
            for row in rows:
                name = str(row.get("Name") or "")
                cmd = str(row.get("CommandLine") or "")
                pid = row.get("ProcessId")
                if name == "Codex.exe" or (name == "codex.exe" and ("app-server" in cmd or "OpenAI.Codex" in cmd)):
                    hits.append(f"{pid} {name}")
            return hits
        output = subprocess.check_output(["ps", "-axo", "pid=,comm=,args="], text=True)
        hits = []
        for line in output.splitlines():
            lower = line.lower()
            if "codex" in lower and ("app-server" in lower or "openai.codex" in lower or "codex desktop" in lower):
                hits.append(line.strip())
        return hits
    except Exception:
        return []


def title_apply_active_state_probe(codex_home: Path) -> ActiveStateProbe:
    system = platform.system()
    if system == "Windows":
        try:
            output = subprocess.check_output(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    (
                        "Get-CimInstance Win32_Process | "
                        "Select-Object Name,ProcessId,CommandLine | "
                        "ConvertTo-Json -Compress"
                    ),
                ],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            return ActiveStateProbe(False, [], "process_probe_unreliable")
        if not output.strip():
            return ActiveStateProbe(True, [], "")
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return ActiveStateProbe(False, [], "process_probe_unreliable")
        rows = data if isinstance(data, list) else [data]
        hits = []
        for row in rows:
            name = str(row.get("Name") or "")
            cmd = str(row.get("CommandLine") or "")
            pid = row.get("ProcessId")
            if name == "Codex.exe" or name == "codex.exe" or "OpenAI.Codex" in cmd:
                hits.append(f"{pid} {name}")
        return ActiveStateProbe(True, hits, "")

    targets = [
        codex_home / "state_5.sqlite",
        codex_home / "state_5.sqlite-wal",
        codex_home / "state_5.sqlite-shm",
    ]
    existing = [str(path) for path in targets if path.exists()]
    if existing:
        try:
            output = subprocess.check_output(
                ["lsof", *existing],
                text=True,
                stderr=subprocess.STDOUT,
            )
        except FileNotFoundError:
            output = ""
        except subprocess.CalledProcessError as exc:
            output = exc.output or ""
            if "denied" in output.lower() or "permission" in output.lower():
                return ActiveStateProbe(False, [], "process_probe_unreliable")
            output = ""
        except Exception:
            return ActiveStateProbe(False, [], "process_probe_unreliable")

        hits = parse_lsof_process_hits(output)
        if hits:
            return ActiveStateProbe(True, hits, "")

    try:
        output = subprocess.check_output(["ps", "-axo", "pid=,comm=,args="], text=True)
    except Exception:
        return ActiveStateProbe(False, [], "process_probe_unreliable")
    current_pid = str(os.getpid())
    hits = []
    for line in output.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 2 or parts[0] == current_pid:
            continue
        comm = Path(parts[1]).name.lower()
        args = parts[2].lower() if len(parts) > 2 else ""
        codex_app_server = (
            "app-server" in args
            and ("--codex-home" in args or "codex.app" in args or "openai.codex" in args)
        )
        if (
            comm in {"codex", "codex.exe"}
            or "openai.codex" in args
            or "codex desktop" in args
            or codex_app_server
        ):
            hits.append(line.strip())
    return ActiveStateProbe(True, hits, "")


def parse_lsof_process_hits(output: str) -> list[str]:
    current_pid = str(os.getpid())
    hits: list[str] = []
    seen_pids: set[str] = set()
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2 or parts[1] == current_pid:
            continue
        if parts[1] in seen_pids:
            continue
        seen_pids.add(parts[1])
        hits.append(line.strip())
    return hits


def wait_for_codex_exit(codex_home: Path, timeout_seconds: int) -> list[str]:
    deadline = time.time() + timeout_seconds
    while True:
        running = codex_processes_running(codex_home)
        if not running:
            return []
        if time.time() >= deadline:
            return running
        time.sleep(2)


def wait_for_title_apply_safe_state(codex_home: Path, timeout_seconds: int) -> ActiveStateProbe:
    deadline = time.time() + timeout_seconds
    while True:
        probe = title_apply_active_state_probe(codex_home)
        if not probe.reliable or not probe.blocking_processes:
            return probe
        if time.time() >= deadline:
            return probe
        time.sleep(2)


def sqlite_backup(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite_connect(src, readonly=True)
    target = sqlite3.connect(dst)
    source.backup(target)
    target.close()
    source.close()


def copy_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(
            src,
            dst,
            ignore=shutil.ignore_patterns(
                "node_modules",
                ".git",
                ".next",
                "dist",
                "build",
                ".venv",
                "__pycache__",
                ".pytest_cache",
            ),
            dirs_exist_ok=True,
        )
    else:
        shutil.copy2(src, dst)
    report(f"backed_up {src.name}")


def backup_metadata(codex_home: Path, backup_root: Path) -> None:
    backup_root.mkdir(parents=True, exist_ok=True)
    for name in [
        ".codex-global-state.json",
        "config.toml",
        "history.jsonl",
        "installation_id",
        "models_cache.json",
        "session_index.jsonl",
        "version.json",
        "memories",
        "skills",
        "rules",
        "plugins",
        "automations",
    ]:
        copy_if_exists(codex_home / name, backup_root / name)
    sqlite_backup(codex_home / "state_5.sqlite", backup_root / "state_5.sqlite")


def load_pinned(codex_home: Path) -> set[str]:
    path = codex_home / ".codex-global-state.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("pinned-thread-ids", []))
    except Exception:
        return set()


def normalize_extended_path(value: str) -> str:
    if value.startswith("\\\\?\\UNC\\"):
        return "\\\\" + value[8:]
    if value.startswith("\\\\?\\"):
        return value[4:]
    return value


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {row[1] for row in conn.execute(f'pragma table_info("{table}")').fetchall()}
    except sqlite3.Error:
        return set()


def has_threads_columns(conn: sqlite3.Connection, required: set[str]) -> bool:
    return required.issubset(table_columns(conn, "threads"))


def bounded_text(value: str, limit: int) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3].rstrip() + "..."


def normalized_text(value: str) -> str:
    return " ".join((value or "").split())


def is_safe_session_index_title(value: str, limit: int) -> bool:
    title = normalized_text(value)
    if not title or len(title) > min(limit, 80):
        return False
    if title.count(" ") > 7:
        return False
    lower = title.lower()
    for pattern in PROMPTISH_TITLE_PATTERNS:
        if pattern.lower() in lower:
            return False
    return True


def load_session_index_names(codex_home: Path, title_limit: int) -> dict[str, str]:
    path = codex_home / "session_index.jsonl"
    names: dict[str, str] = {}
    if not path.exists():
        return names
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return names
    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        thread_id = record.get("id") or record.get("thread_id")
        name = record.get("thread_name") or record.get("name") or record.get("title")
        if (
            isinstance(thread_id, str)
            and isinstance(name, str)
            and is_safe_session_index_title(name, title_limit)
        ):
            names[thread_id] = normalized_text(name)
    return names


def load_session_index_thread_names(codex_home: Path, title_limit: int) -> dict[str, str]:
    path = codex_home / "session_index.jsonl"
    names: dict[str, str] = {}
    if not path.exists():
        return names
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return names
    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        thread_id = record.get("id") or record.get("thread_id")
        name = record.get("thread_name")
        if (
            isinstance(thread_id, str)
            and isinstance(name, str)
            and is_safe_session_index_title(name, title_limit)
        ):
            names[thread_id] = normalized_text(name)
    return names


def sql_text_expr(columns: set[str], *names: str) -> str:
    for name in names:
        if name in columns:
            return f'coalesce("{name}", \'\')'
    return "''"


def archived_location_expr(columns: set[str]) -> str:
    if "archived_at" in columns and "archived" in columns:
        return "case when archived_at is not null or COALESCE(archived,0)<>0 then 'archived' else 'active' end"
    if "archived_at" in columns:
        return "case when archived_at is not null then 'archived' else 'active' end"
    if "archived" in columns:
        return "case when COALESCE(archived,0)<>0 then 'archived' else 'active' end"
    return "'active'"


def thread_title_order_expr(columns: set[str]) -> str:
    if "updated_at" in columns:
        return "updated_at desc, id"
    return "id"


def is_subagent_thread(row: sqlite3.Row, columns: set[str]) -> bool:
    marker_columns = [
        "source",
        "thread_source",
        "agent_role",
        "role",
        "kind",
        "owner",
        "created_by",
    ]
    marker_values = []
    for column in marker_columns:
        if column in columns:
            value = row[column]
            if value is not None:
                marker_values.append(str(value).lower())
    marker = " ".join(marker_values)
    return re.search(r"(^|[^a-z0-9])(sub[-_ ]?agent|system|harness)([^a-z0-9]|$)", marker) is not None


def classify_thread_title(
    *,
    thread_id: str,
    title: str,
    first_user_message: str,
    location: str,
    is_excluded: bool,
    safe_name: str,
    title_limit: int,
) -> TitleDryRunClassification:
    normalized_title = title or ""
    normalized_first_message = first_user_message or ""
    title_matches_first_message = normalized_title == normalized_first_message and normalized_title != ""
    title_is_oversized = len(normalized_title) > title_limit

    if is_excluded:
        return TitleDryRunClassification(
            thread_id=thread_id,
            title=normalized_title,
            first_user_message=normalized_first_message,
            classification="excluded_subagent",
            proposed_action="skip",
            reason="subagent_or_system_thread",
            location=location,
            safe_name=safe_name,
        )
    if not title_matches_first_message:
        return TitleDryRunClassification(
            thread_id=thread_id,
            title=normalized_title,
            first_user_message=normalized_first_message,
            classification="manual_keep",
            proposed_action="preserve_title",
            reason="title_differs_from_first_user_message",
            location=location,
            safe_name=safe_name,
        )
    if not title_is_oversized:
        return TitleDryRunClassification(
            thread_id=thread_id,
            title=normalized_title,
            first_user_message=normalized_first_message,
            classification="manual_keep",
            proposed_action="preserve_title",
            reason="automatic_title_within_limit",
            location=location,
            safe_name=safe_name,
        )
    if safe_name:
        return TitleDryRunClassification(
            thread_id=thread_id,
            title=normalized_title,
            first_user_message=normalized_first_message,
            classification="safe_name_available",
            proposed_action="would_repair_from_session_index_thread_name",
            reason="auto_repair_candidate_with_safe_thread_name",
            location=location,
            safe_name=safe_name,
        )
    return TitleDryRunClassification(
        thread_id=thread_id,
        title=normalized_title,
        first_user_message=normalized_first_message,
        classification="needs_human",
        proposed_action="request_manual_title",
        reason="auto_repair_candidate_without_safe_thread_name",
        location=location,
        safe_name=safe_name,
    )


def title_dry_run_classifications(
    conn: sqlite3.Connection,
    codex_home: Path,
    *,
    title_limit: int,
) -> list[TitleDryRunClassification]:
    required = {"id", "title", "first_user_message"}
    if not has_threads_columns(conn, required):
        report("thread_title_dry_run skipped_missing_threads_columns")
        return []

    columns = table_columns(conn, "threads")
    select_source = sql_text_expr(columns, "source")
    select_thread_source = sql_text_expr(columns, "thread_source")
    select_agent_role = sql_text_expr(columns, "agent_role")
    select_role = sql_text_expr(columns, "role")
    select_kind = sql_text_expr(columns, "kind")
    select_owner = sql_text_expr(columns, "owner")
    select_created_by = sql_text_expr(columns, "created_by")
    select_location = archived_location_expr(columns)
    order_expr = thread_title_order_expr(columns)
    query = f"""
        select
          id,
          coalesce(title, '') as title,
          coalesce(first_user_message, '') as first_user_message,
          {select_location} as location,
          {select_source} as source,
          {select_thread_source} as thread_source,
          {select_agent_role} as agent_role,
          {select_role} as role,
          {select_kind} as kind,
          {select_owner} as owner,
          {select_created_by} as created_by
        from threads
        order by {order_expr}
        """
    old_factory = conn.row_factory
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(query).fetchall()
    finally:
        conn.row_factory = old_factory

    session_index_names = load_session_index_thread_names(codex_home, title_limit)
    items: list[TitleDryRunClassification] = []
    row_columns = {
        "source",
        "thread_source",
        "agent_role",
        "role",
        "kind",
        "owner",
        "created_by",
    }
    for row in rows:
        thread_id = str(row["id"])
        items.append(
            classify_thread_title(
                thread_id=thread_id,
                title=str(row["title"] or ""),
                first_user_message=str(row["first_user_message"] or ""),
                location=str(row["location"] or "active"),
                is_excluded=is_subagent_thread(row, row_columns),
                safe_name=session_index_names.get(thread_id, ""),
                title_limit=title_limit,
            )
        )
    return items


def report_thread_title_dry_run(
    conn: sqlite3.Connection,
    codex_home: Path,
    *,
    details: bool,
    title_limit: int,
) -> None:
    classifications = title_dry_run_classifications(conn, codex_home, title_limit=title_limit)
    counts = {
        "manual_keep": 0,
        "auto_repair_candidate": 0,
        "safe_name_available": 0,
        "needs_human": 0,
        "excluded_subagent": 0,
    }
    active_real = 0
    archived_real = 0
    for item in classifications:
        counts[item.classification] = counts.get(item.classification, 0) + 1
        if item.classification in {"safe_name_available", "needs_human"}:
            counts["auto_repair_candidate"] += 1
        if item.classification != "excluded_subagent":
            if item.location == "archived":
                archived_real += 1
            else:
                active_real += 1

    report(f"thread_title_dry_run_scanned {len(classifications)}")
    report(f"thread_title_dry_run_active_real {active_real}")
    report(f"thread_title_dry_run_archived_real {archived_real}")
    report(f"thread_title_dry_run_manual_keep {counts['manual_keep']}")
    report(f"thread_title_dry_run_auto_repair_candidate {counts['auto_repair_candidate']}")
    report(f"thread_title_dry_run_safe_name_available {counts['safe_name_available']}")
    report(f"thread_title_dry_run_needs_human {counts['needs_human']}")
    report(f"thread_title_dry_run_excluded_subagent {counts['excluded_subagent']}")
    report("thread_title_dry_run_writes false")
    for index, item in enumerate(classifications, start=1):
        label = f"title_thread_{index:03d}"
        title_chars = len(item.title)
        if details:
            safe_name = item.safe_name or ""
            candidate_class = "auto_repair_candidate" if item.classification in {"safe_name_available", "needs_human"} else "none"
            report(
                f"thread_title_dry_run_item {label} thread_id={item.thread_id} "
                f"location={item.location} classification={item.classification} "
                f"candidate_class={candidate_class} proposed_action={item.proposed_action} reason={item.reason} "
                f"title_chars={title_chars} safe_name={safe_name!r} title={item.title!r}"
            )
        else:
            candidate_class = "auto_repair_candidate" if item.classification in {"safe_name_available", "needs_human"} else "none"
            report(
                f"thread_title_dry_run_item {label} location={item.location} "
                f"classification={item.classification} candidate_class={candidate_class} proposed_action={item.proposed_action} "
                f"reason={item.reason} title_chars={title_chars}"
            )


def write_thread_title_manifest(manifest: Path, records: list[dict[str, object]]) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_thread_title_restore_script(manifest: Path, state_db: Path, backup_root: Path) -> None:
    restore = backup_root / "restore-thread-titles.py"
    restore.write_text(
        f'''import json
import sqlite3
from pathlib import Path

manifest = Path(r"{manifest}")
db = Path(r"{state_db}")
conn = sqlite3.connect(db)
conn.execute("pragma busy_timeout=10000")
attempted = 0
restored = 0
skipped = 0
for line in manifest.read_text(encoding="utf-8").splitlines():
    rec = json.loads(line)
    if rec.get("apply_rowcount") != 1:
        skipped += 1
        print(f"restore_skipped_not_owned {{rec['thread_id']}}")
        continue
    row = conn.execute(
        "select title from threads where id=?",
        (rec["thread_id"],),
    ).fetchone()
    if row is None or row[0] != rec.get("chosen_replacement"):
        skipped += 1
        print(f"restore_skipped_current_title_changed {{rec['thread_id']}}")
        continue
    attempted += 1
    conn.execute(
        "update threads set title=? where id=?",
        (rec["original_title"], rec["thread_id"]),
    )
    restored += 1
conn.commit()
conn.close()
print(f"restore_attempted {{attempted}}")
print(f"restore_restored {{restored}}")
print(f"restore_skipped {{skipped}}")
''',
        encoding="utf-8",
    )
    report(f"thread_title_restore_script {restore}")


def restore_mismatched_thread_titles(
    conn: sqlite3.Connection,
    records: list[dict[str, object]],
    repair_by_thread_id: dict[str, ThreadTitleApplyRepair],
) -> tuple[int, int]:
    attempted = 0
    restored = 0
    for record in records:
        if record.get("verification_status") == "verified":
            record["restore_status"] = "not_needed"
            continue
        attempted += 1
        repair = repair_by_thread_id[str(record["thread_id"])]
        if record.get("apply_rowcount") != 1:
            record["restore_status"] = "restore_skipped_not_owned"
            continue
        current = conn.execute(
            "select title from threads where id=?",
            (repair.thread_id,),
        ).fetchone()
        current_title = current[0] if current is not None else None
        if current_title != repair.replacement_title:
            record["restore_status"] = "restore_skipped_current_title_changed"
            continue
        result = conn.execute(
            "update threads set title=? where id=?",
            (repair.original_title, repair.thread_id),
        )
        row = conn.execute(
            "select title from threads where id=?",
            (repair.thread_id,),
        ).fetchone()
        if result.rowcount == 1 and row is not None and row[0] == repair.original_title:
            record["restore_status"] = "restored_original_title"
            record["verification_status"] = f"{record['verification_status']}_restored"
            restored += 1
        else:
            record["restore_status"] = "restore_failed"
    conn.commit()
    return attempted, restored


def apply_thread_title_repairs(
    conn: sqlite3.Connection,
    codex_home: Path,
    backup_root: Path,
    *,
    details: bool,
    title_limit: int,
) -> int:
    classifications = title_dry_run_classifications(conn, codex_home, title_limit=title_limit)
    repairs = [
        ThreadTitleApplyRepair(
            thread_id=item.thread_id,
            original_title=item.title,
            original_first_user_message=item.first_user_message,
            replacement_title=item.safe_name,
            safe_source="session_index.thread_name",
            location=item.location,
        )
        for item in classifications
        if item.classification == "safe_name_available"
    ]
    counts = {
        "manual_keep": 0,
        "safe_name_available": 0,
        "needs_human": 0,
        "excluded_subagent": 0,
    }
    for item in classifications:
        if item.classification in counts:
            counts[item.classification] += 1

    report(f"thread_title_apply_scanned {len(classifications)}")
    report(f"thread_title_apply_manual_keep {counts['manual_keep']}")
    report(f"thread_title_apply_eligible {counts['safe_name_available']}")
    report(f"thread_title_apply_needs_human {counts['needs_human']}")
    report(f"thread_title_apply_excluded_subagent {counts['excluded_subagent']}")
    if not repairs:
        report("thread_title_apply_applied 0")
        report("thread_title_apply_verification_mismatches 0")
        report("thread_title_apply_restore_required 0")
        report("thread_title_apply_restore_attempted 0")
        report("thread_title_apply_restore_succeeded 0")
        return 0

    manifest = backup_root / "thread-title-repairs.jsonl"
    records: list[dict[str, object]] = []
    for item in repairs:
        records.append(
            {
                "thread_id": item.thread_id,
                "original_title": item.original_title,
                "original_first_user_message": item.original_first_user_message,
                "chosen_replacement": item.replacement_title,
                "safe_source": item.safe_source,
                "location": item.location,
                "initial_verification_status": "pending",
                "verification_status": "pending",
                "safe_source_verification_status": "pending",
                "apply_rowcount": 0,
                "restore_status": "not_attempted",
            }
        )
    write_thread_title_manifest(manifest, records)
    report(f"thread_title_repair_manifest {manifest}")
    write_thread_title_restore_script(manifest, codex_home / "state_5.sqlite", backup_root)

    updated = 0
    records_by_thread_id = {str(record["thread_id"]): record for record in records}
    for item in repairs:
        result = conn.execute(
            """
            update threads
            set title=?
            where id=? and title=? and first_user_message=?
            """,
            (
                item.replacement_title,
                item.thread_id,
                item.original_title,
                item.original_first_user_message,
            ),
        )
        updated += result.rowcount
        records_by_thread_id[item.thread_id]["apply_rowcount"] = result.rowcount
    write_thread_title_manifest(manifest, records)
    conn.commit()

    repair_by_thread_id = {item.thread_id: item for item in repairs}
    verified_session_index_names = load_session_index_thread_names(codex_home, title_limit)
    mismatches = 0
    for record in records:
        row = conn.execute(
            "select title, first_user_message from threads where id=?",
            (record["thread_id"],),
        ).fetchone()
        repair = repair_by_thread_id[str(record["thread_id"])]
        verified_safe_name = verified_session_index_names.get(repair.thread_id, "")
        if verified_safe_name == repair.replacement_title:
            record["safe_source_verification_status"] = "verified"
        else:
            record["safe_source_verification_status"] = "mismatch"
        if row is None:
            record["verification_status"] = "missing_after_apply"
            mismatches += 1
        elif (
            record.get("apply_rowcount") == 1
            and row[0] == record["chosen_replacement"]
            and row[1] == repair.original_first_user_message
            and record["safe_source_verification_status"] == "verified"
        ):
            record["verification_status"] = "verified"
        elif record["safe_source_verification_status"] != "verified":
            record["verification_status"] = "safe_source_mismatch_before_restore"
            mismatches += 1
        else:
            record["verification_status"] = "mismatch_before_restore"
            mismatches += 1

    restore_attempted = 0
    restore_succeeded = 0
    if mismatches:
        restore_attempted, restore_succeeded = restore_mismatched_thread_titles(
            conn,
            records,
            repair_by_thread_id,
        )
    else:
        for record in records:
            record["restore_status"] = "not_needed"
    write_thread_title_manifest(manifest, records)

    report(f"thread_title_apply_applied {updated}")
    report(f"thread_title_apply_verification_mismatches {mismatches}")
    report(f"thread_title_apply_restore_required {mismatches}")
    report(f"thread_title_apply_restore_attempted {restore_attempted}")
    report(f"thread_title_apply_restore_succeeded {restore_succeeded}")
    for index, record in enumerate(records, start=1):
        label = f"title_thread_{index:03d}"
        if details:
            report(
                f"thread_title_apply_item {label} thread_id={record['thread_id']} "
                f"location={record['location']} verification_status={record['verification_status']} "
                f"safe_source_verification_status={record['safe_source_verification_status']} "
                f"restore_status={record['restore_status']} safe_source={record['safe_source']} "
                f"replacement_title={record['chosen_replacement']!r}"
            )
        else:
            report(
                f"thread_title_apply_item {label} location={record['location']} "
                f"verification_status={record['verification_status']} "
                f"safe_source_verification_status={record['safe_source_verification_status']} "
                f"restore_status={record['restore_status']} "
                f"safe_source={record['safe_source']}"
            )
    return 4 if mismatches else 0


def report_thread_metadata_bloat(
    conn: sqlite3.Connection,
    *,
    title_limit: int,
    preview_limit: int,
) -> None:
    columns = table_columns(conn, "threads")
    if not {"id", "title"}.issubset(columns):
        report("thread_metadata_bloat skipped_missing_threads_columns")
        return
    archived_expr = "COALESCE(archived,0)=0" if "archived" in columns else "archived_at is null"
    preview_col = "first_user_message" if "first_user_message" in columns else None
    if preview_col:
        row = conn.execute(
            f"""
            select
              count(*),
              coalesce(sum(length(title)), 0),
              coalesce(sum(length(first_user_message)), 0),
              coalesce(max(length(title)), 0),
              coalesce(max(length(first_user_message)), 0),
              sum(case when length(title) > ? then 1 else 0 end),
              sum(case when title = first_user_message and length(title) > ? then 1 else 0 end),
              sum(case when title <> first_user_message and length(title) > ? then 1 else 0 end),
              sum(case when length(first_user_message) > ? then 1 else 0 end),
              sum(case when length(first_user_message) > 10000 then 1 else 0 end)
            from threads
            where {archived_expr}
            """,
            (title_limit, title_limit, title_limit, preview_limit),
        ).fetchone()
        (
            active_rows,
            title_chars,
            preview_chars,
            max_title,
            max_preview,
            title_over_limit,
            auto_title_bloat,
            manual_title_preserve,
            preview_over_limit,
            preview_over_10k,
        ) = row
    else:
        row = conn.execute(
            f"""
            select
              count(*),
              coalesce(sum(length(title)), 0),
              coalesce(max(length(title)), 0),
              sum(case when length(title) > ? then 1 else 0 end)
            from threads
            where {archived_expr}
            """,
            (title_limit,),
        ).fetchone()
        active_rows, title_chars, max_title, title_over_limit = row
        auto_title_bloat = manual_title_preserve = 0
        preview_chars = max_preview = preview_over_limit = preview_over_10k = 0

    report(f"thread_active_rows {active_rows}")
    report(f"thread_title_chars {title_chars}")
    report(f"thread_first_user_message_chars {preview_chars}")
    report(f"thread_max_title_chars {max_title}")
    report(f"thread_max_first_user_message_chars {max_preview}")
    report(f"thread_titles_over_limit {title_over_limit or 0}")
    report(f"thread_auto_title_bloat_candidates {auto_title_bloat or 0}")
    report(f"thread_manual_title_preserve {manual_title_preserve or 0}")
    report(f"thread_first_user_message_over_limit {preview_over_limit or 0}")
    report(f"thread_first_user_message_over_10k {preview_over_10k or 0}")


def repair_thread_metadata_bloat(
    conn: sqlite3.Connection,
    codex_home: Path,
    backup_root: Path,
    *,
    apply: bool,
    details: bool,
    title_limit: int,
    preview_limit: int,
) -> None:
    # Legacy combined repair path. Title-only repair must not call into this
    # helper because it also compacts first_user_message for compatibility.
    required = {"id", "title"}
    if not has_threads_columns(conn, required):
        report("thread_metadata_repair skipped_missing_threads_columns")
        return
    columns = table_columns(conn, "threads")
    has_preview = "first_user_message" in columns
    archived_expr = "COALESCE(archived,0)=0" if "archived" in columns else "archived_at is null"
    select_preview = "first_user_message" if has_preview else "''"
    select_cwd = "cwd" if "cwd" in columns else "''"
    rows = conn.execute(
        f"""
        select id, title, {select_preview}, {select_cwd}
        from threads
        where {archived_expr}
          and (
            length(title) > ?
            {"or length(first_user_message) > ?" if has_preview else ""}
          )
        """,
        (title_limit, preview_limit) if has_preview else (title_limit,),
    ).fetchall()

    repairs: list[ThreadMetadataRepair] = []
    session_index_names = load_session_index_names(codex_home, title_limit)
    manual_title_preserved = 0
    auto_title_replacements = 0
    title_repair_unavailable = 0
    preview_only_repairs = 0
    for thread_id, title, preview, cwd in rows:
        old_title = title or ""
        old_preview = preview or ""
        title_matches_first_message = has_preview and old_title == old_preview and old_title != ""
        if title_matches_first_message and len(old_title) > title_limit:
            indexed_name = session_index_names.get(str(thread_id), "")
            if indexed_name:
                new_title = indexed_name
                title_repair_kind = "from_session_index"
                auto_title_replacements += 1
            else:
                new_title = old_title
                title_repair_kind = "preserve_no_safe_session_index_name"
                title_repair_unavailable += 1
        else:
            new_title = old_title
            title_repair_kind = "preserve_manual_title"
            if len(old_title) > title_limit:
                manual_title_preserved += 1
        new_preview = bounded_text(old_preview, preview_limit) if has_preview else ""
        if new_title != old_title or new_preview != old_preview:
            if new_title == old_title and new_preview != old_preview:
                preview_only_repairs += 1
            repairs.append(
                ThreadMetadataRepair(
                    str(thread_id),
                    old_title,
                    new_title,
                    old_preview,
                    new_preview,
                    title_repair_kind,
                )
            )

    report(f"thread_metadata_repair_candidates {len(repairs)}")
    report(f"thread_metadata_session_index_title_replacements {auto_title_replacements}")
    report(f"thread_metadata_title_repair_unavailable {title_repair_unavailable}")
    report(f"thread_metadata_manual_titles_preserved {manual_title_preserved}")
    report(f"thread_metadata_preview_only_repairs {preview_only_repairs}")
    for index, item in enumerate(repairs[:10], start=1):
        label = f"thread_{index:03d}"
        title_delta = len(item.old_title) - len(item.new_title)
        preview_delta = len(item.old_preview) - len(item.new_preview)
        if details:
            report(
                f"thread_metadata_repair_candidate {label} thread_id={item.thread_id} "
                f"title_delta={title_delta} preview_delta={preview_delta} "
                f"title_repair_kind={item.title_repair_kind}"
            )
        else:
            report(
                f"thread_metadata_repair_candidate {label} "
                f"title_delta={title_delta} preview_delta={preview_delta} "
                f"title_repair_kind={item.title_repair_kind}"
            )

    if not apply or not repairs:
        return

    manifest = backup_root / "thread-metadata-repairs.jsonl"
    with manifest.open("w", encoding="utf-8") as handle:
        for item in repairs:
            record = {
                "thread_id": item.thread_id,
                "old_title": item.old_title,
                "new_title": item.new_title,
                "old_first_user_message": item.old_preview,
                "new_first_user_message": item.new_preview,
                "title_repair_kind": item.title_repair_kind,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    cur = conn.cursor()
    for item in repairs:
        if has_preview:
            cur.execute(
                "update threads set title=?, first_user_message=? where id=?",
                (item.new_title, item.new_preview, item.thread_id),
            )
        else:
            cur.execute(
                "update threads set title=? where id=?",
                (item.new_title, item.thread_id),
            )
    report("thread_metadata_repair applied")
    report(f"thread_metadata_repair_manifest {manifest}")
    write_thread_metadata_restore_script(manifest, codex_home / "state_5.sqlite", backup_root)


def write_thread_metadata_restore_script(manifest: Path, state_db: Path, backup_root: Path) -> None:
    restore = backup_root / "restore-thread-metadata.py"
    restore.write_text(
        f'''import json
import sqlite3
from pathlib import Path

manifest = Path(r"{manifest}")
db = Path(r"{state_db}")
conn = sqlite3.connect(db)
conn.execute("pragma busy_timeout=10000")
cols = {{row[1] for row in conn.execute('pragma table_info("threads")').fetchall()}}
has_preview = "first_user_message" in cols
for line in manifest.read_text(encoding="utf-8").splitlines():
    rec = json.loads(line)
    if has_preview:
        conn.execute(
            "update threads set title=?, first_user_message=? where id=?",
            (rec["old_title"], rec["old_first_user_message"], rec["thread_id"]),
        )
    else:
        conn.execute(
            "update threads set title=? where id=?",
            (rec["old_title"], rec["thread_id"]),
        )
conn.commit()
conn.close()
''',
        encoding="utf-8",
    )
    report(f"thread_metadata_restore_script {restore}")


def normalize_sqlite_paths(conn: sqlite3.Connection, apply: bool) -> int:
    cur = conn.cursor()
    total = 0
    tables = [
        row[0]
        for row in cur.execute(
            "select name from sqlite_master where type='table' and name not like 'sqlite_%'"
        )
    ]
    for table in tables:
        cols = cur.execute(f'pragma table_info("{table}")').fetchall()
        text_cols = [col[1] for col in cols if "TEXT" in (col[2] or "").upper() or col[2] == ""]
        for col in text_cols:
            rows = cur.execute(
                f'select rowid, "{col}" from "{table}" where "{col}" like ?',
                ("\\\\?\\%",),
            ).fetchall()
            changed = 0
            for rowid, value in rows:
                if isinstance(value, str) and value.startswith("\\\\?\\"):
                    changed += 1
                    if apply:
                        cur.execute(
                            f'update "{table}" set "{col}"=? where rowid=?',
                            (normalize_extended_path(value), rowid),
                        )
            if changed:
                report(f"extended_paths {table}.{col} {changed}")
                total += changed
    if total == 0:
        report("extended_paths 0")
    return total


def active_session_candidates(
    conn: sqlite3.Connection,
    codex_home: Path,
    archive_older_than_days: int,
) -> list[SessionCandidate]:
    sessions_root = codex_home / "sessions"
    sessions_root_canonical = canonical_path(sessions_root)
    cutoff = int((datetime.now() - timedelta(days=archive_older_than_days)).timestamp())
    pinned = load_pinned(codex_home)
    rows = conn.execute(
        "select id, title, rollout_path, updated_at from threads where archived_at is null"
    ).fetchall()
    candidates: list[SessionCandidate] = []
    for thread_id, title, rollout_path, updated_at in rows:
        if thread_id in pinned or not rollout_path:
            continue
        if updated_at is not None and int(updated_at) >= cutoff:
            continue
        source = Path(rollout_path)
        if not source.exists():
            continue
        try:
            relative = canonical_path(source).relative_to(sessions_root_canonical)
        except ValueError:
            continue
        candidates.append(
            SessionCandidate(source.stat().st_size, thread_id, title or "", source, relative, updated_at)
        )
    candidates.sort(key=lambda item: item.size, reverse=True)
    return candidates


def archive_sessions(
    conn: sqlite3.Connection,
    candidates: list[SessionCandidate],
    codex_home: Path,
    backup_root: Path,
    stamp: str,
    apply: bool,
    details: bool,
) -> None:
    total = sum(item.size for item in candidates)
    report(f"old_session_candidates {len(candidates)}")
    report(f"old_session_candidate_gb {gb(total)}")
    for index, item in enumerate(candidates[:10], start=1):
        label = f"session_{index:03d}"
        if details:
            report(f"large_session_mb {mb(item.size)} {label} thread_id={item.thread_id} title={item.title[:70]}")
        else:
            report(f"large_session_mb {mb(item.size)} {label}")
    if not apply or not candidates:
        return

    archive_root = codex_home / "archived_sessions" / f"keep-codex-fast-{stamp}"
    manifest = backup_root / "moved-sessions.jsonl"
    archive_root.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    cur = conn.cursor()
    with manifest.open("w", encoding="utf-8") as handle:
        for item in candidates:
            dest = archive_root / item.relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item.source), str(dest))
            record = {
                "thread_id": item.thread_id,
                "bytes": item.size,
                "from": str(item.source),
                "to": str(dest),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            cur.execute(
                "update threads set rollout_path=?, archived=1, archived_at=? where id=?",
                (str(dest), now, item.thread_id),
            )
    write_session_restore_script(manifest, codex_home / "state_5.sqlite", backup_root)
    report(f"archived_sessions_root {archive_root}")
    report(f"archived_sessions_manifest {manifest}")


def write_session_restore_script(manifest: Path, state_db: Path, backup_root: Path) -> None:
    restore = backup_root / "restore-sessions.py"
    restore.write_text(
        f'''import json
import shutil
import sqlite3
from pathlib import Path

manifest = Path(r"{manifest}")
db = Path(r"{state_db}")
conn = sqlite3.connect(db)
conn.execute("pragma busy_timeout=10000")
for line in manifest.read_text(encoding="utf-8").splitlines():
    rec = json.loads(line)
    src = Path(rec["to"])
    dest = Path(rec["from"])
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
    if rec.get("thread_id"):
        conn.execute(
            "update threads set rollout_path=?, archived=0, archived_at=NULL where id=?",
            (str(dest), rec["thread_id"]),
        )
conn.commit()
conn.close()
''',
        encoding="utf-8",
    )
    report(f"session_restore_script {restore}")


def prune_config(codex_home: Path, backup_root: Path, apply: bool, write_artifacts: bool) -> None:
    path = codex_home / "config.toml"
    if not path.exists():
        report("config_prune_candidates 0")
        return
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    out: list[str] = []
    removed: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = PROJECT_HEADER_RE.match(line)
        if not match:
            out.append(line)
            i += 1
            continue
        project_path = match.group(2)
        block = [line]
        i += 1
        while i < len(lines) and not lines[i].startswith("["):
            block.append(lines[i])
            i += 1
        should_remove = bool(TEMP_PROJECT_RE.search(project_path)) or not Path(project_path).exists()
        if should_remove:
            removed.append(project_path)
        else:
            out.extend(block)

    if write_artifacts:
        (backup_root / "pruned-projects.txt").write_text(
            "\n".join(removed) + ("\n" if removed else ""),
            encoding="utf-8",
        )
    report(f"config_prune_candidates {len(removed)}")
    if apply and removed:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        report("config_pruned applied")


def move_stale_worktrees(codex_home: Path, backup_root: Path, days: int, stamp: str, apply: bool) -> None:
    root = codex_home / "worktrees"
    if not root.exists():
        report("worktree_candidates 0")
        return
    cutoff = time.time() - days * 24 * 60 * 60
    candidates = [path for path in root.iterdir() if path.is_dir() and path.stat().st_mtime < cutoff]
    total = sum(size_bytes(path) for path in candidates)
    report(f"worktree_candidates {len(candidates)}")
    report(f"worktree_candidate_gb {gb(total)}")
    if not apply or not candidates:
        return
    archive_root = codex_home / "archived_worktrees" / f"keep-codex-fast-{stamp}"
    manifest = backup_root / "moved-worktrees.jsonl"
    archive_root.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", encoding="utf-8") as handle:
        for source in candidates:
            dest = archive_root / source.name
            item_size = size_bytes(source)
            shutil.move(str(source), str(dest))
            handle.write(json.dumps({"from": str(source), "to": str(dest), "bytes": item_size}) + "\n")
    report(f"worktree_archive_root {archive_root}")
    report(f"worktree_manifest {manifest}")


def rotate_logs(codex_home: Path, threshold_mb: int, stamp: str, apply: bool) -> None:
    files = [path for path in codex_home.glob("logs_2.sqlite*") if path.is_file()]
    total = sum(path.stat().st_size for path in files)
    report(f"logs_mb {mb(total)}")
    if total < threshold_mb * 1024 * 1024:
        report("logs_rotate skipped_below_threshold")
        return
    if apply and files:
        archive_root = codex_home / "archived_logs" / f"keep-codex-fast-{stamp}"
        archive_root.mkdir(parents=True, exist_ok=True)
        for path in files:
            shutil.move(str(path), str(archive_root / path.name))
        report(f"logs_archive_root {archive_root}")


def top_node_processes(details: bool) -> None:
    system = platform.system()
    report("top_node_processes")
    try:
        if system == "Windows":
            command = (
                "Get-Process node -ErrorAction SilentlyContinue | "
                "Sort-Object WorkingSet64 -Descending | Select-Object -First 10 "
                "Id,ProcessName,@{n='MB';e={[math]::Round($_.WorkingSet64/1MB,1)}},Path | "
                "ConvertTo-Json -Compress"
            )
            output = subprocess.check_output(["powershell", "-NoProfile", "-Command", command], text=True)
            if not output.strip():
                return
            data = json.loads(output)
            rows = data if isinstance(data, list) else [data]
            for row in rows:
                if details:
                    report(f"node_mb {row.get('MB')} pid={row.get('Id')} path={row.get('Path')}")
                else:
                    report(f"node_mb {row.get('MB')} process=node")
            return
        output = subprocess.check_output(["ps", "-axo", "pid=,rss=,comm=,args="], text=True)
        rows = []
        for line in output.splitlines():
            parts = line.strip().split(None, 3)
            if len(parts) >= 3 and "node" in parts[2].lower():
                rows.append((int(parts[1]), line.strip()))
        for rss, line in sorted(rows, reverse=True)[:10]:
            if details:
                report(f"node_mb {rss / 1024:.1f} {line}")
            else:
                report(f"node_mb {rss / 1024:.1f} process=node")
    except Exception as exc:
        report(f"node_process_report_skipped {exc}")


def verify_sizes(codex_home: Path) -> None:
    for rel in ["sessions", "archived_sessions", "worktrees", "archived_worktrees", "archived_logs"]:
        path = codex_home / rel
        if path.exists():
            report(f"size_{rel}_gb {gb(size_bytes(path))}")


def maintenance_command(script: Path, codex_home: Path, args: argparse.Namespace, *extra: str) -> str:
    command = [
        "python3",
        str(script),
        "--codex-home",
        str(codex_home),
    ]
    if args.backup_root:
        command.extend(["--backup-root", str(Path(args.backup_root).expanduser())])
    command.extend(extra)
    return " ".join(shlex.quote(part) for part in command)


def render_runbook(codex_home: Path, backup_root: Path, args: argparse.Namespace) -> str:
    script = Path(__file__).resolve()
    report_cmd = maintenance_command(script, codex_home, args)
    backup_cmd = maintenance_command(script, codex_home, args, "--backup-only")
    apply_cmd = maintenance_command(
        script,
        codex_home,
        args,
        "--apply",
        "--archive-older-than-days",
        str(args.archive_older_than_days),
        "--worktree-older-than-days",
        str(args.worktree_older_than_days),
        "--rotate-logs-above-mb",
        str(args.rotate_logs_above_mb),
    )
    repair_cmd = maintenance_command(
        script,
        codex_home,
        args,
        "--repair-thread-metadata-only",
        "--thread-title-limit",
        str(args.thread_title_limit),
        "--thread-preview-limit",
        str(args.thread_preview_limit),
    )
    title_dry_run_cmd = maintenance_command(
        script,
        codex_home,
        args,
        "--repair-thread-titles-dry-run",
        "--thread-title-limit",
        str(args.thread_title_limit),
    )
    title_apply_cmd = maintenance_command(
        script,
        codex_home,
        args,
        "--repair-thread-titles-apply",
        "--confirm-thread-title-repair",
        TITLE_REPAIR_CONFIRM_PHRASE,
        "--thread-title-limit",
        str(args.thread_title_limit),
    )
    lines = [
        "Codex maintenance runbook",
        "mode_safety runbook_only=true state_writes=false",
        "",
        "1. Run report first while Codex is still available:",
        f"   {report_cmd}",
        "",
        "2. Review important active repo chats and create handoffs where needed.",
        "",
        "3. Quit Codex Desktop, Codex CLI sessions, and app-server processes using this Codex home.",
        "",
        "4. Create a backup-only checkpoint:",
        f"   {backup_cmd}",
        "",
        "5. Optional archive/log/config maintenance after explicit operator approval:",
        f"   {apply_cmd}",
        "",
        "6. Optional title-only repair: run dry-run before any apply:",
        f"   {title_dry_run_cmd}",
        "   Review thread_title_dry_run_needs_human before applying; "
        "needs_human means no safe existing session_index.jsonl thread_name "
        "was available, so the operator must choose a manual name outside this tool.",
        f"   {title_apply_cmd}",
        "   Title-only repair updates only eligible threads.title values; "
        "it does not rewrite preview, first_user_message, transcripts, "
        "or session_index.jsonl.",
        "",
        "7. Optional legacy metadata repair as a separate decision, not for title-only repair:",
        f"   {repair_cmd}",
        "",
        "8. Reopen Codex and verify with report:",
        f"   {report_cmd}",
        "",
        f"backup_root_hint {backup_root}",
        "Do not run optional commands until the operator approves that exact step.",
    ]
    return "\n".join(lines) + "\n"


def run_metadata_repair_only(
    conn: sqlite3.Connection,
    codex_home: Path,
    backup_root: Path,
    args: argparse.Namespace,
    *,
    effective_repair: bool,
) -> None:
    report_thread_metadata_bloat(
        conn,
        title_limit=args.thread_title_limit,
        preview_limit=args.thread_preview_limit,
    )
    repair_thread_metadata_bloat(
        conn,
        codex_home,
        backup_root,
        apply=effective_repair,
        details=args.details,
        title_limit=args.thread_title_limit,
        preview_limit=args.thread_preview_limit,
    )


def run(args: argparse.Namespace) -> int:
    codex_home = codex_home_from_args(args.codex_home)
    if not codex_home.exists():
        report(f"codex_home_missing {codex_home}")
        return 2

    stamp = now_stamp()
    backup_root = (
        Path(args.backup_root).expanduser()
        if args.backup_root
        else documents_backup_root() / f"keep-codex-fast-{stamp}"
    )
    backup_root = backup_root.resolve()

    if getattr(args, "runbook", False):
        print(render_runbook(codex_home, backup_root, args), end="")
        return 0

    if getattr(args, "repair_thread_titles_dry_run", False):
        report("requested_mode title-dry-run")
        report("effective_mode title-dry-run")
        report("mode_safety read_only=true privacy=pseudonymous title_only=true")
        state_db = codex_home / "state_5.sqlite"
        if state_db.exists():
            if sqlite_wal_may_have_uncheckpointed_content(state_db):
                report("thread_title_dry_run_blocked non_empty_wal_requires_checkpoint")
                report("thread_title_dry_run_writes false")
                report("done")
                return 3
            conn = sqlite_connect_immutable(state_db)
            conn.execute("pragma busy_timeout=10000")
            try:
                report_thread_title_dry_run(
                    conn,
                    codex_home,
                    details=args.details,
                    title_limit=args.thread_title_limit,
                )
            finally:
                conn.close()
        else:
            report("state_db_missing")
        report("done")
        return 0

    if getattr(args, "repair_thread_titles_apply", False):
        report("requested_mode title-apply")
        state_db = codex_home / "state_5.sqlite"
        if getattr(args, "confirm_thread_title_repair", "") != TITLE_REPAIR_CONFIRM_PHRASE:
            report("effective_mode report")
            report("thread_title_apply_refused confirmation_required")
            report(f"thread_title_apply_confirmation_phrase {TITLE_REPAIR_CONFIRM_PHRASE}")
            report("done")
            return 2
        active_probe = title_apply_active_state_probe(codex_home)
        if active_probe.reliable and active_probe.blocking_processes and args.wait_for_codex_exit:
            report("waiting_for_codex_exit")
            active_probe = wait_for_title_apply_safe_state(
                codex_home,
                timeout_seconds=getattr(args, "wait_timeout_seconds", 300),
            )
            if active_probe.blocking_processes:
                report("wait_for_codex_exit_timeout")
        if not active_probe.reliable:
            report("effective_mode report")
            report(f"thread_title_apply_blocked {active_probe.blocked_reason or 'process_probe_unreliable'}")
            report("done")
            return 3
        if active_probe.blocking_processes:
            report("effective_mode report")
            report("thread_title_apply_skipped_codex_running")
            for index, proc in enumerate(active_probe.blocking_processes, start=1):
                if args.details:
                    report(f"blocking_process {proc}")
                else:
                    report(f"blocking_process codex_process_{index:03d}")
            report("done")
            return 3
        if not state_db.exists():
            report("effective_mode report")
            report("state_db_missing")
            report("done")
            return 2
        if sqlite_wal_may_have_uncheckpointed_content(state_db):
            report("effective_mode report")
            report("thread_title_apply_blocked non_empty_wal_requires_checkpoint")
            report("done")
            return 3

        report("effective_mode title-apply")
        report("mode_safety backup_first=true title_only=true archive_prune_rotate=false")
        if args.details:
            report(f"codex_home {codex_home}")
            report(f"backup_root {backup_root}")
        else:
            report(f"backup_root {backup_root}")
        backup_metadata(codex_home, backup_root)
        post_backup_probe = title_apply_active_state_probe(codex_home)
        if not post_backup_probe.reliable:
            reason = post_backup_probe.blocked_reason or "process_probe_unreliable"
            report(f"thread_title_apply_blocked post_backup_{reason}")
            report("done")
            return 3
        if post_backup_probe.blocking_processes:
            report("thread_title_apply_skipped_post_backup_codex_running")
            for index, proc in enumerate(post_backup_probe.blocking_processes, start=1):
                if args.details:
                    report(f"blocking_process {proc}")
                else:
                    report(f"blocking_process codex_process_{index:03d}")
            report("done")
            return 3
        if sqlite_wal_may_have_uncheckpointed_content(state_db):
            report("thread_title_apply_blocked post_backup_non_empty_wal_requires_checkpoint")
            report("done")
            return 3
        conn = sqlite_connect(state_db, readonly=False)
        conn.execute("pragma busy_timeout=10000")
        try:
            result = apply_thread_title_repairs(
                conn,
                codex_home,
                backup_root,
                details=args.details,
                title_limit=args.thread_title_limit,
            )
            try:
                conn.execute("pragma wal_checkpoint(truncate)")
            except Exception as exc:
                report(f"wal_checkpoint_skipped {exc}")
        finally:
            conn.close()
        report("done")
        return result

    running = codex_processes_running(codex_home)
    repair_only_requested = bool(getattr(args, "repair_thread_metadata_only", False))
    mutating_requested = bool(args.apply or repair_only_requested)
    if mutating_requested and running and args.wait_for_codex_exit:
        report("waiting_for_codex_exit")
        running = wait_for_codex_exit(
            codex_home,
            timeout_seconds=getattr(args, "wait_timeout_seconds", 300),
        )
        if running:
            report("wait_for_codex_exit_timeout")

    effective_apply = bool(args.apply and not running)
    effective_repair_only = bool(repair_only_requested and not running)
    effective_backup = bool(effective_apply or effective_repair_only or args.backup_only)
    requested_mode = (
        "metadata-repair-only"
        if repair_only_requested
        else "apply"
        if args.apply
        else "backup-only"
        if args.backup_only
        else "report"
    )
    effective_mode = (
        "metadata-repair-only"
        if effective_repair_only
        else "apply"
        if effective_apply
        else "backup-only"
        if effective_backup
        else "report"
    )
    if args.details:
        report(f"codex_home {codex_home}")
        if effective_backup:
            report(f"backup_root {backup_root}")
    elif effective_backup:
        report(f"backup_root {backup_root}")
    report(f"requested_mode {requested_mode}")
    report(f"effective_mode {effective_mode}")
    if effective_mode == "report":
        report("mode_safety read_only=true privacy=pseudonymous")
    elif effective_mode == "backup-only":
        report("mode_safety backup_only=true archives=false state_writes=false")
    elif effective_mode == "metadata-repair-only":
        report("mode_safety backup_first=true metadata_repair_only=true archive_prune_rotate=false")
    else:
        report("mode_safety backup_first=true archive_only=true permanent_delete=false")
    if mutating_requested and running:
        if repair_only_requested:
            report("metadata_repair_only_skipped_codex_running")
        if args.apply:
            report("apply_skipped_codex_running")
        for index, proc in enumerate(running, start=1):
            if args.details:
                report(f"blocking_process {proc}")
            else:
                report(f"blocking_process codex_process_{index:03d}")

    if effective_backup:
        backup_metadata(codex_home, backup_root)

    state_db = codex_home / "state_5.sqlite"
    if state_db.exists():
        conn = sqlite_connect(state_db, readonly=not (effective_apply or effective_repair_only))
        conn.execute("pragma busy_timeout=10000")
        if repair_only_requested:
            run_metadata_repair_only(
                conn,
                codex_home,
                backup_root,
                args,
                effective_repair=effective_repair_only,
            )
        else:
            normalize_sqlite_paths(conn, effective_apply)
            report_thread_metadata_bloat(
                conn,
                title_limit=args.thread_title_limit,
                preview_limit=args.thread_preview_limit,
            )
            repair_thread_metadata_bloat(
                conn,
                codex_home,
                backup_root,
                apply=effective_apply and args.repair_thread_metadata_bloat,
                details=args.details,
                title_limit=args.thread_title_limit,
                preview_limit=args.thread_preview_limit,
            )
            candidates = active_session_candidates(conn, codex_home, args.archive_older_than_days)
            archive_sessions(conn, candidates, codex_home, backup_root, stamp, effective_apply, args.details)
        if effective_apply or effective_repair_only:
            conn.commit()
            try:
                conn.execute("pragma wal_checkpoint(truncate)")
            except Exception as exc:
                report(f"wal_checkpoint_skipped {exc}")
            try:
                conn.execute("pragma optimize")
            except Exception as exc:
                report(f"sqlite_optimize_skipped {exc}")
        conn.close()
    else:
        report("state_db_missing")

    if not repair_only_requested:
        prune_config(codex_home, backup_root, effective_apply, effective_backup)
        move_stale_worktrees(codex_home, backup_root, args.worktree_older_than_days, stamp, effective_apply)
        rotate_logs(codex_home, args.rotate_logs_above_mb, stamp, effective_apply)
    verify_sizes(codex_home)
    top_node_processes(args.details)
    report("done")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safe, backup-first, archive-only Codex local-state maintenance."
    )
    parser.add_argument("--runbook", action="store_true", help="Print an operator runbook and exit without writes.")
    parser.add_argument("--apply", action="store_true", help="Apply maintenance actions. Default is report-only.")
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Create backups without applying maintenance actions. Default report mode writes no files.",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Include raw thread IDs, titles, paths, and process paths in output.",
    )
    parser.add_argument(
        "--wait-for-codex-exit",
        action="store_true",
        help="Wait until Codex releases the state database before applying.",
    )
    parser.add_argument(
        "--wait-timeout-seconds",
        type=int,
        default=300,
        help="Maximum seconds to wait with --wait-for-codex-exit.",
    )
    parser.add_argument("--codex-home", help="Override Codex home. Defaults to CODEX_HOME or ~/.codex.")
    parser.add_argument("--backup-root", help="Override backup output folder.")
    parser.add_argument("--archive-older-than-days", type=int, default=10)
    parser.add_argument("--worktree-older-than-days", type=int, default=7)
    parser.add_argument("--rotate-logs-above-mb", type=int, default=64)
    parser.add_argument(
        "--thread-title-limit",
        type=int,
        default=DEFAULT_TITLE_LIMIT,
        help="Title length threshold for metadata-bloat reporting and optional repair.",
    )
    parser.add_argument(
        "--thread-preview-limit",
        type=int,
        default=DEFAULT_PREVIEW_LIMIT,
        help="Preview length threshold for metadata-bloat reporting and optional repair.",
    )
    parser.add_argument(
        "--repair-thread-metadata-bloat",
        action="store_true",
        help=(
            "Legacy combined repair flag: with --apply, compact oversized thread "
            "title/first_user_message metadata. Title-only repair is separate; "
            "use --repair-thread-titles-dry-run then --repair-thread-titles-apply."
        ),
    )
    parser.add_argument(
        "--repair-thread-metadata-only",
        action="store_true",
        help=(
            "Backup and run the legacy combined metadata repair only; do not "
            "archive, prune, move, or rotate. Title-only repair is separate and "
            "uses --repair-thread-titles-dry-run for read-only classification."
        ),
    )
    parser.add_argument(
        "--repair-thread-titles-dry-run",
        action="store_true",
        help=(
            "Read-only title-only repair classifier. Writes no files, reports "
            "safe_name_available and needs_human, and is separate from legacy "
            "metadata repair."
        ),
    )
    parser.add_argument(
        "--repair-thread-titles-apply",
        action="store_true",
        help=(
            "Backup-first title-only repair apply path for eligible threads.title "
            "values only. Requires --confirm-thread-title-repair and is separate "
            "from normal apply and legacy metadata repair."
        ),
    )
    parser.add_argument(
        "--confirm-thread-title-repair",
        default="",
        help="Required confirmation phrase for --repair-thread-titles-apply.",
    )
    args = parser.parse_args(argv)
    if args.apply and args.backup_only:
        parser.error("--apply and --backup-only cannot be used together")
    if args.runbook and (
        args.apply
        or args.backup_only
        or args.repair_thread_metadata_bloat
        or args.repair_thread_metadata_only
        or args.repair_thread_titles_dry_run
        or args.repair_thread_titles_apply
        or args.confirm_thread_title_repair
    ):
        parser.error("--runbook cannot be combined with mutating or backup modes")
    if args.repair_thread_titles_dry_run and (
        args.apply
        or args.backup_only
        or args.repair_thread_metadata_bloat
        or args.repair_thread_metadata_only
        or args.repair_thread_titles_apply
    ):
        parser.error("--repair-thread-titles-dry-run cannot be combined with mutating or legacy repair modes")
    if args.repair_thread_titles_apply and (
        args.apply
        or args.backup_only
        or args.repair_thread_metadata_bloat
        or args.repair_thread_metadata_only
    ):
        parser.error("--repair-thread-titles-apply cannot be combined with normal apply, backup-only, or legacy repair modes")
    if args.confirm_thread_title_repair and not args.repair_thread_titles_apply:
        parser.error("--confirm-thread-title-repair is only valid with --repair-thread-titles-apply")
    if args.repair_thread_metadata_only and (
        args.apply
        or args.backup_only
        or args.repair_thread_metadata_bloat
    ):
        parser.error("--repair-thread-metadata-only cannot be combined with apply, backup-only, or repair flag")
    if args.thread_title_limit < 20:
        parser.error("--thread-title-limit must be at least 20")
    if (
        not args.repair_thread_titles_dry_run
        and not args.repair_thread_titles_apply
        and args.thread_preview_limit < args.thread_title_limit
    ):
        parser.error("--thread-preview-limit must be greater than or equal to --thread-title-limit")
    return args


if __name__ == "__main__":
    raise SystemExit(run(parse_args(sys.argv[1:])))
