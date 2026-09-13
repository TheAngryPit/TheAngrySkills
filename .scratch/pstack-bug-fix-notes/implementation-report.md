# pstack bug-fix fixture and critical-script review

Date: 2026-09-13

Status: fixture-only proof. No bundled pstack Bun/TypeScript script was
installed or executed. No live target application, cloud task, GitHub query,
worktree operation, or external write was used.

## Contextual `bug-fix` proof

The rendered playbook was read from
`sources/cursor-plugins/snapshot/pstack/skills/poteto-mode/playbooks/bug-fix.md`
through the staged `cursor-poteto-mode` tree. Its entries were treated as
structural context; the read result was `READ`, never `APPLIED`.

The test-owned notes app is a temporary Python fixture with a JSON file in its
temporary project directory. The correction is explicitly prewritten by the
fixture caller; this proof does not show that the playbook or an agent
diagnosed or generated the correction.

The contextual steps were executed in order:

1. Before: create `Release checklist` and capture `created:Release checklist`
   with exit code 0.
2. Before: search for the exact-case `Release` and capture
   `found:Release checklist` with exit code 0.
3. Failure: search for lower-case `release` and capture `not-found` with exit
   code 1 and empty stderr.
4. Correction: replace the fixture source with the prewritten correction and
   record distinct before/after SHA-256 values.
5. After: repeat lower-case `release` and capture
   `found:Release checklist` with exit code 0.

The adapter refuses to write the correction unless the failure evidence is
exactly exit code 1, stdout `not-found\n`, and empty stderr. A negative test
uses exit code 2 and confirms the correction is not written. The overall result
is `FIXTURE_ONLY`; the evidence scope is only `exit_code`, `stdout`, and
`stderr`. Filesystem and network isolation are `not_observed`.

This is explicitly partial playbook proof. Exercised source steps are `(1, 4)`:
the synthetic reproduction and repeat verification on the same fixture
surface. Unexercised source steps are `(2, 3, 5, 6)`: binary-search with
`how`/`why` and mechanism confirmation, architect/delegation/review, failing
repro before fix in commit history, and Opening a PR. No additional PR was
opened by this lot.

## Critical pstack script review

Review method: read-only `sed` and `rg` over the files below. This is a static
review, not an execution or sandbox proof.

| Path | Writes / installation | Subprocess, `gh`/`git`, or network surface | Safe execution prerequisites and limits |
| --- | --- | --- | --- |
| `scripts/bootstrap.ts` | Reads `package.json` and `bun.lock`; runs Bun install when the install key is missing; writes `node_modules/.poteto-mode-tools-install-key`; restarts the command. | `Bun.spawnSync([process.execPath, "install", "--frozen-lockfile"])`; restart inherits `process.env` and stdio. Bun install may use registry/cache and network. | Bun, a valid lockfile, writable `node_modules`, dependency-resolution policy, and an explicit network decision. No install or restart was run. |
| `scripts/package.json` | Declares the `test` and `typecheck` commands; dependencies are installed by bootstrap. `bun-types` and `typescript` are declared as `latest`. | Indirectly activates Bun test/typecheck and the bootstrap install path. | Bun and dependency policy are required; lockfile resolves the checked snapshot, but the manifest's `latest` ranges remain an input to future changes. |
| `scripts/bun.lock` | Lock metadata only; no direct write or network operation. | Pins `commander@14.0.0`, `bun-types@1.3.14`, `typescript@7.0.2` plus platform TypeScript packages. | Bun lockfile compatibility and integrity verification; no install was run. |
| `scripts/worktree-audit.sh` | Creates a temporary PR JSON file and removes it at the end; does not delete worktrees. Reads transcript paths under `$HOME/.cursor/projects/...`. | Runs `git rev-parse`, `git worktree`, `git fetch origin main`, `git -C`, `gh pr list`, and shell utilities. `git fetch` and `gh` can egress; `gh` can consume authentication. | A deliberate repo path, `git`, `origin/main`, authenticated `gh` if PR state is desired, `jq`, and transcript-access policy. Do not run until network, home-directory reads, and cleanup are approved. |
| `scripts/check-plan.mjs` | Read-only `readFileSync` of the plan argument. | No subprocess, install, `gh`, or network surface found. | Node and a bounded plan path; safe static candidate, but no execution was needed here. |
| `scripts/orch/orch.ts` | Calls bootstrap first; commands delegate to the store. | `store.ts` uses atomic writes, `.orch.lock`, `mkdir`, `rename`, `unlink`, and optional `--force` lock takeover; frontier paths use `gt` and `git rev-parse` with inherited environment. | Bun, installed `commander`, explicit store directory, lock ownership, and separate `gt`/`git` policy. Store mutation and subprocess behavior were not run. |
| `scripts/orch/store.ts` | Writes store TSV/Markdown state, lock files, inbox files, temporary files, and can remove stale/drained entries. | `execFileSync("gt", ...)` for frontier metadata and `execFileSync("git", ["rev-parse", ...])`; subprocess environments include `process.env`. | Explicit store scope, lock/force policy, `gt`/`git` availability, and inherited-secret review. Not executed. |
| `scripts/watch-pr/watch-pr` | Calls bootstrap before loading the CLI; no direct domain write in the entrypoint. | Bun bootstrap/restart is the indirect process and install surface. | Same Bun/install prerequisites as bootstrap plus an explicit external-query decision. Not executed. |
| `scripts/watch-pr/cli.ts` | Polling/control flow only in this entrypoint; it invokes the real GitHub reader. | Uses `GhGitHubReader`, polling timers, and the `gh`/`git` subprocesses implemented in `github.ts`; normal polling can continue until timeout or error budget. | Bun, `commander`, `gh` authentication, repository/PR context, and a bounded polling policy. Not executed. |
| `scripts/watch-pr/github.ts` | No direct file write found. | Spawns `git remote get-url origin`, `gh pr view`, `gh pr list`, `gh pr checks`, and `gh api graphql`; stdout/stderr are piped, but the generic spawn wrapper has no explicit per-process timeout. GitHub network and auth are prerequisites. | Explicit repo/PR scope, authenticated `gh`, network approval, and an outer timeout/cancellation policy. Not executed. |
| `scripts/watch-pr/render.ts` | Rendering only; no write found. | Emits GitHub PR URLs such as `https://github.com/<owner>/<repo>/pull/<number>`; does not fetch them itself. | Treat rendered URLs as external links; no execution was performed. |

Finding disposition: the static review makes the current hold more precise but
does not reduce it. Keep the bundled scripts disabled and do not install their
dependencies until controlled execution, inherited-environment/credential
review, network/egress policy, and any required worktree/store permissions are
separately authorized and proven.
