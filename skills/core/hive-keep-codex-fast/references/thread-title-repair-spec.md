# Codex Thread Title Repair Spec

Date: 2026-06-20
Status: Draft for operator review

## Problem Statement

Codex thread titles can drift into prompt-sized blobs. When that happens, the
problem is not only visual. The title can become too long to scan, the thread
list becomes noisy, and the operator loses the short manual names that were
meant to organize work.

We need a repair tool that is conservative by default. It must separate:

- automatic oversized titles that can be repaired safely
- manual titles that must be preserved
- subagent or system-owned threads that should not be rewritten automatically
- archived real threads, which may be inspected and repaired under the same
  safety rules as active real threads

The tool must not touch `preview` for now. `preview` is a separate diagnostic
surface and can be analyzed later, but this spec is only about thread titles.

## Goal

Create a Codex thread title repair workflow with two modes:

- `--repair-thread-titles-dry-run`
- `--repair-thread-titles-apply`

`--repair-thread-titles-dry-run` classifies titles and proposes safe actions
without mutating anything.

`--repair-thread-titles-apply` repairs only eligible automatic titles, only
after backup, only with `--confirm-thread-title-repair
APPLY_THREAD_TITLE_REPAIR`, and only when the repair can be verified against the
pre-change and post-change state.

The core rule is simple:

- if a title is manual, preserve it
- if a title is automatic and oversized, only repair it when there is a safe
  existing short name to reuse
- if no safe short name exists, stop and require human input

This spec deliberately does not authorize synthetic name generation from the
prompt, transcript, cwd, model summaries, or any other inferred context. That
can be a later, separately reviewed feature if the operator wants it.

## Scope

In scope:

- read-only classification of thread titles
- backup-first apply flow
- post-fix verification
- restore helper generation
- comparison against `first_user_message`
- comparison against `session_index.jsonl.thread_name`
- support for real threads and archived real threads

Out of scope:

- `preview` mutation
- transcript rewriting
- `session_index.jsonl` rewriting
- cleanup, archive, delete, prune, rotate, install, disable, or deployment
- automatic synthesis of new names from prompt content
- subagent/system threads as automatic repair candidates

## Data Surfaces

The tool should read these surfaces when available:

- `threads.title`
- `threads.first_user_message`
- `threads.preview` for diagnostics only
- `session_index.jsonl.thread_name`
- thread source metadata such as `source`, `thread_source`, `agent_role`, or
  equivalent markers used by the local Codex state

The tool must not write to `threads.first_user_message`, `threads.preview`, or
`session_index.jsonl`. It must not rewrite rollout transcript JSONL files.

## Thread Classification

Each thread should be classified into one of these groups:

- `manual_keep`
  - `title` differs from `first_user_message`
  - preserve by default, even when long

- `auto_repair_candidate`
  - `title` equals `first_user_message`
  - title exceeds the configured maximum length
  - thread is a real user-owned thread, not subagent/system owned

- `safe_name_available`
  - `auto_repair_candidate`
  - a safe short name already exists in `session_index.jsonl.thread_name`
  - that existing name is short enough and operator-facing

- `needs_human`
  - `auto_repair_candidate`
  - no safe short existing name is available

- `excluded_subagent`
  - thread is owned by a subagent or system harness
  - do not auto-repair

Archived real threads are not excluded by default.

## Mode 1: `--repair-thread-titles-dry-run`

`--repair-thread-titles-dry-run` is the first safe title-repair command and must
be read-only.

Dry-run responsibilities:

- scan candidate threads
- classify each thread
- count manual titles, automatic bloat candidates, safe-name candidates, and
  `needs_human` cases
- show the proposed action for each candidate
- show the exact reason a candidate is blocked
- show whether a post-fix verification pass would be able to confirm the change

Dry-run must not:

- write any file
- create any backup
- create any manifest
- create any restore helper
- rewrite any title
- rewrite any `session_index.jsonl` entry
- rewrite `preview`

