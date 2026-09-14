# Interrogate review of verification fixture B

Date: 2026-09-14
Reviewed immutable diff: `614538da..abbe2077` in PR #64.

## Intent

Improve the project-local verification CLI fixture with syntax/version/health
Doctor, independent create/search drives, declared state cleanup, controlled
feature drift and a clean second invocation. Keep caller-supplied source-wave
input distinct from native delegated readers and keep both verification
skills held pending behavioral proof.

## Reviewers and attribution

Two read-only native reviewers received the same scope, intent, pinned
`interrogate` reviewer prompt, rubric, and code-quality lens. The spawn requests
were `gpt-6-astra` low and `gpt-5.6-luna` high. Their returned reviews did not
include trusted runtime model metadata: one self-reported GPT-6 Astra with
effort unknown; the other self-reported GPT-5 Sol medium despite the Luna
request. Self-reports are not model attestation. Independent reviewer execution
is observed; effective model diversity and requested effort are **unknown**.
Neither reviewer edited the checkout.

## Act on

| Finding | Reviewers | Judgment and disposition |
| --- | --- | --- |
| Maintenance could delete a pre-existing `notes.json`. | Astra | Real state-loss path. The shared drive boundary now rejects declared state before execution; a maintenance test verifies the original bytes survive. |
| The generated Doctor syntax command was an invalid `compile(...)` placeholder. | Both | Real delivered-skill defect. The generator now shares the executable syntax code with the runtime Doctor; a test executes the emitted command. |
| Cleanup reported PASS without the declared side-effect file. | Both | Real false-positive proof path. A successful drive must create every declared regular file before cleanup; a no-write command now fails. |
| Doctor could create state on failure and strand retries. | Second reviewer | Real on a disposable fixture when health writes state. The guarded Doctor rejects and cleans newly created declared state, returning BLOCKED with cleanup evidence. |
| Doctor evidence was transient despite the generated skill promising surviving evidence. | Second reviewer | Valid proof gap. Creation now writes `evidence/doctor.json`; maintenance writes `evidence/maintenance-doctor.json`, with readback assertions. |

## Consider

The caller-provided source-wave records are persisted without driving feature
reconciliation. That is intentional for the CLI fixture: source-wave content
has no native-reader provenance and must not become authority for a correction.
The persisted record now states `provenance: caller_supplied_input`, and the
result remains `OBSERVED_INPUT_ONLY`. The separate disposable UI case has two
native read-only source-reader receipts and a real browser re-drive; see
[UI proof](pstack-verification-skills-ui-20260914.md). Its cleanup remains
pending confirmation at action time.

## Agreement map and limits

Both reviewers independently found the invalid Doctor command and missing
side-effect assertion. Only one reported pre-existing-state deletion, Doctor
side effects, and missing persistent Doctor evidence; source tracing confirmed
the first three as actual defects. The second reviewer's apparent model label
is not a trusted runtime observation, so this run proves two independent
adversarial reviews and a synthesized correction, but it does not yet prove
the multi-model routing contract required to promote `cursor-interrogate`.
The reviews did not apply changes automatically; Sol reviewed and committed
the corrections separately.
