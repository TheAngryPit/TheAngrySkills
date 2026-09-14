# Pstack nine-skill closure

**Later scope decision (2026-09-14):** Vítor excluded `cursor-make-bot-ui`
from the Codex mirror. The eight bounded publications below remain; the
Bot UI row is historical evidence only. See
[`cursor-make-bot-ui-exclusion-20260914.md`](cursor-make-bot-ui-exclusion-20260914.md).

Date: 2026-09-14. Base: `eff47293`. Worker branch:
`codex/cursor-full-closure-worker-20260914`.

This report separates bounded native closure from full Cursor parity. It uses
the existing receipts first. No fixture or browser pass was repeated unless a
new adapter needed a deterministic check. No global installation, webhook,
Tailscale action, credential, product mutation, PR, push, or merge was done.

| Skill | Decision | Evidence | Remaining boundary |
| --- | --- | --- | --- |
| `cursor-automate-me` | Promoted bounded explicit-only | Isolated project-local fixture corroborates explicit preferences across two evidence slices, preserves existing content, requires draft approval, reads back the result, rejects symlink/control paths, and leaves the original unchanged when history/unslop/approval is missing. | Native task-history selection, native skill-creator telemetry, full preference loop and global writeback remain unproven. |
| `cursor-create-verification-skill` | Promoted bounded explicit-only | The CLI receipt proves generation, syntax/version/health Doctor, every mapped feature, stdout/stderr/exit evidence, cleanup and second-run drift reconciliation. The separate UI receipt proves a disposable browser target through create, search, empty, clear and reload. | Production target parity, reusable host activation, filesystem/network isolation, and action-time `Reset fixture` cleanup remain unproven. |
| `cursor-figure-it-out` | Promoted bounded explicit-only | The renderer/decision-trail guard is verified, and the isolated notes case supplies adjacent bounded hypothesis-loop evidence with baseline/failure/trace, structural diff, reproduction-before-fix commit, local remote simulation and after-state. This is guidance proof, not a native `figure-it-out` run. | The overlay has only a partial post-change audit: no prospective trigger, full Phase A-E run, independently generated correction, production target or independent review. |
| `cursor-maintain-verification-skill` | Promoted bounded explicit-only | The CLI receipt proves Doctor, source-wave input handling, every feature re-drive, controlled drift repair, persisted before/after evidence, cleanup and clean second run. The separate UI receipt adds two native read-only source readers and clean browser re-drives. | Production target parity, reusable host activation, action-time reset cleanup, and a changed-outcome PR remain unproven. |
| `cursor-make-bot-ui` | Held security quarantine | New local adapter proves server-only key redaction, JSON POST shape, both required headers, one-attempt timeout/non-200 handling, malformed input rejection and local-only endpoint gating. | The real webhook routine, sender-key retrieval, wake turn, Tailnet exposure, network and privileged installer remain unexecuted. The source quarantine is retained. |
| `cursor-no-comments` | Promoted bounded explicit-only | The rendered skill selected native `agent_type: "comment-sicko"`; the named reviewer removed one redundant comment, preserved SPDX, changed no application code, and coordinator syntax/runtime readback passed. Public TOML and pinned source hashes match. | Complex findings, rejected-report rerun, optional encoding, fresh top-level loading, automatic selection and effective model/effort readback remain unproven. |
| `cursor-poteto-mode` | Promoted bounded explicit-only; script execution gated | All 23 playbooks render, the isolated bug-fix/process and scratch checks pass, named `poteto-agent` selection/follow-up was observed, and the independent read-only script audit found no load-time execution or hardcoded credential extraction. | Dependency install, authenticated GitHub reads, store/lock writes, unbounded watchers, cloud lane, sticky mode, fresh profile load, full playbook execution and real PR mutation remain separately gated. |
| `cursor-recall` | Promoted bounded explicit-only | Isolated fixture reconciles exact workspace/topic history selection (excluding current task), live repository state and matching shared record without writes; missing/mismatched exports are partial. | Native task-history selection and full `cursor-why` shared-record sweep remain unproven. |
| `cursor-setup-pstack` | Promoted bounded explicit-only | Fixture covers all 17 roles, four panel lists, aliases, malformed input and no-write behavior; current-channel native model/effort inventory is recorded. Generated `agents/openai.yaml` enforces explicit invocation. | Persistent source/config write/readback, user-owned-task entitlement, parent alias resolution and actual role dispatch remain unproven. |

## Files changed

- The three bounded promotions update manifest availability and overlay
  promotion states without claiming automatic invocation.
- `scripts/cursor_bot_ui_adapters.py` and its tests provide the safe local
  `make-bot-ui` slice. The manifest records its hash and the overlay bundles it
  only for reviewed candidate rendering.
- The catalog README and closure metadata now report 71 published mirrors and
  17 active held skills. `cursor-make-bot-ui` remains security-quarantined;
  `cursor-poteto-mode` is explicit-only with bundled script execution gated.
- `run_automate_me_fixture` and `run_recall_fixture` plus their tests provide
  named isolated receipts; no native history or global writeback is claimed.

## Validation

The Bot UI adapter suite passed seven tests. The remaining bounded pstack
fixture/functional/core suites passed 31 tests, and the focused figure/setup
selection passed 10 tests. The full repository suite passed 254 tests and 2
subtests. The generated catalog check passed with 91 physical sources, 71
published mirrors and 345 output files. All new promotions remain explicit-only; none imply global
installation, automatic skill selection, or external webhook execution.
