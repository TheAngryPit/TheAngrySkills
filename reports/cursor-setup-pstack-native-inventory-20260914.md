# `setup-pstack` native model inventory and role map

Date: 2026-09-14. Source pin: `cursor/plugins`
`889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`.

This is a read-only, current-channel mapping for the held
`cursor-setup-pstack` candidate. It does not configure a new default, switch
this task's model, update the installed router, or prove runtime role dispatch.

## Channel and authority

The current native turn context reports `gpt-5.6-sol` at `medium`. This task's
`collaboration.spawn_agent` contract advertises model overrides
`gpt-5.6-sol`, `gpt-6-astra`, `gpt-5.6-terra`, `gpt-5.6-luna`, and
`gpt-daybreak-blue-latest`. Sol/Astra/Terra expose low through ultra; Luna
exposes low through max; Daybreak exposes low through ultra. This is the
**subagent** channel inventory, not proof that a user-owned task or a ChatGPT
Work cloud task accepts the same choices. The `create_thread` tool documents a
different task palette that includes Spark; Spark is not advertised by this
subagent spawn surface. The exact available native tool schema is the
channel-specific source for this inventory.

The standing `model-capability-router` supplies the policy: Sol medium for
coordination, Astra low for normal planning/review, Astra medium for demanding
decisions, Astra xhigh exceptionally, Luna high for bounded subtasks, Luna
xhigh for defined execution and Luna max only when justified. Its current
installed `SKILL.md` and TheAngrySkills source have different hashes:
installed `061b66a25e3dc4e28a37a8f04a713101708aeece551a0729496698efce23f087`,
source in this reviewed clone `e2867ae60d8e2234681056543888c5b4ae2f9249158cf6bc1ecfa9982d1e33cb`.
The source adds native-agent profile distribution instructions; the routing
paragraphs are otherwise the same. No installation or home change was made.
Another local TheAngrySkills checkout now hashes its router source as
`2303be6127a66c480b8b89fd8b99ac9db9b824d81dd29c5d030d132a6103f3fe`;
it is a separate checkout, not evidence that this pinned branch or the installed
router changed. Reconcile the exact checkout before any future persistence or
installation decision.

## Candidate pstack mapping

The table covers every pinned source label. These are effective candidate
choices under the standing router for this subagent channel, not persisted
role settings. The native task brief may omit a model override for
`inherit-parent`/`auto` only when that channel supports inheritance.

| Source role label | Native candidate | Condition |
| --- | --- | --- |
| feature, refactoring | Luna xhigh | Defined implementation with owned scope. |
| bug-fix | Luna xhigh | Bounded repro, correction and verification. |
| perf-issue | Luna xhigh | Measurement and implementation scope specified. |
| hillclimb | Luna xhigh | Concrete iterative objective and stop rule. |
| judgment and prose | Astra low | Planning/review judgment; Sol medium can retain a tightly coupled task. |
| hardest tasks | Astra medium | Astra xhigh only for exceptional unresolved cases. |
| how explorer | Luna high | Narrow code/source exploration. |
| how explainer | Astra low | Independent explanation after exploration. |
| why investigators | Luna high | Separate bounded source slices when fan-out helps. |
| why synthesizer | Sol medium | Integrate evidence and qualify null sources. |
| reflect tooling | Luna high | Bounded tool-failure lens. |
| reflect judgment, divergent, synthesizer | Astra low | Distinct lenses require distinct task briefs even if model matches. |
| arena runners | `[Luna xhigh, Sol medium, Astra low, Terra medium]` | Four entries preserve default panel count; actual race needs independent artifacts. |
| arena cross-judge pool | `[Astra low, Luna high, Terra medium, Sol medium]` | Select a different model when possible; cross-provider family diversity is unavailable in this advertised palette. |
| swarm workers | Luna high | Override per race arm only when the explicit shape requires it. |
| architect runners | `[Astra low, Sol medium, Luna high, Terra medium]` | Four entries preserve source panel count; ownership and verification per runner. |
| interrogate reviewers | `[Astra low, Luna high, Sol medium, Terra medium]` | Four independent same-scope reviews, then coordinator synthesis. |

The dry-run fixture already checks the 17 labels, four panel lists, unavailable
model/effort, aliases, and malformed input with no write. This read-only pass
adds a live advertised **subagent** inventory and current main-task readback;
it does not connect that inventory to a persistent configuration file. A
source edit would still need an explicit requested policy change, a reviewed
diff and tests. A real installation would additionally need installed-byte
readback and new-session behavior proof. `cursor-setup-pstack` remains held.
