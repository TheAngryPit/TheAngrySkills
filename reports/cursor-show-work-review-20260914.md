# `show-me-your-work` bounded native proof

Date: 2026-09-14. Source: pinned `cursor/plugins` at
`889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`. The source
`pstack/skills/show-me-your-work/SKILL.md` and `scripts/log.sh` remain pinned
unchanged. This report reviews the Codex overlay and one real local trail; it
does not claim automatic skill selection or global installation.

## Source contract and writer review

The pinned skill requires one append-only TSV with a single-line decision,
reason, evidence pointer, and result per row. It requires a transcript audit
and a reviewer from a different model family before handoff. The pinned Bash
helper writes the caller's cells to a local file; the source scanner recorded
`executable-file` and `bundled-script-review` findings for that active writer.
There is no network call or credential read in the helper. Its write target and
cell content still require explicit scope and review.

The Codex overlay keeps the pinned source intact and renders a bounded helper
that requires `--root <task-root>`, rejects escapes, symlink components,
hardlinks and non-regular targets, and sanitizes tabs, newlines and spreadsheet
formula prefixes. This pass added an exclusive file lock around header/row
writes by cooperating processes. It also refuses evident credential-shaped
cells before opening a logfile: Bearer values, common token prefixes, and
key/value assignments including quoted JSON. The refusal emits a constant
error without echoing the cell. This is a heuristic guard; the operator must
still redact other secret forms before logging. No external write or message
permission is granted by the adapter.

## Real trail and audit

The overlay-generated helper created and appended the
[decision trail](cursor-show-work-live-trail-20260914.tsv) under an explicitly
supplied disposable task root. The rows document the actual contract review,
writer changes, focused/full tests, reviewer corrections, and final bounded
verification. Corrections were appended as new rows; earlier rows were not
edited. The current task's native rollout was checked only for this task:
source reads at ordinals 21439–21441, writer edits at 21488/21509, and test
outcomes at 21525 and 21573–21574 supported the original four rows. Later
tool results supported the correction rows. The referenced source, overlay,
tests and this report resolve in the PR tree; the private rollout is not
published as part of the PR.

Fourteen focused tests passed. They cover ordinary and parallel append (24
processes, one header, 24 complete six-cell rows), sanitization, rejection of
evident secret-shaped inputs without logfile mutation or stderr echo, root
and path bounds, symlink/hardlink/FIFO refusal, and unchanged external
sentinels. The full repository suite passed 197 tests and two subtests;
mirror `--check` reported 91 physical, 56 published and 223 output files at
this stage.

## Attention

reviewed by gpt-6-astra

- The independent reviewer found that the first token filter missed `ghp_`
  and quoted JSON assignments. Both patterns were added to the guard and
  checked with synthetic strings. Detection remains heuristic.
- The reviewer requested result pointers for test rows and complete six-cell
  assertions for parallel rows. Both were added. Its follow-up also found a
  test that failed to check full candidate echo for the `ghp_` fixture; that
  assertion was corrected and the focused suite passed again.
- Crash recovery, uncooperative writers, `fsync` durability, unknown secret
  formats, automatic skill selection, and the behavior of other hosts remain
  unproven. The published instruction must keep native task permissions and
  describe those limits.

## Publication decision

The source's required TSV, append-only correction, transcript audit and
different-family reviewer were exercised on a real local task trail. The
mirror's additional positive/missing/error and writer-security criteria were
checked with the focused suite and script review. The generated SKILL now
uses the `--root` helper interface, preserving the source's operational
meaning while preventing the old unbounded invocation. The contextual
executable-writer findings stay recorded in the overlay with the bounded
publication decision. `cursor-show-me-your-work` is published as an
explicit-only local workflow; its automatic selection and the residual limits
above are not claimed as proven.
