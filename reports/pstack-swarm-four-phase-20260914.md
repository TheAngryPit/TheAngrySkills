# Native Swarm four-phase case

Opened before worker launch on 2026-09-14 for PR #64 head
`ea6099fa5b9c80251cfe82467738e133aee17c35`.

- [x] Frame — done predicate: two disjoint read-only reviewers return
  `PASS`, `ISSUES`, or `BLOCKED` with file/line evidence; coordinator drains
  both and publishes one compact table plus gaps. Shape: coverage partition,
  N=2 total. Worker model: available `gpt-5.6-luna` high via native subagent
  channel. No race selection rule applies. Both workers need the local clone,
  so native local execution is used. Neither worker owns a writable output.
- [x] Fan out — launched both bounded workers together as
  `/root/swarm_work_cloud` and `/root/swarm_setup_pstack` after the checklist
  existed. Slice A: Work cloud
  `cursor-orchestrate` source/manifest/overlay/contract report. Slice B:
  `cursor-setup-pstack` source/router/overlay/inventory report and mirror
  accounting. No edits, network calls or PR actions by workers.
- [x] Aggregate — waited for both terminal handoffs; preserved missing or
  blocked slices, verify findings against the current tree, and apply no
  worker edits.
- [x] Report — one compact result table, evidenced issues and explicit gaps.

This is a native Markdown checklist as the available session has no dedicated
todolist tool. Its prelaunch file creation and the subsequent launch order are
part of the proof. It tests the source's four-phase ordering intent, not
Cursor cloud-agent API parity or automatic skill selection.

## Terminal handoffs and coordinator check

The checklist was first written at `2026-09-14T16:22:40+0100`, before the two
native `collaboration.spawn_agent` calls in the same fan-out step. Both workers
used the advertised `gpt-5.6-luna` high subagent channel and local execution
because they needed the operator's clone. They made no edits. Both returned
terminal, source-linked reports; the coordinator checked their cited paths
and the generated count in the same exact head.

| Slice | Native worker | Verdict | Evidence / finding |
| --- | --- | --- | --- |
| A — Work cloud `orchestrate` | `/root/swarm_work_cloud` | `PASS` | Pinned dispatcher/planner and overlay keep explicit-only Cursor tree behavior source-attributed; the Work report labels create as API-contract-only, existing task list/read as observed, auto-review rejection as no task created, and tree/artifact/cancel/recover unproved (`sources/cursor-plugins/overlays/cursor-orchestrate.json`; `reports/cursor-orchestrate-work-cloud-contract-20260914.md`). |
| B — `setup-pstack` | `/root/swarm_setup_pstack` | `PASS` | Pinned source has 17 labels/four list roles; the current-channel report maps each under the router, distinguishes Spark/task channels, and keeps persistent dispatch held. Generated state remains 91 physical, 58 published, 30 active held plus three dormant (`sources/cursor-plugins/snapshot/pstack/skills/setup-pstack/SKILL.md`; `reports/cursor-setup-pstack-native-inventory-20260914.md`; `reports/cursor-plugin-skills-state.json`). |

Aggregate: **PASS for this read-only, two-slice review**. No worker dropped
out, no issue was raised, and no race selection rule applied. `PASS` is a
review verdict for the assigned slices, not proof that `cursor-orchestrate`
or `cursor-setup-pstack` is functionally available. The previously recorded
Swarm case supplied `ISSUES`/`BLOCKED` worker outcomes and preserved a blocked
aggregate; this case adds a visible prelaunch four-phase checklist, terminal
drain and one consolidated report. Automatic skill invocation, Cursor cloud
workers, cross-host behavior and cancellation are still unobserved. No code,
source, manifest, credentials, PR or external system was changed by workers.

## Publication decision

The local-computer path meets the pinned Swarm ordering and fan-out contract:
visible four-phase plan before launch, N=2 parallel workers with disjoint
standalone briefs, source-format verdicts, terminal drain and one in-chat
aggregate. The earlier case preserves a `BLOCKED` aggregate instead of
inventing full coverage. `cursor-swarm` is therefore published only as a
bounded explicit-only native workflow. The generated instruction keeps Work
cloud as the default only when a real worker route is available and authorized,
and permits local execution when workers need the user's computer. It reports
unavailable cloud capability rather than substituting local work. Race
selection, worker dropout, automatic skill trigger and cloud/cross-host parity
remain unproved.
