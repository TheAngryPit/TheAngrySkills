# Native architect/arena adaptation proof

Date: 2026-09-14

## Repository and ownership

- Canonical repository: `TheAngrySkills`.
- Immutable requested base: `ddfb440691f4513bc2d90968c79d54c7cdb6cb42`
  (`feat(cursor): stage native adapters for the full active catalog (#64)`).
- Checkout: `/private/tmp/theangryskills-architect-arena-20260914`.
- Branch: `codex/architect-arena-20260914`.
- Owned changes: `cursor-architect` overlay, `cursor-arena` overlay, one
  focused contract test, and this report.
- Untouched: manifest/marketplace, pinned snapshot source and references,
  router, setup, poteto, no-comments, PR state, and pushes.

The source and pinned support files were read in full before adaptation. Their
source hashes remain the manifest values:

- architect `SKILL.md`: `897a59beaa3cab107d98c256206e062cc4a5e9421a45b9d462fbded19291fea5`;
- architect references: `design-red-flags.md`
  `905066f9bbac81c573c2b325be47751d2c0f9325e0a0772bd4384e82dafe9336`,
  `rationale-template.md`
  `0cedfccdc7b47fc881febd5a8293eecbc542c20f8df825639904a8102d2eb5d3`, and
  `runner-prompt.md`
  `983bf2820cc14ed8ecab6e448e1033e5cfe6031967d0a9287b48c7fa9c33d925`;
- arena `SKILL.md`: `8d431f7b1aa19daf6300366fc876c4d1aadac06417ec5502407345ffaf4e90d9`.

## Native invocation metadata versus self-report

The native tool exposed `multi_agent_v1__spawn_agent`; no exact `architect` or
`arena` agent type and no upstream Cursor runner slug were available. The
following is invocation metadata recorded from the coordinator's tool calls,
not a claim that the worker runtime independently read back its model:

| Role | Agent ID | Native `agent_type` | Requested model/effort | Output |
| --- | --- | --- | --- | --- |
| Candidate 1 | `01a0a0f9-78a7-7911-aa9c-29b349bf2a81` (Descartes) | `general-worker` | `gpt-5.6-luna` / `high` | `/private/tmp/architect-arena-20260914/candidate-1/{candidate,rationale}.md` |
| Candidate 2 | `01a0a0f9-8003-71b1-a971-a8daa53ade17` (Mill) | `general-worker` | `gpt-5.6-luna` / `high` | `/private/tmp/architect-arena-20260914/candidate-2/{candidate,rationale}.md` |
| Cross-judge | `01a0a0fe-28fe-7941-8968-8ebe57428d7d` (Euclid) | `reviewer` | `gpt-6-astra` / `low` | `/private/tmp/architect-arena-20260914/judge/cross-judge.md` materialized by coordinator from returned verdict |
| Review/redesign | `01a0a100-8583-7240-9203-f4b3681810c6` (Copernicus) | `planner` | `gpt-6-astra` / `low` | `/private/tmp/architect-arena-20260914/synthesis/{review-redesign,synthesized-design}.md` materialized by coordinator from returned verdict |

The candidates and reviewers self-reported completion and paths in their final
messages. Euclid explicitly self-reported that its requested file was not
written, and Copernicus explicitly self-reported that its two requested files
were not written; the coordinator then materialized those returned outputs.
That distinction is preserved here. The tool does not expose a separate
runtime model readback, so requested model/effort is metadata, not an
independently verified worker assertion. No Work cloud worker was used.

## Disposable architect/arena case

The fixture is `/private/tmp/architect-arena-fixture-20260914`:

- `notes_store.py` is a real Python domain boundary with frozen `Note`, private
  JSON persistence, ordered `strip().lower()` substring search, and unchanged
  `create`, `search`, and `reset` behavior.
- The task was to design idempotent `export_matching(query, destination)`
  without exposing storage/wire details or creating a second source of truth.
- Candidates had separate writable paths and were forbidden from editing the
  fixture or repository.

Both candidate packages were read end to end before judging. They were
structurally distinct:

- Candidate 1: one deep command/result export service with content revision and
  atomic publication.
- Candidate 2: immutable export plan plus configured destination capability and
  destination-owned receipts/reconciliation.

The cross-judge scored Candidate 1 `19/24` and Candidate 2 `17/24`, selecting
Candidate 1 conditionally. It identified Candidate 2's historical receipt
false-success and atomicity contradiction, and Candidate 1's loose locator and
status semantics. The accepted grafts were configured destination capability
and current-target content verification; Candidate 2's receipt-first ledger
was rejected.

## Architect review and redesign

The failed hypothesis was not papered over. Copernicus reviewed the selected
base and produced a redesign that:

- replaces the plain locator string with an opaque configured
  `ExportDestination` capability;
- preserves configured physical names instead of stripping them;
- defines `CREATED`, `REPLACED`, and `UNCHANGED` at an explicit publication
  decision point, allowing a first call to be `UNCHANGED`;
- requires current full-target validation before `UNCHANGED`;
- fails closed on malformed, foreign, aliased, or unreadable targets;
- protects canonical paths, symlink components, hard-link identity, and
  source/destination identity;
- serializes cooperating exporters before source selection and distinguishes
  pre-replacement failure from uncertain post-replacement outcome;
- limits the first supported guarantee to a quiescent source and exclusively
  managed destination directory.

The synthesized design is in
`/private/tmp/architect-arena-20260914/synthesis/synthesized-design.md`; the
failure ledger is in `review-redesign.md`.

## Verification

The coordinator ran the synthesized disposable contract check:

```text
synthesis-contract: PASS
proof: create, retry-unchanged, changed-replace, malformed-conflict, source-conflict, reset
```

This is a real temporary backend proof of the redesigned contract, not a
production implementation. It does not prove crash recovery, power-loss
durability, hostile-writer protection, or a live product adapter.

Repository checks:

```text
python3 -m json.tool sources/cursor-plugins/overlays/cursor-architect.json
python3 -m json.tool sources/cursor-plugins/overlays/cursor-arena.json
pytest -q tests/test_cursor_architect_arena.py tests/test_cursor_pstack_core.py tests/test_cursor_functional_overlays.py
25 passed in 11.61s
```

The focused test covers exact native role strings, bounded availability,
partial/dropout fallback, held promotion, source-path parity, and explicit
invocation-metadata wording. An initial test run failed only because the new
architect assertion required the phrase `invocation metadata` before the
overlay stated it; that wording was corrected and the clean rerun passed.

## Adaptation boundary and remaining gaps

The two overlays now map:

- architect candidates to native `multi_agent_v1__spawn_agent` with
  `agent_type=general-worker`, cross-judge to `reviewer`, and failed-hypothesis
  redesign to `planner`;
- arena to N=2 separate candidate paths, full-candidate read, independent
  cross-judge, explicit base/graft/rejection, redesign-on-failure, and
  verification.

Promotion remains held. Automatic skill triggering, exact upstream Cursor
runner parity, native model/effort runtime readback, production implementation,
crash/power-loss proof, hostile-writer semantics, and end-to-end host behavior
remain unproven. The fixture and all local state are disposable and no reset or
external mutation was performed.
