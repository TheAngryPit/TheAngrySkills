# pstack installed-cache and Codex mirror audit

Read-only comparison on 2026-09-14. Installed Cursor cache:
`~/.cursor/plugins/cache/cursor-public/pstack/68d834d9ca8f34c375ecb8057bfbcde5396a01f8`
(`.cursor-plugin/plugin.json` says 0.15.1). Mirror input:
`sources/cursor-plugins/snapshot/pstack/`, pinned to Cursor source commit
`889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`. Candidate output was
rendered with `sync-cursor-plugin-skills.py --preview-candidates`; published
output is in `skills/mirrors-cursor/`. A rendered instruction or source hash
is not evidence of native activation. Publication labels in the table record
this comparison checkpoint; the later bounded Architect promotion is recorded
in `pstack-architect-arena-native-20260914.md` and the current capability matrix.

All 47 top-level `skills/*/SKILL.md` IDs match. Forty-five top-level files
are byte-identical. Only `poteto-mode/SKILL.md` and
`setup-pstack/SKILL.md` differ, plus six nested poteto playbooks. The cache
contains 159 files and the skills-only pin 132; 27 cache-only files are plugin
metadata, README/logo, guides/images, and Benny automation documentation or
templates. There are no pin-only files. The two agent Markdown files are
byte-identical between cache and pin. These source-version differences are
separate from the Codex overlay changes below. The snapshot omits plugin
metadata, so its exact pstack release version is unknown.

The table uses the same source path pattern for every row:
`sources/cursor-plugins/snapshot/pstack/skills/<id>/SKILL.md`.
`same` means the installed and pinned top-level skill files match byte for
byte. `Published` means generated in the catalog; `held` means available
only in the review preview. No row claims a native selection or end-to-end run
from publication alone.

