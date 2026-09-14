import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from cursor_bot_ui_adapters import (  # noqa: E402
    BotUiAdapterError,
    MockResponse,
    MockWebhook,
    build_server_request,
    dispatch_local_mock,
    run_bot_ui_fixture,
)


class CursorBotUiAdapterTests(unittest.TestCase):
    def test_server_request_keeps_key_out_of_browser_payload(self):
        request = build_server_request(
            "http://127.0.0.1:4173/webhook",
            "secret",
            {"action": "refresh"},
        )
        self.assertEqual(request["method"], "POST")
        self.assertEqual(request["headers"]["Authorization"], "Bearer secret")
        self.assertEqual(request["headers"]["X-Automation-Key"], "secret")
        self.assertEqual(json.loads(request["body"]), {"action": "refresh"})

    def test_non_local_endpoint_and_malformed_payload_are_rejected(self):
        with self.assertRaisesRegex(BotUiAdapterError, "local HTTP"):
            build_server_request("https://api2.cursor.sh/automations/webhook/id", "secret", {})
        with self.assertRaisesRegex(BotUiAdapterError, "JSON object"):
            build_server_request("http://localhost:4173/webhook", "secret", [])
        with self.assertRaisesRegex(BotUiAdapterError, "credential"):
            build_server_request("http://localhost:4173/webhook", "secret", {"token": "leak"})
        with self.assertRaisesRegex(BotUiAdapterError, "credential"):
            build_server_request(
                "http://localhost:4173/webhook",
                "secret",
                {"form": {"metadata": [{"sender_key": "leak"}]}},
            )
        with self.assertRaisesRegex(BotUiAdapterError, "userinfo"):
            build_server_request("http://user:pass@localhost:4173/webhook", "secret", {})

    def test_timeout_logs_payload_once_without_retry_or_secret(self):
        with tempfile.TemporaryDirectory() as temporary:
            failure_log = Path(temporary) / "failures.jsonl"
            result = dispatch_local_mock(
                "http://localhost:4173/webhook",
                "secret",
                {"action": "refresh"},
                MockWebhook(fail_with_timeout=True),
                failure_log,
                Path(temporary),
            )
            self.assertEqual(result["status"], "FAILED")
            self.assertEqual(result["attempts"], 1)
            self.assertFalse(result["retried"])
            self.assertNotIn("secret", json.dumps(result))
            self.assertEqual(failure_log.read_text(), '{"action": "refresh"}\n')

    def test_timeout_reason_does_not_reflect_responder_error_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            failure_log = Path(temporary) / "failures.jsonl"

            def responder(_request, _timeout):
                raise TimeoutError("secret-in-url-and-header")

            result = dispatch_local_mock(
                "http://localhost:4173/webhook",
                "secret",
                {"action": "refresh"},
                responder,
                failure_log,
                Path(temporary),
            )
            self.assertEqual(result["reason"], "webhook timed out after 8s")
            self.assertNotIn("secret-in-url-and-header", json.dumps(result))

    def test_non_200_response_is_failed_and_not_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            failure_log = Path(temporary) / "failures.jsonl"
            result = dispatch_local_mock(
                "http://localhost:4173/webhook",
                "secret",
                {"action": "refresh"},
                MockWebhook(response=MockResponse(503)),
                failure_log,
                Path(temporary),
            )
            self.assertEqual(result["status"], "FAILED")
            self.assertEqual(result["http_status"], 503)
            self.assertFalse(result["retried"])
            dispatch_local_mock(
                "http://localhost:4173/webhook",
                "secret",
                {"action": "retry-me"},
                MockWebhook(response=MockResponse(503)),
                failure_log,
                Path(temporary),
            )
            self.assertEqual(len(failure_log.read_text().splitlines()), 2)

    def test_symlinked_failure_log_is_rejected_without_touching_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sentinel = root / "sentinel.jsonl"
            sentinel.write_text("preserve\n")
            failure_log = root / "failures.jsonl"
            failure_log.symlink_to(sentinel)
            with self.assertRaisesRegex(BotUiAdapterError, "regular file"):
                dispatch_local_mock(
                    "http://localhost:4173/webhook",
                    "secret",
                    {"action": "refresh"},
                    MockWebhook(fail_with_timeout=True),
                    failure_log,
                    root,
                )
            self.assertEqual(sentinel.read_text(), "preserve\n")

    def test_fixture_reports_external_boundary_without_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_bot_ui_fixture(Path(temporary))
            self.assertEqual(result["status"], "FIXTURE_ONLY")
            self.assertEqual(result["success"]["status"], "DELIVERED")
            self.assertEqual(result["timeout"]["status"], "FAILED")
            self.assertEqual(result["request_count"], 1)
            self.assertFalse(result["key_in_redacted_evidence"])
            self.assertTrue(result["malformed"])
            self.assertTrue(result["non_local"])


if __name__ == "__main__":
    unittest.main()
