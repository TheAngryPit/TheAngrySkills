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

### 3. Choose one mode and map every pstack role

For a full setup, load current project/task choices first and render every exact role label from the router reference `references/pstack-role-presets.json` `roles` array, even when that workflow is not being invoked now. Do not combine or rename role labels. A scoped change affects only its named role. Preserve model families, panel lists, ownership, named specialists and `inherit-parent`/`auto` aliases. Showing roles does not dispatch them.

Choose one mode: a role-aware preset or an upstream global budget. Read the router's canonical `references/pstack-role-presets.json` for the role classes and preset mapping. The presets are `Economia`, `Equilibrado` and `Power`; Equilibrado is the default only for a new setup with no existing role choices when no preset is named. Report whether Equilibrado was the default or a preset was explicitly selected. Existing complete role choices remain unchanged. A role-aware preset fills unbound roles only. Keep each explicit model/effort choice and panel list unchanged, including fixed specialist bindings and aliases. Under Power, unbound execution, explorer and tooling roles use `gpt-6.1-sol` medium with no fallback; judgment and planning use Astra low, with Astra xhigh only when explicitly selected and justified. Show any preserved binding that differs from the preset as a preserved explicit choice, not as a preset default. For Equilibrado execution, use Luna xhigh by default and high for clearly bounded small work. Keep the operator's selected main model/effort unchanged; coordinator settings are recommendations only. If a requested preset model or effort is unavailable on its role's channel, keep it unchanged and mark it as needing a choice; do not silently substitute.

Keep the four upstream global-budget labels exactly as shown and report the current choice when known: `unlimited — keep max`, `large — xhigh reasoning`, `medium — high reasoning`, `small — medium reasoning`. In global-budget mode, `unlimited` retains current efforts; the other options propose xhigh, high or medium for each real role and panel entry. Choose a detected same-family variant at or below the target only in this global-budget mode; leave aliases untouched. Never stack a global budget over a role-aware preset. If the current state or request leaves the mode ambiguous, ask the operator to choose one.

Show the entire resulting table and let the operator adjust specific roles when an answer would change the setup. Mark unavailable entries as needing a choice without changing them. Preserve panel semantics: arena runners, architect runners and interrogate reviewers have one candidate worker per selected list entry when their own workflow calls for it; `arena cross-judge pool` selects one eligible judge where possible; `swarm workers` is the default for that workflow unless a comparison explicitly assigns arms. The router still decides whether and when delegation is useful, with bounded ownership and verification.

### 4. Validate and record

Validate each proposed real model and effort against its actual execution channel, including the parent selection needed by an inherited role. Mark unsupported roles or efforts precisely and leave the affected configuration unchanged; continue independent work with the current agent when it can meet the proof bar. Record requested selection separately from native acceptance and effective runtime readback. An accepted spawn or fixture does not by itself prove which model a running worker used. The coordinator owns integration and checks the deliverable against the requested result and evidence.

### 5. Persist only the requested scope

Keep task-local choices in this task's brief and handoffs; project-only choices in the project-approved configuration or checkpoint. For an explicitly authorized persistent shared-policy change, update the canonical router source and affected fixtures with a reviewed diff. Changing this setup skill itself belongs in its canonical TheAngrySkills mirror source. Do not write `~/.cursor/rules/pstack-models.mdc`, a competing preset, a CLI resolver or native defaults as a proxy for changing the active task. If source or write access is unavailable, report the exact remaining write without claiming persistence.

### 6. Verify the applied result

Run the focused source checks, review the diff and read back any installed copy after an authorized update. Check native config or runtime metadata only where exposed. Source edits, dry-run fixtures, installed files and future-session behavior are distinct proof levels. Report what was actually verified, unresolved channel limits and current owner. Do not infer lower Codex allowance use from API prices, cache assumptions or faster parallel work; compare complete outcomes when observed usage is available.

For implementation work, use the project's existing verification skill. If it lacks a way to drive the real app, propose `cursor-create-verification-skill` once and invoke it only when available and requested; do not call a fixture full runtime proof.
