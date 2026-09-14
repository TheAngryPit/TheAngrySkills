# Native `cursor-interrogate` proof and promotion verdict

Date: 2026-09-14

## Repository and scope

- Separate clone: `disposable-scratch/theangryskills-interrogate-20260914`
- Branch: `codex/interrogate-proof-20260914`
- Starting commit: `ea9dbb53`
- Owned repository changes: this report, the `cursor-interrogate` overlay and
  its contract test only.
- Untouched: manifest/marketplace, snapshot source and refs, router, setup,
  Arena overlay, PR/merge/push state and global installation.

The exact PR #66 diff was unavailable in this worker clone's local refs.
A separate Sol-coordinated review did use immutable PR #66 head `9b595217`;
its observations are recorded below and are not inferred from this fixture.

## Source contract and ledger read

Read in full:

- `sources/cursor-plugins/snapshot/pstack/skills/interrogate/SKILL.md`;
- `references/lead-judgment.md`, `rubric.md`, `reviewer-prompt.md`, and
  `code-quality-review.md`;
- `sources/cursor-plugins/overlays/cursor-interrogate.json`;
- `reports/pstack-interrogate-review-20260914.md`;
- `reports/cursor-held-closure-ledger.md`.

The source requires same-scope reviewers, adversarial findings, deduplication,
lead judgment and no automatic application. The ledger identifies the missing
native multi-review behavior as the next executable step.

## Intent

Run two bounded read-only reviewers over the same disposable diff and rubric,
preserve separate reports, deduplicate findings, produce a lead judgment and
never auto-apply a fix. Record requested and effective model evidence separately;
the fixture does not claim exact PR coverage.

## Native capability/readback boundary

The native `collaboration.spawn_agent` surface returned an agent ID and
nickname. The requested model and reasoning effort were accepted as invocation
metadata. `multi_agent_v1__wait_agent` returned completion status and final
text, but no authoritative effective-model or effective-effort fields. Agent
self-reports are not attestation. Consequently this run proves two independent
reviewer executions and same-scope consensus, but does not prove verified
multi-model diversity or effective effort.

## Disposable case

Target: `disposable-scratch/interrogate-case-20260914/review_target.py`.
Intent/scope: `disposable-scratch/interrogate-case-20260914/scope.md`.

Reviewer A: `01a0a145-6f08-7ac1-b960-0b471a17550a`, requested
`gpt-6-astra`/low. Its report was returned inline and coordinator-materialized
at `disposable-scratch/interrogate-case-20260914/reviewers/reviewer-a.md`.

Reviewer B: `01a0a145-6d85-7623-b537-fd18bdd247ab`, requested
`gpt-5.6-luna`/high. It wrote
`disposable-scratch/interrogate-case-20260914/reviewers/reviewer-b.md`.

Both were instructed read-only and no repository, target or external state was
modified by them.

## Deduplication and lead judgment

The synthesis is at `disposable-scratch/interrogate-case-20260914/synthesis/dedup.md`
and the lead judgment is at
`disposable-scratch/interrogate-case-20260914/synthesis/lead-judgment.md`.

Both reviewers independently found the same four issues:

1. missing target crashes before first publication — Act on;
2. direct `write_text` can destroy the last valid target — Act on;
3. malformed-target behavior has no explicit policy — Act on;
4. revision-only equality can conceal changed content — Consider pending a
   proven revision invariant.

No findings were dismissed. The target remains unmodified and the verdict is
request changes. This is code-level review proof, not target runtime or PR
coverage proof.

## Separate PR #66 review case

Sol assigned two read-only native reviewers the same PR #66 head `9b595217`,
intent paragraph and source rubric/code-quality lens. One requested Astra low
reported a rendered Arena dropout/independent-judge gap. One requested Luna high
reported a missing bounded entry gate, a test-local behavioral helper counted
as product proof, and a stale ledger count. Each finding was assessed by the
coordinator, accepted, fixed, and verified in commit `4e4139a0`; CI passed on
that head. The findings were distinct, so no false cross-reviewer consensus is
claimed. Both reviews were read-only and did not auto-apply patches. Requested
profiles are invocation metadata, not independently verified effective model
identity. This case proves same-diff review and lead judgment for PR #66 but
not full effective multi-model routing.

## Repository validation

```text
python3 -m json.tool sources/cursor-plugins/overlays/cursor-interrogate.json
pytest -q tests/test_cursor_functional_overlays.py tests/test_cursor_pstack_core.py
24 passed in 31.63s
```

The separate clone is clean apart from this report, the `cursor-interrogate`
overlay and its focused contract assertion. No manifest or marketplace diff is
present.

## Promotion verdict

`cursor-interrogate` is published for a bounded explicit-only native review
with at least two distinct model requests accepted by the native spawn surface,
two separate read-only results, the same immutable scope/rubric, deduplication,
lead judgment and no auto-apply. This follows the source's configured-model
request mechanism; the source does not require a second backend attestation
channel. The available Codex tool does not expose authoritative effective
model/effort readback, so actual backend diversity remains unverified and must
not be claimed. If a configured reviewer cannot launch or return, the result
is PARTIAL with the missing slot named. Automatic host trigger, full default
four-reviewer coverage and production parity remain separate gaps. The
worker's earlier held verdict was superseded only after Sol reviewed both
case reports, the source contract and the native selection boundary.

## Observed degraded reviewer path

After a reviewer identified that the promotion proof lacked an observed
dropout, Sol dispatched two native read-only reviewer slots on the same
immutable scope, `5f040667`'s Interrogate overlay and generated skill, and
the same bounded rubric. `/root/interrogate_dropout_survivor` was requested as
Astra low and returned a cited contract review. The configured
`/root/interrogate_dropout_missing` slot was requested as Luna high, accepted
by native dispatch, and then deliberately interrupted while `running`; it
returned no review. Neither slot edited a file.

**Aggregate status: `PARTIAL`.** The missing Luna-high slot is named above.
The survivor found no blocking issue in the written fallback but explicitly
said its own inspection did not prove dropout handling. Sol retained that
single report as evidence, did not deduplicate or claim consensus, and made
no skill edit from this review. The interrupted slot contributes zero findings
and cannot be silently replaced. Requested profiles were accepted; effective
backend model/effort readback was unavailable. This validates the relevant
degraded no-auto-apply boundary in the current native coordinator, not an
automatic host-level skill invocation.
