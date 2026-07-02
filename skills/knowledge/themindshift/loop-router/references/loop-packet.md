# Loop Packet

Every routing result must produce this packet.

```text
classification: manual_gate | same_thread_heartbeat | fresh_scheduled_task | delegated_worker | blocked
issue_id:
current_gate:
current_state:
blockers:
next_loop:
next_artifact:
source_files:
output_target:
proof_bar:
handback_format:
stop_condition:
next_action:
```

## Field Rules

- `classification`: choose exactly one allowed value.
- `issue_id`: name the active issue or say `none`.
- `current_gate`: name the active human gate or say `none`.
- `current_state`: summarize the inspected project state in one or two lines.
- `blockers`: list only real blockers.
- `next_loop`: name the loop that should run next or say `none`.
- `next_artifact`: name the artifact that should be produced next.
- `source_files`: list the files that support the routing decision.
- `output_target`: name the file, folder, or artifact path the next loop should produce.
- `proof_bar`: state the validation level needed for the next action.
- `handback_format`: define what the delegated worker or loop must return.
- `stop_condition`: define when the heartbeat, task, or delegated worker should stop.
- `next_action`: one concrete next action.

If any field is unknown and materially affects routing, use `blocked` and name the missing information.
