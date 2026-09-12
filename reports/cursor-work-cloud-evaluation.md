# ChatGPT Work Cloud as a possible orchestrate backend

Evaluation date: 2026-09-12. This is a contract review against the native
Codex task tools available in this session and current [Work getting-started],
[Work Cloud security] and [workspace model availability] documentation. No
Work Cloud task was created, and no repository content, credentials or private
data was sent to it.

[Work getting-started]: https://learn.chatgpt.com/docs/get-started-with-work
[Work Cloud security]: https://learn.chatgpt.com/docs/enterprise/chatgpt-work-cloud-security
[workspace model availability]: https://learn.chatgpt.com/docs/enterprise/workspace-model-availability

Work Cloud can continue when the desktop app is closed. The official docs also
say it does not inherit local files, apps, browser sessions or private-network
access; Work and Codex share a task-execution harness, but their tools,
permissions and administrative controls differ. Workspace model settings do
not automatically determine the model available in each Codex surface.

| Cursor orchestrate requirement | Exposed Work Cloud surface | Proof / gap |
| --- | --- | --- |
| Dispatch worker | Native `create_thread` advertises `chatgptWorkCloud`; model and thinking overrides are omitted for this target. | Schema evidence only. No task dispatched. No per-worker model/effort contract. |
| Read result and steer | `read_thread` and `send_message_to_thread` accept chats. | No demonstrated immutable handoff, complete stream, structured artifact or retry behavior. |
| Wait for completion | `wait_threads` explicitly targets Codex threads. | Do not pass a Work chat to it; no Work-specific wait contract was exposed. |
| Cancel and recover | Follow-up messages are exposed. | No exposed Work-specific interrupt/kill, idempotent retry or checkpoint contract. |
| Git, branch and isolation | Work Cloud receives intentionally supplied information and authorized connections, not the local checkout. | No branch/worktree/base-commit/writer-isolation/PR contract demonstrated. |
| Worker hierarchy and verifier | A Work chat can be created or messaged individually. | No child hierarchy, cross-judge or coordinator-controlled integration contract demonstrated. |
| Model, cost and permissions | Workspace plan, role, rollout and connected tools affect access. | API price tables cannot establish Work cost; model and permissions require effective readback on the target surface. |

A safe later PoC would use only a public or fully synthetic prompt with a
small literal input and a known answer. It would record dispatch identity,
observed model if exposed, output, artifact retrieval, a follow-up correction,
terminal state, failure behavior and a proven close/cancel path. It would test
Git and hierarchy separately, rather than inferring them from a successful
text task. The creation tool's contract permits a new task only when the user
explicitly asks for one; this evaluation did not interpret the mirror work as
authorization to create a separate Work task. No Work capability is promoted
for `orchestrate` until the missing contracts and a controlled run are proven.
