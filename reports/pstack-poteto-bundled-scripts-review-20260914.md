# Poteto bundled-script admission review

Date: 2026-09-14. Scope: generated `cursor-poteto-mode/scripts/` in the
held-candidate preview, reviewed without executing scripts or network calls.

The deterministic scanner returned `needs_human_review`: 20 bundled-script
warnings, four executable-file warnings and one dependency-manifest warning.
Those are 25 warning records across 20 physical files. A bounded independent
read-only audit found no code that runs merely when the skill is loaded, no
hardcoded credential extraction, and no direct PR mutation in these files.
This supports explicit-only publication of the guidance, **not** unattended
execution of its bundled tools.

| Surface | Observed trigger and effect | Admission boundary |
| --- | --- | --- |
| `scripts/bootstrap.ts:25-61` | An explicit `orch` or `watch-pr` invocation can run `bun install --frozen-lockfile`, write an install key under `node_modules`, and respawn. Even `--help` can take this path with an empty cache. | Treat bootstrap as a separately authorized dependency/network operation in an isolated environment; never execute it on skill load or for help discovery. The historical lockfile test used `--ignore-scripts` and did not instrument network. |
| `scripts/worktree-audit.sh:18,22-23` and `scripts/watch-pr/github.ts:453-601` | Explicit commands use `git fetch`, authenticated `gh`, and GitHub reads. | Require a declared repository/PR target and permission for authenticated egress. |
| `scripts/orch/store.ts:336-345,368-441,1381-1421,1576-1586` and `scripts/orch/orch.ts:262-268` | Explicit orchestration writes store/locks, drains inbox state, and permits `--force` lock takeover. | Use a disposable store; review any takeover or deletion with the caller's authority. |
| `scripts/watch-pr/policy.ts:363-413` and `scripts/watch-pr/github.ts:32-49` | Watcher defaults to no overall timeout; child `gh` calls lack a timeout. | A finite bounded run and child-process lifecycle proof are required before unattended watching. |
| `scripts/watch-pr/render.ts:67-145` | Pretty output can print raw GitHub-supplied text with terminal control characters. | Prefer JSON output or sanitize control characters before terminal/log display. |

The process calls reviewed in `watch-pr/github.ts:32-49` and
`orch/store.ts:1066-1158` use argument arrays rather than string shell
interpolation. `check-plan.mjs:31-37` reads a caller-selected plan and emits
diagnostics. Three current generated files (`watch-pr/policy.ts`, `render.ts`,
`types.ts`) differ from an earlier closure hash ledger; any integrity claim
must bind the current source-plus-overlay render and regenerate hashes.

The pinned Poteto text permits some external actions without asking, but
operator instructions and native host permissions remain authoritative. The
generated mirror is `allow_implicit_invocation: false`; no bundled script was
run in this audit. Full playbook execution, credentialed GitHub behavior,
bootstrap safety, watcher termination, and fresh top-level activation remain
unproven and are separate from admission of explicit guidance.
