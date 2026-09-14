# Cursor plugin scanner conditional closure

pinned source provenance

| source skill | SHA-256 | baseline finding |
| --- | --- | --- |
| `agent-compatibility/skills/check-agent-compatibility/SKILL.md` | `2391a06aec1bfb475690a9c386207e009090e35c624b5ca6cace3ea4c6705970` | `safe_docs_only` |
| `create-plugin/skills/create-plugin-scaffold/SKILL.md` | `b1ca0ef8398d957c59c1ab8c34527fd53120de51318af33ef61acab7961c9b46` | `needs_human_review` (`mcp-plugin-hook-install`) |
| `create-plugin/skills/review-plugin-submission/SKILL.md` | `ff7411fc0426934871ac18f8ed55edcfc49f19443701dbe9109a3395ccded61d` | `needs_human_review` |
| `cursor-sdk/skills/cursor-sdk/SKILL.md` | `3fbe439f366ea94e0a756fc7288d2d8bd3f871bed4b97219dc1aee2f8c8ab979` | `blocked_malicious` |

The compatibility source references four separate role files
(`compatibility-scan-review`, `startup-review`, `validation-review`, and
`docs-reliability-review`). The SDK source references its seven local guides:
`advanced`, `auth`, `error-handling`, `mcp`, `patterns`, `runtime-choice`, and
`streaming`; all were inspected. The create-plugin source references its
`plugin-architect` agent and `plugin-quality-gates` rule; both were inspected.

This report covers the four held overlays `check-agent-compatibility`,
`create-plugin-scaffold`, `review-plugin-submission`, and `cursor-sdk`. The
pinned source files and every relative reference were read from the local
snapshot. Their source contracts remain intact, including the requirement for
four separate compatibility roles, static Cursor plugin layout checks, and
external SDK reference guidance.

The bounded proof surface is local and write-free:

- `scripts/cursor_plugin_scanner_adapters.py` inventories README/test/startup
  evidence while withholding the compatibility score when the published
  `agent-compatibility` scanner is not installed or executed. A supplied score
  remains explicitly unverified caller input, bounded for reporting only, and
  is never promoted or returned as an Agent Compatibility Score.
- `scripts/cursor_plugin_scaffold_fixture.py` creates only a marked disposable
  static fixture and stops before hooks, MCP, marketplace wiring, or the
  default `~/.cursor/plugins/local` destination.
- `scripts/cursor_plugin_submission_audit.py` checks local manifest paths,
  component frontmatter, README presence, and passive hook/MCP signals. It
  never executes components or recommends submission.
- `scripts/cursor_plugin_scanner_adapters.py` reports SDK symbols as
  `REFERENCE_ONLY`, keeps runtime support `UNAVAILABLE`, rejects nested
  credential/authentication/execution/network/MCP configuration inputs, and
  accepts SDK source text only on stdin from its CLI.

Positive proof: the compatibility fixture reports separate evidence with no
invented score; a supplied numeric scanner score is retained only as
unverified input; the scaffold
fixture plus submission auditor produce `FIXTURE_ONLY` and `STRUCTURAL_PASS`;
and the SDK fixture identifies `@cursor/sdk`, `Agent.create`, and
`Agent.prompt` without claiming execution.

Negative proof: scanner installation and network remain false; compatibility
score is `None` without real scanner evidence, and even a supplied score is
kept as unverified input (NaN and out-of-range values are discarded); invalid
or nonempty scaffold destinations stop before writing; hooks, MCP, and
marketplace requests return `REVIEW_REQUIRED`; unsafe manifest paths and
missing frontmatter fail the submission audit; and SDK requests containing
top-level or nested `apiKey`, `CURSOR_API_KEY`, `mcpServers`, or execution
flags fail closed. The SDK CLI rejects file paths and accepts source text only
on stdin.

Validation run in the successor worktree:

- `pytest -q tests/test_cursor_plugin_scanner_adapters.py tests/test_cursor_plugin_scaffold_fixture.py tests/test_cursor_plugin_submission_audit.py` — 15 passed.
- `python3 -m py_compile scripts/cursor_plugin_scanner_adapters.py scripts/cursor_plugin_scaffold_fixture.py scripts/cursor_plugin_submission_audit.py` — passed.
- No npm package was installed, no Cursor SDK was imported, no network or
  credentials were used, and no global Cursor directory or marketplace was
  touched.

The four entries remain held. Static local proof does not establish native
Codex plugin parity, a real deterministic scanner result, live Cursor
marketplace readiness, active hook/MCP behavior, or external SDK runtime/auth
support. The existing source security verdicts are retained: the scaffold and
submission flows remain `needs_human_review`, and the SDK remains
`blocked_malicious` under the repository's scanner ledger.
