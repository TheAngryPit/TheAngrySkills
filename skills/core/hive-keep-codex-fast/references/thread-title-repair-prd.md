# PRD: Codex Thread Title Repair

Date: 2026-06-20
Status: Draft for operator review

## Problem Statement

The user relies on Codex Desktop across many long-running threads and projects.
Thread titles are part of the operator's working memory: they are how the user
finds active work, distinguishes similar projects, and preserves manual
organization across restarts.

Recent Codex state has shown a repeated failure mode: automatic thread metadata
can copy long prompt text into the visible thread title. Repair attempts have
also damaged manual names by treating every title-like field as interchangeable.
That makes the problem worse: the operator loses the carefully renamed titles
and the sidebar fills with unreadable prompt-sized names.

The user needs a title repair workflow that is conservative by design. It must
detect automatic title bloat, preserve manual titles, support backup and restore,
and verify after every mutation. It must not treat title cleanup as general
Codex cleanup, and it must not touch unrelated metadata such as `preview` in
this slice.

## Solution

Build a dedicated Codex thread title repair workflow as an opt-in extension of
the local Codex maintenance tooling.

The workflow has two modes:

- `--repair-thread-titles-dry-run`: read-only classification and proposed
  actions.
- `--repair-thread-titles-apply`: explicit, backup-first repair of only
  eligible automatic titles.

The repair contract is intentionally narrow:

- Manual titles are preserved.
- Automatic oversized titles may be repaired only when a safe short existing
  name is already available for that same thread.
- Threads without a safe existing short name are reported as `needs_human` for
  human naming.
- Subagent/system-owned threads are excluded from automatic repair.
- Archived real threads may be inspected and repaired under the same rules as
  active real threads.
- `preview`, transcripts, `first_user_message`, and `session_index.jsonl` are
  not rewritten by this feature.

This feature is not a general metadata compactor. It is a title integrity tool:
classify, preserve, repair only what can be repaired safely, and prove the
result after writing.

Operator command shape:

```bash
python3 scripts/keep_codex_fast.py --repair-thread-titles-dry-run --codex-home <codex-home>
python3 scripts/keep_codex_fast.py --repair-thread-titles-apply --confirm-thread-title-repair APPLY_THREAD_TITLE_REPAIR --codex-home <codex-home>
```

The operator should run and review dry-run output before apply. In that output,
`needs_human` means the tool found an automatic oversized title but no safe
existing `session_index.jsonl.thread_name` for that thread, so the operator must
choose a manual name outside this tool.

## User Stories

1. As a heavy Codex user, I want oversized automatic thread titles identified, so that my thread list stays readable.
2. As a heavy Codex user, I want my manually renamed thread titles preserved, so that I do not lose my project organization.
3. As a heavy Codex user, I want a dry-run before any repair, so that I can see what would change before it changes.
4. As a cautious operator, I want title repair separated from normal cleanup, so that archive or log maintenance cannot silently rewrite names.
5. As a cautious operator, I want title repair separated from `preview` repair, so that we do not mix different metadata surfaces in one risky operation.
6. As a cautious operator, I want `first_user_message` preserved, so that title repair does not rewrite conversation display metadata beyond its scope.
7. As a cautious operator, I want `session_index.jsonl` preserved, so that a possible source of manual names is not damaged during repair.
8. As a cautious operator, I want a backup before any mutation, so that bad repairs can be reversed.
9. As a cautious operator, I want a repair manifest, so that I can audit exactly which titles changed and why.
10. As a cautious operator, I want a restore helper, so that rollback is not manual archaeology.
11. As a cautious operator, I want post-fix verification, so that the tool proves the title it wrote is actually stored.
12. As a cautious operator, I want failed verification to restore affected titles, so that a partial bad repair does not persist.
13. As a cautious operator, I want the tool to fail closed on uncertainty, so that unknown states do not get guessed into destructive behavior.
14. As a cautious operator, I want Codex-running detection or a bounded wait gate, so that the tool does not write while the app is actively writing state.
15. As a cautious operator, I want explicit confirmation for apply mode, so that copied commands cannot mutate state accidentally.
16. As a cautious operator, I want dry-run to write no files, so that it is safe to run while investigating.
17. As a cautious operator, I want apply to write only its backup, manifest, restore helper, and approved title updates, so that the mutation surface is small.
18. As a cautious operator, I want a count of manual titles preserved, so that preservation is visible instead of assumed.
19. As a cautious operator, I want a `needs_human` count for candidates needing human input, so that I can rename the remaining bad titles deliberately.
20. As a cautious operator, I want subagent/system threads excluded, so that repair does not waste attention on internal or derived runs.
21. As a cautious operator, I want archived real threads handled consistently, so that old useful work can be made searchable without special manual rules.
22. As a cautious operator, I want the tool to distinguish active real threads, archived real threads, and excluded system threads, so that the report matches how I think about the sidebar.
23. As a cautious operator, I want every skipped candidate to include a reason, so that I know whether it needs a manual name, is protected, or is excluded.
24. As a cautious operator, I want default output to avoid leaking raw private titles or prompt text, so that routine reports can be pasted safely.
25. As a diagnostic user, I want an explicit details mode, so that I can inspect raw thread IDs and names when I intentionally need them.
26. As a developer, I want classification tested through a synthetic Codex home, so that tests do not depend on private real state.
27. As a developer, I want dry-run zero-write behavior mechanically tested, so that safety is not just a claim.
28. As a developer, I want apply blocked without confirmation, so that mutation paths cannot be triggered accidentally in tests or scripts.
29. As a developer, I want backup-before-write mechanically tested, so that no title mutation can bypass rollback material.
30. As a developer, I want post-write re-read verification tested, so that a write cannot be reported as successful without proof.
31. As a developer, I want restore-on-mismatch tested, so that failure behavior is as important as the happy path.
32. As a developer, I want manual-title preservation tested, so that the user's main failure mode is guarded forever.
33. As a developer, I want `preview` immutability tested, so that this slice cannot expand silently.
34. As a developer, I want `first_user_message` immutability tested, so that title repair does not corrupt conversation metadata.
35. As a developer, I want `session_index.jsonl` immutability tested, so that the existing name cache remains a source, not a target.
36. As a developer, I want classification rules represented explicitly, so that future agents do not collapse manual and automatic titles again.
37. As a future maintainer, I want generated-name synthesis deferred, so that the first repair version does not depend on model summaries or guessed context.
38. As a future maintainer, I want the feature to live behind a narrow command surface, so that general maintenance and title repair remain separate decisions.
39. As a future maintainer, I want this PRD to name non-goals clearly, so that later work on `preview` repair starts from a separate review.
40. As the operator, I want the remaining `needs_human` titles surfaced in a clean list, so that I can decide names manually without hunting through the sidebar.