Dry-run output should make it obvious which entries are safe to repair now and
which entries need a human name decision.

## Mode 2: `--repair-thread-titles-apply`

`--repair-thread-titles-apply` is explicit and backup-first. Operators should
run and review `--repair-thread-titles-dry-run` before apply.

Apply responsibilities:

- require `--confirm-thread-title-repair APPLY_THREAD_TITLE_REPAIR`
- refuse to run if Codex state is actively being written, unless the operator
  explicitly approves a bounded wait
- create a backup before any mutation
- repair only eligible automatic oversized titles
- use only a safe existing short `session_index.jsonl.thread_name` when one is
  already present
- leave manual titles untouched
- leave `first_user_message` untouched
- leave `preview` untouched
- leave `session_index.jsonl` untouched
- write a restore helper and a repair manifest

Apply must not invent names from content. If a safe existing short name does not
exist, the thread remains unmodified and is reported as `needs_human`.

## Backup And Restore

Every apply run must create a pre-change backup that records, at minimum:

- thread id
- original title
- original first user message
- chosen replacement title, if any
- safe source of the replacement title
- verification result after write

The backup is required so that an unexpected mismatch can be restored without
guesswork.

Restore behavior:

- if any updated thread fails post-fix validation, restore the affected titles
  from the backup before the command exits
- if the tool cannot prove the repaired title stayed correct, it must fail
  closed

## Verification Rules

After apply, the tool must re-read the affected rows and compare:

- stored `title` against the chosen replacement
- `first_user_message` against the pre-change value
- `session_index.jsonl.thread_name` against the pre-change value

If any comparison fails, the tool must report the failure and restore from the
backup.

The verification pass is part of the contract. A mutation is not considered
successful until it has been re-read and matched.

## Validation Output

The tool should report:

- number of threads scanned
- number of manual titles preserved
- number of automatic repair candidates
- number of safe-name repairs applied
- number of `needs_human` candidates needing human input
- number of excluded subagent/system threads
- number of post-fix mismatches
- whether restore was required

## Non-Goals

This spec does not cover:

- metadata preview repair
- log rotation
- worktree pruning
- session archival
- config pruning
- package installation or deployment
- automation or scheduling
- broad Codex maintenance outside title repair

## Acceptance Criteria

1. `--repair-thread-titles-dry-run` runs against a synthetic Codex home and writes nothing.
2. `--repair-thread-titles-dry-run` classifies manual titles, automatic bloat candidates, safe-name
   candidates, `needs_human` candidates, and excluded subagent/system threads.
3. `--repair-thread-titles-apply` cannot run without
   `--confirm-thread-title-repair APPLY_THREAD_TITLE_REPAIR`.
4. `--repair-thread-titles-apply` creates a backup before mutating any title.
5. `--repair-thread-titles-apply` only repairs automatic oversized titles that already have a safe
   short existing name.
6. `--repair-thread-titles-apply` never rewrites `first_user_message`,
   `preview`, transcripts, or `session_index.jsonl`.
7. Manual titles remain unchanged after `--repair-thread-titles-apply`.
8. A post-fix verification pass re-reads the repaired rows and fails closed on
   mismatch.
9. If verification fails, the tool restores from backup.
10. The tool does not synthesize names from prompt text, transcript content,
    cwd, or model summaries.

## Implemented Command Shape

The accepted title-only repair command shape is:

```bash
python3 scripts/keep_codex_fast.py --repair-thread-titles-dry-run --codex-home <codex-home>
python3 scripts/keep_codex_fast.py --repair-thread-titles-apply --confirm-thread-title-repair APPLY_THREAD_TITLE_REPAIR --codex-home <codex-home>
```

The dry-run command is the first safe step. Apply is only for the reviewed,
backup-first repair path. Dry-run and apply output use `needs_human` for
automatic oversized titles that do not have a safe existing
`session_index.jsonl.thread_name`; those entries require operator naming outside
this tool.
