# Operation Policy

This fork keeps the original useful workflow but makes the skill front-door
smaller. The script still owns the deterministic behavior.

## Modes

Runbook mode prints an off-Codex command sequence and exits. It must not inspect
or mutate Codex state beyond resolving the explicit Codex home.

Report mode is the default. It must not write files, create backups, move
folders, rotate logs, edit config, repair metadata, or alter Codex state.

Backup-only creates backups of relevant metadata but must not archive/move
sessions or worktrees, rotate logs, prune config, or repair metadata.

Apply mode is allowed only after explicit operator approval for that exact run.
It is backup-first and archive-only. It should move old candidates into archive
folders and write manifests/restore helpers instead of deleting.

Legacy metadata repair is not part of normal apply. It requires explicit
opt-in with `--repair-thread-metadata-only`.

Legacy combined repair still exists for compatibility:
`--apply --repair-thread-metadata-bloat`. That mode also runs normal apply
operations and may compact `first_user_message`. Prefer
`--repair-thread-metadata-only` when the operator only wants the legacy
metadata repair path; title-only dry-run classification is a separate workflow
via `--repair-thread-titles-dry-run`.

## Safety Gates

- If Codex is actively holding `state_5.sqlite`, default to report-only.
- Use `--wait-for-codex-exit` only when the operator explicitly wants to wait;
  the wait is bounded by `--wait-timeout-seconds` and should not hang forever.
- Use `--details` only when raw paths, thread IDs, titles, or process paths are
needed for diagnosis.
- Never modify or copy credentials unless the operator explicitly asks for that
in a separate scoped task.
- Treat backups as private local artifacts.

## Normal Workflow

1. Run report mode.
2. Summarize sessions, metadata bloat, worktrees, logs, config drift, and heavy
   Node/dev processes.
3. Identify important active repo chats that need handoff before archive.
4. If the operator is currently inside Codex, generate a runbook.
5. If the operator approves apply, ask them to close Codex or approve waiting.
6. Run backup-only first when practical.
7. Run apply with explicit thresholds.
8. Run metadata repair only as a separate decision when needed.
9. Run report again to verify.

## Automation Rule

Recurring automation, if ever requested, must be report/reminder-only. It must
not pass `--apply` or run mutating maintenance automatically.
