"""Local, credential-free behavior fixtures for the pinned Grok voice skills.

The upstream skills describe xAI STT, TTS, realtime WebSocket, microphone and
playback integrations.  This module deliberately does not invoke those
surfaces.  It supplies a small local route for exercising request validation,
server-only credential boundaries, a deterministic synthetic response, a
malformed-event diagnostic, and read-only voice-log diagnosis.

The fixtures are evidence for the local adapter only.  They do not promote the
unproven provider, microphone, playback, network, or production capabilities.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any, Iterable, Mapping


class VoiceAdapterError(ValueError):
    """Invalid fixture input or an unsafe fixture boundary."""


class MissingVoiceCapability(VoiceAdapterError):
    """A live provider capability is unavailable in this local adapter."""


class VoiceRedactionError(VoiceAdapterError):
    """A log entry could not be safely redacted."""


SUPPORTED_SAMPLE_RATES = frozenset({8000, 16000, 22050, 24000, 44100, 48000})
AUDIO_EVENT_TYPES = frozenset(
    {
        "response.output_audio.delta",
        "response.audio.delta",
        "input_audio_buffer.append",
        "audio.delta",
    }
)
SENSITIVE_KEY_PARTS = frozenset(
    {"token", "api_key", "apikey", "authorization", "client_secret", "secret"}
)


def unavailable_provider(capability: str) -> dict[str, Any]:
    """Return an explicit no-call result for an unproven live capability."""

    if not isinstance(capability, str) or not capability.strip():
        raise VoiceAdapterError("capability must be non-empty text")
    return {
        "status": "UNAVAILABLE",
        "capability": capability,
        "reason": "live provider capability is not proven in this Codex session",
        "external_call": False,
        "credential_exposed": False,
        "fallback": "use the local mock fixture and keep the skill held",
    }


def server_credential_boundary(capability: str) -> dict[str, Any]:
    """Describe the server-only credential boundary without accepting a secret."""

    result = unavailable_provider(capability)
    result.update(
        {
            "credential_location": "application-server-only",
            "client_credential": False,
            "provider_request": "not attempted",
        }
    )
    return result


def _validate_audio(audio: bytes | bytearray | memoryview, filename: str, sample_rate: int) -> bytes:
    if not isinstance(audio, (bytes, bytearray, memoryview)) or not audio:
        raise VoiceAdapterError("audio fixture must be non-empty bytes")
    if not isinstance(filename, str) or not filename.strip():
        raise VoiceAdapterError("filename must be non-empty text")
    if Path(filename).name != filename or filename in {".", ".."}:
        raise VoiceAdapterError("filename must be a single path component")
    if type(sample_rate) is not int or sample_rate not in SUPPORTED_SAMPLE_RATES:
        raise VoiceAdapterError("sample_rate is unsupported")
    # The upstream batch contract caps uploads at 500 MB.  Keep the same guard
    # in the fixture without allocating or touching a file.
    if len(audio) > 500 * 1024 * 1024:
        raise VoiceAdapterError("audio fixture exceeds the 500 MB batch limit")
    return bytes(audio)


def mock_dictation(
    audio: bytes | bytearray | memoryview,
    *,
    filename: str = "dictation.wav",
    sample_rate: int = 16000,
    language: str = "en",
    diarize: bool = False,
) -> dict[str, Any]:
    """Exercise the documented STT result shape with deterministic local data.

    The bytes are counted and hashed only; they are never sent to a provider,
    decoded as speech, or exposed in the result.  ``text`` is an explicit mock
    transcript so callers can prove the route and error handling.
    """

    raw = _validate_audio(audio, filename, sample_rate)
    if not isinstance(language, str) or not language.strip():
        raise VoiceAdapterError("language must be non-empty text")
    duration = round(len(raw) / (sample_rate * 2), 3)
    digest = hashlib.sha256(raw).hexdigest()[:12]
    words = [
        {"text": "mock", "start": 0.0, "end": min(duration, 0.25)},
        {"text": "dictation", "start": min(duration, 0.25), "end": duration},
    ]
    if diarize:
        for word in words:
            word["speaker"] = 0
    return {
        "status": "MOCK_VERIFIED",
        "mode": "batch",
        "text": "[mock dictation]",
        "language": language,
        "duration": duration,
        "words": words,
        "audio_bytes": len(raw),
        "fixture_digest": digest,
        "external_call": False,
        "credential_exposed": False,
        "microphone_used": False,
    }


def mock_dictation_route(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Model a local ``POST /api/dictation`` route without HTTP or provider I/O."""

    if not isinstance(payload, Mapping):
        raise VoiceAdapterError("dictation route payload must be an object")
    if "audio" not in payload:
        raise VoiceAdapterError("dictation route requires audio")
    result = mock_dictation(
        payload["audio"],
        filename=payload.get("filename", "dictation.wav"),
        sample_rate=payload.get("sample_rate", 16000),
        language=payload.get("language", "en"),
        diarize=payload.get("diarize", False),
    )
    result["route"] = "/api/dictation"
    return result


