# Held Canvas local adaptation

Date: 2026-09-14. Scope: the held `cursor-docs-canvas` and
`cursor-pr-review-canvas-pr-review-canvas` overlays only.

The pinned sources require `~/.cursor/skills-cursor/canvas/SKILL.md` and Cursor
Canvas SDK declarations. That surface is unavailable in this Codex session.
The adapter therefore keeps the workflows conditional: it reads an explicitly
selected, bounded project-local Markdown source or unified diff fixture and
writes `index.md` plus `index.html` below the supplied project root. It does
not read the Cursor home, call `gh`, access a network, install tools, use hooks
or MCP, change product configuration, publish, or claim Canvas parity.

The implementation is [`scripts/cursor_canvas_adapters.py`](../scripts/cursor_canvas_adapters.py).
`render_docs_canvas` produces a table of contents, section anchors, and links
back to source Markdown. `render_pr_review_canvas` groups diff files in
reviewer-value order (core logic, wiring/integration, mechanical) and emits
bounded attention callouts for security, auth, migration, retry, concurrency,
and TODO markers. Both return `FALLBACK`, `canvas_parity: UNAVAILABLE`, the
artifact paths, and the explicit-only/conditional policy.

The focused proof is [`tests/test_cursor_canvas_adapters.py`](../tests/test_cursor_canvas_adapters.py):

- a positive docs fixture verifies linked Markdown/HTML output and the visible
  Canvas gap;
- a positive diff fixture verifies grouping, stats, and attention callouts;
- implicit invocation is blocked before artifact creation;
- a symlinked source is rejected;
- a GitHub URL is reported as an unavailable live capability.

Validation: `python3 -m unittest -v tests/test_cursor_canvas_adapters.py` passed
4 tests. The pinned source hashes remain unchanged in the overlays:

- `docs-canvas/skills/docs-canvas/SKILL.md`:
  `6b38908f9ab810c72f1d85b7f104520c91ee04f3b4fb84a4352c83be15a60b1d`;
- `pr-review-canvas/skills/pr-review-canvas/SKILL.md`:
  `f494f30a2d423953b4976d41353702fa32d347edf27519dbf936db5717865f03`.

The offline security scanner was run against a disposable skill wrapper that
contained this adapter and returned `safe_to_install` with zero findings. A
direct `security scan` of the standalone script is not a valid scanner input
because that command requires a skill directory; the wrapper result is the
applicable code scan evidence, while the two mirrored overlays retain their
upstream `safe_docs_only` security verdict.

The remaining blocker is the distinct Canvas SDK/component and live PR
metadata path. This work leaves both candidates held and conditional; it does
not promote them or imply interactive Canvas behavior.
