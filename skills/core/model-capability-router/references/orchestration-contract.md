# Orchestration Contract

## Topology

The master orchestrator is the user-facing Sol Medium task. It owns planning,
operator dialogue, routing decisions, integration, independent validation, and
the final status.

The field coordinator is a separate, reusable Terra Medium user-owned task. It
is logically directed by the master but remains a native peer task. Its bounded
contract names the project or ticket, accepted plan, protected state, allowed
mutations, proof bar, stop conditions, and reporting cadence.

The field coordinator may use direct native subagents for Sol/Terra work. Only
the root of that task delegates; subagents remain direct children and must not
spawn further agents.

The router bundles the approved Sol/Terra custom-agent templates under
`assets/agents/`. Luna and Spark are intentionally absent from that native
subagent registry; their model availability on another channel does not make
them valid `spawn_agent` roles.

## Native Subagent Controls

Use the current native controls when exposed:

- `spawn_agent` to start one bounded named or vanilla subagent;
- `followup_task` or `send_message` to steer it;
- `wait_agent` to wait without polling noise;
- `list_agents` to reconcile live state;
- `interrupt_agent` to stop unnecessary work.

Prefer the smallest useful fan-out. Wait for required children to complete and
interrupt unnecessary work before the field coordinator submits its closure
report.

## Native Task Controls

Use native task controls only after the current user authorizes task creation:

- `create_thread` to create a field coordinator or Luna task;
- `list_threads` and `read_thread` to find and verify a reusable task;
- `send_message_to_thread` to direct follow-up work;
- `wait_threads` for bounded progress snapshots;
- `set_thread_archived` only after current user authorization.

`set_thread_title` and `set_thread_pinned` change user-visible metadata; they do
not route work.

`fork_thread` is prohibited inside this router. It copies completed history and
creates a new task lineage, so it must never implement a field coordinator,
subtask, worker, retry, reuse, or continuation.

`handoff_thread` is not a router operation. It moves an existing task and its
associated Git state between execution locations and interrupts it when running.
Use it only when the user explicitly requests that relocation, after verifying
the source task, destination host or checkout, dirty/running state, and resume
point. A handoff does not create a logical child or change the task's routing
role.

A task is reusable only when project binding, purpose, lifecycle, and ownership
match. A title match alone is insufficient.

## Luna Lifecycles

`luna-subtask` is ephemeral and one-shot. Create it for one bounded result with
a stop condition. Do not reuse it. Archive it only after its result is accepted
and the user authorizes archival.

`luna-worker` is reusable for one project and stable purpose. Before creation,
look for an active compatible task. Re-message the same task for later batches;
do not create duplicates merely because another Luna pass is needed.

The field coordinator reports logical lineage explicitly because the platform
does not make these Luna tasks native children.

## Closure

The field coordinator waits for required child results, reconciles conflicts,
stops unnecessary children, and returns: mutations, proof, contradictions,
remaining debt, open gates, and reusable-task state.

The master independently checks closure-bearing claims. It may use separate
Sol/Terra review subagents, but it does not silently take ownership of the field
coordinator's children.
