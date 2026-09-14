"""Safe local adapter for the source bot-UI webhook contract."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse


class BotUiAdapterError(ValueError):
    """Raised when the local mock boundary receives invalid input."""


@dataclass(frozen=True)
class MockResponse:
    status_code: int = 200


@dataclass
class MockWebhook:
    response: MockResponse = field(default_factory=MockResponse)
    fail_with_timeout: bool = False
    requests: list[dict[str, object]] = field(default_factory=list)

    def __call__(self, request: dict[str, object], timeout_seconds: int) -> MockResponse:
        self.requests.append(request)
        if self.fail_with_timeout:
            raise TimeoutError(f"mock webhook exceeded {timeout_seconds}s")
        return self.response


def _validate_local_webhook(url: str) -> str:
    if not isinstance(url, str) or not url:
        raise BotUiAdapterError("webhook URL must be non-empty text")
    parsed = urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise BotUiAdapterError("the safe adapter accepts only a local HTTP webhook")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise BotUiAdapterError("webhook URL must not contain userinfo, query, or fragment")
    return url


def _contains_secret_field(value: object, secret_fields: set[str]) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if str(key).casefold() in secret_fields or _contains_secret_field(nested, secret_fields):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_secret_field(item, secret_fields) for item in value)
    return False


def _validate_payload(payload: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        raise BotUiAdapterError("browser payload must be a JSON object")
    secret_fields = {"api_key", "authorization", "cookie", "credential", "key", "secret", "sender_key", "token", "x-automation-key"}
    if _contains_secret_field(payload, secret_fields):
        raise BotUiAdapterError("browser payload must not contain credential fields")
    try:
        json.dumps(dict(payload), ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError) as error:
        raise BotUiAdapterError("browser payload must be JSON serializable") from error
    return dict(payload)


def build_server_request(
    webhook_url: str,
    sender_key: str,
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Build the server-side request without exposing the key to browser data."""

    url = _validate_local_webhook(webhook_url)
    if not isinstance(sender_key, str) or not sender_key:
        raise BotUiAdapterError("sender key must be supplied to the server")
    safe_payload = _validate_payload(payload)
    body = json.dumps(safe_payload, ensure_ascii=False, sort_keys=True)
    return {
        "method": "POST",
        "url": url,
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {sender_key}",
            "X-Automation-Key": sender_key,
        },
        "body": body,
    }


def _redacted_request(request: Mapping[str, object]) -> dict[str, object]:
    headers = dict(request["headers"])
    headers["Authorization"] = "<redacted>"
    headers["X-Automation-Key"] = "<redacted>"
    return {"method": request["method"], "url": request["url"], "headers": headers, "body": request["body"]}


def _validate_failure_log(failure_log: Path, log_root: Path) -> None:
    if not log_root.is_absolute() or not log_root.is_dir() or log_root.is_symlink():
        raise BotUiAdapterError("failure log root must be an existing regular directory")
    if not failure_log.is_absolute() or failure_log.parent != log_root:
        raise BotUiAdapterError("failure log must stay directly inside the fixture root")
    if failure_log.exists() and (failure_log.is_symlink() or not failure_log.is_file()):
        raise BotUiAdapterError("failure log must be a regular file")


def _record_failure(failure_log: Path, log_root: Path, payload: Mapping[str, object]) -> None:
    _validate_failure_log(failure_log, log_root)
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(failure_log, flags, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False) + "\n")


def dispatch_local_mock(
    webhook_url: str,
    sender_key: str,
    payload: Mapping[str, object],
    responder: Callable[[dict[str, object], int], MockResponse],
    failure_log: Path,
    log_root: Path,
) -> dict[str, object]:
    """Exercise one server-to-webhook attempt and retain only safe failure evidence."""

    request = build_server_request(webhook_url, sender_key, payload)
    _validate_failure_log(failure_log, log_root)
    result = {
        "attempts": 1,
        "timeout_seconds": 8,
        "request": _redacted_request(request),
        "retried": False,
    }
    try:
        response = responder(request, 8)
    except TimeoutError as error:
        _record_failure(failure_log, log_root, payload)
        result.update({"status": "FAILED", "reason": str(error), "failure_logged": True})
        return result
    if response.status_code != 200:
        _record_failure(failure_log, log_root, payload)
        result.update({"status": "FAILED", "http_status": response.status_code, "reason": f"webhook returned HTTP {response.status_code}", "failure_logged": True})
        return result
    result.update({"status": "DELIVERED", "http_status": response.status_code, "failure_logged": False})
    return result


def run_bot_ui_fixture(root: Path) -> dict[str, object]:
    """Run positive, malformed, timeout, and non-local boundary checks offline."""

    root.mkdir(parents=True, exist_ok=True)
    webhook = MockWebhook()
    payload = {"action": "refresh", "message": "safe fixture"}
    success = dispatch_local_mock(
        "http://127.0.0.1:4173/webhook",
        "fixture-secret",
        payload,
        webhook,
        root / "failures.jsonl",
        root,
    )
    timeout_log = root / "timeout.jsonl"
    timeout = dispatch_local_mock(
        "http://127.0.0.1:4173/webhook",
        "fixture-secret",
        payload,
        MockWebhook(fail_with_timeout=True),
        timeout_log,
        root,
    )
    malformed = None
    try:
        build_server_request("http://127.0.0.1:4173/webhook", "fixture-secret", ["not", "an", "object"])
    except BotUiAdapterError as error:
        malformed = str(error)
    non_local = None
    try:
        build_server_request("https://api2.cursor.sh/automations/webhook/id", "fixture-secret", payload)
    except BotUiAdapterError as error:
        non_local = str(error)
    return {
        "status": "FIXTURE_ONLY",
        "success": success,
        "timeout": timeout,
        "malformed": malformed,
        "non_local": non_local,
        "key_in_redacted_evidence": "fixture-secret" in json.dumps(success),
        "request_count": len(webhook.requests),
    }