def _validate_tts(text: str, voice_id: str, language: str) -> None:
    if not isinstance(text, str) or not 1 <= len(text) <= 15_000 or not text.strip():
        raise VoiceAdapterError("TTS text must be 1–15,000 non-empty characters")
    if not isinstance(voice_id, str) or not re.fullmatch(r"[a-z0-9-]{1,64}", voice_id):
        raise VoiceAdapterError("voice_id must match ^[a-z0-9-]{1,64}$")
    if not isinstance(language, str) or not language.strip() or len(language) > 32:
        raise VoiceAdapterError("language must be non-empty text")


def _synthetic_tts_bytes(text: str, voice_id: str, language: str) -> bytes:
    """Make a tiny deterministic WAV marker for local route tests only."""

    seed = hashlib.sha256(f"{voice_id}\0{language}\0{text}".encode()).digest()
    # 100 ms mono PCM16 silence with a digest marker in the metadata-free
    # payload.  It is never played by this module.
    frames = b"\x00\x00" * 2400
    out = bytearray()
    body_size = 36 + len(frames)
    out.extend(b"RIFF")
    out.extend(struct.pack("<I", body_size))
    out.extend(b"WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00")
    out.extend(struct.pack("<I", 24000))
    out.extend(struct.pack("<I", 48000))
    out.extend(b"\x02\x00\x10\x00data")
    out.extend(struct.pack("<I", len(frames)))
    out.extend(frames)
    return bytes(out) + seed[:4]


def mock_read_aloud(
    text: str,
    *,
    voice_id: str = "eve",
    language: str = "auto",
) -> dict[str, Any]:
    """Exercise the documented TTS response shape without playback or egress."""

    _validate_tts(text, voice_id, language)
    audio = _synthetic_tts_bytes(text, voice_id, language)
    return {
        "status": "MOCK_VERIFIED",
        "mode": "batch",
        "content_type": "audio/wav",
        "audio_bytes": len(audio),
        "audio_digest": hashlib.sha256(audio).hexdigest()[:16],
        "text_chars": len(text),
        "voice_id": voice_id,
        "language": language,
        "external_call": False,
        "credential_exposed": False,
        "playback_started": False,
    }


