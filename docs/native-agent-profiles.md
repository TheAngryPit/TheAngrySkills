# Native pstack agent profiles

The public distribution root for native named-agent profiles is
`skills/core/model-capability-router/assets/agents/`. It is the existing
asset convention for the router's global profiles. The two pstack profiles are
adapted TOML assets, not copied Markdown sources:

| Profile | Native invocation point | Pinned source | Required companion surface |
| --- | --- | --- | --- |
| `comment-sicko` | `cursor-no-comments` | `sources/cursor-plugins/snapshot/pstack/agents/comment-sicko.md` | `cursor-how`, `cursor-why`; `cursor-architect` only for the accepted sketch gate |
| `poteto-agent` | `cursor-poteto-mode` playbook delegation | `sources/cursor-plugins/snapshot/pstack/agents/poteto-agent.md` | `cursor-poteto-mode`, the selected `cursor-principle-*` leaf, and native bounded delegation |

The assets preserve the pinned role bodies and adapt only the host-facing
names and routing language. The source Markdown remains in the pinned Cursor
snapshot. No second role copy is placed in the generated Cursor workbench.

## Explicit distribution and loading

Installing `model-capability-router` distributes the assets; it does not imply
that Codex has loaded them. Use the checked, explicit copy path from the repo
root:

```bash
python3 scripts/check-native-agent-profiles.py \
  --install --installed-dir ~/.codex/agents
```

The installer refuses a differing existing profile unless `--replace` is
provided. A read-only installed-state check is:

```bash
python3 scripts/check-native-agent-profiles.py \
  --installed-dir ~/.codex/agents
```

The checker proves TOML syntax, profile names, source-grounded semantic
anchors, absence of Cursor `subagent_type`/`generalPurpose` syntax, and the
installed byte match when a target directory is supplied. If the pinned source
files are available through `--pinned-source-root`, it also compares the
developer-instruction body against the exact normalized adaptation and checks
the reviewed source hash. Without that source root, the comparison is
explicitly `not_observed`, not a claim of equivalence. It cannot prove that a
fresh Codex session loaded or selected the profile; that remains a host session
check. Availability of companion skills and native delegation is also
host-dependent.

A read-only check of `codex-cli 0.154.0` help and the top-level task-tool schemas
found no named-agent selector. `codex --profile` selects a configuration
profile; `codex agents` browses sessions. The top-level task tools expose model
and effort overrides, but no agent-profile field. In this host, the separate
native `collaboration.spawn_agent` surface exposed both named types and a
[bounded runtime probe](../reports/cursor-native-profile-live-probe-20260914.md)
returned from each. This does not establish fresh top-level task loading or
automatic skill invocation.

## Invocation matrix

