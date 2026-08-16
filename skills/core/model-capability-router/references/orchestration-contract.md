# Orchestration Contract

## Topology and Authority

The user-facing master is Sol Medium. It owns operator dialogue, the accepted
plan, routing, integration, independent validation, and final status. For
substantial or ambiguous work it asks a Sol High `planner` for a bounded plan
before execution.

A field coordinator is a separate, reusable Terra Medium user-owned task. The
platform treats it as a peer. In the operator's nomenclature it is a `subtask`
because it works for the master, receives steering, and reports closure back to
that logical parent.

A normal parallel user-owned task is also a platform peer, but it has no logical
parent. It belongs directly to the operator and must not be relabelled as a
subtask merely because it shares a project or exchanges information.

Record both axes explicitly:

| Surface | Platform relationship | Logical relationship |
| --- | --- | --- |
| Native subagent | child | delegated child |
| Fleet worker | child | owned workstream |
| Field coordinator | user-owned peer | delegated subtask |
| Delegated user-owned worker | user-owned peer | delegated subtask |
| Parallel user-owned task | user-owned peer | independent parallel task |

The master does not transfer authority to any child or peer. A coordinator owns
integration only inside its accepted contract. All human, permission, install,
release, secret, and destructive-action gates remain unchanged.

## Role and Compute Binding

Role describes the contract; model and effort describe compute. Keep them
separate. Custom role TOML may omit model and `model_reasoning_effort`, allowing
an explicit native spawn selection or runtime default to apply. If a role file
pins either value, the selected route must match it.

Configuration and tool metadata are preflight evidence, not runtime proof.
Attempt a resolved named role once. If the runtime rejects it, preserve the
exact role and error, feed the rejection back to the resolver, and classify the
route as blocked for the active task. Do not retry through a parent clone or
silently choose another role.

## Native Subagent and Fleet Controls

Use current native controls when exposed:

- `spawn_agent` starts one bounded named or vanilla child;
- `followup_task` gives an idle child another bounded unit and triggers work;
- `send_message` steers a running child without creating a new turn;
- `wait_agent` waits for mailbox updates without noisy polling;
- `list_agents` reconciles live state;
- `interrupt_agent` stops work that is no longer needed.

Fleet work must be separable. Start with two or three direct children and add
only workstreams that can run independently. Eight is the approved session
ceiling for spawned subagent threads; it is not a default target. Assign exact
ownership, expected output, proof, and stop condition. Use no full-history
clone: prefer no inherited turns or a small bounded slice.

The ceiling is policy, not live capacity. Reconcile the runtime limit and active
spawned children before resolving each expansion. Effective fan-out is
`min(requested, policy ceiling, runtime capacity - active children)`. Fail
closed when capacity evidence is missing or no slot is free.

The coordinator waits for required results, resolves contradictions, stops
unnecessary workers, and reports mutations, proof, gaps, gates, and worker
state. A worker never spawns another agent.

## User-Owned Task Controls

Use native task controls only after the current user explicitly authorizes a
new task:

- `create_thread` creates a field coordinator, delegated subtask, or parallel task;
- `list_threads` and `read_thread` verify a reusable task;
- `send_message_to_thread` directs follow-up work;
- `wait_threads` produces bounded progress snapshots;
- `set_thread_archived` requires current user authorization.

`set_thread_title` and `set_thread_pinned` change presentation, not routing.
A title match never proves compatibility.

A delegated subtask is reusable only when project, purpose, ownership, logical
parent, and lifecycle all match. A parallel task is reusable only when project,
purpose, ownership, and lifecycle match and it remains independent. Never reuse
one relationship as the other merely to avoid task creation.

The resolver does not treat a supplied task ID as verification. Inspect the
task live, then pass its ID with explicit reuse verification. Delegated routes
also carry the verified logical parent task ID; independent parallel tasks must
not carry one.

`field_fleet` is deliberately two-stage. First create or reuse the Terra task
through `field_coordinator`. After it is live, reconcile that coordinator's own
model channel, subagent controls, active-child count, and runtime capacity.
Write that readback as a short-lived structured receipt containing task and
parent IDs, observation time, Terra role/model/effort binding, worker
role/model/effort binding, relationship, lifecycle, project/purpose/ownership
verification, channel models, controls, runtime capacity, active children, and
`verification_method=list_threads+read_thread+coordinator_readback`. Only then
resolve `field_fleet` against the existing verified task. Never use the
master's model catalog, role files, controls, or free slots as evidence for the
Terra task's ability to command workers.

The preset sets the maximum receipt age; a route may only tighten it. Include
the coordinator's own `runtime_role_rejections` object and ignore master-side
role rejection evidence for this topology. A receipt hash proves byte identity,
not platform authenticity. Classify the binding as `receipt_claimed_match` and
the reuse evidence as `caller_supplied_structured_coordinator_attestation` until
a native task-readback signature or identifier exists.

`preflight_ready` is not proof. It means only that the routing contract can be
executed. The result carries `proof_requirement` and `proof_state=not_started`;
the native receipt and requested validation must still be collected. Generic
reuse uses caller-attested preflight unless a stronger receipt is present and
must never be described as independently verified.

`fork_thread` is prohibited inside this router. It copies history and creates a
new lineage; it must not implement a subtask, parallel task, coordinator,
worker, retry, reuse, or continuation.

`handoff_thread` is not routing. It moves an existing task and associated Git
state between execution locations. Use it only for an explicit relocation
request after verifying source, destination, running state, dirty state, and
resume point.

## Closure

A field coordinator or delegated subtask returns its result to its logical
parent. A parallel task reports directly to the operator unless the operator
explicitly asks it to collaborate with another task. The master independently
checks closure-bearing claims before reporting them and does not silently take
ownership of a coordinator's live workers.
