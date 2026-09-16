---
name: cursor-setup-pstack
description: Configure which models pstack uses per role and at what reasoning budget. Detects your available models and writes an always-applied rule that overrides the skill defaults. Use for /setup-pstack, "configure pstack models", "pstack budget", or changing pstack's model choices.
---

# Setup pstack for Codex

Configure effective pstack model and reasoning-budget choices using native Codex selection and the standing `model-capability-router`. Do not write `~/.cursor/rules/pstack-models.mdc`, invent Cursor slugs, or switch the active task model. This skill responds to an explicit model-setup request.

## Steps

### 1. Detect native capability

Read the models and efforts advertised for the exact Codex channel being configured. Current task, subagent, user-owned task, and Work cloud channels may differ. Record availability only when that channel accepts it.

### 2. Read canonical policy

Read the installed `model-capability-router` and its canonical TheAngrySkills source when a persistent change is requested. Respect the operator's current model/effort and explicit selections. The router owns routing and total-cost policy; this skill supplies pstack role and budget questions, not a second default table.

### 3. Choose a budget and map roles

Offer these exact labels: `unlimited — keep max`, `large — xhigh reasoning`, `medium — high reasoning`, and `small — medium reasoning`. On a re-run, preserve role families, panel lists, and aliases (`inherit-parent`, `auto`). Apply the selected target effort (`max`, `xhigh`, `high`, or `medium`) to each real model, choosing the highest supported effort at or below the target. If the detected inventory uses a different slug for the same family, select that detected variant; if no supported variant exists, mark the role as needing a choice. Aliases remain unchanged. Cover every upstream role: feature/refactoring, bug-fix, perf-issue, hillclimb, judgment/prose, hardest tasks, how explorer/explainer, why investigators/synthesizer, reflect tooling/judgment/divergent/synthesizer, arena runners/cross-judge pool, swarm workers, architect runners, and interrogate reviewers. Panel list length still controls fan-out.

### 4. Validate

Validate every real model and effort against the exact channel inventory. A missing model, effort, or budget target is a bounded block; keep configuration unchanged and report the role needing a choice. `inherit-parent` and `auto` omit the model override only when the native channel supports inheritance.

### 5. Persist when requested

For an authorized persistent change, update the canonical `model-capability-router` source or its conditional pstack role reference with a reviewed diff and affected routing fixtures. A task-local selection stays in the task brief and handoffs. If source checkout or write authority is unavailable, return the mapping and exact blocked write; never claim persistence.

### 6. Read back

After an authorized persistent update, run router checks and verify the source diff. If installation is separately authorized and performed, read back the installed skill and effective native config. A source edit or fixture-only mapping does not prove runtime selection, new-session behavior, parent alias resolution, or full pstack execution.

### 7. Offer verification

If the project has no way to drive the real app for proof, offer once to create a project-local verification skill. Invoke the installed `cursor-create-verification-skill` by exact name only when available and explicitly requested; otherwise report that dependency rather than claiming it ran.
