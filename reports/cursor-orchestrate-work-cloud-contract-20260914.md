# `cursor-orchestrate` → ChatGPT Work cloud contract

Date: 2026-09-14. Source pin: `cursor/plugins` commit
`889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`. PR #64 review base:
`f0d54a94baa6b2f9074fe90e066d5bb3f55ca2db`.

The operator selected ChatGPT Work cloud as the desired cloud destination for
the Codex adaptation. This is a target contract, not a claim that the Cursor
SDK runtime has been replaced or that a Work cloud tree has run. The source
skill remains pinned and unpublished.

## Source behavior and native surface

The pinned `orchestrate` skill is explicit-only. Its dispatcher takes a goal,
launches one Cursor cloud root planner through `scripts/cli.ts kickoff`,
returns an agent URL, and stops. The planner writes `plan.json`, launches
isolated workers/subplanners/verifiers, reads one structured handoff per task,
and iterates from `state.json` and `handoffs/*.md`. It also defines recovery,
cancellation, optional Slack visibility, branch/PR artifacts and git-backed
state. These are requirements, not generic words for parallel delegation.

Current native Codex app tool contracts expose the following partial mapping:

| Source operation | Available Work cloud surface | Proof / limit |
| --- | --- | --- |
| Explicit goal and root dispatch | `create_thread` accepts `target.type: chatgptWorkCloud` and a user-visible prompt, optionally a ChatGPT project ID. | Tool contract exists; no Work cloud root was created in this lot. Creation is for an explicitly requested new task, not an implicit subagent spawn. |
| Task status and handoff | `list_threads` lists chats/tasks; `read_thread` reads recent turns of a task or chat; `send_message_to_thread` continues one. | Read/list tools were observed for existing tasks. A structured Work handoff, cursor/resume, and terminal status have not been demonstrated. |
| Wait/drain | `wait_threads` is documented for Codex threads, while ChatGPT Work cloud creates a ChatGPT Work task. | No documented Work-cloud wait/drain equivalent in the available surface; do not assume `wait_threads` accepts it. |
| Worker/subplanner/verifier fan-out | The local `collaboration.spawn_agent` supports bounded parallel subagents in this Codex task; `create_thread` creates separate user-owned tasks. | Local subagents are not Work cloud workers. No Work-cloud child-task API, isolation, dependency gate or recursive planner contract is exposed here. |
| Artifact/PR and repository state | Work cloud creation accepts an optional ChatGPT project ID; available saved ChatGPT projects do not include a TheAngrySkills repository project. | No repo checkout, branch, Git artifact, `plan.json`/`state.json` sync or PR behavior is evidenced for Work tasks. A link to a task is not a branch or artifact receipt. |
| Cancel/recover/Andon | `send_message_to_thread` can send a follow-up; `set_thread_archived` is an archive operation for Codex tasks. | Neither is documented as Work-cloud cancellation. Restart attachment, descendant cancellation and Andon state are unproved. |
| Optional Slack visibility | Slack connector exists separately. | No operator request to message Slack in this lot; no Slack write, channel mirror or reaction polling occurred. |

An earlier `create_thread` attempt was rejected before task creation because
the specific Work task was not yet authorized. Vítor later explicitly approved
one narrower projectless proof using only two synthetic records (`alpha` and
`beta`) and at most one child. The authorized creation call was made exactly
once and returned provisional client ID
`local-chatgpt:a146a047-7138-4d84-ba2b-6e7d6824e555`, but no definitive
`threadId` or host. Task listing first found no matching task and then blocked.
Pending list calls were cancelled and creation was not retried. No result,
child, handoff, artifact, cancellation or recovery became observable, so the
post-acceptance Work execution state remains unknown.

## Adapter admission gates

1. Preserve explicit-only invocation. Capture the verbatim user goal, the
   selected Work destination, repository/project context, constraints, model
   selection and an output predicate. Never infer a repository from this
   local checkout for a remote Work task.
2. Before dispatch, make a reviewable plan with stable task IDs, dependencies,
   ownership, verifier criteria, artifact paths and a recovery policy. Keep a
   planner separate from coding workers as the pinned source requires.
3. Dispatch only through a documented Work cloud creation surface. Record
   returned task ID/URL and host; do not pass a queued `clientThreadId` to
   tools that require a ready `threadId`.
4. Treat every child outcome as a structured handoff with `PASS`, `ISSUES` or
   `BLOCKED`, evidence, branch/artifact identity and remaining gaps. Drain only
   through an observed Work-compatible status mechanism; no guessed polling.
5. On failure, preserve last confirmed state and ask the operator for a
   specific recovery decision when no native cancel/recover primitive exists.
   Archive is not cancellation. Merge, publish and Slack writes remain
   separate actions with their own authorization.

The current API surface documents creation and the authorized attempt proves
only provisional request acceptance. It does not prove definitive task
creation or Work read/list behavior. This does not meet the source's tree,
handoff, artifact, cancellation and recovery bar. `cursor-orchestrate` remains
held. The next safe action is reconciliation from the preserved client ID when
the native surface can resolve it. Do not create another task unless the
existing request is first proved to have failed without creating one. No
Cursor credentials or bundled scripts are needed for the Work lane.
