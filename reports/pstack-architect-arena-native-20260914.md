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

The public orchestration surface used was `collaboration.spawn_agent`; no exact
`architect` or `arena` agent type and no upstream Cursor runner slug were
available. The following is invocation metadata recorded from the
coordinator's tool calls, not a claim that the worker runtime independently
read back its model:

| Role | Agent ID | Public surface | Native `agent_type` | Requested model/effort | Output |
| --- | --- | --- | --- | --- | --- |
| Candidate 1 | `01a0a0f9-78a7-7911-aa9c-29b349bf2a81` (Descartes) | `collaboration.spawn_agent` | `general-worker` | `gpt-5.6-luna` / `high` | `/private/tmp/architect-arena-20260914/candidate-1/{candidate,rationale}.md` |
| Candidate 2 | `01a0a0f9-8003-71b1-a971-a8daa53ade17` (Mill) | `collaboration.spawn_agent` | `general-worker` | `gpt-5.6-luna` / `high` | `/private/tmp/architect-arena-20260914/candidate-2/{candidate,rationale}.md` |
| Cross-judge | `01a0a0fe-28fe-7941-8968-8ebe57428d7d` (Euclid) | `collaboration.spawn_agent` | `reviewer` | `gpt-6-astra` / `low` | `/private/tmp/architect-arena-20260914/judge/cross-judge.md` materialized by coordinator from returned verdict |
| Review/redesign | `01a0a100-8583-7240-9203-f4b3681810c6` (Copernicus) | `collaboration.spawn_agent` | `planner` | `gpt-6-astra` / `low` | `/private/tmp/architect-arena-20260914/synthesis/{review-redesign,synthesized-design}.md` materialized by coordinator from returned verdict |

Technical invocation receipt: the public calls were backed by the internal
`multi_agent_v1__spawn_agent` tool identifier. This backend identifier is kept
as factual receipt metadata; user-facing adaptation guidance uses only
`collaboration.spawn_agent`.

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

## Phase A how/why context

The exact installed-skill lookup found no `cursor-how` or `cursor-why` preview
under the configured Codex skill roots. Therefore no current-session exact-name
preview invocation is claimed. The pinned snapshot `how/SKILL.md` and
`why/SKILL.md` were read for the Phase A contract, and the prior
`reports/pstack-how-why-real-20260914.md` was preserved as context rather than
replayed as a new invocation.

The manual how grounding traced the fixture's source authority, frozen `Note`,
private JSON persistence, ordered search, and the required ownership boundary:
the export policy belongs behind `NoteStore.export_matching`, while destination
mechanisms remain private. The manual why context used the local overlay/source
history and retained the proof-gated hold: deterministic rendering and native
role-flow evidence do not prove automatic trigger or production parity.

This makes Architect Phase A evidence-backed but partial for the exact adapted
`cursor-how`/`cursor-why` preview path. The gap is recorded, not substituted by
a guessed trigger, and promotion remains held.

## Verification

The coordinator first ran the synthesized disposable contract check, then
implemented the final contract in a copied runtime app at
`/private/tmp/architect-arena-runtime-20260914`.

```text
synthesis-contract: PASS
proof: create, retry-unchanged, changed-replace, malformed-conflict, source-conflict, reset
```

The runtime implementation then produced this reproducible readback:

```text
PYTHONPATH=/private/tmp/architect-arena-runtime-20260914 python3 runtime_probe.py
runtime-after-fix: PASS
runtime: create/retry/drift-replace/changed-replace/query-filter/malformed-conflict/source-conflict/source-read-error/reset
```

Before the correction, the same runtime returned `UNCHANGED` after the target
payload was mutated while its revision field was left unchanged. The probe
failed with `AssertionError: revision-only equality incorrectly accepted drifted
target`. The service was reviewed against the redesign and corrected to require
full current-target payload equality before `UNCHANGED`; the rerun passed.
This is the requested real failure/drift and revision loop. It remains a
disposable implementation proof, not production code: crash recovery,
power-loss durability, hostile-writer protection, and a live product adapter
remain unproven.

Repository checks:

```text
python3 -m json.tool sources/cursor-plugins/overlays/cursor-architect.json
python3 -m json.tool sources/cursor-plugins/overlays/cursor-arena.json
pytest -q tests/test_cursor_architect_arena.py tests/test_cursor_pstack_core.py tests/test_cursor_functional_overlays.py
26 passed in 6.27s
```

The focused test covers exact native role strings, bounded availability,
partial/dropout fallback, Architect's held status, source-path parity, explicit
invocation-metadata wording, and a repo-owned behavioral fixture that
observes create/retry/replace/malformed-target/source-conflict results. The
test first exposed a harness path-conflict bug, which was corrected before the
clean rerun. The runtime drift failure above is separate and exercises the
actual copied implementation.

## Adaptation boundary and remaining gaps

The two overlays now map:

- architect candidates to native `collaboration.spawn_agent` with
  `agent_type=general-worker`, cross-judge to `reviewer`, and failed-hypothesis
  redesign to `planner`;
- arena to N=2 separate candidate paths, full-candidate read, independent
  cross-judge, explicit base/graft/rejection, redesign-on-failure, and
  verification.

Arena is published only for the bounded explicit local design path; Architect
remains held pending its exact `cursor-how`/`cursor-why` Phase A invocation.
Automatic skill triggering, exact upstream Cursor runner parity,
native model/effort runtime readback, production implementation,
crash/power-loss proof, hostile-writer semantics, and end-to-end host behavior
remain unproven. The fixture/runtime and all local state are disposable and no
reset or external mutation was performed.