| Skill | Trigger, workflow and completion | Dependencies, model and agent route | Cache vs pin; Codex output and proof gap |
| --- | --- | --- | --- |
| architect | `/architect`; ground subsystem, sketch interfaces, implement, redesign if wrong. | `how`, `why`, `arena`, `interrogate`; three references and architect runners. | Same; held `cursor-architect`, bounded native runners specified; no live delegation or redesign proof. |
| arena | `/arena`; fan out N candidates, cross-judge, choose/graft, verify. | Configured model pool, cross-judge, isolated output paths. | Same; held `cursor-arena`; no actual parallel competition, cross-judge, or verified graft. |
| automate-me | History-to-personal-mode skill, with scoped preference synthesis. | Transcripts, native skill writer, `cursor-unslop`, history miners. | Same; held `cursor-automate-me`; paths adapted to Codex, transcript read and skill creation unproven. |
| blast-radius | Change-impact map ending in one load-bearing proof. | `how`, `why`, sometimes `arena`. | Same; published `cursor-blast-radius`; named sibling availability and actual impact proof untested. |
| bro | Restate the previous answer in plain language. | No specialist model or delegate required. | Same; published `cursor-bro`; native trigger/selection untested. |
| create-verification-skill | Create project-local `verify-*` skill with feature map, launch/doctor/drive/evidence/cleanup. | Target app and control surface; feature observations. | Same; held. Disposable notes CLI fixture captures subprocess results and evidence, but real target, full doctor and activation unproven. |
| figure-it-out | Select auditable workflow when no narrower playbook fits; converge on falsifiable done state. | `cursor-poteto-mode`, `cursor-architect`, `cursor-arena`, `cursor-show-me-your-work`, principles. | Same; held; generic fixture only, no end-to-end selection or completion proof. |
| how | Explain behavior, ownership, layers and runtime flow from source. | Separate explorers/explainer; source defaults Grok for explorer and Fable for explainer, subject to operator routing. | Same; held. Cursor Task/Glob/Grep/Read mapped to native bounded search; multi-reader and synthesis execution unproven. |
| interrogate | Adversarial multi-model diff review, quality check and lead judgment. | Four configurable reviewers, rubric/reviewer/quality/lead references. | Same; held; no live independent reviewer coverage, consensus, or lead judgment proof. |
| maintain-verification-skill | One read-only source scout per feature; coordinator alone drives live app; distinguish doc drift from product bug; retain evidence and cleanup. | Project `verify-*`, doctor and control surface; source-wave delegates. | Same; held. CLI fixture reconciles controlled drift and clean rerun; no source-wave, live target, changed-outcome PR or native activation. |
| make-bot-ui | Grok Bot webhook UI, sender-key handoff, local host and Tailscale exposure. | Real webhook, credential, host, Tailscale. | Same; security-held. No Codex equivalent or live webhook proof; heartbeat is not the webhook. |
| no-comments | Spawn Comment Sicko, parent checks report/diff, one rejected rerun, fixes accepted flags, architect sketch only for shape, optional constraint encoding gate. | Named `comment-sicko`; `cursor-how`, `cursor-why`, `cursor-architect` on their source branches. | Same; held. Native named-profile asset and exact source adaptation now exist, but fresh-session selection and the whole fix loop are unproven. |
| poteto-mode | Select one of 23 playbooks; conditional reminder; route named companions, delegates, proof and final reply. | Ordinary playbook helpers use `poteto-agent`; routed `how/why/interrogate/reflect/swarm` keep their own types. `cursor-deslop`, `cursor-control-cli`, `cursor-control-ui`, model router, proof orchestrator; Bun scripts. | One top-level wording drift; held. All 23 preview playbooks render, but sticky mode, cross-turn reuse, native agent selection, cloud, script/polling and live completion unproven. |
| recall | Reconstruct bounded task context and source-backed handoff. | Native thread/history access and `cursor-why` when rationale is needed. | Same; held; actual bounded history reconstruction and selection unproven. |
| reflect | Three transcript-review lenses, separate synthesizer, Accepted/Rejected/Backlog; ask approval before changing skills. | Judgment/tooling/divergent roles, MCP context access when available. Cursor `readonly:false` is an MCP workaround, not a Codex permission requirement. | Same; held with contextual security findings; no live transcript/reviewer/synthesizer or approved edit proof. |
| setup-pstack | Detect available models, preserve per-role override map/fanout/cross-judge, validate then write configuration. | Native model router and explicit operator selection; `auto`/`inherit-parent` omit model override. | Installed defaults for bug-fix/perf-issue/hillclimb are Fable; pin defaults are Grok. Held preview maps to Codex config; live inventory/config proof absent. Do not silently choose one source default over standing routing. |
| show-me-your-work | TSV decision trail, transcript audit and cross-review before handoff. | Local `scripts/log.sh`, TSV template, independent reviewer. | Same; held due executable writer review; no full writer/history/reviewer proof. |
| swarm | N workers, bounded drain, aggregate PASS/ISSUES/BLOCKED. | Configured worker model; cloud default, local for access to user's computer; N distinct from concurrency; remote branch/race policy. | Same; held; no actual N-way fanout, cloud/local routing, branch race or aggregation proof. |
| why | Seven evidence categories with separate investigators and synthesizer, visible empty/skipped sources, confidence-separated rationale. | Git/history plus authorized issue/docs/chat/observability/errors/analytics connectors; role-specific models. | Same; held with connector finding. Read-only native inventory is specified; category coverage, MCP authorization, investigator/synthesis execution unproven. |
| principle-attack-the-premise | Repeated fixes share a premise: census actors and redesign premise. | No required delegate. | Same; published; selection/application unproven. |
| principle-boundary-discipline | At external boundaries, parse/validate; trust internal types. | No required delegate. | Same; published; selection/application unproven. |
| principle-build-the-lever | Non-trivial repeated work: build rerunnable script/codemod/skill. | Delegate only if task warrants it. | Same; published guide; lever creation unproven. |
| principle-encode-lessons-in-structure | Repeated instruction: encode as lint/metadata/runtime check. | No required delegate. | Same; published; application unproven. |
| principle-exhaust-the-design-space | Novel UI/design: compare competing prototypes. | Independent variants as needed. | Same; published; prototype comparison unproven. |
| principle-experience-first | Product/UX tradeoff: optimize a focused usable experience. | No required delegate. | Same; published; application unproven. |
| principle-fix-root-causes | Debug: reproduce, trace mechanism, fix at source. | No required delegate. | Same; published; application unproven. |
| principle-foundational-thinking | Before state/logic/concurrency: define authoritative domain shape. | No required delegate. | Same; published; application unproven. |
| principle-guard-the-context-window | Large context: route bulk to bounded agents, retain pointers. | Native delegates when justified. | Same; published guide; actual context/routing effect unproven. |
| principle-laziness-protocol | Refactor temptation: delete dead weight, choose smallest change. | No required delegate. | Same; published guide; destructive boundaries still follow native permissions. |
| principle-make-operations-idempotent | Lifecycle/retry: converge after partial reruns. | No required delegate. | Same; published; application unproven. |
| principle-migrate-callers-then-delete-legacy-apis | Internal API replacement: migrate callers and remove legacy path. | No required delegate. | Same; published; application unproven. |
| principle-minimize-reader-load | Hard-to-trace code: remove needless wrappers/state. | References `principle-guard-the-context-window`. | Same; published; application unproven. |
| principle-model-the-domain | Stateful branch shapes: encode states in structures. | No required delegate. | Same; published; application unproven. |
| principle-never-block-on-the-human | Reversible work: act; reserve approval for actual gates. | No required delegate. | Same; published; application unproven. |
| principle-outcome-oriented-execution | Planned rewrite/migration: phase toward target architecture. | No required delegate. | Same; published; application unproven. |
| principle-prove-it-works | Before completion: run real artifact and inspect result. | Surface-specific control/proof. | Same; published guide; live result must be shown for each use. |
| principle-redesign-from-first-principles | New requirement crosses design: rederive from first principles. | No required delegate. | Same; published; application unproven. |
| principle-separate-before-serializing-shared-state | Shared-state concurrency: remove sharing before locks. | No required delegate. | Same; published; application unproven. |
| principle-sequence-verifiable-units | Migration/sweep: each unit ends with proof. | No required delegate. | Same; published; application unproven. |
| principle-subtract-before-you-add | Addition/refactor: remove stale paths first. | No required delegate. | Same; published; application unproven. |
| principle-test-behavior-not-implementation | Tests: call user path and assert literal result. | No required delegate. | Same; published; application unproven. |
| principle-type-system-discipline | Typed design: illegal states unrepresentable; parse external data. | No required delegate. | Same; published; application unproven. |
| tdd | Explicit TDD/cheap regression: red, fix, green, nearby validation. | No required delegate. | Same; published; native trigger and live behavior unproven. |
| teach | Teaching request: use how and why, then explain incrementally. | `cursor-how` and `cursor-why` required. | Same; published; companion execution unproven. |
| technical-writing | Docs/RFC/README/PR/commit: apply layered style and `unslop` to every touched document. | Published `cursor-unslop` is required, not optional. | Same; published. Overlay previously weakened dependency; corrected in this branch. Combined workflow/trigger unproven. |
| typescript-best-practices | Any TS/TSX read/edit; apply type and boundary principles and patterns. | `cursor-principle-type-system-discipline`, `cursor-principle-boundary-discipline`, bundled `references/patterns.md`. | Same; published. Principle names corrected in this branch; live path-based trigger unproven. |
| unslop | Any writing: remove filler, AI tells and vague prose. | No required delegate. | Same; published; automatic application unproven. |

