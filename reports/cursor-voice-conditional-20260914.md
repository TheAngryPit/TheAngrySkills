# Conditional voice adapter proof

Date: 2026-09-14

This lot covers the four held `grok-voice` overlays: `cursor-add-dictation`,
`cursor-add-read-aloud`, `cursor-add-voice`, and `cursor-debug-voice`. The
pinned source commit is `889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`.

## Local behavior

[`scripts/cursor_voice_adapters.py`](../scripts/cursor_voice_adapters.py)
provides four local entrypoints:

- `mock_dictation_route` validates the batch STT input shape and returns a
  deterministic mock transcript with duration, words, optional speaker data,
  and byte count. It never uses a microphone or sends audio.
- `mock_read_aloud_route` validates TTS text, voice, and language and returns
  deterministic synthetic WAV metadata. It never invokes playback or sends
  reply text.
- `mock_realtime` runs a small local state machine for the documented
  `session.update`, audio-buffer, conversation, and response events. A
  malformed event closes the fixture with a `MALFORMED_EVENT` diagnostic;
  output audio is represented by byte counts only.
- `diagnose_voice_log` reads one NDJSON file, redacts audio to decoded byte
  counts, bounds the file to 4 MiB and 5,000 entries (with 16,000-byte lines),
  bounds strings/objects/arrays, redacts credential-shaped fields, and matches
  the source starter signatures. Missing, mismatched, unsafe, empty,
  malformed, oversize, or unredactable logs return `INCONCLUSIVE` and never
  write. Malformed numeric and unhashable event fields fail closed.

Each provider-facing capability has an explicit `UNAVAILABLE` result and a
server-only credential boundary. The module contains no HTTP, WebSocket,
microphone, playback, environment-secret, or provider call.

## Security context retained

The overlays preserve the pinned scanner context. `add-dictation` retains the
critical `network-exfiltration` finding at source `SKILL.md:156` for the active
curl upload to xAI STT with a server key. `add-read-aloud` retains the critical
`network-exfiltration` finding at source `SKILL.md:172` for the active curl TTS
request and audio write. `add-voice` and `debug-voice` retain their source
security status and held promotion state. This local fixture does not dismiss
or exercise those provider paths.

## Proof

Focused tests: `python3 -m unittest -v tests.test_cursor_voice_adapters`

Result: 10 tests passed. The module and test file also pass `py_compile`, and
all four modified overlays parse as JSON. The focused tests cover positive
dictation, read-aloud, realtime, and log diagnosis cases plus empty/path-invalid
input, malformed realtime events, invalid TTS input, missing logs, failed
audio redaction, malformed numeric/unhashable fields, and oversize log files
and entry counts.

## Remaining gaps

The provider endpoints, credentials, server relay, real application wiring,
microphone capture, audio playback, production gating, native Cursor skill
activation, and live source event behavior remain unproven. No network,
credential, microphone, playback, global install, manifest, marketplace, or
PR action was performed.
