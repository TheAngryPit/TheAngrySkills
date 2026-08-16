# gstack Compatibility

## Authority Boundary

When a gstack skill is invoked, gstack owns workflow order, artifacts, STOP
points, human questions, QA, review, ship, canary, and completion status. The
Model Capability Router may choose topology, role, model, and effort for a
bounded step. It must not skip, reorder, auto-answer, or weaken a gstack gate.

Without an invoked gstack workflow, routing remains native and must not require
gstack to be installed. Select the overlay explicitly; never infer it merely
because gstack exists on disk. A normal parallel task may independently invoke
gstack inside itself without becoming part of another task's gstack loop.

Do not duplicate gstack's workflow inside the routing preset. Do not edit
generated gstack skill files to replace runtime-specific tool names. Interpret
`Agent`, `Task`, or similar imported-runtime language as role intent and map it
to a current Codex surface only when the contract is unambiguous.

## Loop Mapping

| gstack phase | Default routing | Invariant |
| --- | --- | --- |
| Shape/spec | `single` or a bounded Sol High `planner` | The master retains operator dialogue and the accepted plan. |
| Plan reviews | independent `direct_subagent` reviewers | Reviewers receive the plan and evidence, not mutation ownership. |
| Implementation | `field_coordinator`, `direct_fleet`, or second-stage `field_fleet` | Workers get disjoint ownership and return proof to the coordinator; `field_fleet` requires a live reconciled Terra task. |
| Code review | fresh Sol High `reviewer` | A worker must not approve its own changes. |
| QA/canary | bounded probes may delegate; verdict stays in master | Browser/runtime evidence and gstack STOP rules remain authoritative. |
| Ship/deploy | master task only | Task creation or compute selection never authorizes release, push, merge, or deploy. |
| Save/restore | gstack artifact and real Git/worktree state | Conversation inheritance is not durable context or proof. |

The common loop is:

1. master shapes the goal;
2. Sol High planner or plan reviewers produce a reviewable plan;
3. master accepts the plan and stops at unresolved human gates;
4. Terra field coordinator and/or Luna Fleet execute separable units;
5. coordinator reconciles results and returns proof;
6. independent Sol High review attacks the closure claim;
7. gstack QA/ship/canary proceed only through their own gates.

## Dual-Voice Reviews

gstack `autoplan` deliberately seeks independent voices and records degraded
states such as Codex-only or subagent-only. A same-family Fleet is throughput,
not model diversity. Never replace a requested Codex-versus-Claude review with
multiple Luna workers and call it equivalent. If the required independent
voice is unavailable, preserve gstack's degraded label and evidence gap.

## Context and Task Relationships

Run interactive gstack decisions in the user-facing master. A native subagent
or delegated user-owned subtask receives only a bounded contract plus the
minimum artifacts needed for that step. It must not decide a human gate for the
master.

Prefer no inherited turns or a small bounded slice for Fleet workers. Use the
plan file, repository state, test output, gstack artifacts, and explicit
closure reports as context. A full conversation clone is neither necessary nor
proof of current state.

The resolver checks required context keys but does not prove their contents.
It labels them `caller_supplied_unverified_references`, returns only
`preflight_ready`, and keeps `proof_state=not_started`. Before execution or a
closure claim, the owning gstack phase must validate the referenced repository,
revision, plan, test evidence, verdict, or target through its native contract.

For a delegated user-owned subtask, record its logical parent and report back to
that parent. For an independent parallel task, report directly to the operator.
Do not reuse one relationship as the other.

## Safety Overlays

If gstack `careful`, `guard`, or `freeze` is active, copy its scope and mutation
constraints into every delegated contract. A child or peer never receives
broader write, host, credential, release, or destructive authority than the
master.

Eight is only the Fleet capacity ceiling. gstack phase order, proof independence,
human gates, and useful separability determine actual fan-out. Capacity never
authorizes parallelizing dependent phases or running review before the evidence
under review exists.
