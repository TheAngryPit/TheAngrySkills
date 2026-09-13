# pstack bug-fix fixture and critical-script review

Date: 2026-09-13

Status: fixture-only proof. No bundled pstack dependency installation,
bootstrap, CLI entrypoint, live target application, cloud task, real GitHub
query, real worktree operation, or external write was used. Bun `1.4.2` did
execute selected dependency-free TypeScript modules from scratch copies with
mocked subprocesses.

## Contextual `bug-fix` proof

The rendered playbook was read from
`sources/cursor-plugins/snapshot/pstack/skills/poteto-mode/playbooks/bug-fix.md`
through the staged `cursor-poteto-mode` tree. Its entries were treated as
structural context; the read result was `READ`, never `APPLIED`.

The test-owned notes app is a temporary Python fixture with a JSON file in its
temporary project directory. The correction is explicitly prewritten by the
fixture caller; this proof does not show that the playbook or an agent
diagnosed or generated the correction.

The fixture actions were executed in order (these are not a claim that the
source's six steps map one-to-one to these actions):

- Before: create `Release checklist` and capture `created:Release checklist`
  with exit code 0, then search exact-case `Release` and capture
  `found:Release checklist` with exit code 0.
- Reproduce: search lower-case `release` and capture `not-found` with exit
  code 1 and empty stderr.
- Diagnose: run `trace-search release` and capture
  `comparison=case-sensitive;matched=false` for the stored title.
- Plan: retain candidate hypotheses, select the case-sensitive predicate, and
  record a structural-only unified diff. The correction source is explicitly
  supplied by the fixture caller; it is not generated here.
- History: initialize Git only in a root containing the explicit
  `.pstack-disposable-fixture` marker, commit the buggy source first, then
  write and commit the prewritten correction. The two subjects are recorded
  newest-first as `fix(pstack): normalize notes search` and
  `test(pstack): reproduce notes search failure`.
- PR flow: push only to a temporary local bare remote and verify its head; the
  result is `SIMULATED_ONLY`, with `real_pr: false` and no external
  publication.
- After: repeat lower-case `release` and capture
  `found:Release checklist` with exit code 0.

The adapter refuses to write the correction unless the failure evidence is
exactly exit code 1, stdout `not-found\n`, and empty stderr. A negative test
uses exit code 2 and confirms the correction is not written. The overall result
is `FIXTURE_ONLY`; the evidence scope is only `exit_code`, `stdout`, and
`stderr`. The local Git helper also rejects an unmarked root, unexpected root
entries, an existing `.git`, and a timeout. Filesystem and network isolation
are `not_observed`.

This is explicitly partial playbook proof. On the source `bug-fix` steps,
fixture-local portions exercised are `(1, 4, 5)`: reproduction, repeat verification, and
local commit ordering. Partial are `(2, 3, 6)`: the fixture has a bounded
hypothesis cut from baseline/failure/trace, a structural-only plan/diff record
with no independent architect/delegation/review, and a local bare-remote PR
simulation only. The source's two binary-search/how/why mechanism loop,
architect/delegation/review, and real Opening a PR flow are not fully proven;
the remaining source obligations are not claimed complete: each step is
accounted for only within the synthetic fixture scope. No real PR was opened by this lot.

The positive fixture does not claim full contextual app parity: it is one
synthetic Python process surface with a JSON file, and filesystem/network
isolation remain `not_observed`.

## Safe bundled-script subset

The critical scripts were first reviewed statically. The following bounded
local checks were then run:

| Script | Fixture and result | Boundary |
| --- | --- | --- |
| `scripts/check-plan.mjs` | Node ran against a temporary valid plan: exit 0 and `1 PR sections, 0 problems`; a temporary invalid plan: exit 1 with missing-section diagnostics. | Read-only plan parsing; no subprocess, install, `gh`, or network surface. |
| `scripts/worktree-audit.sh` | Bash ran against temporary repo/child directories with disposable `HOME` and transcript path, using mocked `git`, `gh`, `jq`, and `rg`; exit 0 and the expected audit header, child path, and `no-remote` classification. | The mock prevented real GitHub/git activity; no real home or repository was read and no deletion was performed. |
| `orch/store.ts` | Bun `1.4.2` ran five selected store tests from a scratch copy: init/idempotence, unit CRUD/counts, ledger record/check/summary, inbox push/peek/drain, and gates/standing/status; `5 pass`, `0 fail`, no `node_modules`. | Dependency-free module path only; the `orch.ts` CLI and its bootstrap were not loaded or run. |
| `watch-pr/github.ts` | Bun `1.4.2` ran the real `GhGitHubReader` from a scratch copy with mocked `git` and `gh`; origin, PR facts, open PRs, checks, rollup, threads, and commit status were parsed. A slow mocked `gh` was bounded by an external 1-second timeout and returned `-9` on this host. | This proves parser/command wiring with mocks and an outer timeout, not GitHub access, credentials, real CLI/bootstrap, or an intrinsic child-process timeout. |

The `orch` and `watch-pr` CLI entrypoints were not executed. Bun is available, but
`scripts/node_modules` is absent and their entrypoints call `bootstrap.ts`,
which can install dependencies and restart with inherited environment/stdio.
The offline install probe in a scratch copy failed exactly because the lock
pins were absent from cache: `bun-types`, `typescript`, `commander`,
`@types/node`, and `undici-types`. No installation, network egress, credential
use, or uncontrolled dependency activation was authorized. This is a
dependency-free module and safe-subset check, not CLI/bootstrap or real
GitHub bundled-script parity.

## Critical pstack script review

Review method: read-only `sed` and `rg` over the files below. This is a static
review, not an execution or sandbox proof.

| Path | Writes / installation | Subprocess, `gh`/`git`, or network surface | Safe execution prerequisites and limits |
| --- | --- | --- | --- |
| `scripts/bootstrap.ts` | Reads `package.json` and `bun.lock`; runs Bun install when the install key is missing; writes `node_modules/.poteto-mode-tools-install-key`; restarts the command. | `Bun.spawnSync([process.execPath, "install", "--frozen-lockfile"])`; restart inherits `process.env` and stdio. Bun install may use registry/cache and network. | Bun, a valid lockfile, writable `node_modules`, dependency-resolution policy, and an explicit network decision. No install or restart was run. |
| `scripts/package.json` | Declares the `test` and `typecheck` commands; dependencies are installed by bootstrap. `bun-types` and `typescript` are declared as `latest`. | Indirectly activates Bun test/typecheck and the bootstrap install path. | Bun and dependency policy are required; lockfile resolves the checked snapshot, but the manifest's `latest` ranges remain an input to future changes. |
| `scripts/bun.lock` | Lock metadata only; no direct write or network operation. | Pins `commander@14.0.0`, `bun-types@1.3.14`, `typescript@7.0.2` plus platform TypeScript packages. | Bun lockfile compatibility and integrity verification; no install was run. |
| `scripts/worktree-audit.sh` | Creates a temporary PR JSON file and removes it at the end; does not delete worktrees. Reads transcript paths under `$HOME/.cursor/projects/...`. | Runs `git rev-parse`, `git worktree`, `git fetch origin main`, `git -C`, `gh pr list`, and shell utilities. `git fetch` and `gh` can egress; `gh` can consume authentication. | Executed only against temporary repo/child directories with disposable `HOME`/transcripts and mocked `git`, `gh`, `jq`, and `rg`; no real home, repo, remote, or auth was used. |
| `scripts/check-plan.mjs` | Read-only `readFileSync` of the plan argument. | No subprocess, install, `gh`, or network surface found. | Node ran against a temporary valid and invalid plan only; no write or external access was used. |
| `scripts/orch/orch.ts` | Calls bootstrap first; commands delegate to the store. | `store.ts` uses atomic writes, `.orch.lock`, `mkdir`, `rename`, `unlink`, and optional `--force` lock takeover; frontier paths use `gt` and `git rev-parse` with inherited environment. | Bun, installed `commander`, explicit store directory, lock ownership, and separate `gt`/`git` policy. Store mutation and subprocess behavior were not run. |
| `scripts/orch/store.ts` | Writes store TSV/Markdown state, lock files, inbox files, temporary files, and can remove stale/drained entries. | `execFileSync("gt", ...)` for frontier metadata and `execFileSync("git", ["rev-parse", ...])`; subprocess environments include `process.env`. | Explicit store scope, lock/force policy, `gt`/`git` availability, and inherited-secret review. Not executed. |
| `scripts/watch-pr/watch-pr` | Calls bootstrap before loading the CLI; no direct domain write in the entrypoint. | Bun bootstrap/restart is the indirect process and install surface. | Same Bun/install prerequisites as bootstrap plus an explicit external-query decision. Not executed. |
| `scripts/watch-pr/cli.ts` | Polling/control flow only in this entrypoint; it invokes the real GitHub reader. | Uses `GhGitHubReader`, polling timers, and the `gh`/`git` subprocesses implemented in `github.ts`; normal polling can continue until timeout or error budget. | Bun, `commander`, `gh` authentication, repository/PR context, and a bounded polling policy. Not executed. |
| `scripts/watch-pr/github.ts` | No direct file write found. | Spawns `git remote get-url origin`, `gh pr view`, `gh pr list`, `gh pr checks`, and `gh api graphql`; stdout/stderr are piped, but the generic spawn wrapper has no explicit per-process timeout. GitHub network and auth are prerequisites. | Explicit repo/PR scope, authenticated `gh`, network approval, and an outer timeout/cancellation policy. Not executed. |
| `scripts/watch-pr/render.ts` | Rendering only; no write found. | Emits GitHub PR URLs such as `https://github.com/<owner>/<repo>/pull/<number>`; does not fetch them itself. | Treat rendered URLs as external links; no execution was performed. |

Finding disposition: the safe subset confirms the read-only behavior of
`check-plan.mjs`, exercises only the control flow of `worktree-audit.sh` behind
mocks, and proves selected dependency-free `orch/store.ts` and
`watch-pr/github.ts` paths with mocks. It does not reduce the current hold.
Keep the bundled CLI scripts
disabled and do not install their dependencies until controlled execution,
inherited-environment/credential review, network/egress policy, and any
required worktree/store permissions are separately authorized and proven.
