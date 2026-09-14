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
        "token",
        "secret",
    }
)


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


def compatibility_report(
    fixture_root: str | Path,
    *,
    scanner_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Combine a supplied real scanner result with local evidence.

    The adapter never computes, verifies, or promotes a score.  A caller may
    pass the scanner's own structured result, but its score remains explicitly
    unverified caller input and is never returned as ``agent_compatibility_score``.
    """

    result = inspect_compatibility_fixture(fixture_root)
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


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("compatibility", "sdk-reference"))
    parser.add_argument("path", nargs="?", help="explicit local fixture root (compatibility mode only)")
    args = parser.parse_args()
    if args.mode == "compatibility":
        if not args.path:
            parser.error("compatibility mode requires an explicit fixture root")
        result = compatibility_report(args.path)
    else:
        if args.path:
            parser.error("sdk-reference accepts source text on stdin; it never reads a path")
        result = sdk_reference_report(sys.stdin.read())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
