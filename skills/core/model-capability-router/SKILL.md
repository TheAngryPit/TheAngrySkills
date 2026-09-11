---
name: model-capability-router
description: "Use when explicitly asked to choose or configure native Codex models and reasoning effort, or when authorised delegation needs a compute choice. Provides Spark, Luna XHigh/Max and Astra Medium/XHigh profiles without mandatory routing stages or wrappers."
---

# Native Model Routing

Use native Codex model, effort and agent selection. Respect the operator's
selected main model and effort; this skill does not switch an active task.
Choose the execution arrangement before the worker model.

## Execution arrangement

Keep small, tightly coupled work and immediate follow-ups with the agent that
already holds the relevant context. A cheaper worker model alone does not
justify a handoff. Batch related operations rather than delegating each one.

Delegate a bounded package when its benefit justifies briefing, startup,
coordination, verification and likely correction costs. Reuse a suitable worker
for related follow-ups. Send only context needed for its acceptance checks.

Parallelise independently executable packages with clear ownership when the
benefit outweighs duplicated context and integration costs. Sequence dependent
work. Faster completion and lower consumption are separate benefits.

Continue the current thread when its context remains useful. A fresh task suits
an independent objective; a full-history fork copies history rather than
providing a clean context.

## Five profiles

| Profile | Model | Effort | Use |
|---|---|---|---|
| Ultra-fast | `gpt-5.3-codex-spark` | `low` | Tiny deterministic edits, targeted lookups, short iterations with clear context and an immediate check. |
| Bounded execution | `gpt-5.6-luna` | `xhigh` | Well-specified implementation, extraction or transformations with concrete acceptance checks. |
| Substantial execution | `gpt-5.6-luna` | `max` | Larger implementation with bounded ownership, tests and observable acceptance criteria. |
| Capable default | `gpt-6-astra` | `medium` | Interpretation, cross-cutting diagnosis, technical decisions and coordination where understanding the problem dominates. |
| Difficult problems | `gpt-6-astra` | `xhigh` | Particularly difficult reasoning, complex terminal/system work or unresolved ambiguity needing deeper investigation. |

Choose directly for the task. There is no Spark-first or Luna-first ladder,
mandatory failed attempt, coordinator stage, planning/review delegation, CLI
resolver, receipt workflow or preset wrapper. Importance alone does not justify
XHigh. A read-only task can still need Astra. Patch size alone does not prove
that Luna is suitable for autonomous systems administration.

This five-profile policy explicitly permits Luna Max for the substantial
execution profile; no repeated conversational approval is required merely for
that effort. It does not authorise new spending routes, external actions or
additional access. Astra Max and Ultra are outside the habitual palette.
Sol and Terra are not habitual defaults, not forbidden models or proven
universally inferior alternatives. Honour explicit operator selections and
fixed specialist bindings, including bindings outside this palette.

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
Respect actual available slots;
eight concurrent children is a ceiling, not a target or permission to spawn.
Do not make specialists coordinators or enable recursive delegation implicitly.
The coordinator integrates and verifies the result.

Creating a user-owned task, forking, moving or archiving tasks still requires
the corresponding explicit user request. Routing grants no authority over
hosts, accounts, private data, credentials, publication or destructive actions.
Respect native approvals and refusals. Do not force feature flags.

## Cost and evidence

Compare remaining whole-task consumption, including parent and worker calls,
using each model's input, cache and output rates. Existing context is not free;
cache reuse can reduce its cost but is not guaranteed across threads, models
or changed prefixes. Include cache writes when the meter exposes them.
Reasoning may already be included in output; count it once. Avoid double-counting
child usage in parent aggregates or costs already included in measurements.
Distinguish benchmark results from native task proof and projected savings
from measured account usage. Keep changing benchmark scores out of durable
routing rules. Report unavailable capabilities and unverified claims plainly.

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