| Upstream/adapted reference | Trigger | Native agent type | Payload and context | Reuse/spawn | Async and return | Codex destination |
| --- | --- | --- | --- | --- | --- | --- |
| `pstack/skills/no-comments/SKILL.md`, step 1, adapted as `cursor-no-comments` | no-comments review request | exact `agent_type: "comment-sicko"` through `collaboration.spawn_agent` | Parent-scoped files or diff; if absent, current diff against `main`; the profile's rules are not rewritten into the prompt | Spawn a fresh named reviewer for the bounded review; no generic-agent substitution | Native bounded delegation may be asynchronous; the coordinator receives the report and owns integration | Current task's bounded delegate result; no application-code mutation by the reviewer |
| `cursor-no-comments`, steps 2-5 | report review, accepted finding, one rerun, optional architecture sketch | coordinator plus `cursor-how`, `cursor-why`, or `cursor-architect` as named sibling skills | Exact symbol/call, rejected finding, accepted scope, or constraint-encoding approval gate | One rerun after rejection; `cursor-architect` is a sketch only when the accepted set crosses a shape boundary | Return report/diff for coordinator review; a second rejection fails the flow | Coordinator's current task and explicitly assigned files |
| `pstack/skills/poteto-mode/SKILL.md`, Subagents section | a playbook needs a code-writing or bounded helper delegate | exact `agent_type: "poteto-agent"` through `collaboration.spawn_agent` | Full bounded brief, file pointers, selected model/effort, ownership and proof contract; no inlined bulk | Reuse the existing `poteto-agent` conversation through `collaboration.followup_task`; start a named one only when no suitable instance exists | Native asynchronous delegation replaces Cursor `is_background`; coordinator drains and reviews the result | Current task's native delegate result, with coordinator authority retained |
| `cursor-poteto-mode/playbooks/multi-phase-plan.md` and other playbooks | playbook-specific exploration or execution step | `agent_type: "poteto-agent"` for ordinary playbook delegates | Playbook step, exact paths, conventions, tests and entry points; the selected leaf `cursor-principle-*` is read when applied | Reuse within the bounded conversation through `collaboration.followup_task`; after an interrupt-chained resume drops directives, start a fresh named delegate with a consolidated brief | Native return to the coordinator; no recursive delegation is implied by the profile | Current task, selected project/worktree, and the coordinator's proof ledger |
| Routed `cursor-how`, `cursor-why`, `cursor-interrogate`, `cursor-reflect`, `cursor-swarm`, and `cursor-arena` paths | their own trigger, not generic poteto style | Their own bounded explorer, evidence, reviewer, candidate or cross-judge contract | Keep their role-specific payload, file pointers, reviewer count, cross-judge family and evidence category | Do not flatten these routes into `poteto-agent`; reuse only where that skill's contract permits | Native parallelism is conditional on host capability; missing delegates are labeled, not fabricated | Their caller's current task and declared output surface |
| `cursor-setup-pstack` | role/model override request | model-capability-router's selected native models and efforts | Operator-selected role map, detected availability, panel fan-out, `inherit-parent`/`auto` aliases and cross-judge family rule | Preserve explicit selections; do not replace a configured role with a default profile | Selection/configuration is returned as a bounded plan or approved config change; no automatic profile activation | Explicit project/global destination only after the workflow's approval gate |

The matrix describes routing contracts and output destinations. A separate
[bounded probe](../reports/cursor-native-profile-live-probe-20260914.md)
observed two native named delegates returning in this host; it did not exercise
the full matrix, background completion, or top-level task profile loading.

## Orientation and conditional sources

The named profiles carry decision rules, not just personas. The pinned files
below are the source; the generated held skill and public TOML are the Codex
entry and role. Read only the source required by the selected workflow.
An exact-name scan of the pinned pstack snapshot finds five files with
`Comment Sicko`, `comment-sicko`, or `poteto-agent`: the two agent Markdown
sources, `no-comments/SKILL.md`, `poteto-mode/SKILL.md`, and
`poteto-mode/playbooks/multi-phase-plan.md`. The latter three invocation
references are all mapped above; other routed workflows use their own source
roles.

