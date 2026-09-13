"""Small, local proof harnesses for promoted Cursor mirror boundaries.

These helpers do not activate Cursor, cloud, connector, or marketplace
surfaces. They exercise isolated playbook and verification fixtures while
keeping missing capabilities and failed proof states explicit.
"""

from __future__ import annotations

import difflib
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


class AdapterError(ValueError):
    """The bounded adapter input or proof state is invalid."""


class MissingCapability(AdapterError):
    """A required optional capability is not available."""


class PermissionDenied(AdapterError):
    """The requested operation exceeds the read-only adapter boundary."""


@dataclass(frozen=True)
class CapabilityResult:
    status: str
    missing: tuple[str, ...] = ()
    fallback: str = ""


PSTACK_PLAYBOOK_FILES = (
    "authoring-a-skill",
    "autonomous-run",
    "autopilot-full",
    "autopilot-stack",
    "babysit",
    "bug-fix",
    "eval",
    "feature",
    "hillclimb",
    "investigation",
    "multi-phase-plan",
    "opening-a-pr",
    "orchestrate",
    "pause-safely",
    "perf-issue",
    "prototype",
    "refactoring",
    "runtime-forensics",
    "session-pickup",
    "shipping",
    "trace-forensics",
    "visual-parity",
    "worktree-cleanup",
)
BUG_FIX_COMPLETED_STEPS = (1, 4, 5)
BUG_FIX_PARTIAL_STEPS = (2, 3, 6)
PSTACK_FIXTURE_MARKER = ".pstack-disposable-fixture"
PSTACK_FIXTURE_MARKER_CONTENT = "pstack-local-bug-fix-fixture-v1\n"


def read_pstack_playbook_fixture(
    playbook_root: str | Path,
    playbook: str,
    *,
    available_capabilities: Iterable[str] = ("local skill reader",),
    required_capabilities: Iterable[str] = (),
) -> dict[str, object]:
    """Read one exact playbook file structurally in a read-only fixture.

    The fixture records headings and ordered entries from the selected file.
    It does not apply contextual steps, run bundled commands, start a cloud
    task, or claim live playbook behavior.
    """

    if playbook not in PSTACK_PLAYBOOK_FILES:
        raise AdapterError(f"unknown pstack playbook: {playbook}")
    root = Path(playbook_root)
    path = root / f"{playbook}.md"
    if not path.is_file():
        return {
            "status": "FALLBACK",
            "playbook": playbook,
            "reason": "selected playbook file is missing; use sequential native steps",
            "external_writes": False,
        }
    if path.is_symlink():
        raise AdapterError("playbook fixture must not be a symlink")
    text = path.read_text()
    if not text.strip():
        return {
            "status": "ERROR",
            "playbook": playbook,
            "reason": "selected playbook fixture is empty",
            "external_writes": False,
        }
    capability_result = resolve_capabilities(
        required_capabilities,
        available_capabilities,
        "use sequential native steps",
    )
    if capability_result.status == "FALLBACK":
        return {
            "status": "FALLBACK",
            "playbook": playbook,
            "missing": capability_result.missing,
            "reason": capability_result.fallback,
            "external_writes": False,
        }
    entries = tuple(
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("#")
        or (len(line.strip()) > 2 and line.strip()[0].isdigit() and line.strip()[1:3] == ". ")
    )
    if not entries:
        return {
            "status": "ERROR",
            "playbook": playbook,
            "reason": "selected playbook fixture has no bounded sections",
            "external_writes": False,
        }
    return {
        "status": "READ",
        "playbook": playbook,
        "path": str(path),
        "entries": entries,
        "environment": "isolated-read-only-fixture",
        "external_writes": False,
    }


def _validate_fixture_component(value: str, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
    ):
        raise AdapterError(f"{label} must be a single non-empty path component")


def _reject_symlink_components(root: Path, relative: Path) -> None:
    if root.is_symlink():
        raise AdapterError("verification fixture project root must not be a symlink")
    current = root
    for component in relative.parts:
        current /= component
        if current.is_symlink():
            raise AdapterError("verification fixture path must not contain symlinks")


