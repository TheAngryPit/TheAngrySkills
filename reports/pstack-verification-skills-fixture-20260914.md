# Verification-skill fixture proof

Date: 2026-09-14
Repository: `TheAngrySkills` (isolated clone)
Branch: `codex/verification-skills-b-20260914`
Authority head: `5fdd1894ea10716a51e5f42ce87a24d1da33013a`

This lot owns only the local adaptations/tests for
`cursor-create-verification-skill` and `cursor-maintain-verification-skill`.
The pinned source SKILL files were read completely before editing, together
with the feature-map examples, existing fixture report, and both overlays.
Pinned source, manifest, marketplace, product code, global home, hooks, PR,
push, merge, and external state were not changed.

## Target and proof boundary

The disposable target is the notes Python CLI from
`.scratch/pstack-bug-fix-notes/`. A CLI surface is valid for the source
contract, so no browser or screenshot proof is applicable here; this run does
not claim UI coverage. Each user-facing feature is driven in its own
`subprocess` with `shell=False`, closed stdin, a stripped environment, and
captured exit code, stdout, stderr, and regular-file side effects.

## Create proof

The generated target is `.agents/skills/verify-notes/`. Before the feature
drives, the fixture runs a read-only Doctor with all three required checks:

- Syntax: `syntax:ok`, exit `0`, empty stderr.
- Version: `notes-fixture 1.0`, exit `0`, empty stderr.
- Health: `health:ok`, exit `0`, empty stderr.

The positive pass then drives both mapped features:

| Feature | Exact observed result | Side effect |
|---|---|---|
| `create-note` | exit `0`, stdout `created:Release checklist\n`, empty stderr | `notes.json` observed as a regular file |
| `search-note` | exit `0`, stdout `found:Release checklist\n`, empty stderr | same declared notes state |

The generated skill contains Launch, Doctor, Drive, Evidence, Cleanup, and
Helpers, a feature README, one map file per feature, and JSON evidence. Cleanup
removed only declared `notes.json`, left no remaining app state, and preserved
the generated evidence, including `doctor.json`. The emitted syntax command
was executed from the generated skill and returned `syntax:ok`. Result:
`FIXTURE_ONLY`.

## Maintain proof

The run introduced controlled text drift only in
`features/create-note.md`. The source-wave input contained exactly one
summary, entry-point description, and live recipe for each of
`create-note` and `search-note`; the adapter persisted one source-wave JSON
record per feature. This is explicit feature-map/source-wave evidence, not a
claim that native delegated readers were available.

The first maintenance pass:

- ran Doctor again;
- re-drove both features;
- rewrote only the drifted `create-note` feature file;
- persisted `maintenance-before-*` and `maintenance-after-*` evidence;
- persisted `maintenance-doctor.json` and labelled each source-wave record
  `caller_supplied_input`;
- cleaned declared app state after the pass.

Observed result: `FIXTURE_ONLY`, `changed_features=("create-note",)`, source
wave `OBSERVED_INPUT_ONLY`, and both cleanup results `PASS`. A second maintenance
invocation returned `changed_features=()` with the same successful feature observations.

## Missing and error branches

- `app_available=False` returns `BLOCKED` before creating a skill tree.
- An unhealthy Doctor returns `BLOCKED`; no target tree is written.
- A pre-existing `notes.json` is rejected before generation.
- Maintenance also rejects a pre-existing `notes.json` without altering it.
- A Doctor that creates declared app state is blocked and that newly created
  state is cleaned before return.
- An expected confirmation without its declared regular-file side effect
  fails instead of returning `FIXTURE_ONLY`.
- A deliberately wrong expected result returns `ERROR` for `search-note` and
  still reports cleanup `PASS`; no target tree remains.
- Unsafe app/feature slugs and reserved `README` feature names are rejected.

## Validation and limits

Commands/results:

- `pytest -q tests/test_cursor_pstack_core.py -k verification` — `4 passed`.
- `pytest -q tests/test_cursor_pstack_core.py tests/test_cursor_functional_overlays.py` — `23 passed`.
- `pytest -q tests` — `197 passed, 2 subtests passed`.
- `git diff --check` — clean.

The adapter now requires explicit version and health checks when a Doctor is
provided, performs syntax checking without creating bytecode, drives every
mapped feature, cleans only declared regular files, records source-wave
evidence, and preserves evidence across cleanup. Filesystem/network
isolation, a live product target, browser parity, native host activation,
native delegated source readers, and PR correction remain unproven. The result
is fixture-only and neither candidate is promoted.
