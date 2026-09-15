# Cursor plugin and SDK batch

Date: 2026-09-15. This batch covers the four selected source skills
`cursor-check-agent-compatibility`, `cursor-create-plugin-scaffold`,
`cursor-review-plugin-submission`, and `cursor-cursor-sdk`. The source snapshot
remains pinned at `cursor/plugins` commit `889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`.
The central manifest, catalog README, and generated state were intentionally
left to the coordinator. This pass adds a deterministic local Codex scanner
and a safe native capability map; neither is presented as Cursor runtime parity.

## Decisions and proof

| Skill | Result | Observed bounded behavior | Remaining boundary |
| --- | --- | --- | --- |
| `cursor-check-agent-compatibility` | Local Codex scanner, explicit-only | The new `codex-local-plugin-compatibility-v1` scanner runs four independent deterministic checks against the generated disposable plugin. The fixture scored **100/100 locally**, with separate scanner, startup, validation, and docs role results; the upstream Agent Compatibility Score remains withheld. | The published scanner package was not installed or executed. The local startup and validation roles are static plugin-contract checks and do not claim to boot or execute a target application. |
| `cursor-create-plugin-scaffold` | Conditional explicit adapter | A marked disposable root creates a Cursor-format manifest, README, caller-supplied LICENSE, and static rules/skills/agents/commands. The output is passed directly to the structural submission auditor. Invalid names, missing markers, nonempty roots, hooks, MCP, and marketplace requests stop before writing. | Cursor native plugin activation, active hooks/MCP semantics, marketplace wiring, global installation, and publication remain unproven. |
| `cursor-review-plugin-submission` | Conditional explicit adapter | The read-only auditor checks manifest JSON, bounded relative paths, required metadata, discoverable component files, README presence, and passive hook/MCP declarations. The generated disposable scaffold returns `STRUCTURAL_PASS`; malformed, escaping, symlinked, and active surfaces produce explicit errors or `REVIEW_REQUIRED`. | Full YAML validity, repository marketplace uniqueness, submission policy, runtime behavior, and human review remain unproven. |
| `cursor-cursor-sdk` | Safe native capability map, source remains held | The reference reader identifies the external symbols without importing or executing the SDK. A new non-executing map describes the closest native Codex capabilities (`create_thread`, `send_message_to_thread`, `wait_threads`, and bounded `read_thread`) with conceptual-only labels, no streaming-equivalence claim, and no task creation. Credential, authentication, execution, network, and MCP configuration requests fail closed. | The source `blocked_malicious` verdict is retained. No Cursor SDK runtime or credential path is proven; the map is documentation only and Codex task/agent APIs remain a different contract. |

The source findings remain unchanged: `safe_docs_only` for the compatibility
skill, `needs_human_review` with `mcp-plugin-hook-install` for the scaffold,
`needs_human_review` for submission review, and `blocked_malicious` for the SDK.
The overlay descriptions now record the disposable evidence without converting
static proof into Cursor runtime parity or dismissing those findings.

## Validation

- `pytest -q tests/test_cursor_plugin_scanner_adapters.py tests/test_cursor_plugin_scaffold_fixture.py tests/test_cursor_plugin_submission_audit.py tests/test_cursor_functional_overlays.py` — **28 passed**.
- The scanner test generated a marked disposable plugin, ran the scaffold, passed that output into the submission auditor, and recorded a deterministic local score of **100/100** across all four roles.
- The scanner CLI also returned `LOCAL_SCANNER_RESULT` with the same 100/100 score; its provenance explicitly says it is not the upstream Agent Compatibility Score.
- `python3 scripts/cursor_plugin_scanner_adapters.py sdk-native-contract` — returned the safe native mapping without creating a task or invoking a tool.
- `python3 -m py_compile scripts/cursor_plugin_scanner_adapters.py scripts/cursor_plugin_scaffold_fixture.py scripts/cursor_plugin_submission_audit.py` — passed.
- `python3 scripts/sync-cursor-plugin-skills.py --preview-candidates /private/tmp/plugin-sdk-preview-final-remaining-20260915` — rendered 83 active candidates, including the four held candidates, with pinned overlays and support files.
- Four overlay JSON files parse successfully.

No npm package was installed, no Cursor SDK was imported, no network or
credentials were used, no hooks/MCP servers or marketplace were activated, and
no global Cursor directory, PR, or merge was touched.
