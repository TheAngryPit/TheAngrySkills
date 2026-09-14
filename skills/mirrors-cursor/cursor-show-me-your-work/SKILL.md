---
name: cursor-show-me-your-work
description: "Keep a reviewable decision trail for long-running or unattended work: a TSV log with one row per decision (what, why, evidence, result). Local by default; commit it when a reviewer needs the trail to trust the result. Use for /show-me-your-work, autonomous or multi-phase runs, or work a human reviews after stepping away."
---

## Codex runtime mapping

Keep the canonical TSV and pinned source `scripts/log.sh` intact. The bundled helper requires `--root <task-root>` and a logfile below that root; it rejects path escapes and symlink components or targets while preserving append-only TSV sanitization. Write only inside the authorized workspace or task scratch path, verify evidence links, and use the native task history/rollout for transcript audit. Independent review follows the standing model router and is reported only when performed.

# Show me your work

Keep one canonical log.

## The format

A single TSV file, one row per decision. Cells stay single-line. Evidence is a pointer, not prose.

Copy `references/decision-log-template.tsv` (the header row) to start a clean log. Columns:

- **ts.** ISO8601 timestamp.
- **phase.** The phase or workstream.
- **decision.** What was chosen or done, one line.
- **why.** The reason in plain words. If a principle drove it, say it plainly, not as a jargon tag.
- **evidence.** A link or path that proves it: commit SHA, PR number, `file:line`, or an artifact, trace, or screenshot path. Never a paragraph.
- **result.** The outcome or predicate state: `tests green`, `reverted`, `pixel-diff 0`, `INCONCLUSIVE`, `open`.

An example, plain-spoken so a reviewer reads it at a glance. This is illustration only. Don't copy these rows into a real log.

```
ts	phase	decision	why	evidence	result
2026-05-24T09:02:00Z	frame	counted the work first, about 100 components and roughly 75 hours	wanted to know the size before starting a long run	commit 3a9f1c2	found 5 things to sort out before starting
2026-05-24T09:40:00Z	harness	took screenshots of the old version before changing anything	so we can compare old against new and catch any visual change	scripts/snapshot.sh, baseline/	saved 120 reference screenshots
2026-05-24T11:15:00Z	widget	moved the widget styles over without changing how it looks	keep the change small and the result identical	commit 7c21e0a, pixel-diff 0	looks identical, tests pass
2026-05-24T12:30:00Z	widget	threw out a helper's work because its screenshots were blank	checked the real files instead of trusting its summary	worktree reset	reverted, tightened the instructions for next time
```

## Logging a row

Write each entry the way you'd tell a teammate what you did. Plain words, concrete actions, no AI speak or abstract jargon (the **unslop** skill applies to log text too).

Use the bounded helper `scripts/log.sh --root <task-root> <logfile> <phase> <decision> <why> <evidence> <result>`. It stamps `ts`, writes the header on first use, strips stray tabs/newlines, and prefixes any cell starting with `=`, `+`, `-`, or `@` with a single quote. Use the bounded helper for generated or user-supplied cells. A manual `printf` is only appropriate inside the authorized task root after the same single-line, formula-prefix and secret checks.

Log decision points and checkpoints, not every action: a fork chosen, a unit completed with its verification result, a pivot or revert with its trigger, a blocker surfaced, a gate fixed. For loop runs, one row per iteration. Skip the trivial and self-evident.

## Where it lives

By default the log is a working artifact, not committed. Keep it at `decisions.tsv` in the work dir, or `.audit/<task-slug>.tsv` when several efforts run at once, and leave it out of git.

Commit it only when the work is ambitious enough that a reviewer needs the trail to trust the result.

## Rules

- One row is one decision or checkpoint.
- Append-only. A wrong call gets a new row that supersedes it. Never edit or delete history.
- Prefer evidence produced by committed scripts over hand-made one-offs (the **encode-lessons-in-structure** principle skill).

## Audit the log against the transcript

At the end of the run, before handing back, check the log told the truth. Read the current Codex task history through the native thread reader or its verified local rollout path when available. Do not glob other projects or rely on a Cursor transcript path; if full tool history is inaccessible, name that audit limit. Walk the log against what actually happened:

- Every row maps to a real action. Cut invented or aspirational entries.
- Each row's evidence resolves and shows what the row claims.
- A fork, pivot, or abandoned approach that shaped the work but isn't logged is a gap. Add it.
- Drop padding.

Fix the log, not the story. If the work diverged from what a row claims, the row is wrong.

## Cross-model review of the trail

Before handing back, use an authorized independent Codex reviewer when a different model perspective is available under the standing `model-capability-router` policy. If no reviewer or full transcript access is available, report the evidence limit without inventing cross-model sign-off. The subagent reads the audit trail and the run's transcript, then flags what the user should pay attention to. Not a redo of the work, a scan for what's suboptimal or risky.

- Decisions logged with weak or absent evidence.
- Verification steps skipped or claimed without proof in the transcript.
- Choices that look risky in hindsight (premature, scope-creeping, papering over a symptom).
- Gaps the user would otherwise miss on a casual skim.

Every reply for a run that produced a trail ends with an "Attention" section. Name the actual reviewer model when one ran, then list flags tied to rows or moments. If review could not run, label it not assessed; never infer a reviewer from the selected route.

## Reviewing the trail

Read top to bottom, follow the evidence pointers, spot-check. GitHub renders a committed TSV as a table. `column -s$'\t' -t decisions.tsv` renders it in a terminal.

## Composing this skill

Other skills route their audit trail here instead of inventing one. Reference it by name and let it own the format. Don't restate the columns.
