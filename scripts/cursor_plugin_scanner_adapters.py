#!/usr/bin/env python3
"""Read-only adapters for the four held Cursor plugin-scanner overlays.

The pinned compatibility workflow asks for a published npm scanner and three
behavioral checks.  This module provides a bounded local inventory of the
available evidence without installing or running that scanner.  It also
provides a documentation-only Cursor SDK symbol report.  Neither helper
starts agents, calls a network, reads credentials, executes plugin components,
or writes files.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Mapping


class AdapterError(ValueError):
    """Invalid fixture input."""


class PermissionDenied(AdapterError):
    """The request crosses the read-only adapter boundary."""


_SDK_SYMBOLS = (
    "@cursor/sdk",
    "Agent.create",
    "Agent.prompt",
    "Agent.resume",
    "agent.send",
    "run.stream",
    "CursorAgentError",
    "run.wait",
    "mcpServers",
)
_CREDENTIAL_KEYS = frozenset(
    {
        "apiKey",
        "CURSOR_API_KEY",
        "LINEAR_API_KEY",
        "GITHUB_TOKEN",
        "Authorization",
        "headers",
        "env",
        "mcpServers",
    }
)
_CREDENTIAL_KEY_NORMALIZED = frozenset(
    re.sub(r"[_-]", "", key.lower()) for key in _CREDENTIAL_KEYS
) | frozenset(
    {
        "clientid",
        "clientsecret",
        "credentials",
        "token",
        "secret",
    }
)

LOCAL_SCANNER_ID = "codex-local-plugin-compatibility-v1"
LOCAL_SCANNER_ROLES = (
    "deterministic-scanner",
    "startup-review",
    "validation-review",
    "docs-reliability-review",
)
CODEX_NATIVE_SDK_MAPPING = {
    "Agent.create": {
        "native_capability": "create_thread",
        "equivalence": "conceptual_only",
        "operation": "creates a separate Codex task only when explicitly requested",
    },
    "Agent.prompt": {
        "native_capability": "create_thread or send_message_to_thread",
        "equivalence": "conceptual_only",
        "operation": "sends a user-visible prompt through the native task surface",
    },
    "Agent.resume": {
        "native_capability": "send_message_to_thread",
        "equivalence": "conceptual_only",
        "operation": "continues an existing task after its ID and host are verified",
    },
    "agent.send": {
        "native_capability": "send_message_to_thread",
        "equivalence": "conceptual_only",
        "operation": "sends a follow-up to an existing task",
    },
    "run.stream": {
        "native_capability": "wait_threads plus read_thread",
        "equivalence": "no_streaming_equivalent_claimed",
        "operation": "waits for task progress and reads bounded turn output",
    },
    "run.wait": {
        "native_capability": "wait_threads",
        "equivalence": "conceptual_only",
        "operation": "waits for completion or attention on a native task",
    },
    "CursorAgentError": {
        "native_capability": "native tool result and task status",
        "equivalence": "conceptual_only",
        "operation": "reports native failure status without importing Cursor errors",
    },
    "mcpServers": {
        "native_capability": "installed connector or MCP surface when advertised",
        "equivalence": "no_configuration_equivalent_claimed",
        "operation": "requires separately verified native capability and permission",
    },
}


def _root(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_dir():
        raise AdapterError("fixture root must be an existing non-symlink directory")
    return candidate.resolve()


def _surface(root: Path, names: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(name for name in names if (root / name).is_file())


def inspect_compatibility_fixture(
    fixture_root: str | Path,
    *,
    scanner_available: bool = False,
) -> dict[str, Any]:
    """Inventory evidence for the four compatibility roles without scoring.

    A score is returned only when a caller supplies a real scanner result.
    The default deliberately reports the scanner as unavailable, matching the
    pinned skill's requirement not to invent an Agent Compatibility Score.
    """

    root = _root(fixture_root)
    if not isinstance(scanner_available, bool):
        raise AdapterError("scanner_available must be boolean")
    checks = {
        "startup": "README.md" in _surface(root, ("README.md",)),
        "validation": any(
            (root / name).exists() for name in ("tests", "test", "pyproject.toml", "package.json")
        ),
        "docs_reliability": bool(_surface(root, ("README.md", "CONTRIBUTING.md", "AGENTS.md"))),
    }
    result: dict[str, Any] = {
        "status": "EVIDENCE_ONLY" if not scanner_available else "SCANNER_REQUIRED",
        "deterministic_scanner": "AVAILABLE" if scanner_available else "UNAVAILABLE",
        "agent_compatibility_score": None,
        "checks": checks,
        "roles": (
            "compatibility-scan-review",
            "startup-review",
            "validation-review",
            "docs-reliability-review",
        ),
        "separate_evidence_required": True,
        "external_writes": False,
        "network_used": False,
        "package_installed": False,
        "environment": "isolated-read-only-fixture",
    }
    if scanner_available:
        result["reason"] = "scanner availability is an input claim; score still requires a real scanner result"
    else:
        result["reason"] = "published scanner was not installed or executed; score withheld"
    return result


def _local_role(score: int, *, evidence: tuple[str, ...], issues: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "score": score,
        "evidence": evidence,
        "issues": issues,
        "executed_runtime": False,
        "external_writes": False,
    }


def local_plugin_compatibility_scan(plugin_root: str | Path) -> dict[str, Any]:
    """Run a deterministic, local Codex scanner against one plugin directory.

    This is a safe substitute for the unavailable upstream npm scanner. It
    scores four independent, observable static contracts and deliberately
    never labels the result as an Agent Compatibility Score. It does not run
    plugin components, hooks, MCP servers, startup commands, or tests.
    """

    root = _root(plugin_root)
    try:
        from cursor_plugin_submission_audit import audit_plugin_fixture
    except ImportError as exc:  # pragma: no cover - import path is repo-local
        raise AdapterError("local structural auditor is unavailable") from exc

    audit = audit_plugin_fixture(root)
    manifest_path = root / ".cursor-plugin" / "plugin.json"
    readme_path = root / "README.md"
    manifest_exists = manifest_path.is_file()
    readme_exists = readme_path.is_file()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_exists else {}
    except (OSError, UnicodeError, json.JSONDecodeError):
        manifest = {}
    if not isinstance(manifest, dict):
        manifest = {}

    deterministic_issues = tuple(str(item) for item in audit.get("issues", ()))
    deterministic_score = 100 if audit.get("status") == "STRUCTURAL_PASS" else max(
        0, 100 - 20 * len(deterministic_issues)
    )
    startup_evidence = []
    startup_issues = []
    if manifest_exists:
        startup_evidence.append("bounded manifest exists")
    else:
        startup_issues.append("bounded manifest is missing")
    if readme_exists:
        startup_evidence.append("README exists")
    else:
        startup_issues.append("README is missing")
    if not startup_issues:
        startup_score = 100
    else:
        startup_score = max(0, 100 - 50 * len(startup_issues))

    validation_evidence = []
    validation_issues = []
    checked = audit.get("checked_component_files", 0)
    if isinstance(checked, int) and checked > 0:
        validation_evidence.append(f"{checked} component files have required metadata")
    else:
        validation_issues.append("no component metadata was validated")
    if audit.get("status") == "ERROR":
        validation_issues.extend(deterministic_issues)
    validation_score = 100 if not validation_issues else max(0, 100 - 20 * len(validation_issues))

    docs_evidence = []
    docs_issues = []
    readme = ""
    if readme_exists:
        try:
            readme = readme_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            docs_issues.append("README cannot be read as UTF-8")
        if isinstance(manifest.get("name"), str) and manifest["name"] in readme:
            docs_evidence.append("README names the plugin")
        else:
            docs_issues.append("README does not name the plugin")
        if "Components:" in readme or "component" in readme.lower():
            docs_evidence.append("README describes component coverage")
        else:
            docs_issues.append("README does not describe component coverage")
    else:
        docs_issues.append("README is missing")
    docs_score = 100 if not docs_issues else max(0, 100 - 25 * len(docs_issues))

    roles = {
        "deterministic-scanner": _local_role(
            deterministic_score,
            evidence=("read-only structural auditor",),
            issues=deterministic_issues,
        ),
        "startup-review": _local_role(
            startup_score, evidence=tuple(startup_evidence), issues=tuple(startup_issues)
        ),
        "validation-review": _local_role(
            validation_score, evidence=tuple(validation_evidence), issues=tuple(validation_issues)
        ),
        "docs-reliability-review": _local_role(
            docs_score, evidence=tuple(docs_evidence), issues=tuple(docs_issues)
        ),
    }
    score = round(sum(item["score"] for item in roles.values()) / len(roles))
    return {
        "status": "LOCAL_SCANNER_PASS" if score == 100 else "LOCAL_SCANNER_REVIEW",
        "scanner": LOCAL_SCANNER_ID,
        "roles": roles,
        "local_codex_compatibility_score": score,
        "agent_compatibility_score": None,
        "score_provenance": "DETERMINISTIC_LOCAL_CODEX_SCAN_NOT_UPSTREAM_AGENT_COMPATIBILITY",
        "upstream_scanner": "UNAVAILABLE",
        "runtime_executed": False,
        "components_executed": False,
        "network_used": False,
        "external_writes": False,
        "credentials_read": False,
        "reason": "local static Codex contract only; no upstream scanner or plugin runtime was executed",
    }


def compatibility_report(
    fixture_root: str | Path,
    *,
    scanner_result: Mapping[str, Any] | None = None,
    local_scan: bool = False,
) -> dict[str, Any]:
    """Combine a supplied real scanner result with local evidence.

    The adapter never computes, verifies, or promotes a score.  A caller may
    pass the scanner's own structured result, but its score remains explicitly
    unverified caller input and is never returned as ``agent_compatibility_score``.
    """

    result = inspect_compatibility_fixture(fixture_root)
    if not isinstance(local_scan, bool):
        raise AdapterError("local_scan must be boolean")
    if local_scan:
        result.update(local_plugin_compatibility_scan(fixture_root))
        result["status"] = "LOCAL_SCANNER_RESULT"
        return result
    if scanner_result is None:
        result["status"] = "SCANNER_UNAVAILABLE"
        return result
    if not isinstance(scanner_result, Mapping):
        raise AdapterError("scanner_result must be a mapping")
    result["status"] = "UNVERIFIED_SCANNER_RESULT_SUPPLIED"
    result["score_provenance"] = "UNVERIFIED_CALLER_INPUT"
    result["scanner_result_fields"] = tuple(sorted(str(key) for key in scanner_result))
    score = scanner_result.get("score")
    valid_score = (
        isinstance(score, (int, float))
        and not isinstance(score, bool)
        and math.isfinite(float(score))
        and 0 <= float(score) <= 100
    )
    if valid_score:
        result["unverified_scanner_score"] = score
        result["agent_compatibility_score"] = None
        result["reason"] = "numeric scanner result supplied but not independently verified; score withheld"
    else:
        result["unverified_scanner_score"] = None
        result["agent_compatibility_score"] = None
        result["reason"] = "scanner result lacks a finite score in the range 0..100; score withheld"
    return result


def _credential_paths(value: Any, path: str = "request") -> tuple[str, ...]:
    """Find credential-shaped keys at any depth without inspecting values."""

    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = re.sub(r"[_-]", "", key_text.lower())
            child_path = f"{path}.{key_text}"
            if normalized in _CREDENTIAL_KEY_NORMALIZED:
                findings.append(child_path)
            findings.extend(_credential_paths(child, child_path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            findings.extend(_credential_paths(child, f"{path}[{index}]"))
    return tuple(findings)


def sdk_reference_report(
    source_text: str,
    *,
    request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract SDK symbols while rejecting credential/runtime requests.

    This is intentionally a reference report.  It does not import
    ``@cursor/sdk`` or infer that a matching symbol proves runtime support.
    """

    if not isinstance(source_text, str) or not source_text.strip():
        raise AdapterError("source_text must be non-empty text")
    if request is not None and not isinstance(request, Mapping):
        raise AdapterError("request must be a mapping when supplied")
    requested = set()
    if request:
        requested = {str(key) for key in request}
        credential_paths = _credential_paths(request)
        if credential_paths:
            raise PermissionDenied(
                "credential or MCP configuration input is outside the reference-only boundary: "
                + ", ".join(credential_paths)
            )
        if request.get("execute") or request.get("authenticate") or request.get("network"):
            raise PermissionDenied("SDK execution, authentication, and network access are unavailable")
    symbols = tuple(symbol for symbol in _SDK_SYMBOLS if symbol in source_text)
    return {
        "status": "REFERENCE_ONLY",
        "symbols": symbols,
        "unrecognized_symbols": tuple(
            sorted(
                set(re.findall(r"\b(?:Agent|Cursor|run|agent)\.[A-Za-z]+\b", source_text))
                - set(symbols)
            )
        ),
        "runtime": "UNAVAILABLE",
        "credentials_read": False,
        "authenticated": False,
        "network_used": False,
        "external_writes": False,
        "request_keys": tuple(sorted(requested)),
        "reason": "external Cursor SDK reference inspected without installation or execution",
    }