## Implementation Decisions

- Implement title repair as a separate opt-in workflow from normal Codex maintenance.
- Keep `--repair-thread-titles-dry-run` as the first title-repair step and make
  it strictly read-only.
- Require explicit confirmation for `apply`.
- Require backup creation before any title mutation.
- Treat a title as manual when it differs from the first user message; preserve it by default even if it is long.
- Treat a title as an automatic repair candidate only when it equals the first user message and exceeds the configured title length.
- Use only an existing safe short thread name for replacement. The replacement source must already belong to the same thread.
- Do not synthesize replacement names from prompt text, transcript content, working directory, model summaries, or inferred context in this PRD.
- Report candidates without a safe short name as `needs_human` instead of
  guessing.
- Exclude subagent or system-owned threads from automatic repair.
- Include archived real threads in classification and repair under the same rules as active real threads.
- Leave `preview` untouched. It may be analyzed later, but it is not repaired in this PRD.
- Leave the first user message untouched.
- Leave the session index untouched; it is a read source for safe names, not a write target.
- Preserve rollout transcripts and chat history. This is display-title repair, not history deletion.
- Use a private repair manifest to record original title, chosen replacement, replacement source, and verification result.
- Generate a restore helper for every apply run.
- Re-read affected state after apply and compare it against the intended repaired title and preserved metadata.
- If verification fails, restore affected titles from backup before exiting.
- Keep the CLI implementation standard-library only unless a later implementation plan proves a dependency is worth adding.
- Keep the skill wrapper small; deterministic behavior belongs in scripts, while policy belongs in references.

## Testing Decisions

- The highest testing seam is the command-line workflow against a synthetic Codex home fixture.
- Tests should exercise the public command behavior and stable report/apply outcomes, not private helper internals.
- The fixture should include real SQLite state and a session index representation so classification and repair use realistic persistence behavior.
- Dry-run tests must snapshot the fixture tree before and after the command and assert no writes.
- Classification tests must cover manual titles, automatic oversized titles, safe-name candidates, `needs_human` candidates, archived real threads, and excluded subagent/system threads.
- Apply tests must prove that confirmation is required before mutation.
- Apply tests must prove backup material exists before any title update is made.
- Apply tests must prove only eligible automatic titles are changed.
- Apply tests must prove manual titles remain unchanged.
- Apply tests must prove `preview`, the first user message, transcripts, and the session index remain unchanged.
- Verification tests must re-read the repaired rows and assert the stored title matches the chosen replacement.
- Failure-path tests must simulate a post-write mismatch and assert restore occurs before the command exits.
- Privacy tests must prove default output does not expose raw private titles, prompts, or thread IDs.
- Details-mode tests must prove raw diagnostics appear only when explicitly requested.
- Process-safety tests should assert apply refuses or waits when Codex appears to be actively writing state.
- The existing maintenance CLI fixture tests are useful prior art because they already prove report-mode safety, privacy gating, and synthetic Codex-home inspection.

## Out of Scope

- Repairing or compacting `preview`.
- Rewriting transcripts or rollout JSONL files.
- Rewriting first user messages.
- Rewriting or appending to the session index.
- Generating new thread names from prompt content, cwd, transcript summaries, or model summaries.
- Archiving sessions.
- Moving or deleting worktrees.
- Rotating logs.
- Pruning config.
- Installing, uninstalling, enabling, disabling, or updating skills, plugins, MCP servers, model providers, credentials, or automations.
- Creating a recurring mutating automation.
- Running against real Codex state before the fixture-backed behavior and backup/restore path are proven.
- Publishing or deploying this workflow to other machines before the local operator approves the behavior.

## Further Notes

- This PRD intentionally narrows the earlier metadata repair idea. The user explicitly wants to stop losing manual titles before attempting broader metadata cleanup.
- `preview` is acknowledged as a separate persisted surface, but it should not be touched in this slice because its UI role and performance impact need a separate decision.
- The product direction follows the existing Hive Codex Maintenance posture: inspect first, mutate only after explicit approval, backup before mutation, and prove the exact claim being made.
- The implemented command surface is the flag-based workflow above: dry-run
  first, then backup-first apply only with the explicit confirmation phrase.
