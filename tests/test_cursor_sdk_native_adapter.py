"""Behavior proofs for the bounded Cursor SDK to Codex migration bridge."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cursor_sdk_native_adapter import (  # noqa: E402
    AdapterError,
    PermissionDenied,
    build_native_migration_plan,
    run_native_migration,
)


class CursorSdkNativeAdapterTests(unittest.TestCase):
    def test_positive_prompt_plan_is_bounded_and_maps_to_native_create(self) -> None:
        result = build_native_migration_plan(
            {
                "operation": "prompt",
                "prompt": "Inspect the local fixture and report findings.",
                "target": {"type": "projectless", "directoryName": "sdk-proof"},
                "authorized": True,
            }
        )
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["operations"][0]["tool"], "create_thread")
        self.assertEqual(
            result["operations"][0]["arguments"]["target"],
            {"type": "projectless", "directoryName": "sdk-proof"},
        )
        self.assertTrue(result["authorization_required"])
        self.assertTrue(result["authorized"])
        self.assertFalse(result["cursor_sdk_imported"])
        self.assertFalse(result["cursor_sdk_executed"])
        self.assertFalse(result["mcp_configured"])
        self.assertFalse(result["external_writes"])

    def test_positive_read_only_native_bridge_path_is_observable(self) -> None:
        calls: list[tuple[str, dict]] = []

        def wait_threads(**arguments):
            calls.append(("wait_threads", arguments))
            return {"status": "completed", "threadId": "native-fixture"}

        def read_thread(**arguments):
            calls.append(("read_thread", arguments))
            return {"status": "completed", "turns": []}

        result = run_native_migration(
            {
                "operation": "stream",
                "thread_id": "native-fixture",
                "host_id": "local-fixture",
                "timeout_ms": 250,
                "turn_limit": 2,
                "max_output_chars": 500,
            },
            native_surface={"wait_threads": wait_threads, "read_thread": read_thread},
            execute=True,
        )
        self.assertEqual(result["status"], "NATIVE_DELEGATION_OBSERVED")
        self.assertEqual([name for name, _ in calls], ["wait_threads", "read_thread"])
        self.assertEqual(calls[0][1]["targets"], [{"threadId": "native-fixture", "hostId": "local-fixture"}])
        self.assertEqual(calls[1][1]["maxOutputCharsPerItem"], 500)
        self.assertFalse(result["native_execution_attested"])
        self.assertFalse(result["external_writes"])
        self.assertFalse(result["cursor_sdk_executed"])
        self.assertFalse(result["streaming_equivalent"])

    def test_unavailable_and_missing_native_capability_are_explicit(self) -> None:
        request = {"operation": "wait", "thread_id": "known-thread", "timeout_ms": 0}
        unavailable = run_native_migration(request, execute=True)
        self.assertEqual(unavailable["status"], "UNAVAILABLE")
        self.assertFalse(unavailable["native_execution_attempted"])
        self.assertFalse(unavailable["external_writes"])

        missing = run_native_migration(
            {"operation": "stream", "thread_id": "known-thread"},
            native_surface={"wait_threads": lambda **_: {"status": "completed"}},
            execute=True,
        )
        self.assertEqual(missing["status"], "MISSING_CAPABILITY")
        self.assertEqual(missing["missing_tools"], ("read_thread",))
        self.assertFalse(missing["native_execution_attempted"])

    def test_mutating_native_path_requires_explicit_authorization(self) -> None:
        calls: list[str] = []

        def create_thread(**_):
            calls.append("create_thread")
            return {"status": "created"}

        result = run_native_migration(
            {"operation": "create", "prompt": "do not dispatch"},
            native_surface={"create_thread": create_thread},
            execute=True,
        )
        self.assertEqual(result["status"], "PERMISSION_REQUIRED")
        self.assertEqual(calls, [])
        self.assertFalse(result["native_execution_attempted"])

    def test_credentials_and_mcp_fail_closed_before_bridge_call(self) -> None:
        calls: list[str] = []
        surface = {
            "wait_threads": lambda **_: calls.append("wait") or {"status": "completed"},
        }
        for unsafe in (
            {"apiKey": "secret"},
            {"options": {"CURSOR_API_KEY": "secret"}},
            {"mcpServers": {"local": {"command": "echo"}}},
            {"target": {"mcp": {"name": "local"}}},
        ):
            request = {"operation": "wait", "thread_id": "known-thread", **unsafe}
            result = run_native_migration(request, native_surface=surface, execute=True)
            self.assertEqual(result["status"], "FAIL_CLOSED")
            self.assertFalse(result["native_execution_attempted"])
        self.assertEqual(calls, [])

        with self.assertRaises(PermissionDenied):
            build_native_migration_plan(
                {"operation": "wait", "thread_id": "known-thread", "mcpServers": {}}
            )

    def test_bridge_error_is_bounded_and_does_not_echo_exception(self) -> None:
        def wait_threads(**_):
            raise RuntimeError("CURSOR_API_KEY=do-not-echo")

        result = run_native_migration(
            {"operation": "wait", "thread_id": "known-thread"},
            native_surface={"wait_threads": wait_threads},
            execute=True,
        )
        self.assertEqual(result["status"], "NATIVE_ERROR")
        self.assertEqual(result["failed_tool"], "wait_threads")
        self.assertNotIn("CURSOR_API_KEY", json.dumps(result))
        self.assertNotIn("do-not-echo", json.dumps(result))
        self.assertTrue(result["native_execution_attempted"])

    def test_bridge_error_result_and_credential_result_fail_closed(self) -> None:
        native_error = run_native_migration(
            {"operation": "wait", "thread_id": "known-thread"},
            native_surface={"wait_threads": lambda **_: {"status": "error", "message": "private"}},
            execute=True,
        )
        self.assertEqual(native_error["status"], "NATIVE_ERROR")
        self.assertEqual(native_error["failed_tool"], "wait_threads")
        self.assertNotIn("private", json.dumps(native_error))

        unsafe_result = run_native_migration(
            {"operation": "wait", "thread_id": "known-thread"},
            native_surface={"wait_threads": lambda **_: {"status": "completed", "token": "secret"}},
            execute=True,
        )
        self.assertEqual(unsafe_result["status"], "FAIL_CLOSED")
        self.assertFalse(unsafe_result["external_writes"])

    def test_invalid_bounds_and_cli_unavailable_path(self) -> None:
        with self.assertRaises(AdapterError):
            build_native_migration_plan(
                {"operation": "stream", "thread_id": "thread", "turn_limit": 21}
            )
        completed = subprocess.run(
            [sys.executable, "scripts/cursor_sdk_native_adapter.py", "run", "--execute"],
            cwd=Path(__file__).resolve().parent.parent,
            input=json.dumps({"operation": "wait", "thread_id": "thread"}),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertFalse(result["native_execution_attempted"])


if __name__ == "__main__":
    unittest.main()
