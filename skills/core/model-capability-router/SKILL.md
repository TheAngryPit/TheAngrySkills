---
name: model-capability-router
description: "Use when the operator explicitly asks for native Codex model or reasoning-effort routing, including an active standing request."
---

# Native Model Routing

Use native Codex model, effort and agent selection. Respect the operator's
selected main model and effort; this skill does not switch an active task.
For this operator's home, Sol Medium is the separately configured Codex default.
Choose the execution arrangement before a delegated worker's model.
Authorization to delegate alone does not require consulting this router.

## Execution arrangement

Keep small, tightly coupled work and immediate follow-ups with the agent that
already holds the relevant context. A cheaper worker model alone does not
justify a handoff. Batch related operations rather than delegating each one.

When the operator requests delegation, preserve that workflow for suitable
bounded work. Otherwise delegate when the benefit justifies briefing, startup,
coordination, verification and likely correction costs. Reuse a suitable worker
and its relevant context for related follow-ups, without assuming cache reuse.
Give it the context needed for its acceptance checks.

Parallelise independently executable packages with clear ownership when the
benefit outweighs duplicated context and integration costs. Sequence dependent
work. Faster completion and lower consumption are separate benefits.

Continue the current thread when its context remains useful. A fresh task suits
an independent objective; a full-history fork copies history rather than
providing a clean context.

## Operator profiles

| Profile | Model | Effort | Use |
|---|---|---|---|
| Home default and coordination | `gpt-5.6-sol` | `medium` | This home's selected default; sustained coordination, integration and open-ended execution. |
| Planning and review | `gpt-6-astra` | `low` | Habitual Astra setting for conversation, planning and review when its judgment helps. |
| Demanding decisions | `gpt-6-astra` | `medium` | Substantial ambiguity, cross-cutting decisions or tradeoffs requiring more analysis. |
| Exceptional reasoning | `gpt-6-astra` | `xhigh` | Rare difficult decisions or unresolved investigations after the task warrants deeper effort. |
| Bounded subtask | `gpt-5.6-luna` | `high` | Narrow, well-specified work with clear ownership and acceptance checks. |
| Defined execution | `gpt-5.6-luna` | `xhigh` | Implementation or transformation with a concrete outcome and verification. |
| Substantial execution | `gpt-5.6-luna` | `max` | Justified when deeper effort materially helps a bounded implementation with observable proof. |
| Tiny iteration, when available | `gpt-5.3-codex-spark` | `low` | Small deterministic edits or lookups with an immediate check. |

Choose directly for the task. There is no Spark-first or Luna-first ladder,
mandatory failed attempt, coordinator stage, automatic planning/review
delegation, CLI resolver, receipt workflow or preset wrapper. Requested
planning or review delegation remains available when suitable. Importance
alone does not justify XHigh. A read-only task can still need Astra. Patch
size alone does not prove that Luna suits autonomous systems administration.

Luna Max is available when justified by the work; it requires no repeated
approval merely for that effort. These profiles do not authorise new spending
routes, external actions or additional access. Astra Max and Ultra are outside
the habitual palette. Terra and other supported models remain available when
selected by the operator or bound to a specialist. Honour explicit selections
and fixed bindings, including those outside this palette.

## Runtime and delegation

Before selecting compute, check the exact channel's current advertised models
and efforts. Current-task, native-subagent and user-owned-task support differ.
Spark may be available in the main/task picker but absent from `spawn_agent`:
do not invent support, create a task to work around it, or silently substitute.
Report the gap and continue locally when the existing selection can meet the
proof bar; otherwise surface the specific decision needed.

For permitted delegation, give bounded ownership, relevant context, expected
output and verification requirements. A differently modelled native worker
needs fresh or bounded context: full-history forks inherit the parent model.
Respect actual available slots; a concurrency ceiling is neither a target nor
permission to spawn.
Do not make specialists coordinators or enable recursive delegation implicitly.
The coordinator integrates and verifies the result.

Creating a user-owned task, forking, moving or archiving tasks still requires
the corresponding explicit user request. Routing grants no authority over
hosts, accounts, private data, credentials, publication or destructive actions.
Respect native approvals and refusals. Do not force feature flags.

## Cost and evidence

Compare the remaining whole task, including parent and worker input, output,
briefing, startup, coordination, verification and rework. Reusing a worker can
save context transfer; cached input is possible, not guaranteed across tasks,
models or changed prefixes. Count reasoning and child usage once if a meter
already includes them. API token prices and benchmarks inform comparisons but
do not measure this account's Codex allowance or prove a routing saving. Use
observed account usage or a like-for-like native task comparison for such claims;
state when that evidence is unavailable. Keep changing prices and benchmark
scores out of durable profile rules.

## Installation and updates

The sole install source is `TheAngryPit/TheAngrySkills`, not Workbench.

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git -g -a codex -y -s model-capability-router
```

Use one canonical installed skill per OS user, shared by Codex profiles through
native discovery or links. A profile link is not a second independent version.
Keep source metadata pointed at the normal repository. `npx skills` records
update provenance; it does not provide an automatic update schedule. Inspect
the installed CLI's update/check behavior before using it as a read-only check.
