---
name: cursor-setup-pstack
description: Configure which models pstack uses per role. Detects your available models and writes an always-applied rule that overrides the skill defaults. Use for /setup-pstack, "configure pstack models", or changing pstack's model choices.
---

## Codex runtime mapping

The standing `model-capability-router` is the single policy owner. Read reports/cursor-setup-pstack-native-inventory-20260914.md for the current subagent-channel inventory and 17-role/four-panel candidate map. Current-task, subagent, user-owned task and Work cloud channels differ. This route is explicit-only because persistent model configuration requires a deliberate request. This setup skill maps roles only to models/efforts advertised by the target channel and verifies persistent source changes when requested. The current inventory and dry-run fixture do not prove a write, new-session selection, or full pstack execution.

# Setup pstack for Codex

Configure effective pstack model choices using native Codex selection and the standing `model-capability-router`. Do not write `~/.cursor/rules/pstack-models.mdc` or invent Cursor slugs. This skill responds to an explicit model-setup request; it does not switch the model of an active task.

## Steps

### 1. Detect native capability

Read the models and efforts advertised for the exact Codex channel being configured. Current task, subagent and user-owned task may differ. Record availability only when that channel accepts it.

### 2. Read canonical policy

Read the installed `model-capability-router` and its canonical TheAngrySkills source when a persistent change is requested. Respect the operator's current model/effort and explicit selections. The router owns routing and total-cost policy; this skill supplies pstack role questions, not a second default table.

### 3. Map roles

Cover every upstream role: feature/refactoring, bug-fix, perf-issue, hillclimb, judgment/prose, hardest tasks, how explorer/explainer, why investigators/synthesizer, reflect tooling/judgment/divergent/synthesizer, arena runners/cross-judge pool, swarm workers, architect runners and interrogate reviewers. Panel list length still controls fan-out. Resolve each to an available native model and effort under the standing router. `inherit-parent`/`auto` mean omit a model override, subject to native support. Show the effective mapping and unsupported roles. Ask Vítor only for an unresolved preference that changes policy.

### 4. Validate and persist when requested

Validate each selected model/effort against the native channel. For a persistent change, update the canonical `model-capability-router` source or its conditional pstack role reference in TheAngrySkills, with a diff and affected routing fixtures. A task-local selection stays in the task brief and handoffs. If source checkout or write authority is unavailable, return the mapping and exact blocked write; never claim persistence.

### 5. Read back

After an authorized persistent update, run router checks and verify the source diff. If installation was separately authorized and performed, read back the installed skill and effective native config in the target home. Report configured/dynamic roles and unsupported model/channel. A source edit alone does not prove runtime selection.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke the installed `cursor-create-verification-skill` by exact name; if unavailable, report that dependency rather than claiming it ran. On no, move on without pushing.
