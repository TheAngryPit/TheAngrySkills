"""Read-only Benny event and triage-marker gates.

This module is a native boundary fixture, not an automation runner.  It only
validates caller-supplied event/config data and returns a JSON-safe decision. It
does not call Slack, a tracker, an app controller, Git, a scheduler, or an
automation editor, and it never writes files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from typing import Any


def _result(status: str, reason: str, **fields: Any) -> dict[str, Any]:
    """Return an explicit no-write result for every gate outcome."""

    return {
        "status": status,
        "reason": reason,
        "external_writes": False,
        "scheduled": False,
        "activated": False,
        "write_actions": [],
        **fields,
    }


def _text(value: Any, label: str) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _nested_text(mapping: Mapping[str, Any], section: str, key: str) -> str | None:
    value = mapping.get(section)
    if not isinstance(value, Mapping):
        return None
    return _text(value.get(key), f"{section}.{key}")


def _config(config: Mapping[str, Any]) -> tuple[str, str, dict[str, str]] | None:
    channel = _nested_text(config, "slack", "source_channel_id")
    identity = _nested_text(config, "slack", "triage_identity_user_id")
    markers = config.get("verdict_markers")
    if not channel or not identity or not isinstance(markers, Mapping):
        return None
    parsed: dict[str, str] = {}
    for name in ("bug", "performance", "other"):
        marker = _text(markers.get(name), f"verdict_markers.{name}")
        if not marker or marker in parsed.values():
            return None
        parsed[name] = marker
    return channel, identity, parsed


def _event_channel(event: Mapping[str, Any]) -> str | None:
    values = [
        _text(event.get(name), name)
        for name in ("source_channel_id", "channel_id")
        if event.get(name) is not None
    ]
    if not values or any(value != values[0] for value in values):
        return None
    return values[0]


def _unsafe_request(event: Mapping[str, Any]) -> bool:
    return bool(
        event.get("activation_requested")
        or event.get("schedule_requested")
        or event.get("enable_requested")
    )


def evaluate_intake_event(
    event: Mapping[str, Any], config: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate a new top-level report without posting or scheduling anything.

    A ready result freezes the top-level message timestamp as the source root
    timestamp. Replies are rejected so a caller cannot accidentally move the
    source coordinate to a child message.
    """

    if not isinstance(event, Mapping) or not isinstance(config, Mapping):
        return _result("BLOCKED", "event and config must be mappings")
    parsed = _config(config)
    if parsed is None:
        return _result("BLOCKED", "required source channel, triage identity, or markers are missing")
    source_channel, _, _ = parsed
    channel = _event_channel(event)
    if channel != source_channel:
        return _result("BLOCKED", "event channel does not match configured source channel")
    if _unsafe_request(event):
        return _result("BLOCKED", "event requests scheduling or activation")
    message_ts = _text(event.get("message_ts"), "message_ts")
    if not message_ts:
        return _result("BLOCKED", "top-level report has no message timestamp")
    thread_ts = event.get("thread_ts")
    if thread_ts not in (None, ""):
        return _result("BLOCKED", "reply event cannot become a new source root")
    if event.get("is_top_level") is False:
        return _result("BLOCKED", "event is not top-level")
    return _result(
        "READY_FOR_TRIAGE",
        "source channel and immutable top-level root accepted",
        source_channel_id=source_channel,
        source_thread_ts=message_ts,
        source_message_ts=message_ts,
    )


def accept_triage_reply(
    reply: Mapping[str, Any],
    config: Mapping[str, Any],
    root: Mapping[str, Any],
) -> dict[str, Any]:
    """Accept only one trusted marker reply under one frozen source root."""

    if not isinstance(reply, Mapping) or not isinstance(config, Mapping) or not isinstance(root, Mapping):
        return _result("BLOCKED", "reply, config, and root must be mappings")
    parsed = _config(config)
    if parsed is None:
        return _result("BLOCKED", "required source channel, triage identity, or markers are missing")
    source_channel, identity, markers = parsed
    channel = _event_channel(reply)
    root_channel = _event_channel(root)
    root_ts = _text(root.get("source_thread_ts") or root.get("thread_ts"), "root thread")
    reply_thread = _text(reply.get("thread_ts"), "reply thread")
    if channel != source_channel or root_channel != source_channel:
        return _result("BLOCKED", "reply or root channel does not match configured source channel")
    if not root_ts or reply_thread != root_ts:
        return _result("BLOCKED", "reply is outside the frozen source thread")
    if reply.get("is_reply") is not True or not reply_thread:
        return _result("BLOCKED", "triage marker must be a source-thread reply")
    if _text(reply.get("author_id"), "author_id") != identity:
        return _result("BLOCKED", "triage marker author is not the configured identity")
    body = _text(reply.get("text"), "text")
    if not body:
        return _result("WAITING_FOR_TRIAGE", "triage reply has no text")
    counts = {name: len(re.findall(re.escape(marker), body)) for name, marker in markers.items()}
    total = sum(counts.values())
    if total == 0:
        return _result("WAITING_FOR_TRIAGE", "no configured triage marker is present")
    if total != 1:
        return _result("BLOCKED", "triage reply must contain exactly one configured marker", marker_counts=counts)
    category = next(name for name, count in counts.items() if count)
    if category == "other":
        return _result(
            "TRIAGE_STOPPED",
            "other marker stops repro without a write",
            category=category,
            source_thread_ts=root_ts,
        )
    return _result(
        "TRIAGE_ACCEPTED",
        "trusted bug or performance marker accepted",
        category=category,
        marker=markers[category],
        source_thread_ts=root_ts,
    )


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("intake", "triage-reply"))
    args = parser.parse_args()
    try:
        payload = json.load(sys.stdin)
        result = (
            evaluate_intake_event(payload.get("event"), payload.get("config"))
            if args.mode == "intake"
            else accept_triage_reply(payload.get("reply"), payload.get("config"), payload.get("root"))
        )
    except (json.JSONDecodeError, AttributeError, TypeError) as exc:
        result = _result("BLOCKED", f"invalid JSON payload: {exc}")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
