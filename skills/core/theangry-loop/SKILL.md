---
name: theangry-loop
description: "Use when Vitor asks to loop, keep checking, follow up later, retry on a cadence, monitor a thread, or create/update a Codex heartbeat. Complements loop-me: loop-me designs workflows, theangry-loop schedules thread heartbeats."
---

# TheAngry Loop

Create and manage Codex heartbeat loops without making Vitor manually babysit recurring work.

This skill is inspired by `jxnl/personal-monorepo-template`'s `loop` skill, but adapted to TheAngryPit/Echo operating rules.

## Role Split

- `loop-me`: design the workflow through grilling.
- `theangry-loop`: create or manage the recurring heartbeat after the task is clear.
- Project-specific loop routers: decide the next loop inside a known domain.
- Goal-authoring: define long-running proof-bound outcomes.

Do not merge these roles.

## Use When

Use this when Vitor asks for any of:

- "loop this"
- "keep checking"
- "follow up later"
- "retry every X"
- "monitor this"
- "wake this thread up"
- "check again tomorrow"
- "keep this project moving"

Use it only when time or external state matters. If the work can be finished now, finish it instead.

## Workflow

1. Identify the task, target thread or work surface, cadence, stop condition, and notification rule.
2. Check whether the task is blocked by a human gate.
3. If the task is unclear, ask one concise question. Do not make Vitor design RRULEs or scheduling syntax.
4. Prefer the native Codex automation tool for heartbeat creation or update.
5. Create or update a thread heartbeat only when the automation surface is available.
6. Use a short verb-led name.
7. Make the prompt self-contained:
   - what to inspect;
   - what counts as progress;
   - what counts as blocked;
   - when to notify Vitor;
   - when to stop.
8. If native thread-title tools are available, use lifecycle prefixes:
   - `loop: <short task name>` while active;
   - `done: <short task name>` only after the completion condition is met.
9. Return only:
   - loop name;
   - cadence;
   - target;
   - stop condition;
   - what it will do.

## Human Gates

Do not create or continue a heartbeat that would bypass:

- paid actions;
- credentials or account setup;
- private data access;
- public claims;
- external contact;
- legal, financial, medical, family, or health judgement;
- promotion from draft to canon or public use.

Words like `continue`, `repeat`, `resume`, or a scheduled heartbeat are not approval to pass a human gate.

## Guardrails

- Do not emit raw automation directives as a workaround.
- Do not invent thread IDs.
- Do not create duplicate loops if an existing matching loop can be updated.
- Do not poll faster than the underlying state can plausibly change.
- Do not create token-heavy empty status loops.
- Do not treat scheduled activity as proof of progress.
- If the automation tool is unavailable, say so and provide the exact manual prompt instead.

## Output Shape

```text
Loop: <name>
Cadence: <plain English cadence>
Target: <thread/work surface>
Stop condition: <condition>
Will do: <one sentence>
Needs Vitor: <none or exact decision>
```
