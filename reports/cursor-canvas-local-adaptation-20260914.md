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
`render_docs_canvas` produces a table of contents with document and
section-level cross-references, unique document-scoped anchors, safe links back
to source Markdown, and escaped common inline emphasis/code. Link schemes are
limited to relative, `http`, `https`, and `mailto`; executable or data schemes
are rendered as text. Relative links in source Markdown are rebased from the
source file’s directory to the generated artifact, with outside-root escapes
rejected before writing. `render_pr_review_canvas` groups diff files in
reviewer-value order (core logic, wiring/integration, mechanical), summarizes
mechanical files without copying their patch, and emits bounded attention
callouts only when evidence appears on a changed line. Both return `FALLBACK`,
`canvas_parity: UNAVAILABLE`, the artifact paths, and the explicit-only/conditional
policy. The HTML fallback has a narrow mobile layout for headings, lists, and
diff blocks.

The focused proof is [`tests/test_cursor_canvas_adapters.py`](../tests/test_cursor_canvas_adapters.py):

- a positive docs fixture verifies linked Markdown/HTML output, visible Canvas
  gap, safe URL schemes, source-relative link rebasing, emphasis/code rendering,
  and mobile-ready HTML;
- duplicate documents and headings receive unique anchors and section-level
  TOC links;
- unsafe source cross-reference escapes are rejected before artifact creation;
- a positive diff fixture verifies grouping, stats, changed-line evidence, and
  mechanical summaries;
- implicit invocation is blocked before artifact creation;
- a symlinked source is rejected;
- a GitHub URL is reported as an unavailable live capability.

Validation: `python3 -m unittest -v tests/test_cursor_canvas_adapters.py` passed
6 tests. The pinned source hashes remain unchanged in the overlays:

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

## Visual QA

Two isolated Impeccable assessment paths inspected the original rendered
documentation and PR pages. The design pass found duplicate heading IDs,
document-only navigation, literal Markdown, mechanical diff noise, and
attention callouts overtriggered by TODO text. The detector found one flat
typography warning on each page; browser overlays also flagged long warning
lines. The follow-up implementation addressed these in one batch. A single
browser confirmation found zero detector warnings, no duplicate IDs, correct
PR heading outline, no literal Markdown, a compact mechanical summary, and no
horizontal overflow at 390px. That browser snapshot predated the final
same-level-heading and source-link corrections. Focused tests now verify both
corrections. No further visual parity with Cursor Canvas is claimed.

The final security re-review found that the Markdown fallback still retained
unsafe source links even though the HTML renderer dropped them. Both outputs
now apply the same link policy: executable and data schemes, protocol-relative
targets, controls, backslashes, and scheme lookalikes are removed. The focused
test asserts the negative cases in the Markdown artifact as well as HTML;
6 tests passed after the correction.

Questions skipped: this was a publication-gate assessment of a held fallback,
not a request for a new visual direction.
