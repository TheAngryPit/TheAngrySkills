# Pstack supporting-file parity audit

Source: `cursor/plugins@df581122cde17e6e27686b5a448bde23e4ad4318` (0.15.15). No installation or live activation.

## Source and distribution inventory

| Skill | Skill-owned upstream support files | Distribution |
|---|---:|---|
| `cursor-reproduce-and-fix-issues` | 3 | all bundled |
| `cursor-setup-benny` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-triage-issue-reports` | 1 | all bundled |
| `cursor-architect` | 3 | all bundled |
| `cursor-arena` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-automate-me` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-benchmark-checklist` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-blast-radius` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-bro` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-correct` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-create-verification-skill` | 3 | all bundled |
| `cursor-figure-it-out` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-how` | 2 | all bundled |
| `cursor-interrogate` | 4 | all bundled |
| `cursor-maintain-verification-skill` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-make-bot-ui` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-no-comments` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-poteto-mode` | 44 | all bundled |
| `cursor-principle-attack-the-premise` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-boundary-discipline` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-build-the-lever` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-encode-lessons-in-structure` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-exhaust-the-design-space` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-experience-first` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-explain-the-number` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-fix-root-causes` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-foundational-thinking` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-guard-the-context-window` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-laziness-protocol` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-make-operations-idempotent` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-migrate-callers-then-delete-legacy-apis` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-minimize-reader-load` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-model-the-domain` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-never-block-on-the-human` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-outcome-oriented-execution` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-prove-it-works` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-redesign-from-first-principles` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-separate-before-serializing-shared-state` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-sequence-verifiable-units` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-subtract-before-you-add` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-test-behavior-not-implementation` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-principle-type-system-discipline` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-recall` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-reflect` | 4 | all bundled |
| `cursor-setup-pstack` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-show-me-your-work` | 2 | all bundled |
| `cursor-swarm` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-tdd` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-teach` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-technical-writing` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-typescript-best-practices` | 1 | all bundled |
| `cursor-unslop` | 0 | no skill-owned support (shared bundles listed separately) |
| `cursor-why` | 12 | all bundled |
| `cursor-poteto-help` | 2 | all bundled |

All skill-owned pstack support files are bundled; the full 903-file raw upstream tree remains intact. Shared guide snapshot is refreshed from the current pinned raw tree (including all eleven Markdown pages and six images); a native guide is bundled in `cursor-poteto-help/references/guide`. Shared agents and Benny templates retain their existing explicit distribution mappings.

## Demonstrated corrections

- Comparison detects changed, deleted and newly added shared guide documents; no source import or pin advancement occurs during comparison.
- Native guide preserves current upstream sections while adapting invocation, setup, model selection, scoped authoring, cloud capability and recurrence assumptions. Relative guide, image and skill links are checked.
- Reflect reviewer templates recognize native reads and collaboration evidence, without requiring Cursor Read/Task events.
- Orchestration uses actual native collaboration/concurrency and explicit scoped state; no assumed Cursor Task environment or cloud default.
- Worktree audit preserves paths with spaces, exposes cached Git facts and disk size, holds unknown native usage and untracked work, and never fetches, reads private transcripts, or deletes. Cleanup uses native managed archival or authorized recoverable removal.
- CLI bootstrap reuses the pinned installed commander version; missing/mismatched dependencies fail without installation or restart. An obsolete legacy stamp does not trap a correctly reprovisioned installation.

## Proof limits

Source parity and synthetic executable tests are distinct from live playbook operation. Existing externally integrated orchestration/watch tooling retains its task-specific execution gates; no credentials, recurring jobs, API spending or installation were activated. Explicit unsupported Cursor-product references remain provenance where appropriate.

Shared distribution also includes the 12-file Benny pack and license/provenance in setup, plus the native read-only worktree helper. Security adds one reviewed bundled-script signal for that helper; blocking signals remain zero and the ten existing review-needed packages retain their execution gates.

Final local verification: 363 tests and 11 subtests passed. Deterministic generation passes (510 output files), raw upstream integrity passes (903 files), native adaptation coverage passes (zero unresolved links), catalog has zero errors, JavaScript syntax and Matt adaptation checks pass. Native Astra review cleared the corrected source. Guide drift (modify/delete) and newly added Benny support regressions failed before the corresponding owner repair and pass afterward. The security ledger records exact changed-package findings.
