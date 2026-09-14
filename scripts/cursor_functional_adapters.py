"""Small, local proof harnesses for promoted Cursor mirror boundaries.

These helpers do not activate Cursor, cloud, connector, or marketplace
surfaces. They exercise isolated playbook and verification fixtures while
keeping missing capabilities and failed proof states explicit.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import shlex
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
BUG_FIX_FIXTURE_COMPLETED_STEPS = (1, 4, 5)
BUG_FIX_PARTIAL_STEPS = (2, 3, 6)
PSTACK_FIXTURE_MARKER = ".pstack-disposable-fixture"
PSTACK_FIXTURE_MARKER_CONTENT = "pstack-local-bug-fix-fixture-v1\n"
PSTACK_MODEL_ALIASES = ("inherit-parent", "auto")
PSTACK_MODEL_ROLES = (
    "feature, refactoring",
    "bug-fix",
    "perf-issue",
    "hillclimb",
    "judgment and prose",
    "hardest tasks",
    "how explorer",
    "how explainer",
    "why investigators",
    "why synthesizer",
    "reflect tooling",
    "reflect judgment, divergent, synthesizer",
    "arena runners",
    "arena cross-judge pool",
    "swarm workers",
    "architect runners",
    "interrogate reviewers",
)
PSTACK_MODEL_PANEL_ROLES = frozenset(
    {
        "arena runners",
        "arena cross-judge pool",
        "architect runners",
        "interrogate reviewers",
    }
)


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


def _assert_verification_output_path(root: Path, path: Path, label: str) -> None:
    _reject_symlink_components(root, path.relative_to(root))
    if path.exists() and not path.is_file():
        raise AdapterError(f"{label} must be a regular file")


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


def _resolve_verification_target(
    project_root: str | Path,
    app_name: str,
    *,
    require_existing: bool,
) -> tuple[Path, Path]:
    _validate_verification_slug(app_name, "app_name")
    root_path = Path(project_root)
    if root_path.is_symlink():
        raise AdapterError("verification fixture project root must not be a symlink")
    root = root_path.resolve()
    if not root.is_dir():
        raise AdapterError("verification fixture project root must be a directory")
    target = root / ".agents" / "skills" / f"verify-{app_name}"
    _reject_symlink_components(root, target.relative_to(root))
    if require_existing:
        if not target.is_dir():
            raise AdapterError("verification target is not a directory")
        if target.is_symlink():
            raise AdapterError("verification target must not be a symlink")
    elif target.exists():
        raise AdapterError("verification target already exists")
    return root, target


def _validate_verification_slug(value: str, label: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value) is None:
        raise AdapterError(
            f"{label} must match [A-Za-z0-9][A-Za-z0-9_-]* without whitespace or quoting characters"
        )
    if value.casefold() == "readme":
        raise AdapterError(f"{label} README is reserved for the generated feature index")


def _normalize_verification_commands(
    commands: Mapping[str, Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    if not commands:
        raise AdapterError("verification commands need at least one feature")
    normalized: dict[str, dict[str, object]] = {}
    for feature, spec in commands.items():
        _validate_verification_slug(feature, "feature name")
        if not isinstance(spec, Mapping):
            raise AdapterError("verification command spec must be a mapping")
        arguments = spec.get("arguments")
        if isinstance(arguments, (str, bytes)) or not isinstance(arguments, Iterable):
            raise AdapterError("verification command arguments must be an iterable")
        argv = tuple(arguments)
        if any(not isinstance(item, str) or "\x00" in item for item in argv):
            raise AdapterError("verification command arguments must be NUL-free strings")
        expected_stdout = spec.get("expected_stdout")
        if not isinstance(expected_stdout, str) or "\x00" in expected_stdout:
            raise AdapterError("verification expected_stdout must be NUL-free text")
        expected_exit_code = spec.get("expected_exit_code", 0)
        if not isinstance(expected_exit_code, int) or isinstance(expected_exit_code, bool):
            raise AdapterError("verification expected_exit_code must be an integer")
        timeout_seconds = spec.get("timeout_seconds", 2.0)
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
            raise AdapterError("verification timeout_seconds must be a positive number")
        if timeout_seconds <= 0:
            raise AdapterError("verification timeout_seconds must be a positive number")
        description = spec.get("description", f"Run the {feature} CLI flow and record evidence.")
        if not isinstance(description, str) or not description.strip() or "\x00" in description:
            raise AdapterError("verification feature description must be non-empty text")
        cleanup_paths = spec.get("cleanup_paths", ())
        if isinstance(cleanup_paths, (str, bytes)) or not isinstance(cleanup_paths, Iterable):
            raise AdapterError("verification cleanup_paths must be an iterable")
        cleanup = tuple(cleanup_paths)
        if any(
            not isinstance(item, str)
            or "\x00" in item
            or not item.strip()
            or item in {".", ".."}
            or "/" in item
            or "\\" in item
            for item in cleanup
        ):
            raise AdapterError("verification cleanup_paths must be safe single path components")
        normalized[feature] = {
            "arguments": argv,
            "expected_stdout": expected_stdout,
            "expected_exit_code": expected_exit_code,
            "timeout_seconds": float(timeout_seconds),
            "description": description,
            "cleanup_paths": cleanup,
        }
    return normalized


def _normalize_verification_doctor(
    doctor: Mapping[str, Mapping[str, object]] | None,
) -> dict[str, dict[str, object]]:
    if doctor is None:
        return {}
    normalized = _normalize_verification_commands(doctor)
    required = {"version", "health"}
    actual = set(normalized)
    if actual != required:
        raise AdapterError(
            "verification doctor must provide exactly version and health checks"
        )
    if any(spec["cleanup_paths"] for spec in normalized.values()):
        raise AdapterError("verification doctor checks must not declare cleanup paths")
    return normalized


def _normalize_verification_source_wave(
    features: Iterable[str],
    source_wave: Mapping[str, Mapping[str, object]] | None,
) -> dict[str, dict[str, str]] | None:
    if source_wave is None:
        return None
    expected = set(features)
    if set(source_wave) != expected:
        raise AdapterError(
            "verification source wave must return exactly one result per feature"
        )
    normalized: dict[str, dict[str, str]] = {}
    for feature, result in source_wave.items():
        if not isinstance(result, Mapping):
            raise AdapterError("verification source-wave result must be a mapping")
        required = ("summary", "entry_points", "recipe")
        if any(
            not isinstance(result.get(key), str) or not result[key].strip()
            for key in required
        ):
            raise AdapterError(
                "verification source-wave results need summary, entry_points, and recipe"
            )
        normalized[feature] = {
            key: result[key]  # type: ignore[assignment]
            for key in required
        }
    return normalized


_VERIFICATION_SYNTAX_CODE = (
    "from pathlib import Path; import sys; "
    "compile(Path(sys.argv[1]).read_text(encoding='utf-8'), sys.argv[1], 'exec'); "
    "print('syntax:ok')"
)


def _run_verification_syntax_check(root: Path, app: Path) -> dict[str, object]:
    relative_app = str(app.relative_to(root))
    command = (
        sys.executable,
        "-c",
        _VERIFICATION_SYNTAX_CODE,
        relative_app,
    )
    environment = {
        "PATH": str(Path(sys.executable).parent),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    try:
        completed = subprocess.run(
            command,
            cwd=str(root),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            shell=False,
            timeout=2.0,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "TIMEOUT",
            "command": command,
            "evidence": {
                "exit_code": None,
                "stdout": _process_output(exc.stdout),
                "stderr": _process_output(exc.stderr),
            },
        }
    return {
        "status": "PASS"
        if completed.returncode == 0
        and completed.stdout == "syntax:ok\n"
        and completed.stderr == ""
        else "FAIL",
        "command": command,
        "evidence": {
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
    }


def _run_verification_doctor(
    root: Path, app: Path, doctor: Mapping[str, Mapping[str, object]]
) -> dict[str, object]:
    checks: dict[str, object] = {"syntax": _run_verification_syntax_check(root, app)}
    for name in ("version", "health"):
        spec = doctor[name]
        checks[name] = run_local_app_fixture(
            root,
            app,
            spec["arguments"],  # type: ignore[arg-type]
            expected_stdout=spec["expected_stdout"],  # type: ignore[arg-type]
            expected_exit_code=spec["expected_exit_code"],  # type: ignore[arg-type]
            timeout_seconds=spec["timeout_seconds"],  # type: ignore[arg-type]
        )
    status = "PASS" if all(check["status"] == "PASS" for check in checks.values()) else "FAIL"
    return {"status": status, "checks": checks}


def _cleanup_verification_state(
    root: Path, commands: Mapping[str, Mapping[str, object]]
) -> dict[str, object]:
    removed: list[str] = []
    for filename in _cleanup_paths(commands):
        path = root / filename
        _reject_symlink_components(root, path.relative_to(root))
        if path.is_symlink():
            raise AdapterError(f"verification cleanup path must not be a symlink: {filename}")
        if path.exists() and not path.is_file():
            raise AdapterError(f"verification cleanup path must be a regular file: {filename}")
        if path.is_file():
            path.unlink()
            removed.append(filename)
    remaining = tuple(filename for filename in _cleanup_paths(commands) if (root / filename).exists())
    return {"status": "PASS" if not remaining else "FAIL", "removed": tuple(removed), "remaining": remaining}


def _run_verification_doctor_guarded(
    root: Path,
    app: Path,
    doctor: Mapping[str, Mapping[str, object]],
    commands: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    _assert_cleanup_paths_absent(root, commands)
    result = _run_verification_doctor(root, app, doctor)
    appeared = tuple(
        filename
        for filename in _cleanup_paths(commands)
        if (root / filename).exists() or (root / filename).is_symlink()
    )
    if appeared:
        cleanup = _cleanup_verification_state(root, commands)
        return {
            **result,
            "status": "FAIL",
            "reason": "Doctor created declared app state",
            "unexpected_state": appeared,
            "cleanup": cleanup,
        }
    return result


def _capture_verification_commands_with_cleanup(
    root: Path,
    app: Path,
    commands: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, dict[str, object]], dict[str, object] | None, dict[str, object]]:
    _assert_cleanup_paths_absent(root, commands)
    observations: dict[str, dict[str, object]] = {}
    failure: dict[str, object] | None = None
    cleanup: dict[str, object]
    try:
        observations, failure = _capture_verification_commands(root, app, commands)
        if failure is None:
            _assert_cleanup_paths_regular(root, commands)
    finally:
        cleanup = _cleanup_verification_state(root, commands)
    return observations, failure, cleanup


def _capture_verification_commands(
    root: Path,
    app: Path,
    commands: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, dict[str, object]], dict[str, object] | None]:
    observations: dict[str, dict[str, object]] = {}
    for feature, spec in commands.items():
        result = run_local_app_fixture(
            root,
            app,
            spec["arguments"],  # type: ignore[arg-type]
            expected_stdout=spec["expected_stdout"],  # type: ignore[arg-type]
            expected_exit_code=spec["expected_exit_code"],  # type: ignore[arg-type]
            timeout_seconds=spec["timeout_seconds"],  # type: ignore[arg-type]
        )
        observations[feature] = {
            "feature": feature,
            "arguments": tuple(spec["arguments"]),  # type: ignore[arg-type]
            "evidence": result["evidence"],
            "side_effects": _capture_verification_side_effects(root),
            "status": result["status"],
        }
        if result["status"] != "PASS":
            return observations, {
                "feature": feature,
                "reason": "verification command evidence did not match the expected result",
                "result": result,
            }
    return observations, None


def _capture_verification_side_effects(root: Path) -> dict[str, object]:
    files: list[str] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if path.name.startswith(".") or not path.is_file() or path.is_symlink():
            continue
        files.append(path.name)
    return {"regular_files": files}


def _cleanup_paths(commands: Mapping[str, Mapping[str, object]]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                filename
                for spec in commands.values()
                for filename in spec["cleanup_paths"]  # type: ignore[index]
            }
        )
    )


def _assert_cleanup_paths_absent(
    root: Path, commands: Mapping[str, Mapping[str, object]]
) -> None:
    for filename in _cleanup_paths(commands):
        path = root / filename
        _reject_symlink_components(root, path.relative_to(root))
        if path.exists() or path.is_symlink():
            raise AdapterError(
                f"verification cleanup path must be absent before the first drive: {filename}"
            )


def _assert_cleanup_paths_regular(
    root: Path, commands: Mapping[str, Mapping[str, object]]
) -> None:
    for filename in _cleanup_paths(commands):
        path = root / filename
        _reject_symlink_components(root, path.relative_to(root))
        if path.is_symlink() or not path.is_file():
            raise AdapterError(
                f"verification cleanup path was not created as a regular file: {filename}"
            )


def _verification_skill_document(
    root: Path,
    app: Path,
    app_name: str,
    commands: Mapping[str, Mapping[str, object]],
    doctor: Mapping[str, Mapping[str, object]] | None = None,
) -> str:
    app_relative = str(app.relative_to(root))
    command_lines = [
        f"- `{shlex.join(('python3', app_relative, *tuple(spec['arguments'])))}` — {spec['description']}"
        for spec in commands.values()
    ]
    doctor = doctor or {}
    version_spec = doctor.get("version")
    health_spec = doctor.get("health")
    version_command = (
        shlex.join(("python3", app_relative, *tuple(version_spec["arguments"])))
        if version_spec
        else "(version check not observed)"
    )
    health_command = (
        shlex.join(("python3", app_relative, *tuple(health_spec["arguments"])))
        if health_spec
        else "(health check not observed)"
    )
    version_expected = (
        version_spec["expected_stdout"].rstrip() if version_spec else "not observed"
    )
    health_expected = (
        health_spec["expected_stdout"].rstrip() if health_spec else "not observed"
    )
    state_files = _cleanup_paths(commands)
    cleanup_state = (
        ", ".join(f"`{filename}`" for filename in state_files)
        if state_files
        else "no app-state path is declared by this fixture"
    )
    return (
        "---\n"
        f"name: verify-{app_name}\n"
        f"description: \"Verify {app_name} through its short-lived Python CLI; use when checking the mapped user flows.\"\n"
        "---\n\n"
        f"# Verify {app_name}\n\n"
        "This project-local verification skill was generated from bounded CLI observations. "
        "It is fixture-only and must run against an instance started by the verification run.\n\n"
        "## Launch\n\n"
        "This app is a short-lived CLI, not a server. Launch means starting each drive in its own "
        "disposable project directory with `python3`; readiness is established only after the Doctor "
        "syntax, version, and health checks pass. "
        "There is no long-lived process or shared port to keep alive.\n\n"
        "## Doctor\n\n"
        f"Run `{shlex.join(('python3', '-c', _VERIFICATION_SYNTAX_CODE, app_relative))}` "
        f"for syntax (expect `syntax:ok`), then `{version_command}` "
        f"(expect `{version_expected}`) and `{health_command}` "
        f"(expect `{health_expected}`). Any failure blocks the run.\n\n"
        "## Drive\n\n"
        "Use the exact observed CLI commands below, one process per feature:\n\n"
        + "\n".join(command_lines)
        + "\n\n"
        "## Evidence\n\n"
        "Capture Doctor syntax/version/health evidence plus exit code, stdout, stderr, and the observed "
        "regular-file state for every user-facing drive. "
        f"The surviving Doctor and feature JSON evidence is kept under `.agents/skills/verify-{app_name}/evidence/`; "
        "feature-map files are not evidence of a live target. Verify the user-visible output and "
        "the side effect state before calling a feature passed.\n\n"
        "## Cleanup\n\n"
        f"Remove only processes and app-state files created by the drives (for this fixture: {cleanup_state}); "
        f"keep `.agents/skills/verify-{app_name}/` and its `evidence/` directory, then verify the evidence path remains. "
        "Never kill by process name; these CLI drives are short-lived and are bounded by the runner timeout.\n\n"
        "## Helpers\n\n"
        "No helper script is shipped. The invocation is the explicit `python3` command in each feature file; "
        "a future helper must remain inside this project-local verification skill and document its command.\n"
    )


def _verification_feature_readme(app_name: str, commands: Mapping[str, Mapping[str, object]]) -> str:
    lines = [
        f"# verify-{app_name} feature map",
        "",
        "This map records user-facing CLI flows generated from independent disposable-process observations.",
        "Each feature file names the route, exact command, and observable end state; captured JSON lives in `../evidence/`.",
        "",
        "## Features",
        "",
    ]
    lines.extend(
        f"- [{feature}](./{feature}.md) — {spec['description']}"
        for feature, spec in commands.items()
    )
    return "\n".join(lines) + "\n"


def _verification_feature_document(
    root: Path,
    app: Path,
    feature: str,
    spec: Mapping[str, object],
    observation: Mapping[str, object],
) -> str:
    payload = _verification_feature_payload(root, app, feature, spec, observation)
    command_text = shlex.join(payload["command"])  # type: ignore[arg-type]
    return (
        f"# {feature}\n\n{spec['description']}\n\n"
        "## Sub-features\n\n"
        "- Run the mapped CLI action and verify its resulting output and file side effect.\n\n"
        "## How to get to it (user POV)\n\n"
        f"Start from the disposable notes project and choose the `{feature}` user flow.\n\n"
        "## Driving it with the bounded Python subprocess runner\n\n"
        f"Run `{command_text}`. The runner captures the process exit code, stdout, stderr, and regular-file state.\n\n"
        "## Gotchas\n\n"
        "This is a short-lived CLI fixture; it is not a live target, and its filesystem/network isolation is not observed. "
        "The captured observation below is evidence for this run, not an instruction to trust future output.\n\n"
        "### Captured observation\n\n"
        "```json\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)}\n"
        "```\n"
    )


def _verification_feature_payload(
    root: Path,
    app: Path,
    feature: str,
    spec: Mapping[str, object],
    observation: Mapping[str, object],
) -> dict[str, object]:
    command = [str(app.relative_to(root)), *tuple(spec["arguments"])]  # type: ignore[arg-type]
    return {
        "arguments": list(spec["arguments"]),  # type: ignore[arg-type]
        "command": command,
        "evidence": observation["evidence"],
        "feature": feature,
        "observation_source": "independent subprocess stdout/stderr/exit capture",
        "side_effects": observation["side_effects"],
    }


def _verification_result_base(target: Path) -> dict[str, object]:
    return {
        "target": str(target),
        "product_code_edits": False,
        "product_edits": False,
        "app_state_writes": "allowed within disposable fixture; not prevented",
        "external_writes": False,
        "environment": "isolated-project-fixture-process",
        "evidence_scope": ("exit_code", "stdout", "stderr"),
        "filesystem_isolation": "not_observed",
        "network_isolation": "not_observed",
    }


def run_cli_verification_fixture(
    project_root: str | Path,
    app_name: str,
    app_path: str | Path,
    commands: Mapping[str, Mapping[str, object]],
    *,
    app_available: bool = True,
    doctor: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Create a project-local verification fixture from real CLI observations.

    Doctor syntax/version/health checks run before the feature drives. Each
    feature command is a separate subprocess before any skill file is written;
    declared app state is cleaned after the drives while captured evidence
    survives. This is a disposable fixture proof, not live target verification.
    """

    normalized = _normalize_verification_commands(commands)
    normalized_doctor = _normalize_verification_doctor(doctor)
    root, target = _resolve_verification_target(
        project_root, app_name, require_existing=False
    )
    result = _verification_result_base(target)
    if not app_available:
        result.update(
            {
                "status": "BLOCKED",
                "reason": "verification app is unavailable",
                "observations": {},
                "doctor": None,
            }
        )
        return result
    _, app = _resolve_local_app_fixture(root, app_path)
    _assert_cleanup_paths_absent(root, normalized)
    doctor_result = (
        _run_verification_doctor_guarded(root, app, normalized_doctor, normalized)
        if normalized_doctor
        else {"status": "NOT_OBSERVED", "checks": {}}
    )
    if doctor_result["status"] != "PASS":
        result.update(
            {
                "status": "BLOCKED",
                "reason": "verification Doctor failed or was not supplied",
                "doctor": doctor_result,
                "observations": {},
            }
        )
        return result
    observations, failure, cleanup = _capture_verification_commands_with_cleanup(
        root, app, normalized
    )
    if failure is not None:
        result.update(
            {
                "status": "ERROR",
                "reason": failure["reason"],
                "failed_feature": failure["feature"],
                "observations": observations,
                "doctor": doctor_result,
                "cleanup": cleanup,
            }
        )
        return result
    if cleanup["status"] != "PASS":
        raise AdapterError("verification cleanup left declared app state behind")

    target.mkdir(parents=True, exist_ok=False)
    features_dir = target / "features"
    features_dir.mkdir()
    (target / "SKILL.md").write_text(
        _verification_skill_document(root, app, app_name, normalized, normalized_doctor)
    )
    (features_dir / "README.md").write_text(
        _verification_feature_readme(app_name, normalized)
    )
    evidence_dir = target / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "doctor.json").write_text(
        f"{json.dumps(doctor_result, ensure_ascii=False, indent=2, sort_keys=True)}\n"
    )
    for feature, spec in normalized.items():
        (features_dir / f"{feature}.md").write_text(
            _verification_feature_document(root, app, feature, spec, observations[feature])
        )
        (evidence_dir / f"{feature}.json").write_text(
            f"{json.dumps(_verification_feature_payload(root, app, feature, spec, observations[feature]), ensure_ascii=False, indent=2, sort_keys=True)}\n"
        )
    result.update(
        {
            "status": "FIXTURE_ONLY",
            "created_skill": True,
            "reconciled_features": tuple(sorted(normalized)),
            "observations": observations,
            "doctor": doctor_result,
            "cleanup": cleanup,
            "launch": {
                "status": "PASS",
                "mode": "short-lived-cli",
                "readiness": "Doctor syntax/version/health passed before drives",
            },
            "observation_source": "independent subprocess stdout/stderr/exit capture",
        }
    )
    return result


