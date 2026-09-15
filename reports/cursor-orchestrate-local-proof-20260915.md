# `cursor-orchestrate` local preparation — 2026-09-15

This report records the local work that can be completed while the selected
ChatGPT Work cloud route remains unproved. The pinned Cursor source remains
held with its `blocked_malicious` finding. The bundled Cursor TypeScript/Bun
runtime, `CURSOR_API_KEY`, Slack adapter and dependency installation were not
used.

## Local contract

`scripts/cursor_orchestrate_adapters.py` provides three non-dispatching checks:

1. `prepare_local_plan` validates one planner, stable task IDs, known
   dependencies, explicit acceptance criteria and a child limit. It returns
   `PLAN_ONLY`, marks cloud execution `UNAVAILABLE`, and records that no
   dispatch or external write occurred.
2. `reconcile_local_handoffs` accepts only `PASS`, `ISSUES` or `BLOCKED`,
   requires evidence, requires an artifact identity for `PASS`, and reports
   missing or blocked tasks as `BLOCKED`. It never invents a handoff.
3. `build_work_cloud_approval_payload` returns one exact request for review.
   It does not call `create_thread` or any other task API.

Focused proof: `pytest -q tests/test_cursor_orchestrate_adapters.py` — **5
passed**.

## Exact approval payload

The following is the only cloud action prepared in this worktree. It is a
request for explicit approval; it has not been dispatched.

```yaml
recipient: ChatGPT Work cloud (one user-owned task)
destination:
  type: chatgptWorkCloud
prompt: >-
  Run one read-only orchestration proof using only this synthetic/public data:
  {"records":[{"id":1,"value":"alpha"},{"id":2,"value":"beta"}]}.
  Return the record count and the two values in a single structured handoff.
  Exercise root status, at most one child, handoff readback, artifact identity,
  stop/cancel, and recovery readback only when the Work surface exposes each
  operation. Do not access repositories, private data, credentials, secrets,
  connectors, or external services. Do not edit, publish, message, purchase,
  merge, or create artifacts outside this task.
max_children: 1
operations:
  - create one root task
  - read root status
  - request at most one child when exposed
  - read structured handoff and artifact identity
  - stop or cancel the exact task when exposed
  - recover by readback or one bounded follow-up when exposed
stop_cancel_recovery:
  stop: stop after the first available readback or immediately if the task exceeds the stated scope
  cancel: cancel only the exact returned task identity through a documented native operation; never archive as a substitute
  recovery: preserve the last confirmed status and request one bounded readback/follow-up; report unavailable cancellation or recovery as a gap
safety:
  repo_data: false
  private_data: false
  secrets: false
  external_publication: false
  connectors: false
```

The recipient is the native Work destination represented by
`target.type: chatgptWorkCloud`; no ChatGPT project or repository is supplied.
The exact data sent is the two-record synthetic fixture in the prompt. The
request authorizes one user-owned root task and, only if the destination
exposes it, one child. It does not authorize a repository checkout, private
context, credentials, connectors, publication or external messaging.

## Still indispensable decision

Vítor must explicitly approve this exact one-task payload before any Work
cloud creation attempt. After approval, the returned task identity and native
status/readback surface must be observed. Child fan-out, structured handoff,
artifact identity, cancellation and recovery remain separate proof points; an
unavailable operation stays a reported gap. No Cursor runtime or local worker
is a substitute for those Work cloud observations.
