# Cursor SDK bounded native closure

Date: 2026-09-15

Proof target: provide a useful, bounded migration path for the pinned Cursor
SDK skill while preserving its `blocked_malicious` hold and keeping Cursor
runtime, credentials, and MCP configuration outside the mirror.

Required proof level: `test_proven` for the adapter contract. Cursor SDK
runtime parity and actual native Codex task execution remain
`not_proven_yet` because this pass is prohibited from importing the SDK,
reading credentials, activating MCP, creating tasks, or making network calls.

## Implementation

`scripts/cursor_sdk_native_adapter.py` translates a small explicit request
shape into the closest native Codex operations:

| Cursor SDK intent | Native Codex operation | Boundary |
| --- | --- | --- |
| `Agent.prompt` / `Agent.create` | `create_thread` | Plan only by default; explicit authorization is required before a caller-supplied bridge can attempt a task mutation. |
| `Agent.resume` / `agent.send` | `send_message_to_thread` | Exact thread ID is required; no ambient task lookup. |
| `run.wait` | `wait_threads` | Bounded timeout, exact thread target. |
| `run.stream` | `wait_threads` then `read_thread` | Bounded readback pair; no streaming-equivalence claim. |

The pure plan path is functional and write-free. An optional in-process
bridge can exercise the same ordered native operation contract for a
read-only request. The bridge is caller-owned and external; its result does
not attest the Cursor SDK, native host, or provider runtime.

## Safety and provenance

The overlay keeps source path
`cursor-sdk/skills/cursor-sdk/SKILL.md`, source SHA-256
`3fbe439f366ea94e0a756fc7288d2d8bd3f871bed4b97219dc1aee2f8c8ab979`, pinned
upstream commit `889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`, and scanner verdict
`blocked_malicious`.

The concrete `references/auth.md:100` credential-path finding and MCP
configuration finding are retained in the overlay security ledger. The
reference files are not present in the skills-only snapshot and are not copied
into the native artifact. The adapter rejects credential-shaped keys at any
depth, including `CURSOR_API_KEY`, `apiKey`, headers, environment credentials,
tokens, and `mcpServers`, before dispatch. It also rejects unsafe native
results and does not echo external exception text.

## Fresh validation

- `python3 -m unittest -v tests/test_cursor_sdk_native_adapter.py` — **8 passed**.
- `python3 -m py_compile scripts/cursor_sdk_native_adapter.py scripts/cursor_plugin_scanner_adapters.py` — passed.
- `python3 scripts/cursor_sdk_native_adapter.py plan` with a bounded stream request — emitted ordered `wait_threads` and `read_thread` operations with `streaming_equivalent: false`.
- CLI `run --execute` without a bridge — returned `UNAVAILABLE` with no attempted execution or external write.

The focused tests cover a positive prompt plan, positive ordered read-only
bridge result, unavailable bridge, missing bridge method, explicit mutation
authorization, nested credential/MCP fail-closed behavior, native exception
redaction, native error status, unsafe result rejection, bounds, and the CLI
unavailable path.

No npm package was installed, no Cursor SDK was imported or executed, no
`CURSOR_API_KEY` or other secret was read, no MCP server or hook was
configured, no network request was made, and no Codex task was created.

## Remaining gap

An explicitly authorized coordinator would still need to provide and verify a
native Codex bridge on a supported host for one read-only `wait_threads` /
`read_thread` operation. A separate operator decision would be required for
any mutating native task operation. Neither proof is part of this closure.
