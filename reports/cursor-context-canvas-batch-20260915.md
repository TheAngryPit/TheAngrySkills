# Cursor context and Canvas batch

Date: 2026-09-15. Scope: `cursor-workflow-from-chats`, `cursor-docs-canvas`,
and `cursor-pr-review-canvas-pr-review-canvas` only.

## Outcome

The three overlays now describe bounded, explicit-only Codex adaptations. The
two Canvas skills produce project-local linked Markdown/HTML artifacts when
the Cursor Canvas surface is unavailable. `workflow-from-chats` accepts one
explicitly supplied, project-local JSONL export and produces a redacted,
traceable preference proposal plus receipt. None of the adapters writes a
skill, rule, memory, product configuration, global setting, PR, or external
service.

The source text and pinned hashes remain unchanged. The adapters preserve the
upstream intent while recording the exact capability boundary: Cursor Canvas
SDK/primitive behavior, live PR metadata, and native automatic task-history
acquisition remain unavailable in this Codex session.

## Functional proof

`extract_workflow_from_chats` was exercised with a disposable export containing
two parent turns, one linked child record, and one unrelated thread. The
adapter selected only the requested parent scope and linked child evidence,
applied the seven-day window, corroborated repeated preference atoms, labeled
confidence, redacted a credential-shaped value, and wrote only `proposal.md`
and `receipt.json` beneath the selected project root. The receipt contains
metadata and atoms, never raw transcript text or the source path. Missing native
history, remote input, implicit invocation, missing/out-of-window records, and
malformed JSON remain write-free `PARTIAL`/`BLOCKED` or explicit errors.

The successful result reports those two local artifact writes explicitly and
separately reports that no durable skill, rule, memory, or configuration
writeback occurred.

The docs fallback retains its existing proof for document and section TOCs,
unique anchors, safe/rebased source links, escaped inline content, symlink and
root-escape rejection, and no product configuration. The PR fallback retains
its existing proof for bounded local unified diffs, reviewer-value grouping,
changed-line attention callouts, mechanical summaries, live URL rejection,
and no `gh`/network access.

Validation command:

```sh
python3 -m unittest -v tests/test_cursor_canvas_adapters.py
```

Result: 9 tests passed. The repository's previously recorded Impeccable
browser inspection remains applicable to the unchanged docs/PR HTML renderer:
zero detector warnings, correct heading outline, no literal Markdown, compact
mechanical summaries, and no horizontal overflow at 390px. This batch does not
claim visual parity with Cursor Canvas or repeat a screenshot when no visual
renderer code changed.

## Remaining gaps

Native history selection and automatic skill routing are unproven. Canvas SDK
primitives and live PR metadata are unavailable. The published status means
the bounded adapters are usable for explicitly supplied local inputs; it does
not mean the original Cursor runtime or Canvas product surface is available.