def sdk_native_contract_report() -> dict[str, Any]:
    """Describe safe Codex capability mappings without importing Cursor SDK."""

    return {
        "status": "CODEX_NATIVE_MAPPING_REFERENCE_ONLY",
        "mappings": CODEX_NATIVE_SDK_MAPPING,
        "cursor_sdk_imported": False,
        "cursor_sdk_executed": False,
        "credentials_read": False,
        "authenticated": False,
        "network_used": False,
        "external_writes": False,
        "equivalence": "conceptual_only; native Codex task APIs are a different contract",
        "permission_boundary": "mapping does not create tasks or invoke tools",
        "reason": "safe native capability map for external SDK references; no Cursor runtime claim",
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("compatibility", "sdk-reference", "sdk-native-contract"))
    parser.add_argument("path", nargs="?", help="explicit local fixture root (compatibility mode only)")
    parser.add_argument("--local-scan", action="store_true", help="run the deterministic local Codex plugin scan")
    args = parser.parse_args()
    if args.mode == "compatibility":
        if not args.path:
            parser.error("compatibility mode requires an explicit fixture root")
        result = compatibility_report(args.path, local_scan=args.local_scan)
    elif args.mode == "sdk-reference":
        if args.path:
            parser.error("sdk-reference accepts source text on stdin; it never reads a path")
        result = sdk_reference_report(sys.stdin.read())
    else:
        if args.path or args.local_scan:
            parser.error("sdk-native-contract accepts no path or scan flag")
        result = sdk_native_contract_report()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