| Workflow | Pinned orientation and payload | Codex resolution | Observation and remaining gap |
| --- | --- | --- | --- |
| `cursor-no-comments` | `pstack/agents/comment-sicko.md` gives the legal/API/foreign-behavior exceptions, `MUST KILL` flags, suppression handling and the ban on application-code edits. `pstack/skills/no-comments/SKILL.md` gives coordinator review, one rejected-report rerun, optional architect sketch and constraint-encoding gate. | Generated Step 1 calls `agent_type: "comment-sicko"`; the TOML is byte-matched to the installed native profile. Read `cursor-how`/`cursor-why` for an ambiguous thin constraint, and `cursor-architect` only for an accepted shape fix. | [Read-and-dispatch receipt](../reports/cursor-no-comments-role-fixture.md) observed the generated Step 1, named reviewer, accepted deletion and syntax/runtime readback. No ambiguous branch, rerun, encoding, automatic trigger or model/effort metadata. |
| `cursor-poteto-mode` | `pstack/agents/poteto-agent.md` requires the full mode skill and Principles index. The mode skill supplies 23 playbooks, delegation/reuse, writing and verification rules, and conditional `cursor-deslop`, `cursor-control-cli`, `cursor-control-ui`, `proof-orchestrator` and `model-capability-router` routing. | Generated mode and `multi-phase-plan.md` name `agent_type: "poteto-agent"` and `collaboration.followup_task`; selected playbook and applied `cursor-principle-*` leaf are read by path. Routed `how`/`why`/`interrogate`/`reflect`/`swarm` keep their own roles. | Existing named agent was reused for a read-only Investigation of `cursor-setup-pstack`; it reported reading the full generated skill and selected playbook, and cited the previously read `cursor-principle-prove-it-works` leaf. Exact file reads inside its runtime are agent-reported, not independently exposed tool metadata. Full 23-playbook execution and automatic trigger remain open. |
| `cursor-setup-pstack` | Pinned setup skill supplies 17 labels, four panel lists, alias and cross-judge rules; these are configuration semantics, not a second model policy. | Candidate mapping checks the exact native channel and defers model/effort authority to `model-capability-router`. The task brief can carry a scoped choice; persistent source changes need diff and readback. | Fixture confirms labels/panel counts/no-write errors. This task selected named roles, but did not apply a persisted per-role setup map or prove all panel dispatch; user-owned-task and Work channels remain separate. |
| `cursor-how`, `cursor-why` | Pinned skills use generic explorers/investigators and evidence-specific synthesis, with `why` covering seven source categories and null results. | Their adapted skills resolve their own bounded explorer/evidence roles under the router; neither is replaced with `poteto-agent`. | Bounded local cases exist in their reports; named-profile requirements do not apply to these source routes. Connector coverage and automatic trigger remain conditional. |
| `cursor-interrogate`, `cursor-reflect` | Interrogate passes one identical rubric to each configured reviewer; Reflect uses judgment/tooling/divergent templates and a separate synthesizer. | Native delegates keep independent scopes and templates; actual model identity must come from host metadata. No generic-to-poteto substitution. | [Interrogate proof](../reports/pstack-interrogate-native-20260914.md) covers two same-scope reviewers, distinct requested profiles, separate outputs, synthesis and no auto-apply. Effective backend model metadata remains open. [Reflect fixture](../reports/cursor-reflect-disposable-20260914.md) covers three read-only lenses, separate synthesis and no auto-edit on a scoped disposable transcript; live history selection remains open. |
| `cursor-swarm`, `cursor-arena`, `cursor-architect` | Swarm uses partition/race and four phases; Arena uses isolated candidates, a cross-judge, graft and verification; Architect grounds with `how`/`why` and tests a sketch. | Each adapted skill owns its worker/candidate/design contract. A poteto style wrapper does not change its delegate type, count or ownership. | Local Swarm, Arena and Architect cases are bounded and published; [Arena/Architect receipt](../reports/pstack-architect-arena-native-20260914.md) records a prospective Architect how/why Ground before two design candidates, an independent judge, graft and disposable verification. Work cloud, automatic selection, production parity and authoritative worker model readback remain unproven. |

The checker returned `PASS` with pinned-source hashes and installed-byte match
for both TOML assets in this home. The native subagent tool exposed both exact
agent types and accepted both; its result does not expose authoritative
model/effort or prove picker activation in a fresh user-owned task. A profile
or adapted skill absent from a target host is an explicit gap, not permission
to replace it with a generic worker or copy its instructions into a prompt.

## Provenance and audit commands

Run the profile checker and the relevant repository tests from the repository
root:

```bash
python3 scripts/check-native-agent-profiles.py \
  --installed-dir ~/.codex/agents
python3 -m unittest -q tests.test_native_agent_profiles
python3 -m unittest -q tests.test_cursor_pstack_core.CursorPstackCoreTests.test_verification_cli_fixture_runs_doctor_captures_evidence_and_reconciles_drift
```

The checker records the SHA-256 of each public asset and the reviewed pinned
Markdown source. It does not update the pinned source, alter Cursor's cache, or
claim that the installed cache is current. The two pstack agent Markdown files
are vendored under `sources/cursor-plugins/snapshot/pstack/agents/`. Pass
`--pinned-source-root sources/cursor-plugins/snapshot/pstack` or use
`--require-pinned-source` for the exact body comparison.
