"""Focused local proofs for the four held conditional voice overlays."""

import json
import io
import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from cursor_voice_adapters import (  # noqa: E402
    _synthetic_tts_bytes,
    VoiceAdapterError,
    diagnose_voice_entries,
    diagnose_voice_log,
    MAX_LOG_BYTES,
    MAX_LOG_ENTRIES,
    mock_dictation_route,
    mock_read_aloud_route,
    mock_realtime,
    redact_voice_entry,
    server_credential_boundary,
    unavailable_provider,
)


class CursorVoiceAdapterTests(unittest.TestCase):
    def test_provider_is_explicitly_unavailable_and_server_boundary_is_key_free(self):
        unavailable = unavailable_provider("xAI STT API")
        self.assertEqual(unavailable["status"], "UNAVAILABLE")
        self.assertFalse(unavailable["external_call"])
        boundary = server_credential_boundary("xAI TTS API")
        self.assertEqual(boundary["credential_location"], "application-server-only")
        self.assertNotIn("key", json.dumps(boundary).lower())

    def test_dictation_local_route_proves_shape_without_mic_or_egress(self):
        result = mock_dictation_route(
            {"audio": b"\x00" * 3200, "filename": "fixture.wav", "sample_rate": 16000, "diarize": True}
        )
        self.assertEqual(result["status"], "MOCK_VERIFIED")
        self.assertEqual(result["text"], "[mock dictation]")
        self.assertEqual(result["audio_bytes"], 3200)
        self.assertEqual(result["words"][0]["speaker"], 0)
        self.assertFalse(result["microphone_used"])
        self.assertFalse(result["external_call"])

    def test_dictation_rejects_path_escape_and_empty_audio(self):
        with self.assertRaises(VoiceAdapterError):
            mock_dictation_route({"audio": b"x", "filename": "../voice.wav"})
        with self.assertRaises(VoiceAdapterError):
            mock_dictation_route({"audio": b""})

    def test_read_aloud_local_route_returns_synthetic_metadata_without_playback(self):
        result = mock_read_aloud_route({"text": "Hello locally", "voice_id": "eve"})
        self.assertEqual(result["status"], "MOCK_VERIFIED")
        self.assertEqual(result["route"], "/api/tts")
        self.assertGreater(result["audio_bytes"], 0)
        self.assertFalse(result["playback_started"])
        self.assertFalse(result["external_call"])
        wav_bytes = _synthetic_tts_bytes("Hello locally", "eve", "auto")
        with wave.open(io.BytesIO(wav_bytes), "rb") as wav:
            self.assertEqual(wav.getnchannels(), 1)
            self.assertEqual(wav.getframerate(), 24000)
            self.assertEqual(wav.getnframes(), 2400)
            self.assertEqual(len(wav.readframes(2400)), 4800)
        self.assertEqual(result["audio_bytes"], len(wav_bytes))

    def test_read_aloud_rejects_invalid_voice_and_oversized_text(self):
        with self.assertRaises(VoiceAdapterError):
            mock_read_aloud_route({"text": "hello", "voice_id": "../eve"})
        with self.assertRaises(VoiceAdapterError):
            mock_read_aloud_route({"text": "x" * 15001})

    def test_realtime_mock_closes_with_diagnostic_on_malformed_event(self):
        good = mock_realtime(
            [
                {"type": "session.update"},
                {"type": "input_audio_buffer.append", "audio": "AA=="},
                {"type": "conversation.item.create", "item": {"type": "message"}},
                {"type": "response.create"},
            ]
        )
        self.assertEqual(good["status"], "MOCK_VERIFIED")
        self.assertFalse(good["microphone_used"])
        self.assertFalse(good["playback_started"])
        self.assertTrue(any(event["type"] == "response.output_audio.delta" for event in good["events"]))
        bad = mock_realtime([{"type": "not-a-realtime-event"}])
        self.assertEqual(bad["status"], "ERROR")
        self.assertEqual(bad["diagnostic"]["code"], "MALFORMED_EVENT")
        self.assertTrue(bad["closed"])

    def test_audio_and_secret_redaction_preserves_diagnostics(self):
        entry = redact_voice_entry(
            {
                "kind": "server",
                "type": "response.output_audio.delta",
                "delta": "AAECAwQ=",
                "authorization": "Bearer should-not-appear",
                "message": "x" * 401,
            }
        )
        self.assertEqual(entry["bytes"], 5)
        self.assertNotIn("delta", entry)
        self.assertEqual(entry["authorization"], "[redacted]")
        self.assertTrue(entry["message"].endswith("…[401 chars]"))

    def test_debug_log_positive_missing_and_redaction_failure(self):
        entries = [
            {"kind": "start", "type": "start"},
            {"kind": "env", "play_state": "suspended"},
            {"kind": "audio.out", "underruns": 2, "drain_ms_max": 400},
        ]
        diagnosis = diagnose_voice_entries(entries)
        self.assertEqual(diagnosis["status"], "DIAGNOSED")
        self.assertEqual({item["signature"] for item in diagnosis["findings"]}, {"playback_suspended", "choppy_audio", "missing_transcript"})
        self.assertFalse(diagnosis["write"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session1.ndjson"
            path.write_text("\n".join(json.dumps(item) for item in entries) + "\n")
            self.assertEqual(diagnose_voice_log(path, session_id="session1")["status"], "DIAGNOSED")
            self.assertEqual(diagnose_voice_log(Path(directory) / "missing.ndjson")["status"], "INCONCLUSIVE")
            path.write_text(json.dumps({"kind": "server", "type": "response.output_audio.delta", "delta": "%%%"}) + "\n")
            failed = diagnose_voice_log(path, session_id="session1")
            self.assertEqual(failed["status"], "INCONCLUSIVE")
            self.assertFalse(failed["write"])

    def test_debug_diagnosis_fails_closed_on_malformed_types(self):
        # String numbers and unhashable event types must not escape as a
        # TypeError or accidentally become a positive diagnosis.
        for entry in (
            {"kind": "audio.out", "underruns": "2"},
            {"kind": "audio.out", "drain_ms_max": []},
            {"type": []},
        ):
            result = diagnose_voice_entries([entry])
            self.assertEqual(result["status"], "INCONCLUSIVE")
            self.assertFalse(result["write"])

    def test_debug_log_rejects_oversize_bytes_and_entry_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.ndjson"
            path.write_bytes(b"x" * (MAX_LOG_BYTES + 1))
            self.assertEqual(diagnose_voice_log(path, session_id="large")["status"], "INCONCLUSIVE")

            path = Path(directory) / "many.ndjson"
            line = json.dumps({"kind": "start", "type": "start"}) + "\n"
            path.write_text(line * (MAX_LOG_ENTRIES + 1))
            self.assertEqual(diagnose_voice_log(path, session_id="many")["status"], "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
