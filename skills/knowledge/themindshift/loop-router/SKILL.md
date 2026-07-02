---
name: themindshift-loop-router
description: Route TheMindShift editorial work into the correct next loop, manual approval gate, same-thread heartbeat, fresh scheduled task, delegated worker, or blocked state. Use when Vitor or TheAngry_Editor-inChief asks what should happen next in TheMindShift, asks to continue an issue lifecycle, asks about heartbeat or scheduled work, or needs a loop handoff packet.
---

# TheMindShift Loop Router

Use this skill to route repeated TheMindShift editorial work. Do not use it as project authority.

TheMindShift project files and `TheAngry_Editor-inChief` remain authority. This skill only produces a routing packet.

## Required Reads

Read `references/state-sources.md` first. Inspect the required TheMindShift files before routing.

If the TheMindShift project root is missing, ask for it. Do not route from memory alone.

## Routing Steps

1. Identify the active issue, current gate, blockers, next artifact, and proof bar.
2. Classify the work as exactly one of:
   - `manual_gate`
   - `same_thread_heartbeat`
   - `fresh_scheduled_task`
   - `delegated_worker`
   - `blocked`
3. Check `references/human-gates.md` before recommending any continuation.
4. Produce a loop packet using `references/loop-packet.md`.
5. Stop with `blocked` if a human gate, missing source, unclear project state, private-data boundary, or external-action risk prevents safe routing.

## Classification Rules

Use `manual_gate` when Vitor's taste, public judgment, private context, final approval, or publication readiness is required.

Use `same_thread_heartbeat` when the next run needs the current manager thread context, such as active issue continuity, parked approval follow-up, or status polling with a stop condition.

Use `fresh_scheduled_task` when each run can start fresh from project files and current external sources.

Use `delegated_worker` when bounded execution would reduce load or improve quality and can return to the Editor-in-Chief before promotion.

Use `blocked` when routing would bypass a human gate, act externally, depend on missing source files, or rely on stale or unclear state.

## Hard Stops

Stop before:

- publication;
- posting;
- emailing;
- contacting anyone;
- external system changes;
- final theme approval;
- final voice approval;
- source package lock;
- final image approval;
- publishing readiness approval.

## Output

Return only the loop packet and any short note needed to explain a blocker.

Do not produce a draft, research report, approval artifact, automation, issue update, or external action from this skill alone.