def introduce_verification_feature_drift(
    project_root: str | Path,
    app_name: str,
    feature: str,
    drift_text: str = "\nControlled fixture drift.\n",
) -> dict[str, object]:
    """Add controlled content drift to one existing project-local feature file."""

    root, target = _resolve_verification_target(
        project_root, app_name, require_existing=True
    )
    _validate_verification_slug(feature, "feature name")
    if not isinstance(drift_text, str) or not drift_text.strip() or "\x00" in drift_text:
        raise AdapterError("drift_text must be non-empty NUL-free text")
    path = target / "features" / f"{feature}.md"
    _reject_symlink_components(root, path.relative_to(root))
    if path.is_symlink() or not path.is_file():
        raise AdapterError("verification feature must be a regular file")
    if drift_text in path.read_text():
        raise AdapterError("verification feature already contains the requested drift")
    path.write_text(path.read_text() + drift_text)
    return {
        "status": "DRIFT_INTRODUCED",
        "target": str(target),
        "feature": feature,
        "product_edits": False,
        "external_writes": False,
    }


def maintain_cli_verification_fixture(
    project_root: str | Path,
    app_name: str,
    app_path: str | Path,
    commands: Mapping[str, Mapping[str, object]],
    *,
    app_available: bool = True,
    doctor: Mapping[str, Mapping[str, object]] | None = None,
    source_wave: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Reconcile a project-local verification fixture and rerun its CLI flows.

    When supplied, ``source_wave`` is one read-only source result per feature;
    it is recorded as evidence but does not claim native delegated readers.
    """

    normalized = _normalize_verification_commands(commands)
    normalized_doctor = _normalize_verification_doctor(doctor)
    normalized_source_wave = _normalize_verification_source_wave(
        normalized, source_wave
    )
    root, target = _resolve_verification_target(
        project_root, app_name, require_existing=True
    )
    result = _verification_result_base(target)
    if not app_available:
        result.update(
            {
                "status": "BLOCKED",
                "reason": "verification app is unavailable",
                "changed_features": (),
                "source_wave": "NOT_OBSERVED"
                if normalized_source_wave is None
                else "OBSERVED_INPUT_ONLY",
            }
        )
        return result
    _, app = _resolve_local_app_fixture(root, app_path)
    _assert_cleanup_paths_absent(root, normalized)
    features_dir = target / "features"
    _reject_symlink_components(root, features_dir.relative_to(root))
    if not features_dir.is_dir() or features_dir.is_symlink():
        raise AdapterError("verification features directory must be a regular directory")
    actual_features = tuple(
        sorted(path.stem for path in features_dir.glob("*.md") if path.name != "README.md")
    )
    expected_features = tuple(sorted(normalized))
    if actual_features != expected_features:
        result.update(
            {
                "status": "ERROR",
                "reason": "feature file reconciliation mismatch",
                "expected_features": expected_features,
                "actual_features": actual_features,
                "changed_features": (),
            }
        )
        return result

    doctor_result = (
        _run_verification_doctor_guarded(root, app, normalized_doctor, normalized)
        if normalized_doctor
        else {"status": "NOT_OBSERVED", "checks": {}}
    )
    if doctor_result["status"] != "PASS":
        result.update(
            {
                "status": "BLOCKED",
                "reason": "verification Doctor failed or was not supplied",
                "doctor": doctor_result,
                "changed_features": (),
            }
        )
        return result

    first_run, failure, first_cleanup = _capture_verification_commands_with_cleanup(
        root, app, normalized
    )
    if failure is not None:
        result.update(
            {
                "status": "ERROR",
                "reason": failure["reason"],
                "failed_feature": failure["feature"],
                "first_run": first_run,
                "first_cleanup": first_cleanup,
                "doctor": doctor_result,
                "changed_features": (),
            }
        )
        return result
    if first_cleanup["status"] != "PASS":
        raise AdapterError("verification cleanup left declared app state behind")

    changed: list[str] = []
    evidence_dir = target / "evidence"
    _reject_symlink_components(root, evidence_dir.relative_to(root))
    if evidence_dir.exists() and (evidence_dir.is_symlink() or not evidence_dir.is_dir()):
        raise AdapterError("verification evidence directory must be a regular directory")
    evidence_dir.mkdir(exist_ok=True)
    doctor_path = evidence_dir / "maintenance-doctor.json"
    _assert_verification_output_path(root, doctor_path, "maintenance Doctor evidence")
    doctor_path.write_text(
        f"{json.dumps(doctor_result, ensure_ascii=False, indent=2, sort_keys=True)}\n"
    )
    for feature, spec in normalized.items():
        path = features_dir / f"{feature}.md"
        _reject_symlink_components(root, path.relative_to(root))
        if path.is_symlink() or not path.is_file():
            raise AdapterError("verification feature must be a regular file")
        expected_document = _verification_feature_document(
            root, app, feature, spec, first_run[feature]
        )
        if path.read_text() != expected_document:
            path.write_text(expected_document)
            changed.append(feature)
        evidence_path = evidence_dir / f"{feature}.json"
        _assert_verification_output_path(root, evidence_path, "verification evidence")
        evidence_path.write_text(
            f"{json.dumps(_verification_feature_payload(root, app, feature, spec, first_run[feature]), ensure_ascii=False, indent=2, sort_keys=True)}\n"
        )

    if normalized_source_wave is not None:
        for feature, source_result in normalized_source_wave.items():
            source_path = evidence_dir / f"maintenance-source-wave-{feature}.json"
            _assert_verification_output_path(root, source_path, "maintenance source-wave evidence")
            source_path.write_text(
                f"{json.dumps({'feature': feature, 'provenance': 'caller_supplied_input', **source_result}, ensure_ascii=False, indent=2, sort_keys=True)}\n"
            )

    for feature, spec in normalized.items():
        before_path = evidence_dir / f"maintenance-before-{feature}.json"
        _assert_verification_output_path(root, before_path, "maintenance-before evidence")
        before_path.write_text(
            f"{json.dumps(_verification_feature_payload(root, app, feature, spec, first_run[feature]), ensure_ascii=False, indent=2, sort_keys=True)}\n"
        )
    second_run, second_failure, second_cleanup = _capture_verification_commands_with_cleanup(
        root, app, normalized
    )
    for feature, spec in normalized.items():
        after_path = evidence_dir / f"maintenance-after-{feature}.json"
        if feature in second_run:
            _assert_verification_output_path(root, after_path, "maintenance-after evidence")
            after_path.write_text(
                f"{json.dumps(_verification_feature_payload(root, app, feature, spec, second_run[feature]), ensure_ascii=False, indent=2, sort_keys=True)}\n"
            )
    if second_failure is not None:
        result.update(
            {
                "status": "ERROR",
                "reason": second_failure["reason"],
                "failed_feature": second_failure["feature"],
                "first_run": first_run,
                "second_run": second_run,
                "first_cleanup": first_cleanup,
                "second_cleanup": second_cleanup,
                "doctor": doctor_result,
                "changed_features": tuple(changed),
            }
        )
        return result
    if second_cleanup["status"] != "PASS":
        raise AdapterError("verification cleanup left declared app state behind")
    result.update(
        {
            "status": "FIXTURE_ONLY",
            "changed_features": tuple(changed),
            "first_run": first_run,
            "second_run": second_run,
            "first_cleanup": first_cleanup,
            "second_cleanup": second_cleanup,
            "doctor": doctor_result,
            "source_wave": "OBSERVED_INPUT_ONLY" if normalized_source_wave is not None else "NOT_OBSERVED",
            "launch": {
                "status": "PASS",
                "mode": "short-lived-cli",
                "readiness": "Doctor syntax/version/health passed before maintenance drives",
            },
            "reconciled_features": expected_features,
            "observation_source": "independent subprocess stdout/stderr/exit capture",
        }
    )
    return result


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
                "fixture_completed": (),
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
                "fixture_completed": (1,),
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
                "fixture_completed": (1,),
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
                "fixture_completed": (1,),
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
            "fixture_completed": BUG_FIX_FIXTURE_COMPLETED_STEPS,
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


def run_pstack_model_mapping_fixture(
    inventory: Mapping[str, Iterable[str]],
    choices: Mapping[str, object],
) -> dict[str, object]:
    """Dry-run the pstack role mapping against a supplied channel inventory.

    This is deliberately a fixture-only boundary.  ``inventory`` is the
    caller's already-observed ``model -> supported efforts`` mapping; this
    helper does not discover models, call a provider, or persist config.  The
    two pstack aliases are valid without appearing in that inventory.
    """

    def fail(reason: str, details: Iterable[str] = ()) -> dict[str, object]:
        detail_lines = tuple(details)
        return {
            "status": "ERROR",
            "fixture_only": True,
            "writes_performed": False,
            "configuration_changed": False,
            "reason": reason,
            "details": detail_lines,
            "dry_run": "DRY-RUN cursor-setup-pstack (fixture-only; no config write)\n"
            + "ERROR: "
            + reason
            + ("\n" + "\n".join(detail_lines) if detail_lines else ""),
        }

    if not isinstance(inventory, Mapping):
        return fail("model inventory must be a mapping of model to efforts")
    if not isinstance(choices, Mapping):
        return fail("pstack choices must be a mapping of role to selection")

    try:
        normalized_inventory: dict[str, tuple[str, ...]] = {}
        for model, efforts in inventory.items():
            if not isinstance(model, str) or not model.strip():
                raise AdapterError("inventory model names must be non-empty strings")
            if isinstance(efforts, (str, bytes)):
                raise AdapterError(
                    f"inventory efforts for {model!r} must be an iterable of strings"
                )
            normalized_efforts = tuple(efforts)
            if any(
                not isinstance(effort, str) or not effort.strip()
                for effort in normalized_efforts
            ):
                raise AdapterError(
                    f"inventory efforts for {model!r} must be non-empty strings"
                )
            normalized_inventory[model] = tuple(dict.fromkeys(normalized_efforts))

        expected_roles = set(PSTACK_MODEL_ROLES)
        supplied_roles = set(choices)
        missing_roles = tuple(sorted(expected_roles - supplied_roles))
        extra_roles = tuple(sorted(supplied_roles - expected_roles))
        if missing_roles or extra_roles:
            details = []
            if missing_roles:
                details.append("missing roles: " + ", ".join(missing_roles))
            if extra_roles:
                details.append("unknown roles: " + ", ".join(extra_roles))
            return fail("choices must cover exactly every pstack role", details)

        def normalize_selection(selection: object, label: str) -> dict[str, object]:
            if isinstance(selection, str):
                model = selection
                effort = None
            elif isinstance(selection, Mapping):
                unknown = set(selection) - {"model", "effort"}
                if unknown:
                    raise AdapterError(
                        f"{label} has unsupported selection fields: {sorted(unknown)}"
                    )
                model = selection.get("model")
                effort = selection.get("effort")
                if effort is not None and (
                    not isinstance(effort, str) or not effort.strip()
                ):
                    raise AdapterError(f"{label} effort must be a non-empty string")
            else:
                raise AdapterError(
                    f"{label} selection must be a model string or model/effort mapping"
                )
            if not isinstance(model, str) or not model.strip():
                raise AdapterError(f"{label} model must be a non-empty string")
            if model in PSTACK_MODEL_ALIASES and effort is not None:
                raise AdapterError(
                    f"{label} cannot validate an effort for {model!r} "
                    "without the parent model"
                )
            result: dict[str, object] = {"model": model}
            if effort is not None:
                result["effort"] = effort
            return result

        normalized_choices: dict[str, tuple[dict[str, object], ...]] = {}
        for role in PSTACK_MODEL_ROLES:
            raw = choices[role]
            if role in PSTACK_MODEL_PANEL_ROLES:
                if not isinstance(raw, (list, tuple)) or not raw:
                    raise AdapterError(f"{role} must be a non-empty model panel list")
                selections = tuple(
                    normalize_selection(item, f"{role}[{index}]")
                    for index, item in enumerate(raw)
                )
            else:
                if isinstance(raw, (list, tuple)):
                    raise AdapterError(f"{role} must be a single model selection")
                selections = (normalize_selection(raw, role),)
            normalized_choices[role] = selections
    except (AdapterError, TypeError, ValueError) as exc:
        return fail(str(exc))

    unavailable: list[str] = []
    mapping: dict[str, dict[str, object]] = {}
    for role in PSTACK_MODEL_ROLES:
        selections = normalized_choices[role]
        selection_report: list[dict[str, object]] = []
        for index, selection in enumerate(selections):
            model = selection["model"]
            effort = selection.get("effort")
            label = f"{role}[{index}]" if role in PSTACK_MODEL_PANEL_ROLES else role
            if model in PSTACK_MODEL_ALIASES:
                availability = "alias-preserved"
            elif model not in normalized_inventory:
                unavailable.append(f"{label}: unavailable model {model!r}")
                availability = "unavailable-model"
            elif effort is not None and effort not in normalized_inventory[model]:
                unavailable.append(
                    f"{label}: unavailable effort {effort!r} for model {model!r}"
                )
                availability = "unavailable-effort"
            else:
                availability = "available"
            selection_report.append(
                {
                    "selection": dict(selection),
                    "availability": availability,
                }
            )
        mapping[role] = {
            "panel": role in PSTACK_MODEL_PANEL_ROLES,
            "count": len(selections),
            "selections": selection_report,
        }

    lines = [
        "DRY-RUN cursor-setup-pstack (fixture-only; no config write)",
        f"inventory: {len(normalized_inventory)} model(s); roles: {len(mapping)}",
    ]
    for role in PSTACK_MODEL_ROLES:
        entries = mapping[role]["selections"]
        rendered = ", ".join(
            "/".join(
                str(value)
                for value in (
                    item["selection"].get("model"),
                    item["selection"].get("effort"),
                )
                if value is not None
            )
            for item in entries
        )
        suffix = (
            f" [panel x{mapping[role]['count']}]"
            if mapping[role]["panel"]
            else ""
        )
        lines.append(f"- {role}{suffix}: {rendered}")

    if unavailable:
        lines.append("BLOCKED: unavailable model/effort; configuration unchanged")
        lines.extend(f"- {item}" for item in unavailable)
        return {
            "status": "BLOCKED",
            "fixture_only": True,
            "writes_performed": False,
            "configuration_changed": False,
            "unavailable": tuple(unavailable),
            "mapping": mapping,
            "dry_run": "\n".join(lines),
        }

    lines.append("PASS: every role and panel entry is valid; configuration unchanged")
    return {
        "status": "DRY_RUN",
        "fixture_only": True,
        "writes_performed": False,
        "configuration_changed": False,
        "mapping": mapping,
        "dry_run": "\n".join(lines),
    }


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


def run_automate_me_fixture(
    project_root: str | Path,
    evidence_slices: Mapping[str, Iterable[str]],
    user_preferences: Iterable[str],
    *,
    unslop_available: bool,
    draft_approved: bool,
) -> dict[str, object]:
    """Draft one project-local mode skill from corroborated bounded evidence.

    This is an isolated adapter proof, not native task-history or skill-creator
    telemetry.  It requires two distinct evidence slices, accepts only
    preferences corroborated in both, and never writes a personal/global path.
    """

    root = Path(project_root)
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise AdapterError("project root must be an existing regular directory")
    if not isinstance(evidence_slices, Mapping):
        raise AdapterError("evidence_slices must be a mapping of source to items")
    normalized: dict[str, tuple[str, ...]] = {}
    for source, items in evidence_slices.items():
        if not isinstance(source, str) or not source.strip():
            raise AdapterError("evidence source names must be non-empty strings")
        if isinstance(items, (str, bytes)):
            raise AdapterError("evidence slice items must be an iterable of strings")
        values = tuple(item for item in items if isinstance(item, str) and item.strip())
        if any(any(ord(char) < 32 for char in item) for item in values):
            raise AdapterError("evidence items must not contain control characters")
        normalized[source] = tuple(dict.fromkeys(values))
    if len(normalized) < 2:
        return {
            "status": "PARTIAL",
            "reason": "at least two distinct bounded evidence slices are required",
            "writes_performed": False,
            "destination": ".agents/skills/fixture-mode/fixture-mode-mode/SKILL.md",
        }
    preferences = tuple(dict.fromkeys(item for item in user_preferences if isinstance(item, str) and item.strip()))
    if any(any(ord(char) < 32 for char in item) for item in preferences):
        raise AdapterError("user preferences must not contain control characters")
    counts = {
        preference: sum(preference in values for values in normalized.values())
        for preference in preferences
    }
    confirmed = tuple(preference for preference, count in counts.items() if count >= 2)
    omitted = tuple(preference for preference, count in counts.items() if count < 2)
    if not confirmed:
        return {
            "status": "PARTIAL",
            "reason": "no user preference is corroborated by two evidence slices",
            "confirmed": (),
            "omitted": omitted,
            "writes_performed": False,
        }
    if not unslop_available:
        return {
            "status": "PARTIAL",
            "reason": "cursor-unslop is unavailable; existing skill preserved",
            "confirmed": confirmed,
            "omitted": omitted,
            "writes_performed": False,
        }

    destination = root / ".agents/skills/fixture-mode/fixture-mode-mode/SKILL.md"
    component = root
    for part in (".agents", "skills", "fixture-mode", "fixture-mode-mode"):
        component /= part
        if component.is_symlink():
            raise AdapterError("project-local mode destination contains a symlink component")
    if destination.exists() and (destination.is_symlink() or not destination.is_file()):
        raise AdapterError("project-local mode destination must be a regular file")
    existing = destination.read_text(encoding="utf-8") if destination.exists() else (
        "---\nname: fixture-mode\ndescription: bounded fixture mode\n---\n\n"
        "## Existing contract\n\nKeep explicit evidence and project-local scope.\n"
    )
    marker = "\n## Confirmed preferences\n"
    base = existing.split(marker, 1)[0].rstrip()
    draft = base + marker + "\n" + "\n".join(f"- {item}" for item in confirmed) + "\n"
    prose = review_prose(draft, unslop_available=True)
    if prose["status"] != "PASS":
        return {
            "status": "PARTIAL",
            "reason": "bounded prose review did not pass",
            "review": prose,
            "writes_performed": False,
        }
    if not draft_approved:
        return {
            "status": "PARTIAL",
            "reason": "draft requires explicit approval before landing",
            "review": prose,
            "writes_performed": False,
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(draft, encoding="utf-8")
    readback = destination.read_text(encoding="utf-8")
    if readback != draft:
        raise AdapterError("project-local mode readback mismatch")
    return {
        "status": "FIXTURE_ONLY",
        "destination": str(destination),
        "confirmed": confirmed,
        "omitted": omitted,
        "evidence_sources": tuple(normalized),
        "review": prose,
        "writes_performed": True,
        "global_write": False,
        "native_history": False,
        "native_skill_creator": False,
    }


def run_recall_fixture(
    history_records: Iterable[Mapping[str, object]],
    *,
    topic: str,
    workspace: str,
    live_state: Mapping[str, object],
    shared_record: Mapping[str, object] | None,
    current_thread_id: str | None = None,
) -> dict[str, object]:
    """Reconcile a supplied bounded history slice with live/shared records."""

    if not topic.strip() or not workspace.strip():
        raise AdapterError("topic and workspace must be non-empty")
    if not isinstance(live_state, Mapping):
        raise AdapterError("live_state must be a mapping")
    if live_state.get("workspace") != workspace:
        return {
            "status": "PARTIAL",
            "reason": "live state workspace does not match requested scope",
            "writes_performed": False,
        }
    selected: list[Mapping[str, object]] = []
    for record in history_records:
        if not isinstance(record, Mapping):
            raise AdapterError("history records must be mappings")
        record_id = record.get("thread_id")
        if current_thread_id and record_id == current_thread_id:
            continue
        if record.get("workspace") != workspace:
            continue
        searchable = " ".join(str(record.get(key, "")) for key in ("title", "summary", "topic"))
        if topic.casefold() in searchable.casefold():
            selected.append(record)
    if not selected:
        return {
            "status": "PARTIAL",
            "reason": "no exact scoped history record matched",
            "writes_performed": False,
            "missing_export": True,
        }
    if shared_record is None:
        return {
            "status": "PARTIAL",
            "reason": "shared record is missing; history and live state preserved",
            "writes_performed": False,
            "selected_history": tuple(record.get("thread_id") for record in selected),
            "missing_export": True,
        }
    if shared_record.get("workspace") != workspace or topic.casefold() not in str(shared_record.get("topic", "")).casefold():
        return {
            "status": "PARTIAL",
            "reason": "shared record does not match requested scope",
            "writes_performed": False,
            "selected_history": tuple(record.get("thread_id") for record in selected),
        }
    brief = {
        "scope": {"workspace": workspace, "topic": topic},
        "history": [
            {"thread_id": record.get("thread_id"), "title": record.get("title"), "updated_at": record.get("updated_at")}
            for record in selected
        ],
        "live_state": dict(live_state),
        "shared_record": {"record_id": shared_record.get("record_id"), "summary": shared_record.get("summary")},
    }
    return {
        "status": "FIXTURE_ONLY",
        "brief": brief,
        "selected_history": tuple(record.get("thread_id") for record in selected),
        "writes_performed": False,
        "missing_export": False,
    }


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