def run_verification_fixture(
    project_root: str | Path,
    app_name: str,
    features: Mapping[str, str],
    *,
    app_available: bool,
    observed_features: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Create and exercise a project-local verification fixture.

    The fixture writes only a temporary `.agents/skills/verify-<app>/` tree,
    reconciles its feature files, and compares supplied observations. The
    observations stand in for an app conduct pass; no real application is
    started and no product or external state is changed.
    """

    _validate_fixture_component(app_name, "app_name")
    if not features:
        raise AdapterError("verification fixture needs at least one feature")
    for name, body in features.items():
        _validate_fixture_component(name, "feature name")
        if not isinstance(body, str) or not body.strip():
            raise AdapterError("feature fixture content must be non-empty text")

    root_path = Path(project_root)
    if root_path.is_symlink():
        raise AdapterError("verification fixture project root must not be a symlink")
    root = root_path.resolve()
    target = root / ".agents" / "skills" / f"verify-{app_name}"
    _reject_symlink_components(root, target.relative_to(root))
    if target.exists() and not target.is_dir():
        raise AdapterError("verification target is not a directory")
    target.mkdir(parents=True, exist_ok=True)
    features_dir = target / "features"
    _reject_symlink_components(root, features_dir.relative_to(root))
    features_dir.mkdir(exist_ok=True)
    skill_path = target / "SKILL.md"
    if skill_path.is_symlink():
        raise AdapterError("verification fixture file must not be a symlink")
    skill_path.write_text(
        f"---\nname: verify-{app_name}\n---\n\n"
        "This is an isolated verification fixture.\n"
    )
    for name, body in features.items():
        feature_path = features_dir / f"{name}.md"
        if feature_path.is_symlink():
            raise AdapterError("verification fixture file must not be a symlink")
        feature_path.write_text(body)

    expected = tuple(sorted(features))
    actual = tuple(sorted(path.stem for path in features_dir.glob("*.md")))
    if actual != expected:
        return {
            "status": "ERROR",
            "target": str(target),
            "reason": "feature file reconciliation mismatch",
            "expected_features": expected,
            "actual_features": actual,
            "product_edits": False,
        }
    result: dict[str, object] = {
        "target": str(target),
        "created_skill": True,
        "reconciled_features": actual,
        "product_edits": False,
        "external_writes": False,
        "environment": "isolated-project-fixture",
    }
    if not app_available:
        result.update(
            {
                "status": "BLOCKED",
                "reason": "verification app is unavailable",
                "fixture_observations": (),
            }
        )
        return result
    if observed_features is None:
        result.update(
            {
                "status": "BLOCKED",
                "reason": "verification observations are missing",
                "fixture_observations": (),
            }
        )
        return result
    observed = tuple(sorted(observed_features))
    if dict(observed_features) != dict(features):
        result.update(
            {
                "status": "ERROR",
                "reason": "observed feature results do not match the reconciled map",
                "fixture_observations": observed,
            }
        )
        return result
    result.update(
        {
            "status": "FIXTURE_ONLY",
            "fixture_observations": observed,
        }
    )
    return result


def _process_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _resolve_local_app_fixture(
    project_root: str | Path, app_path: str | Path
) -> tuple[Path, Path]:
    root_path = Path(project_root)
    if root_path.is_symlink():
        raise AdapterError("local app fixture project root must not be a symlink")
    root = root_path.resolve()
    if not root.is_dir():
        raise AdapterError("local app fixture project root must be a directory")

    candidate = Path(app_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    if candidate.is_symlink():
        raise AdapterError("local app fixture must not be a symlink")
    try:
        relative = candidate.resolve().relative_to(root)
    except ValueError as exc:
        raise AdapterError("local app fixture must stay inside the project root") from exc
    _reject_symlink_components(root, relative)
    app = candidate.resolve()
    if app.suffix != ".py" or not app.is_file():
        raise AdapterError("local app fixture must be a regular Python file")
    return root, app


def run_local_app_fixture(
    project_root: str | Path,
    app_path: str | Path,
    arguments: Iterable[str],
    *,
    expected_stdout: str,
    expected_exit_code: int = 0,
    timeout_seconds: float = 2.0,
) -> dict[str, object]:
    """Run one local Python app fixture and compare independently captured evidence.

    The runner is intentionally narrower than a generic command adapter: it
    accepts only a regular Python file under a non-symlink project root,
    invokes it through the current interpreter with ``shell=False``, closes
    stdin and strips inherited environment variables. Tests supply a local
    fixture app, not a live product, cloud task, or bundled pstack helper.
    This runner is not a security sandbox: filesystem writes and network
    access by the supplied app are not observed or prevented. The proof claim
    is limited to captured output and exit status.
    """

    root, app = _resolve_local_app_fixture(project_root, app_path)

    if isinstance(arguments, (str, bytes)):
        raise AdapterError("local app fixture arguments must be an iterable of strings")
    argv = tuple(arguments)
    if any(not isinstance(item, str) or "\x00" in item for item in argv):
        raise AdapterError("local app fixture arguments must be NUL-free strings")
    if not isinstance(expected_stdout, str) or "\x00" in expected_stdout:
        raise AdapterError("expected_stdout must be NUL-free text")
    if not isinstance(expected_exit_code, int) or isinstance(expected_exit_code, bool):
        raise AdapterError("expected_exit_code must be an integer")
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
        raise AdapterError("timeout_seconds must be a positive number")
    if timeout_seconds <= 0:
        raise AdapterError("timeout_seconds must be a positive number")

    command = (sys.executable, str(app), *argv)
    isolated_environment = {
        "PATH": str(Path(sys.executable).parent),
        "PYTHONIOENCODING": "utf-8",
    }
    try:
        completed = subprocess.run(
            command,
            cwd=str(root),
            env=isolated_environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            shell=False,
            timeout=float(timeout_seconds),
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "TIMEOUT",
            "app": str(app),
            "arguments": argv,
            "evidence": {
                "exit_code": None,
                "stdout": _process_output(exc.stdout),
                "stderr": _process_output(exc.stderr),
            },
            "expected": {
                "exit_code": expected_exit_code,
                "stdout": expected_stdout,
            },
            "environment": "local-app-fixture-process",
            "evidence_scope": ("exit_code", "stdout", "stderr"),
            "filesystem_isolation": "not_observed",
            "network_isolation": "not_observed",
        }

    evidence = {
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    expected = {
        "exit_code": expected_exit_code,
        "stdout": expected_stdout,
    }
    return {
        "status": "PASS"
        if completed.returncode == expected_exit_code
        and completed.stdout == expected_stdout
        else "FAIL",
        "app": str(app),
        "arguments": argv,
        "evidence": evidence,
        "expected": expected,
        "environment": "local-app-fixture-process",
        "evidence_scope": ("exit_code", "stdout", "stderr"),
        "filesystem_isolation": "not_observed",
        "network_isolation": "not_observed",
    }


def _run_local_git(root: Path, arguments: Iterable[str]) -> str:
    executable = shutil.which("git")
    if executable is None:
        raise MissingCapability("git is unavailable for local history proof")
    argv = tuple(arguments)
    if any(not isinstance(item, str) or "\x00" in item for item in argv):
        raise AdapterError("local git fixture arguments must be NUL-free strings")
    environment = {
        "HOME": str(root / ".git-home"),
        "PATH": str(Path(executable).parent),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
    }
    (root / ".git-home").mkdir(exist_ok=True)
    try:
        completed = subprocess.run(
            (executable, "-C", str(root), *argv),
            cwd=str(root),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            shell=False,
            timeout=5.0,
        )
    except subprocess.TimeoutExpired as exc:
        raise MissingCapability("local git fixture command timed out") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise AdapterError(
            f"local git fixture command failed ({completed.returncode}): {detail}"
        )
    return completed.stdout


def _record_local_bug_fix_history(
    root: Path, app: Path, buggy_source: str, corrected_source: str
) -> dict[str, object]:
    marker = root / PSTACK_FIXTURE_MARKER
    if marker.is_symlink() or not marker.is_file():
        raise AdapterError(
            "local bug-fix history requires an explicit disposable fixture marker"
        )
    if marker.read_text() != PSTACK_FIXTURE_MARKER_CONTENT:
        raise AdapterError("local bug-fix fixture marker has unexpected content")
    if (root / ".git").exists():
        raise AdapterError("local bug-fix history fixture must start without .git")
    try:
        relative_app = app.relative_to(root)
    except ValueError as exc:
        raise AdapterError("fixture app must be inside the disposable fixture root") from exc
    allowed_root_entries = {
        PSTACK_FIXTURE_MARKER,
        relative_app.parts[0],
        "notes.json",
        "staging",
    }
    unexpected_entries = sorted(
        entry.name for entry in root.iterdir() if entry.name not in allowed_root_entries
    )
    if unexpected_entries:
        raise AdapterError(
            "local bug-fix fixture root has unexpected entries: "
            + ", ".join(unexpected_entries)
        )
    if app.read_text() != buggy_source:
        raise AdapterError("fixture app changed before local reproduction commit")
    relative_app = str(relative_app)
    _run_local_git(root, ("init", "--quiet"))
    _run_local_git(root, ("add", "--", relative_app))
    _run_local_git(
        root,
        (
            "-c",
            "user.name=pstack fixture",
            "-c",
            "user.email=pstack-fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "test(pstack): reproduce notes search failure",
        ),
    )
    reproduction_commit = _run_local_git(root, ("log", "-1", "--format=%H")).strip()
    before_hash = hashlib.sha256(app.read_bytes()).hexdigest()

    app.write_text(corrected_source)
    after_hash = hashlib.sha256(app.read_bytes()).hexdigest()
    _run_local_git(root, ("add", "--", relative_app))
    _run_local_git(
        root,
        (
            "-c",
            "user.name=pstack fixture",
            "-c",
            "user.email=pstack-fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "fix(pstack): normalize notes search",
        ),
    )
    correction_commit = _run_local_git(root, ("log", "-1", "--format=%H")).strip()
    subjects = tuple(
        line.strip()
        for line in _run_local_git(root, ("log", "-2", "--format=%s")).splitlines()
        if line.strip()
    )

    with tempfile.TemporaryDirectory(prefix="pstack-pr-remote-") as remote_dir:
        remote = Path(remote_dir)
        _run_local_git(root, ("init", "--bare", "--quiet", str(remote)))
        _run_local_git(root, ("remote", "add", "fixture-remote", str(remote)))
        _run_local_git(
            root,
            ("push", "--quiet", "fixture-remote", "HEAD:refs/heads/fix/notes-search"),
        )
        remote_head = _run_local_git(
            root,
            ("ls-remote", "fixture-remote", "refs/heads/fix/notes-search"),
        ).split()[0]

    return {
        "status": "LOCAL_ONLY",
        "reproduction_commit": reproduction_commit,
        "correction_commit": correction_commit,
        "subjects_newest_first": subjects,
        "source_before_sha256": before_hash,
        "source_after_sha256": after_hash,
        "pr_simulation": {
            "status": "SIMULATED_ONLY",
            "remote_kind": "temporary local bare git remote",
            "branch": "fix/notes-search",
            "remote_head": remote_head,
            "external_publish": False,
            "real_pr": False,
        },
    }


def run_bug_fix_playbook_fixture(
    playbook_root: str | Path,
    project_root: str | Path,
    app_path: str | Path,
    *,
    buggy_source: str,
    corrected_source: str,
) -> dict[str, object]:
    """Execute contextual bug-fix steps against the synthetic notes app.

    The exact ``bug-fix`` playbook is read first, then the fixture performs a
    create/baseline search, reproduces a case-sensitive search failure, and
    runs a trace command that supplies the observable mechanism. It records a
    bounded hypothesis cut, a plan and diff review, commits the reproduction
    before writing the supplied prewritten correction, pushes only to a
    temporary local bare remote, and repeats the search. The correction is not
    generated by this playbook adapter. Each app step is checked from
    independently captured process evidence. The result is always fixture-only;
    this does not drive a live application or execute any bundled pstack
    helper.
    """

    playbook_read = read_pstack_playbook_fixture(playbook_root, "bug-fix")
    if playbook_read["status"] != "READ":
        return {
            "status": playbook_read["status"],
            "playbook": "bug-fix",
            "playbook_read": playbook_read,
            "playbook_step_scope": {
                "completed": (),
                "partial": (),
                "unexercised": (1, 2, 3, 4, 5, 6),
            },
            "evidence_scope": (),
            "filesystem_isolation": "not_observed",
            "network_isolation": "not_observed",
        }
    if not isinstance(buggy_source, str) or not buggy_source.strip():
        raise AdapterError("buggy_source must be non-empty text")
    if not isinstance(corrected_source, str) or not corrected_source.strip():
        raise AdapterError("corrected_source must be non-empty text")
    if buggy_source == corrected_source:
        raise AdapterError("buggy_source and corrected_source must differ")

    root, app = _resolve_local_app_fixture(project_root, app_path)
    if app.read_text() != buggy_source:
        raise AdapterError("fixture app does not contain the supplied buggy source")
    before_create = run_local_app_fixture(
        root,
        app,
        ("create", "Release checklist", "Tag and publish"),
        expected_stdout="created:Release checklist\n",
    )
    before_search = run_local_app_fixture(
        root,
        app,
        ("search", "Release"),
        expected_stdout="found:Release checklist\n",
    )
    before = {
        "status": "PASS"
        if before_create["status"] == "PASS" and before_search["status"] == "PASS"
        else "FAIL",
        "create": before_create,
        "search": before_search,
    }
    failure = run_local_app_fixture(
        root,
        app,
        ("search", "release"),
        expected_stdout="found:Release checklist\n",
    )
    expected_failure = {
        "exit_code": 1,
        "stdout": "not-found\n",
        "stderr": "",
    }
    if failure["status"] != "FAIL" or failure["evidence"] != expected_failure:
        return {
            "status": "ERROR",
            "playbook": "bug-fix",
            "playbook_read": playbook_read,
            "before": before,
            "failure": failure,
            "diagnosis": {"status": "NOT_RUN"},
            "plan": {"status": "NOT_RUN"},
            "correction": {
                "status": "NOT_RUN",
                "reason": "bug-specific failure evidence did not match",
            },
            "after": {"status": "NOT_RUN"},
            "local_history": {"status": "NOT_RUN"},
            "playbook_step_scope": {
                "completed": (1,),
                "partial": (),
                "unexercised": (2, 3, 4, 5, 6),
            },
            "evidence_scope": ("exit_code", "stdout", "stderr"),
            "environment": "local-notes-bug-fix-fixture",
            "filesystem_isolation": "not_observed",
            "network_isolation": "not_observed",
        }

    diagnostic = run_local_app_fixture(
        root,
        app,
        ("trace-search", "release"),
        expected_stdout=(
            "trace:query=release;title=Release checklist;"
            "comparison=case-sensitive;matched=false\n"
        ),
    )
    if before["status"] != "PASS" or diagnostic["status"] != "PASS":
        return {
            "status": "ERROR",
            "playbook": "bug-fix",
            "playbook_read": playbook_read,
            "before": before,
            "failure": failure,
            "diagnosis": {
                "status": "NOT_CONFIRMED",
                "evidence": diagnostic["evidence"],
                "reason": "observable diagnosis did not match the case-sensitive mechanism",
            },
            "plan": {"status": "NOT_RUN"},
            "correction": {"status": "NOT_RUN"},
            "after": {"status": "NOT_RUN"},
            "local_history": {"status": "NOT_RUN"},
            "playbook_step_scope": {
                "completed": (1,),
                "partial": (2,),
                "unexercised": (3, 4, 5, 6),
            },
            "evidence_scope": ("exit_code", "stdout", "stderr"),
            "environment": "local-notes-bug-fix-fixture",
            "filesystem_isolation": "not_observed",
            "network_isolation": "not_observed",
        }

    diagnosis = {
        "status": "HYPOTHESIS_SUPPORTED",
        "candidate_hypotheses": ("missing note data", "case-sensitive search predicate"),
        "surviving_hypothesis": "case-sensitive search predicate",
        "mechanism": "lower-case query is compared without normalizing the stored title",
        "observed": {
            "baseline": before_search["evidence"],
            "failure": failure["evidence"],
            "trace": diagnostic["evidence"],
        },
    }
    diff_text = "".join(
        difflib.unified_diff(
            buggy_source.splitlines(keepends=True),
            corrected_source.splitlines(keepends=True),
            fromfile="app.py (reproduction)",
            tofile="app.py (prewritten correction)",
        )
    )
    plan = {
        "status": "PLAN_RECORDED",
        "hypothesis": diagnosis["surviving_hypothesis"],
        "change": "normalize query and stored title with casefold before membership",
        "diff": diff_text,
        "review": {
            "status": "DIFF_RECORDED",
            "scope": "single search predicate",
            "source": "prewritten correction supplied by fixture caller",
            "mode": "structural_only",
            "delegation": "NOT_RUN",
        },
    }
    try:
        local_history = _record_local_bug_fix_history(
            root,
            app,
            buggy_source,
            corrected_source,
        )
    except (AdapterError, MissingCapability) as exc:
        return {
            "status": "ERROR",
            "playbook": "bug-fix",
            "playbook_read": playbook_read,
            "before": before,
            "failure": failure,
            "diagnosis": diagnosis,
            "plan": plan,
            "correction": {
                "status": "NOT_RUN",
                "reason": f"local history proof unavailable: {exc}",
            },
            "after": {"status": "NOT_RUN"},
            "local_history": {"status": "BLOCKED", "reason": str(exc)},
            "playbook_step_scope": {
                "completed": (1,),
                "partial": (2, 3),
                "unexercised": (4, 5, 6),
            },
            "evidence_scope": ("exit_code", "stdout", "stderr"),
            "environment": "local-notes-bug-fix-fixture",
            "filesystem_isolation": "not_observed",
            "network_isolation": "not_observed",
        }
    correction = {
        "status": "CORRECTED"
        if local_history["source_before_sha256"] != local_history["source_after_sha256"]
        else "ERROR",
        "source": "prewritten correction supplied by fixture caller",
        "source_before_sha256": local_history["source_before_sha256"],
        "source_after_sha256": local_history["source_after_sha256"],
        "changed": local_history["source_before_sha256"]
        != local_history["source_after_sha256"],
    }
    after = run_local_app_fixture(
        root,
        app,
        ("search", "release"),
        expected_stdout="found:Release checklist\n",
    )
    successful = (
        before["status"] == "PASS"
        and failure["status"] == "FAIL"
        and diagnosis["status"] == "HYPOTHESIS_SUPPORTED"
        and plan["status"] == "PLAN_RECORDED"
        and plan["review"]["status"] == "DIFF_RECORDED"
        and local_history["status"] == "LOCAL_ONLY"
        and correction["status"] == "CORRECTED"
        and after["status"] == "PASS"
    )
    return {
        "status": "FIXTURE_ONLY" if successful else "ERROR",
        "playbook": "bug-fix",
        "playbook_read": playbook_read,
        "before": before,
        "failure": failure,
        "diagnosis": diagnosis,
        "plan": plan,
        "correction": correction,
        "after": after,
        "local_history": local_history,
        "playbook_step_scope": {
            "completed": BUG_FIX_COMPLETED_STEPS,
            "partial": BUG_FIX_PARTIAL_STEPS,
            "unexercised": (),
        },
        "contextual_steps": (
            "create note",
            "baseline exact-case search",
            "reproduce lower-case search failure",
            "trace observable search mechanism",
            "record hypothesis cut and review prewritten correction diff",
            "commit reproduction before correction",
            "write prewritten corrected fixture source and commit correction",
            "push to temporary local bare remote as PR simulation",
            "repeat lower-case search",
        ),
        "evidence_scope": ("exit_code", "stdout", "stderr"),
        "environment": "local-notes-bug-fix-fixture",
        "filesystem_isolation": "not_observed",
        "network_isolation": "not_observed",
    }


def select_verification_target(
    candidates: Iterable[str], *, requested: str | None = None
) -> dict[str, object]:
    """Select one project-local verification target without widening edit scope."""

    unique = tuple(dict.fromkeys(item for item in candidates if item))
    if requested:
        if requested not in unique:
            return {
                "status": "BLOCKED",
                "reason": "requested verification skill is not present",
            }
        return {"status": "READY", "target": requested}
    if not unique:
        return {"status": "BLOCKED", "reason": "no verification skill target exists"}
    if len(unique) > 1:
        return {"status": "NEEDS_INPUT", "candidates": unique}
    return {"status": "READY", "target": unique[0]}


def resolve_capabilities(
    required: Iterable[str], available: Iterable[str], fallback: str
) -> CapabilityResult:
    """Return a native path or an explicit fallback for missing capabilities."""

    required_set = {item for item in required if item}
    available_set = {item for item in available if item}
    missing = tuple(sorted(required_set - available_set))
    if missing:
        if not fallback.strip():
            raise MissingCapability("missing capabilities without a fallback")
        return CapabilityResult("FALLBACK", missing, fallback)
    return CapabilityResult("NATIVE")


def prove_rerunnable(first_output: str, second_output: str) -> dict[str, str]:
    """Prove that a lever returns the same output twice."""

    if not first_output or not second_output:
        raise AdapterError("lever output is empty")
    if first_output != second_output:
        raise AdapterError("lever output changed between identical runs")
    return {"status": "VERIFIED", "comparison": "identical"}


def bound_context(
    items: list[str], max_items: int, required_anchors: Iterable[str] = ()
) -> dict[str, object]:
    """Keep a context slice bounded while retaining named anchors when present."""

    if max_items < 1:
        raise AdapterError("max_items must be positive")
    anchors = [item for item in required_anchors if item in items]
    selected = list(dict.fromkeys(anchors + items))[:max_items]
    omitted = len(items) - len(selected)
    return {"status": "BOUNDED", "items": selected, "omitted": max(0, omitted)}


def choose_smallest(
    original: str, candidate: str, *, tests_pass: bool, deletion_safe: bool
) -> dict[str, str]:
    """Choose the smallest safe change, or preserve the original."""

    if not original or not candidate:
        raise AdapterError("change candidates must be non-empty")
    if not tests_pass or not deletion_safe:
        return {"status": "PRESERVED", "value": original}
    value = candidate if len(candidate) <= len(original) else original
    return {"status": "SMALLEST_SAFE", "value": value}


def verify_readback(expected: str, actual: str | None, *, runtime_available: bool) -> dict[str, str]:
    """Verify the value read from the real path, never a compile-only proxy."""

    if not runtime_available:
        return {"status": "NOT VERIFIED", "reason": "runtime unavailable"}
    if actual is None:
        raise AdapterError("real readback is missing")
    if expected != actual:
        return {"status": "NOT VERIFIED", "reason": "readback mismatch"}
    return {"status": "VERIFIED", "reason": "real readback matches"}


def review_prose(text: str, *, unslop_available: bool) -> dict[str, object]:
    """Run the bounded, instruction-only technical-writing checks."""

    if not text.strip():
        raise AdapterError("prose is empty")
    sentences = [part.strip() for part in text.split(".") if part.strip()]
    issues = []
    if any(word in text.lower().split() for word in ("simply", "utilize")):
        issues.append("replace filler or long synonym")
    if any(" should be " in f" {sentence.lower()} " for sentence in sentences):
        issues.append("use an active instruction")
    result = {"status": "PASS" if not issues else "ISSUES", "issues": issues}
    if not unslop_available:
        result["status"] = "PARTIAL" if result["status"] == "PASS" else result["status"]
        result["fallback"] = "built-in checks applied; optional unslop reference unavailable"
    return result


def review_canvas_request(
    *, gh_available: bool, local_diff: list[str] | None, action: str = "render"
) -> dict[str, object]:
    """Resolve a read-only PR review source without external writes."""

    if action not in {"render", "read"}:
        raise PermissionDenied("only read and render actions are allowed")
    if gh_available:
        source = "gh-read-only"
    elif local_diff:
        source = "local-fixture"
    else:
        raise MissingCapability("gh is unavailable and no local diff fixture exists")
    if local_diff is not None and not any(line.startswith(("+", "-", "@@")) for line in local_diff):
        raise AdapterError("diff fixture has no reviewable lines")
    return {"status": "READY", "source": source, "external_writes": False}
