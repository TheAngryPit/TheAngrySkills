### Worktree and simulator cleanup

1. Audit with `df -h /`, native worktree state and `scripts/worktree-audit.sh [-b <pr-base-ref>] [repo-path]`. The buckets are advice, not permission. Check current project-owned usage and the operator's pinned/active tasks; never mine unrelated transcripts.
2. Verify each candidate's exact path, ownership, commits, uncommitted and untracked work, and active consumers. A clean worktree can still be in use. Show work that would be lost and obtain the operator's decision where the existing grant does not cover it.
3. Remove only the confirmed authorized targets through Trash, preserving recoverable files and Git history. If Trash is unavailable, stop that removal. Do not use force removal or recursive permanent deletion as a fallback. Reconcile worktree metadata through the supported Git operation after the files are safely moved.
4. Simulator, runtime, Xcode and package-cache removals require their exact targets and an authorization covering their effects. Shared or user-owned state is not disposable merely because the audit calls it a cache. Keep active consumers and explicit exclusions.
5. Re-list worktrees and compare disk space. Report each removed target and why each retained target remains.

**Reply:** before/after space, confirmed removals and the owner or unfinished work behind each retained target.
