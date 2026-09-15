#!/usr/bin/env python3
"""Bounded migration bridge for the held Cursor SDK mirror.

The Cursor source describes ``@cursor/sdk`` operations that are unavailable in
this repository's Python runtime.  This module translates a small, explicit
request into the closest native Codex tool calls.  A caller may supply an
already-authorized native bridge for a read-only proof, but this module never
imports Cursor, reads credentials, configures MCP, performs network I/O, or
creates a Codex task by itself.

The distinction between a migration plan and a delegated native result is
intentional.  A plan proves the adapter's bounded translation.  A delegated
result only proves that a caller supplied a bridge returned a well-formed
result; it does not establish Cursor SDK parity or attest the bridge's host.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable, Mapping
from typing import Any


class AdapterError(ValueError):
    """Invalid migration input or an unsafe bridge response."""


class PermissionDenied(AdapterError):
    """The request crosses the credential, MCP, or mutation boundary."""


MAX_PROMPT_CHARS = 16_000
MAX_TIMEOUT_MS = 60_000
MAX_TURN_LIMIT = 20
MAX_OUTPUT_CHARS = 4_000
_OPERATIONS = frozenset({"prompt", "create", "resume", "send", "wait", "stream"})
_MUTATING_OPERATIONS = frozenset({"prompt", "create", "resume", "send"})
_TARGET_TYPES = frozenset({"projectless", "project"})
_SENSITIVE_KEY_PARTS = frozenset(
    {
        "apikey",
        "authorization",
        "auth",
        "authentication",
        "clientid",
        "clientsecret",
        "credential",
        "credentials",
        "env",
        "headers",
        "mcp",
        "mcpserver",
        "mcpservers",
        "password",
        "secret",
        "token",
    }
)


def _key_is_sensitive(key: object) -> bool:
    normalized = re.sub(r"[_-]", "", str(key).lower())
    return normalized in _SENSITIVE_KEY_PARTS or normalized.startswith("cursorapikey")


def _sensitive_paths(value: Any, path: str = "request") -> tuple[str, ...]:
    """Find sensitive-shaped keys without reading or echoing their values."""

    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if _key_is_sensitive(key):
                findings.append(child_path)
            findings.extend(_sensitive_paths(child, child_path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            findings.extend(_sensitive_paths(child, f"{path}[{index}]"))
    return tuple(findings)


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdapterError(f"{label} must be an object")
    return value


def _require_text(value: Any, label: str, *, maximum: int = MAX_PROMPT_CHARS) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdapterError(f"{label} must be non-empty text")
    if len(value) > maximum:
        raise AdapterError(f"{label} exceeds the bounded maximum of {maximum} characters")
    if any(ord(char) < 32 and char not in "\n\t\r" for char in value):
        raise AdapterError(f"{label} contains control characters")
    return value


def _bounded_int(value: Any, label: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise AdapterError(f"{label} must be an integer from {minimum} to {maximum}")
    return value


def _target(value: Any) -> dict[str, Any]:
    """Validate the small native target subset used by this bridge.

    ``projectless`` is the safe default for a prepared plan.  The adapter does
    not resolve project paths or infer a repository from ambient state.
    """

    if value is None:
        return {"type": "projectless"}
    target = _require_mapping(value, "target")
    if _sensitive_paths(target, "target"):
        raise PermissionDenied("credential or MCP configuration is outside the native bridge boundary")
    target_type = target.get("type")
    if target_type not in _TARGET_TYPES:
        raise AdapterError("target.type must be projectless or project")
    if target_type == "project":
        project_id = _require_text(target.get("projectId"), "target.projectId", maximum=256)
        if "/" in project_id or "\\" in project_id:
            raise AdapterError("target.projectId must be an identifier")
        return {"type": "project", "projectId": project_id}
    directory_name = target.get("directoryName")
    if directory_name is None:
        return {"type": "projectless"}
    directory_name = _require_text(directory_name, "target.directoryName", maximum=128)
    if directory_name in {".", ".."} or "/" in directory_name or "\\" in directory_name:
        raise AdapterError("target.directoryName must be one path component")
    return {"type": "projectless", "directoryName": directory_name}


def _explicit_authorization(request: Mapping[str, Any]) -> bool:
    value = request.get("authorized", request.get("explicit_authorization", False))
    if not isinstance(value, bool):
        raise AdapterError("authorized must be boolean")
    return value


def _thread_target(request: Mapping[str, Any]) -> dict[str, str]:
    thread_id = _require_text(request.get("thread_id"), "thread_id", maximum=256)
    if any(char in thread_id for char in "\r\n"):
        raise AdapterError("thread_id must be a single-line identifier")
    result = {"threadId": thread_id}
    host_id = request.get("host_id")
    if host_id is not None:
        result["hostId"] = _require_text(host_id, "host_id", maximum=256)
    return result


def build_native_migration_plan(request: Mapping[str, Any]) -> dict[str, Any]:
    """Translate one Cursor SDK-shaped request to native Codex operations.

    The function is pure: it performs no native call and returns no secret or
    ambient project information.  Mutation requests carry an explicit
    authorization requirement that the execution function enforces again.
    """

    request = _require_mapping(request, "request")
    if _sensitive_paths(request):
        raise PermissionDenied("credential or MCP configuration is outside the native bridge boundary")
    operation = request.get("operation")
    if operation not in _OPERATIONS:
        raise AdapterError("operation must be one of prompt, create, resume, send, wait, or stream")

    operations: list[dict[str, Any]] = []
    if operation in {"prompt", "create"}:
        prompt = _require_text(request.get("prompt"), "prompt")
        arguments: dict[str, Any] = {
            "prompt": prompt,
            "target": _target(request.get("target")),
        }
        operations.append({"tool": "create_thread", "arguments": arguments})
    elif operation in {"resume", "send"}:
        prompt = _require_text(request.get("prompt"), "prompt")
        arguments = _thread_target(request)
        arguments["prompt"] = prompt
        operations.append({"tool": "send_message_to_thread", "arguments": arguments})
    elif operation == "wait":
        timeout = _bounded_int(request.get("timeout_ms", 30_000), "timeout_ms", 0, MAX_TIMEOUT_MS)
        operations.append(
            {
                "tool": "wait_threads",
                "arguments": {
                    "targets": [_thread_target(request)],
                    "timeoutMs": timeout,
                },
            }
        )
    else:  # stream: bounded wait then readback, with no streaming claim.
        timeout = _bounded_int(request.get("timeout_ms", 30_000), "timeout_ms", 0, MAX_TIMEOUT_MS)
        turn_limit = _bounded_int(request.get("turn_limit", 5), "turn_limit", 1, MAX_TURN_LIMIT)
        max_output = _bounded_int(
            request.get("max_output_chars", 2_000), "max_output_chars", 1, MAX_OUTPUT_CHARS
        )
        target = _thread_target(request)
        operations.extend(
            (
                {
                    "tool": "wait_threads",
                    "arguments": {"targets": [target], "timeoutMs": timeout},
                },
                {
                    "tool": "read_thread",
                    "arguments": {
                        **target,
                        "turnLimit": turn_limit,
                        "includeOutputs": False,
                        "maxOutputCharsPerItem": max_output,
                    },
                },
            )
        )

    authorized = _explicit_authorization(request) if operation in _MUTATING_OPERATIONS else False
    return {
        "status": "READY",
        "operation": operation,
        "operations": operations,
        "authorization_required": operation in _MUTATING_OPERATIONS,
        "authorized": authorized,
        "cursor_sdk_runtime": "UNAVAILABLE",
        "cursor_sdk_imported": False,
        "cursor_sdk_executed": False,
        "streaming_equivalent": False,
        "mcp_configured": False,
        "credentials_read": False,
        "network_used": False,
        "external_writes": False,
        "execution_boundary": "caller_supplied_native_codex_bridge_only",
    }


def _common_result(**values: Any) -> dict[str, Any]:
    return {
        "cursor_sdk_imported": False,
        "cursor_sdk_executed": False,
        "credentials_read": False,
        "credentials_exposed": False,
        "mcp_configured": False,
        "network_used_by_adapter": False,
        "external_writes_by_adapter": False,
        "native_execution_attested": False,
        "streaming_equivalent": False,
        **values,
    }


def _bridge_methods(surface: Mapping[str, Any], tools: tuple[str, ...]) -> tuple[str, ...]:
    if _sensitive_paths(surface, "native_surface"):
        raise PermissionDenied("credential or MCP configuration is outside the native bridge boundary")
    missing = tuple(tool for tool in tools if not callable(surface.get(tool)))
    return missing


def _safe_native_result(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdapterError("native bridge result must be an object")
    if _sensitive_paths(value, "native_result"):
        raise PermissionDenied("credential or MCP data in a native result is rejected")
    return value


def _result_failed(value: Mapping[str, Any]) -> bool:
    status = value.get("status")
    return isinstance(status, str) and status.lower() in {"error", "failed", "failure", "cancelled"}


def run_native_migration(
    request: Mapping[str, Any],
    *,
    native_surface: Mapping[str, Callable[..., Mapping[str, Any]]] | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    """Prepare or delegate a bounded migration through a supplied native bridge.

    ``execute`` defaults to false.  With no bridge, the result is
    ``UNAVAILABLE``.  A supplied bridge is an external capability boundary;
    this function only calls the named methods and validates their result
    shapes.  It does not make Cursor SDK calls or infer runtime equivalence.
    """

    if not isinstance(execute, bool):
        raise AdapterError("execute must be boolean")
    try:
        plan = build_native_migration_plan(request)
    except PermissionDenied as exc:
        return _common_result(
            status="FAIL_CLOSED",
            reason=str(exc),
            native_execution_attempted=False,
            external_writes=False,
        )
    except AdapterError:
        raise

    if not execute:
        return _common_result(
            status="READY",
            plan=plan,
            native_execution_attempted=False,
            external_writes=False,
            reason="bounded native operation plan prepared; execution was not requested",
        )
    if native_surface is None:
        return _common_result(
            status="UNAVAILABLE",
            plan=plan,
            native_execution_attempted=False,
            external_writes=False,
            reason="native Codex bridge was not supplied in this session",
        )
    if not isinstance(native_surface, Mapping):
        raise AdapterError("native_surface must be an object mapping native tool names to callables")
    if plan["authorization_required"] and not plan["authorized"]:
        return _common_result(
            status="PERMISSION_REQUIRED",
            plan=plan,
            native_execution_attempted=False,
            external_writes=False,
            reason="mutating native task operation requires explicit authorization",
        )

    tool_names = tuple(item["tool"] for item in plan["operations"])
    try:
        missing = _bridge_methods(native_surface, tool_names)
    except PermissionDenied as exc:
        return _common_result(
            status="FAIL_CLOSED",
            plan=plan,
            reason=str(exc),
            native_execution_attempted=False,
            external_writes=False,
        )
    if missing:
        return _common_result(
            status="MISSING_CAPABILITY",
            plan=plan,
            missing_tools=missing,
            native_execution_attempted=False,
            external_writes=False,
            reason="required native Codex bridge method is unavailable",
        )

    observed: list[dict[str, Any]] = []
    for operation in plan["operations"]:
        tool = operation["tool"]
        try:
            value = _safe_native_result(native_surface[tool](**operation["arguments"]))
        except PermissionDenied as exc:
            return _common_result(
                status="FAIL_CLOSED",
                plan=plan,
                observed=observed,
                reason=str(exc),
                native_execution_attempted=True,
                external_writes=False,
            )
        except Exception:
            # Do not return exception messages: an external bridge may include
            # credentials, paths, or provider internals in its exception text.
            return _common_result(
                status="NATIVE_ERROR",
                plan=plan,
                observed=observed,
                failed_tool=tool,
                reason="caller-supplied native bridge raised an error",
                native_execution_attempted=True,
                external_writes=False,
            )
        observed.append({"tool": tool, "status": value.get("status", "returned")})
        if _result_failed(value):
            return _common_result(
                status="NATIVE_ERROR",
                plan=plan,
                observed=observed,
                failed_tool=tool,
                reason="caller-supplied native bridge returned an error status",
                native_execution_attempted=True,
                external_writes=False,
            )

    mutation_attempted = bool(plan["authorization_required"])
    return _common_result(
        status="NATIVE_DELEGATION_OBSERVED",
        plan=plan,
        observed=observed,
        native_execution_attempted=True,
        native_execution_attested=False,
        delegated_bridge_result=True,
        external_writes=False,
        native_external_mutation_attempted=mutation_attempted,
        reason=(
            "caller-supplied bridge returned bounded results; this does not attest "
            "Cursor SDK runtime or native host execution"
        ),
    )


def sdk_native_migration_report(request: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Public alias used by the overlay and downstream callers."""

    return run_native_migration(request, **kwargs)


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    parser.add_argument("--execute", action="store_true", help="delegate only through a supplied in-process bridge")
    args = parser.parse_args()
    try:
        request = json.load(sys.stdin)
        if args.mode == "plan":
            result = build_native_migration_plan(request)
        else:
            # The CLI intentionally has no bridge injection surface.  It can
            # therefore only produce the explicit unavailable result.
            result = run_native_migration(request, execute=args.execute)
    except (AdapterError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
