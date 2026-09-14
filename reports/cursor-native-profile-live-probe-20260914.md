# Native pstack profile probe — 2026-09-14

This is a bounded observation of native named subagents in the current Codex
host, not a fresh top-level task or a claim that the held pstack skills are
installed. The only input file was the disposable
`/private/tmp/native-profile-proof-20260914/total.js` (162 bytes, SHA-256
`7c7144933540ec7ab17fc4d2d60cfa74ab57a7da24bffff7f0848814e398e55b`).
It contains an SPDX license header, a redundant explanatory comment, and a
`total(values)` function.

| Boundary | Observed result | Limit |
| --- | --- | --- |
| Discovery and selection | This host's native `collaboration.spawn_agent` exposed and accepted `agent_type: comment-sicko` and `agent_type: poteto-agent`. Both were launched with `fork_turns: none` and returned to the coordinator. | No fresh top-level task was created. This does not establish discovery in every host or session. |
| `comment-sicko` instructions and execution | The named agent inspected only `total.js`, proposed deleting the redundant comment (count 1), kept the SPDX header, reported no `MUST KILL`, and named `cursor-how`/`cursor-why` as unnecessary. Those skill names were not in the brief; the behavior is consistent with its public TOML. | The agent's returned final text did not contain the profile's exact first-output marker `Yes... Ha ha ha... Yes!`. The host did not expose the raw injected instruction body or intermediate first message, so exact loading and complete compliance are unproven. No fix loop ran. |
| `poteto-agent` instructions and skill-file calls | The named agent reported reading the held preview's `cursor-poteto-mode/SKILL.md` in full, its `playbooks/eval.md`, `cursor-principle-prove-it-works/SKILL.md`, `cursor-unslop/SKILL.md`, the available `proof-orchestrator/SKILL.md`, and `total.js`. It selected Eval and returned the observed Bun result `{"input":[2,3,5],"output":10}`. The coordinator independently reran the same command and saw the same output. | These were explicit file reads through the agent, not proof of Codex's automatic skill trigger. `model-capability-router` was unavailable to that subagent as an installed skill; `cursor-deslop` was also absent but not needed for this read-only probe. No 23-playbook, sticky, cross-turn, cloud, or global-install parity is claimed. |

The coordinator rechecked the public profile assets with
`python3 scripts/check-native-agent-profiles.py --require-pinned-source --installed-dir /Users/vitorcepedalopes/.codex/agents`:
both installed files matched the public assets and both developer-instruction
bodies matched the pinned source after the exact documented adaptation. That
static check still reports `live_session_load: not_observed`; the native
subagent probes above are separate runtime evidence, not a modification of
the checker's contract. The fixture hash matched after the probes. Neither
agent modified the fixture or sent a network request.
