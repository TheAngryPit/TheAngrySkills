# Agent-loop conversion batch

Date: 2026-09-15

This batch revisits the five selected Cursor sources below from the pinned
snapshot. It records bounded Codex adaptations and their observable checks; it
does not claim Cursor runtime equivalence or automatic hook activation.

| Published skill | Pinned source | Source SHA-256 | Current decision |
| --- | --- | --- | --- |
| `cursor-advisor` | `advisor/skills/advisor/SKILL.md` | `e34d52a0f9948057ac754151b2e116db47205674418de0548cd9df4477f52bf8` | Retain conditional; trusted hook, live advisor role and native consult are unproven |
| `cursor-continual-learning` | `continual-learning/skills/continual-learning/SKILL.md` | `f627f733a33879b63523da7e92c8b33e6086df42a49a8139a87d1c21e7bd9b16` | Retain conditional; trusted hook, real transcript scope and live updater are unproven |
| `cursor-orchestrate` | `orchestrate/skills/orchestrate/SKILL.md` | `a56718f3acf4bbc13e44ca7b8e00d499e818fb16ee293bbe3d58621968c28e22` | Retain held; Work tree fan-out/drain/artifact/cancel/recovery are unproven and bundled scripts are security-held |
| `cursor-ralph-loop` | `ralph-loop/skills/ralph-loop/SKILL.md` | `3583d0868329b2b1a0f081cd7d0d1ef51cf5a12696e407edbc6b8cdca41f8a09` | Retain conditional; trusted Stop hook and live continuation are unproven |
| `cursor-cancel-ralph` | `ralph-loop/skills/cancel-ralph/SKILL.md` | `5824c5344af837c1cc56659d362124f75bdc1460ae66bf616e592fb2d8e8ea43` | Retain conditional; live task/session state and cancellation readback are unproven |

## Adaptation and proof

The existing native adapter at `scripts/cursor_native_hook_adapters.py` remains
the only runtime support surface for advisor, continual-learning and Ralph
state. It is inactive until a project hook is separately installed and trusted.
The fixture wrapper at `scripts/cursor_hooks_loops_adapters.py` keeps all test
state inside a caller-owned temporary project.

The adapter now validates the project path before any state operation and rejects
symlink components, including `/project-alias`. It validates an explicitly
supplied continual-learning transcript root and rejects symlinked transcript
components before inspecting metadata. Ralph cancellation continues to remove
only the matching state file; it never follows the upstream recursive
`.cursor/ralph` deletion instruction.

The focused observable test pass was:

```text
pytest -q tests/test_cursor_native_hooks.py tests/test_cursor_hooks_loops_adapters.py
21 passed in 2.40s
```

The new CLI cases exercise a symlinked project rejection with no `.codex` state
written and a symlinked transcript-root rejection with no outside files read or
changed. Existing cases continue to exercise task/session binding, advisor
identity and verdict checks, Ralph continuation/max/promise/cancellation, and
continual-learning turn/time/mtime/duplicate boundaries.

The existing bounded updater role fixture remains the only learning write proof:
it mines a synthetic single-transcript fixture, updates fixture `AGENTS.md` and
its index, then produces no update on an unchanged-mtime second pass. It does
not read a real transcript or edit the workspace `AGENTS.md`.

`cursor-orchestrate` has no safe local runtime added in this batch. Its overlay
continues to map the explicit root request to native Work task creation and
readback where that surface exists, while requiring separate proof for child
dispatch, drain, structured handoffs, Git artifacts, cancellation and recovery.
The bundled Cursor SDK/Slack scripts remain outside the adapter path and were
not installed or executed.

## Exact gaps and viable next proof

| Skill | Missing native operation | Viable next action |
| --- | --- | --- |
| `cursor-advisor` | Trusted project hook, native read-only named advisor invocation and role/verdict correlation | Run one explicitly authorized read-only different-role/model consult in a disposable task, bind the returned task/agent ID, and verify the verdict readback |
| `cursor-continual-learning` | Trusted Stop hook, verified current-task transcript source and live updater delegation | Supply one explicitly scoped transcript and delegate extraction to the bounded updater; review a proposed `AGENTS.md` diff before any write |
| `cursor-orchestrate` | Work-compatible child fan-out/drain, artifact identity, cancellation and recovery | Request a bounded native Work tree proof only if the destination exposes those operations; otherwise keep the conditional plan-only path |
| `cursor-ralph-loop` | Trusted project Stop hook and automatic follow-up/continuation readback | Exercise a disposable task with an explicitly trusted hook, a finite max iteration and a completion promise, then verify cancellation |
| `cursor-cancel-ralph` | Live task/session state correlation and terminal cancellation readback | Cancel only the matching disposable child and verify its terminal status; an unknown session must remain a no-op |

No global installation, credential use, external provider, Cursor SDK request,
Work cloud tree, hook registration/trust change, PR or merge was performed by
this batch.