Nested source drift is bounded. Installed `bug-fix`, `hillclimb`, and
`perf-issue` playbooks change delegate defaults from pinned Grok to Fable.
`autopilot-full`, `autopilot-stack`, and `multi-phase-plan` change
operator pronouns; the latter also changes a tick from posting in chat to
sending the operator a status message. The pin remains unchanged. The
installed model defaults are not an operator choice for Codex; the standing
model-capability-router and explicit task selections govern native routing.

The cache-only `docs/guide/`, plugin metadata, README/logo, and Benny
automation docs are outside this skills-only pinned snapshot. The three
nested Benny skills remain source-dormant, not part of the 47 active pstack
skills or the published catalog. The upstream agent source hashes are
`comment-sicko.md` `c0fd0383008da45fc78cfac17b9007d62c42f87ad1c8d5c2fb658b1fd01f7c82`
and `poteto-agent.md` `c3850be1b97bc97cec0568ed8b26d04e7693c4e07868137c58fe546d37f288e9`.

The repo's 169 tests plus 2 subtests, mirror `--check` at 91/54/167, and
the pstack Bun 52/52/typecheck are existing bounded evidence for the current
draft. They do not prove 47 native workflows. The live proof queue is the
named-agent selection and no-comments loop, poteto playbook routing,
how/why evidence delegation, arena/interrogate reviewers, verification
source-wave and target control, and the remaining external/cloud/script
surfaces. Keep all held and security-gated states visible until each named
behavior is exercised.
