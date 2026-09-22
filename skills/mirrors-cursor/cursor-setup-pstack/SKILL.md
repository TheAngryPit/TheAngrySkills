---
name: cursor-setup-pstack
description: Use when setting up pstack native Codex model choices for the current task or an explicitly requested persistent policy, including /setup-pstack or pstack budget changes.
---

# Setup pstack for Codex

Use the standing `model-capability-router` as the sole authority for model, effort, delegation and total-cost decisions. This skill maps pstack roles onto native Codex capabilities when the operator asks for setup; it does not create a second routing policy, switch the active task model, write a Cursor rule, or start agents merely to configure them.

## Steps

### 1. Establish scope and capability

Identify whether the request is for this task, a particular project, or a persistent shared policy. Read the installed router and, for a persistent source change, the canonical `TheAngryPit/TheAngrySkills` source. Respect the operator's selected main model, effort, role bindings and workflow. Check the models, efforts and inheritance exposed by each exact channel that would execute a choice; current task, native subagent, user-owned task and Work cloud can differ. Do not present the router's recommended profiles as detected runtime configuration.

### 2. Choose execution before compute

Keep small or tightly coupled work with the agent that has context. Use bounded delegation or parallel workers only when authorized and useful after briefing, startup, integration and verification costs. Preserve a requested delegation workflow for suitable work. There is no required Astra → Sol → Luna ladder, coordinator stage, automatic planning or review delegate, failed-attempt escalation, fixed fan-out or model race. Create a separate user-owned task only under the router's explicit-request and task-boundary rules. A full-history subagent fork inherits the parent model; request a differently modelled native worker with bounded or fresh context only when that channel supports it.

### 3. Map the pstack roles that will actually run

For each selected pstack workflow, preserve its role ownership, review contract, panel membership and named specialists. This includes feature/refactoring, bug-fix, perf-issue, hillclimb, judgment/prose, hardest tasks, how, why, reflect, arena, swarm, architect and interrogate when those workflows are in scope. Do not dispatch every upstream role simply because it exists. Panel length describes that workflow's available slots, not an instruction to fill them all. Use the router's current palette as recommendations: Sol medium for sustained coordination, Astra low for planning/review, Luna high for bounded work, Luna xhigh for defined execution; Sol high, Luna max or Astra xhigh require a task-specific reason, and explicit selections or fixed specialist bindings take precedence. Choose model and effort for the work, not by patch size, read/write status or one uniform budget.

If the operator explicitly asks for the upstream budget menu, offer these labels unchanged: `unlimited — keep max`, `large — xhigh reasoning`, `medium — high reasoning`, `small — medium reasoning`. Treat the selected level as an optional ceiling for requested role choices, not an automatic effort setting or a replacement for the router's task-specific judgment. Do not raise a role's effort to meet the ceiling; a lower, justified effort stays lower. If the ceiling conflicts with an explicit model/effort binding or the proof required, surface the specific choice. Preserve `inherit-parent` and `auto` aliases only where the native channel implements their intended behavior. Do not invent Cursor model slugs or assume another variant in a model family is equivalent.

### 4. Validate and record

Validate each proposed real model and effort against its actual execution channel, including the parent selection needed by an inherited role. Mark unsupported roles or efforts precisely and leave the affected configuration unchanged; continue independent work with the current agent when it can meet the proof bar. Record requested selection separately from native acceptance and effective runtime readback. An accepted spawn or fixture does not by itself prove which model a running worker used. The coordinator owns integration and checks the deliverable against the requested result and evidence.

### 5. Persist only the requested scope

Keep task-local choices in this task's brief and handoffs; project-only choices in the project-approved configuration or checkpoint. For an explicitly authorized persistent shared-policy change, update the canonical router source and affected fixtures with a reviewed diff. Changing this setup skill itself belongs in its canonical TheAngrySkills mirror source. Do not write `~/.cursor/rules/pstack-models.mdc`, a competing preset, a CLI resolver or native defaults as a proxy for changing the active task. If source or write access is unavailable, report the exact remaining write without claiming persistence.

### 6. Verify the applied result

Run the focused source checks, review the diff and read back any installed copy after an authorized update. Check native config or runtime metadata only where exposed. Source edits, dry-run fixtures, installed files and future-session behavior are distinct proof levels. Report what was actually verified, unresolved channel limits and current owner. Do not infer lower Codex allowance use from API prices, cache assumptions or faster parallel work; compare complete outcomes when observed usage is available.

For implementation work, use the project's existing verification skill. If it lacks a way to drive the real app, propose `cursor-create-verification-skill` once and invoke it only when available and requested; do not call a fixture full runtime proof.
