# Cursor mirror scope selection

Date: 2026-09-14. After PR #68 merged, Vítor excluded seven more upstream
sources from the Codex mirror and selected all other twelve pending candidates
for conversion. This decision changes scope; it does not claim the twelve have
been converted or installed.

## Intentionally excluded

- `cursor-make-bot-ui` (earlier decision)
- `cursor-add-dictation`, `cursor-add-read-aloud`, `cursor-add-voice`,
  `cursor-debug-voice` (Grok Voice)
- `cursor-setup-benny`, `cursor-triage-issue-reports`,
  `cursor-reproduce-and-fix-issues` (Benny automations)

Each exclusion has `excluded_from_mirror: true` and an operator reason in the
manifest. The generator rejects publication of excluded sources and omits
them from candidate previews. Their pinned upstream files, hashes, license
evidence, earlier findings, and historical reports remain available for
provenance. Refresh can detect changed upstream files but cannot silently
publish or preview an excluded source.

## Selected for conversion

- Agent, hook, and loop workflows: `cursor-advisor`,
  `cursor-continual-learning`, `cursor-orchestrate`, `cursor-ralph-loop`,
  `cursor-cancel-ralph`.
- Plugin and SDK workflows: `cursor-check-agent-compatibility`,
  `cursor-create-plugin-scaffold`, `cursor-review-plugin-submission`,
  `cursor-cursor-sdk`.
- Context and Canvas workflows: `cursor-workflow-from-chats`,
  `cursor-docs-canvas`, `cursor-pr-review-canvas-pr-review-canvas`.

These twelve remain unpublished until each native Codex adaptation meets its
own behavior and security proof. Source-only rendering or mocks do not prove
runtime parity. External credentials, provider calls, hook trust, global
installation, and merge require their own authority.

Current accounting: 91 historical physical sources = 71 published mirrors +
12 selected pending conversions + 8 intentionally excluded sources. The three
Benny sources are among the eight exclusions, not additional candidates.
