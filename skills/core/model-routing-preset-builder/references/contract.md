# Preset Contract

Presets use TOML and `schema_version = 2`.

Each `routes.<name>` entry declares:

- `execution_kind`: `current_task`, `native_subagent`, or `native_task`;
- `channel`: respectively `current_task`, `spawn_agent`, or `create_thread`;
- `selection_mode`: `vanilla` or `pinned`;
- `role`, `model`, and `effort` for pinned routes;
- `required_tools`, `proof`, and a checkable `stop_condition`;
- `lifecycle` and `creation_requires_user_authorization = true` for native
  tasks.

Model availability is channel-specific. A model listed in a catalog, TOML, or
UI badge is not proof that a particular execution channel can run it.

Use reader-facing Light in prose and `low` in TOML. Max and Ultra routes must
declare `operator_authorization_required = true`.

Reusable native tasks must state a reuse scope. Their logical parent does not
create a native parent-child relationship.

The opinionated preset's approved Sol/Terra custom-agent templates live under
`model-capability-router/assets/agents/`. Normal subagent registration excludes
Luna and Spark; model availability on another channel does not make either a
valid `spawn_agent` role.

Every schema 2 preset excludes `fork_thread` and `handoff_thread` from model
routing. Forking creates a new copied-history lineage. Handoff is a separate,
explicitly requested relocation of an existing task and associated Git state.
