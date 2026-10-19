# pstack 0.15.28 source refresh

## Source and scope

- Base: TheAngrySkills `7d4dd0098a07d8a879ba2ea2c29cd83aae7027d3`.
- Previously accepted pstack: 0.15.15 at `df581122cde17e6e27686b5a448bde23e4ad4318`.
- Reviewed pstack: 0.15.28 at `d457567332aa6989e753ea289f30ea2bfbc80bc0` in cursor/plugins.
- Refresh only pstack. The original full-tree inventory remains historical; the validated family ledger records the newer pstack tree without advancing unrelated plugins.
- Add explicit-only `cursor-create-formal-verification-skill` and `cursor-maintain-formal-verification-skill`.
- Preserve five existing exclusions, namespaced cross-skill links, native model routing and permission boundaries. Update both named native agent profiles and their bundled installer checks.
- Generated catalog: 112 physical sources, 107 published skills, 5 held adaptations, 14 agent mappings and 531 generated files.

## Fresh validation

- Untouched base: 374 tests passed, 2 skipped, 11 subtests passed.
- Candidate: 386 tests passed, 2 skipped, 11 subtests passed.
- Focused compatibility checks: 61 tests passed, 6 subtests passed.
- Deterministic generation, full source-family tree comparison, adaptation coverage and cross-skill links passed; zero unresolved links.
- Both named profiles match exact normalized current source bodies; no live-session load is claimed.
- Shared catalog: 307 skills, zero errors. Existing advisory warnings remain.
- JavaScript syntax and Git whitespace checks passed.
- Test audit and deslop reviewed adapter/checker changes. Comment Sicko found no actionable changed-code comments.

## Security comparison

The exact base and candidate trees were scanned with the same scanner and options. The Cursor mirror has zero blocking skills and the same ten skills requiring human review. Findings were compared by skill, file, rule, severity and evidence, rather than totals alone.

The only added finding is `bundled-script-review` for `cursor-poteto-mode/scripts/check-plan.test.ts`. It is an exact upstream Bun test file. Inspection found bounded temporary fixture creation, invocation of the adjacent plan checker and cleanup of its own temporary directory. It does not add install-time execution, network calls or credentials. No findings were removed or suppressed. Both new formal-verification skills scan as safe to install after quality review.

The complete source catalog comparison also retains 21 pre-existing blocking scanner classifications and 59 review-signal skills, all unchanged by identity and evidence. None is in the touched Cursor mirror or native-router skill. This bounded refresh neither resolves those findings nor authorizes installing that unrelated content. The only new catalog-wide finding is the upstream test file described above.

## Independent review

The initial seven-pass Codex review found five distinct defects: duplicated native/upstream workflows, non-native guide prompts, an upstream-checkout provenance hazard, conflicting model routing and duplicated How control flow. All were corrected. The helper now refuses tracked, untracked and ignored pstack changes before any output writes; regression tests also cover classification preservation and repeated-run stability.

A focused independent Codex review of those fixes returned scoped-clean through P2. This is static review; the automated-test results above are separate evidence.

## Proof limits

This is source and test proof. It does not establish automatic skill selection, complete live workflow parity, new global installation, target-machine health or native profile loading. Historical runtime evidence is explicitly retained as historical. The existing upstream automation remains detector/report-only.
