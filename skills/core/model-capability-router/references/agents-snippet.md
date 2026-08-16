# AGENTS.md Integration

Keep the instruction compact; the skill owns routing semantics and the preset
contains only operator-specific defaults and gates.

```md
For model, reasoning-effort, agent-role, or capability selection, use
`model-capability-router` with the nearest operator-approved routing preset.
Verify availability on the exact `current_task`, `spawn_agent`, or
`create_thread` channel before routing. Keep role separate from model/effort.
Distinguish delegated user-owned subtasks from independent parallel tasks.
Treat the bundled operator preset as the coherent baseline and external copies
as mirrors only when schema and checksum match; other bundled presets remain
examples until adopted. Native task creation and max or ultra require current
operator authorization. gstack is optional and owns workflow gates only when
explicitly invoked.
```

Do not duplicate the route algorithm in `AGENTS.md`. A project may use a nearer
approved preset when its runtime or proof bar is materially different.
