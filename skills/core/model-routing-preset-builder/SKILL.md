---
name: model-routing-preset-builder
description: Create, clone, explain, or customize a schema 2 channel-aware Codex routing preset for current tasks, native subagents, and user-owned tasks based on available models, vanilla or pinned selection, roles, capabilities, fallbacks, lifecycles, usage preferences, and human gates.
---

# Model Routing Preset Builder

Build one reviewable preset instead of scattering model and lifecycle choices
across prompts and agent files.

## Build

1. Inventory model availability separately for `current_task`, `spawn_agent`,
   and `create_thread`. Inventory native tools, named roles, skills, and
   supported efforts. Mark unverified entries unavailable.
2. Record the desired topology: master orchestrator, field coordinator, normal
   subagents, Luna tasks, and validation roles.
3. Copy `assets/vitor-opinionated.toml` or `assets/neutral-balanced.toml`. Never
   edit an adopted preset without versioning it.
4. For each route, choose `current_task`, `native_subagent`, or `native_task`.
   Choose `vanilla` unless a proof, role, lifecycle, or cost requirement
   justifies `pinned`.
5. Native tasks must declare `ephemeral` or `reusable` lifecycle and require a
   current-user creation gate. They are peer user-owned tasks, not native child
   subagents.
6. Validate with the sibling router:

```bash
python3 <model-capability-router>/scripts/route.py validate --preset <preset.toml>
```

7. Show the channel matrix, task gates, unavailable routes, and changed
   assumptions before asking the operator to adopt the preset.

## Required Routes

Cover the master, vanilla, coordinator, planning, implementation, debugging,
review, audit, release, Luna subtask, Luna worker, and memory branches required
by the schema 2 router. A custom preset may add routes but must not silently
remove required branches.

## Gates

`max` and `ultra` remain operator-authorized. Task creation and archival require
current-user authorization independently of model choice. Host mutation,
secrets, deployment, publishing, spending, and cross-account work retain their
own gates.

## Completion Contract

Return the preset path, base example, changed routes, channel availability,
vanilla/pinned decisions, task lifecycles, unavailable models, missing tools or
skills, validation result, and approval status.
