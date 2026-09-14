# Cursor plugin scanner conditional closure

This report covers the four held overlays `check-agent-compatibility`,
`create-plugin-scaffold`, `review-plugin-submission`, and `cursor-sdk`. The
pinned source files and every relative reference were read from the local
snapshot. Their source contracts remain intact, including the requirement for
four separate compatibility roles, static Cursor plugin layout checks, and
external SDK reference guidance.

The bounded proof surface is local and write-free:

- `scripts/cursor_plugin_scanner_adapters.py` inventories README/test/startup
  evidence while withholding the compatibility score when the published
  `agent-compatibility` scanner is not installed or executed. A supplied real
  scanner result is preserved as input; the adapter never computes a score.
- `scripts/cursor_plugin_scaffold_fixture.py` creates only a marked disposable
  static fixture and stops before hooks, MCP, marketplace wiring, or the
  default `~/.cursor/plugins/local` destination.
- `scripts/cursor_plugin_submission_audit.py` checks local manifest paths,
  component frontmatter, README presence, and passive hook/MCP signals. It
  never executes components or recommends submission.
- `scripts/cursor_plugin_scanner_adapters.py` reports SDK symbols as
  `REFERENCE_ONLY`, keeps runtime support `UNAVAILABLE`, and rejects
  credential, authentication, execution, network, and MCP configuration
  inputs.

Positive proof: the compatibility fixture reports separate evidence with no
invented score; a supplied numeric scanner score is retained; the scaffold
fixture plus submission auditor produce `FIXTURE_ONLY` and `STRUCTURAL_PASS`;
and the SDK fixture identifies `@cursor/sdk`, `Agent.create`, and
`Agent.prompt` without claiming execution.

Negative proof: scanner installation and network remain false; compatibility
score is `None` without real scanner evidence; invalid or nonempty scaffold
destinations stop before writing; hooks, MCP, and marketplace requests return
`REVIEW_REQUIRED`; unsafe manifest paths and missing frontmatter fail the
submission audit; and SDK requests containing `apiKey`, `CURSOR_API_KEY`,
`mcpServers`, or execution flags fail closed.

Validation run in the successor worktree:

- `pytest -q tests/test_cursor_plugin_scanner_adapters.py tests/test_cursor_plugin_scaffold_fixture.py tests/test_cursor_plugin_submission_audit.py` — 13 passed.
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
