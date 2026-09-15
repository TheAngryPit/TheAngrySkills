# Cursor plugin and SDK batch

Date: 2026-09-15. This batch covers the four selected source skills
`cursor-check-agent-compatibility`, `cursor-create-plugin-scaffold`,
`cursor-review-plugin-submission`, and `cursor-cursor-sdk`. The source snapshot
remains pinned at `cursor/plugins` commit `889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`.
The central manifest, catalog README, and generated state were intentionally
left to the coordinator.

## Decisions and proof

| Skill | Result | Observed bounded behavior | Remaining boundary |
| --- | --- | --- | --- |
| `cursor-check-agent-compatibility` | Conditional explicit adapter | The rendered skill preserves four separate reviewer roles. A disposable repository inventory reports README, validation, and documentation evidence separately and withholds the Agent Compatibility Score when the scanner is unavailable. | The published scanner package was not installed or executed; cold startup, the three behavioral checks, and a combined score remain unproven. |
| `cursor-create-plugin-scaffold` | Conditional explicit adapter | A marked disposable root creates a Cursor-format manifest, README, caller-supplied LICENSE, and static rules/skills/agents/commands. The output is passed directly to the structural submission auditor. Invalid names, missing markers, nonempty roots, hooks, MCP, and marketplace requests stop before writing. | Cursor native plugin activation, active hooks/MCP semantics, marketplace wiring, global installation, and publication remain unproven. |
| `cursor-review-plugin-submission` | Conditional explicit adapter | The read-only auditor checks manifest JSON, bounded relative paths, required metadata, discoverable component files, README presence, and passive hook/MCP declarations. The generated disposable scaffold returns `STRUCTURAL_PASS`; malformed, escaping, symlinked, and active surfaces produce explicit errors or `REVIEW_REQUIRED`. | Full YAML validity, repository marketplace uniqueness, submission policy, runtime behavior, and human review remain unproven. |
| `cursor-cursor-sdk` | Held external reference | The reference reader identifies `@cursor/sdk`, `Agent.create`, `Agent.prompt`, `Agent.resume`, `agent.send`, `run.stream`, `run.wait`, `CursorAgentError`, and `mcpServers` without importing or executing the SDK. Credential, authentication, execution, network, and MCP configuration requests fail closed. | The source `blocked_malicious` verdict is retained. No Cursor SDK runtime, credential path, or native Codex equivalence is claimed; Codex task/agent APIs are a different contract. |

The source findings remain unchanged: `safe_docs_only` for the compatibility
skill, `needs_human_review` with `mcp-plugin-hook-install` for the scaffold,
`needs_human_review` for submission review, and `blocked_malicious` for the SDK.
The overlay descriptions now record the disposable evidence without converting
static proof into Cursor runtime parity or dismissing those findings.

## Validation

- `pytest -q tests/test_cursor_plugin_scanner_adapters.py tests/test_cursor_plugin_scaffold_fixture.py tests/test_cursor_plugin_submission_audit.py` — **16 passed**.
- `python3 -m py_compile scripts/cursor_plugin_scanner_adapters.py scripts/cursor_plugin_scaffold_fixture.py scripts/cursor_plugin_submission_audit.py` — passed.
- `python3 scripts/sync-cursor-plugin-skills.py --preview-candidates /private/tmp/plugin-sdk-preview-20260915` — rendered 83 active candidates, including the four held candidates, with pinned overlays and support files.
- Four overlay JSON files parse successfully.

No npm package was installed, no Cursor SDK was imported, no network or
credentials were used, no hooks/MCP servers or marketplace were activated, and
no global Cursor directory, PR, or merge was touched.
