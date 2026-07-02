---
name: "hive-keep-codex-fast"
description: "Use when Codex Desktop or Codex CLI feels slow, local Codex sessions/logs/worktrees/config look bloated, or the operator asks for safe Codex local-state maintenance."
metadata:
  short-description: "Safe Codex local-state maintenance"
---

# Hive Keep Codex Fast

Operator-owned fork of `keep-codex-fast`.

Default stance: inspect first, preserve continuity, never delete permanently.

## Start Here

Resolve this skill directory, then run the script from it.

Read-only report:

```bash
python3 scripts/keep_codex_fast.py
```

Report with raw diagnostics only when the operator asks:

```bash
python3 scripts/keep_codex_fast.py --details
```

Fixture/sandbox path:

```bash
python3 scripts/keep_codex_fast.py --codex-home <fixture-or-explicit-codex-home>
```

## Modes

- Runbook: prints a safe off-Codex command sequence, no writes.
- Report: default, privacy-safe, no writes.
- Backup-only: creates backups, does not archive/move/repair.
- Apply: backup-first, archive-only, blocked while Codex holds the state database unless explicitly waiting.
- Metadata repair only: the legacy combined repair path. Backup-first, no archive/prune/move/rotate. Do not reuse it for title-only repair; that follows the stricter contract in `references/thread-title-repair-spec.md`.
- Title repair dry-run: `--repair-thread-titles-dry-run` classifies thread titles only, writes no files, and is separate from legacy metadata repair.
- Title repair apply: after dry-run review, `--repair-thread-titles-apply --confirm-thread-title-repair APPLY_THREAD_TITLE_REPAIR` repairs only eligible `threads.title` values from safe existing `session_index.jsonl.thread_name` values. It does not rewrite `preview`, `first_user_message`, transcripts, or `session_index.jsonl`.
- Legacy combined repair: `--apply --repair-thread-metadata-bloat` also runs normal apply and may compact `first_user_message` for compatibility.

Before any non-report mode, read `references/operation-policy.md`.

## Report Should Summarize

- active and archived session size
- largest active sessions
- thread title/preview metadata bloat
- stale worktree candidates
- local log size
- bad path/config drift candidates
- top Node/dev/Codex-related processes

Default output must not reveal raw thread IDs, chat titles, private paths, or
process args. Use `--details` only for deliberate diagnosis.

## Hard Rules

- Do not run `--apply` until the operator explicitly approves that exact run.
- Do not archive active repo chats until continuity is preserved or waived.
- Do not treat metadata repair as normal maintenance.
- Do not use legacy metadata repair for title-only repair. Follow `references/thread-title-repair-spec.md`; legacy first-message compaction requires an explicit operator request and stays on the compatibility path.
- For title-only repair, run `--repair-thread-titles-dry-run` first and inspect `thread_title_dry_run_needs_human` before any apply.
- Do not create recurring mutating automation.
- Do not modify memories, skills, plugins, automations, credentials, or API keys.

## Operational Guardrails

After report, summarize findings and explicitly say no mutations were made.

Before apply, read `references/operation-policy.md`, ask the operator to close
Codex or approve bounded waiting, and confirm handoff status for important active
repo chats.

If the operator is currently using Codex, generate a runbook instead of trying
to run mutating maintenance inside Codex:

```bash
python3 scripts/keep_codex_fast.py --runbook --codex-home <codex-home>
```

After apply, run report again and explain backup/archive/restore locations
without exposing private backup contents.

## References

- `references/operation-policy.md`: modes, safety gates, apply/backup rules.
- `references/thread-metadata-bloat.md`: metadata bloat diagnosis and legacy repair context.
- `references/thread-title-repair-spec.md`: accepted dry-run/apply contract for preserving manual thread titles.
- `references/thread-title-repair-prd.md`: PRD for the title repair feature before implementation/issues.
- `references/handoff-template.md`: handoff content before archiving important chats.
- `references/evaluation-scenarios.md`: pressure tests before install/deploy.
- `references/upstream-license.txt`: copied upstream license text.