def mock_read_aloud_route(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Model a local ``POST /api/tts`` route with no network or audio playback."""

    if not isinstance(payload, Mapping):
        raise VoiceAdapterError("TTS route payload must be an object")
    result = mock_read_aloud(
        payload.get("text", ""),
        voice_id=payload.get("voice_id", "eve"),
        language=payload.get("language", "auto"),
    )
    result["route"] = "/api/tts"
    return result


class MockRealtimeSession:
    """Small state machine for the documented realtime event loop."""

    VALID_EVENTS = frozenset(
        {
            "session.update",
            "conversation.item.create",
            "response.create",
            "input_audio_buffer.append",
            "input_audio_buffer.commit",
            "input_audio_buffer.speech_started",
            "input_audio_buffer.speech_stopped",
        }
    )

    def __init__(self) -> None:
        self.phase = "connecting"
        self.closed = False
        self.audio_bytes = 0
        self.events: list[dict[str, Any]] = []

    def send(self, event: Mapping[str, Any]) -> list[dict[str, Any]]:
        if self.closed:
            return [{"type": "error", "code": "SESSION_CLOSED", "diagnostic": "mock session is closed"}]
        if not isinstance(event, Mapping) or not isinstance(event.get("type"), str):
            return self._malformed("event must be an object with a type")
        kind = event["type"]
        if kind not in self.VALID_EVENTS:
            return self._malformed(f"unsupported event type: {kind}")
        if kind == "session.update":
            self.phase = "listening"
            return self._record({"type": "session.updated", "phase": self.phase})
        if kind == "input_audio_buffer.append":
            chunk = event.get("audio", event.get("delta", b""))
            if isinstance(chunk, str):
                try:
                    chunk_bytes = len(base64.b64decode(chunk, validate=True))
                except (binascii.Error, ValueError) as exc:
                    return self._malformed(f"audio payload is not valid base64: {exc}")
            elif isinstance(chunk, (bytes, bytearray, memoryview)):
                chunk_bytes = len(chunk)
            else:
                return self._malformed("audio payload must be bytes or base64")
            self.audio_bytes += chunk_bytes
            return self._record({"type": "input_audio_buffer.appended", "bytes": chunk_bytes})
        if kind in {"input_audio_buffer.commit", "input_audio_buffer.speech_stopped"}:
            return self._record({"type": "input_audio_buffer.committed"})
        if kind == "input_audio_buffer.speech_started":
            self.phase = "listening"
            return self._record({"type": "input_audio_buffer.speech_started", "phase": self.phase})
        if kind == "conversation.item.create":
            return self._record({"type": "conversation.item.created"})
        # A response is represented by metadata and byte counts only.
        self.phase = "speaking"
        response = [
            {"type": "response.created", "response_id": "mock-response-1"},
            {"type": "response.output_audio.delta", "response_id": "mock-response-1", "bytes": 3200},
            {"type": "response.output_audio_transcript.delta", "delta": "[mock response]"},
            {"type": "response.done", "status": "completed", "phase": "speaking"},
        ]
        self.phase = "listening"
        return self._record_many(response)

    def _record(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        self.events.append(event)
        return [event]

    def _record_many(self, events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        values = list(events)
        self.events.extend(values)
        return values

    def _malformed(self, diagnostic: str) -> list[dict[str, Any]]:
        self.closed = True
        event = {"type": "error", "code": "MALFORMED_EVENT", "diagnostic": diagnostic}
        self.events.append(event)
        return [event]


def mock_realtime(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Run a local realtime relay fixture and close with a diagnostic on error."""

    session = MockRealtimeSession()
    observed: list[dict[str, Any]] = []
    for event in events:
        observed.extend(session.send(event))
        if session.closed:
            return {
                "status": "ERROR",
                "diagnostic": observed[-1],
                "closed": True,
                "external_call": False,
                "microphone_used": False,
                "playback_started": False,
                "credential_exposed": False,
            }
    return {
        "status": "MOCK_VERIFIED",
        "phase": session.phase,
        "events": observed,
        "audio_bytes": sum(event.get("bytes", 0) for event in observed if isinstance(event, dict)),
        "closed": False,
        "external_call": False,
        "microphone_used": False,
        "playback_started": False,
        "credential_exposed": False,
    }


def _audio_bytes(value: Any) -> int:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return len(value)
    if not isinstance(value, str):
        raise VoiceRedactionError("audio field must be bytes or base64 text")
    try:
        return len(base64.b64decode(value, validate=True))
    except (binascii.Error, ValueError) as exc:
        raise VoiceRedactionError("audio field is not valid base64") from exc


def _is_sensitive_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9_]", "_", key.lower())
    return normalized in SENSITIVE_KEY_PARTS or any(
        part in normalized for part in ("api_key", "authorization", "client_secret", "access_token")
    )


