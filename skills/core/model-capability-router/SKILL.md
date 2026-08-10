---
name: model-capability-router
description: Route Codex work across the current task, native Sol/Terra subagents, and explicitly authorized user-owned Terra/Luna tasks. Use when selecting a model, reasoning effort, vanilla versus pinned execution, master orchestrator, field coordinator, planner, worker lifecycle, capability chain, fallback, proof bar, or escalation from an approved channel-aware preset.
---

# Model Capability Router

Route from task requirements and fresh channel capability evidence. A preset is
policy; runtime inventory is truth; visual badges are never authority.

## Route

1. Locate the nearest operator-approved schema 2 preset. Do not treat a bundled
   example as adopted policy.
2. Classify the actor and lane:
   - keep the master orchestrator in the current Sol Medium task;
   - use a reusable Terra Medium native task as field coordinator;
   - use normal Sol/Terra subagents for bounded direct work;
   - use Luna only through explicitly authorized native tasks;
   - retain vanilla model/effort selection when no proof, role, or cost
     requirement justifies pinning.
3. Inventory model availability per execution channel, not globally:
   `current_task`, `spawn_agent`, and `create_thread`. Inventory the exact native
   tools exposed in the current session, relevant skills, and custom agent
   files. The bundled `assets/agents/` directory is the source template; the
   active Codex agent directory is runtime binding evidence. Do not infer
   reachability from source TOML or UI badges.
4. Resolve one route:

```bash
python3 scripts/route.py resolve \
  --preset <preset.toml> \
  --route <route> \
  --channel-model spawn_agent=gpt-5.6-sol \
  --channel-model spawn_agent=gpt-5.6-terra \
  --available-tool spawn_agent \
  --available-tool wait_agent \
  --agent-root <codex-home>/agents \
  --skill-root <skills-root>
```

Pass every required native tool reported by the session. For a native task, pass
`--channel-model create_thread=<model>`. Pass `--existing-task-id <id>` only
after `list_threads` and `read_thread` prove that a reusable task has the same
project, purpose, ownership, and lifecycle.

The resolver accepts both canonical names such as `create_thread` and exposed
namespaced identifiers such as `codex_app__create_thread`; its evidence output
retains both forms.

5. Follow the resolver result:
   - `ready`: execute only the returned channel and action;
   - `needs_authorization`: stop and request the named current-user gate;
   - `blocked`: do not substitute another channel, model, role, or generic task.
6. Attach the capability chain, proof bar, and stop condition to the delegated
   contract. The master validates the field coordinator's closure report before
   reporting to the operator.

Read [orchestration-contract.md](references/orchestration-contract.md) before
creating, reusing, steering, waiting on, or archiving a field coordinator or
Luna task.

## Authority Gates

`create_thread` creates a peer, user-owned task. It is not a native child
subagent and must never be presented as one. Use it only when the user explicitly
asks for a new task in the current request. Reuse an existing compatible task
before proposing another. Archive only with current user authorization.

`fork_thread` is excluded from this router: copying completed task history is
not model routing, delegation, coordination, or worker reuse. `handoff_thread`
is also outside the router. Use it only in a separate, explicitly requested task
relocation flow after verifying the existing task, destination, running state,
and associated Git state.

`max` and `ultra` require explicit operator authorization in the current task.
Neither expands permissions, targets, credentials, mutation authority, or
delegation depth.
The preset must mark every route that can select either effort with
`operator_authorization_required = true`; pass `--operator-authorized` only
after that authorization is present in the current task.

## Output Contract

Return the route, execution kind and channel, vanilla or pinned selection,
model/effort/role when pinned, lifecycle and reuse action, missing tools or
skills, authorization gates, proof bar, escalation trigger, preset
name/version, excluded operations, and the fresh availability evidence used.