def _redact(value: Any, *, depth: int, audio_event: bool, key: str | None = None) -> Any:
    if key is not None and _is_sensitive_key(key):
        return "[redacted]"
    if isinstance(value, str):
        if len(value) > 400:
            return value[:400] + f"…[{len(value)} chars]"
        return value
    if isinstance(value, (bytes, bytearray, memoryview)):
        if audio_event and key in {"audio", "delta"}:
            return {"bytes": len(value)}
        return "[binary]"
    if isinstance(value, Mapping):
        if depth >= 4:
            return "[depth]"
        return {
            str(k): _redact(v, depth=depth + 1, audio_event=audio_event, key=str(k))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        if depth >= 4:
            return "[depth]"
        values = list(value[:50])
        result = [_redact(v, depth=depth + 1, audio_event=audio_event) for v in values]
        if len(value) > 50:
            result.append("[… truncated]")
        return result
    return value


def redact_voice_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Redact one log entry, reducing documented audio events to byte counts."""

    if not isinstance(entry, Mapping):
        raise VoiceRedactionError("voice log entry must be an object")
    kind = entry.get("type", entry.get("kind", ""))
    audio_event = kind in AUDIO_EVENT_TYPES
    result = _redact(entry, depth=0, audio_event=audio_event)
    if not isinstance(result, dict):
        raise VoiceRedactionError("redacted voice entry is not an object")
    if audio_event:
        for field in ("delta", "audio"):
            if field in entry:
                result.pop(field, None)
                result["bytes"] = _audio_bytes(entry[field])
    return result


def _load_ndjson(path: str | Path, *, session_id: str | None = None) -> tuple[str, list[dict[str, Any]]]:
    target = Path(path)
    if target.is_symlink():
        return "INCONCLUSIVE", []
    if not target.is_file():
        return "INCONCLUSIVE", []
    if session_id is not None and target.stem != session_id:
        return "INCONCLUSIVE", []
    entries: list[dict[str, Any]] = []
    try:
        for line in target.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                return "INCONCLUSIVE", []
            entries.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "INCONCLUSIVE", []
    return "READ", entries


SIGNATURES: tuple[tuple[str, str, str], ...] = (
    ("playback_suspended", "playback state is suspended", "resume one playback context inside the user gesture"),
    ("choppy_audio", "audio output has underruns or a large drain", "schedule a 150–250 ms lead and reuse one audio context"),
    ("provider_token", "server token result is not ok", "inspect server token status without exposing the credential"),
    ("connection_closed", "socket closed before session.updated", "inspect relay and session negotiation"),
    ("mic_silent", "audio input RMS is zero", "inspect device and permission settings"),
    ("missing_transcript", "no input transcription update was observed", "set the documented input transcription model"),
)


def diagnose_voice_entries(entries: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Redact and match the source's starter signatures without writing state."""

    try:
        redacted = [redact_voice_entry(entry) for entry in entries]
    except VoiceRedactionError as exc:
        return {"status": "INCONCLUSIVE", "reason": f"redaction failed: {exc}", "write": False}
    if not redacted:
        return {"status": "INCONCLUSIVE", "reason": "voice log is empty", "write": False}

    types = {entry.get("type") for entry in redacted}
    findings: list[dict[str, str]] = []
    for signature, description, fix in SIGNATURES:
        matched = False
        if signature == "playback_suspended":
            matched = any(entry.get("play_state") == "suspended" for entry in redacted)
        elif signature == "choppy_audio":
            matched = any(
                entry.get("kind") == "audio.out"
                and (entry.get("underruns", 0) > 0 or entry.get("drain_ms_max", 0) > 250)
                for entry in redacted
            )
        elif signature == "provider_token":
            matched = any(entry.get("kind") == "server.token" and entry.get("ok") is False for entry in redacted)
        elif signature == "connection_closed":
            matched = any(entry.get("kind") == "ws.close" for entry in redacted) and "session.updated" not in types
        elif signature == "mic_silent":
            matched = any(entry.get("kind") == "audio.in" and entry.get("rms_max", 1) == 0 for entry in redacted)
        elif signature == "missing_transcript":
            matched = "conversation.item.input_audio_transcription.updated" not in types
        if matched:
            findings.append({"signature": signature, "description": description, "suggested_fix": fix})
    return {
        "status": "DIAGNOSED",
        "findings": findings,
        "entries": redacted,
        "write": False,
        "audio_exposed": False,
        "credentials_exposed": False,
    }


def diagnose_voice_log(path: str | Path, *, session_id: str | None = None) -> dict[str, Any]:
    """Read one scoped NDJSON file and return a write-free diagnostic result."""

    status, entries = _load_ndjson(path, session_id=session_id)
    if status != "READ":
        return {"status": "INCONCLUSIVE", "reason": "missing, mismatched, or unsafe voice log", "write": False}
    return diagnose_voice_entries(entries)


__all__ = [
    "MissingVoiceCapability",
    "MockRealtimeSession",
    "VoiceAdapterError",
    "VoiceRedactionError",
    "diagnose_voice_entries",
    "diagnose_voice_log",
    "mock_dictation",
    "mock_dictation_route",
    "mock_read_aloud",
    "mock_read_aloud_route",
    "mock_realtime",
    "redact_voice_entry",
    "server_credential_boundary",
    "unavailable_provider",
]
