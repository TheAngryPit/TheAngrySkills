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
| `pstack/skills/no-comments/SKILL.md`, step 1, published as `cursor-no-comments` | no-comments review request | named `comment-sicko` | Parent-scoped files or diff; if absent, current diff against `main`; the profile's rules are not rewritten into the prompt | Reuse an existing suitable named reviewer when available; otherwise invoke the named profile once for the bounded review | Native bounded delegation may be asynchronous; the coordinator receives the report and owns integration | Current task's bounded delegate result; no application-code mutation by the reviewer |
| `cursor-no-comments`, steps 2-5 | report review, accepted finding, one rerun, optional architecture sketch | coordinator plus `cursor-how`, `cursor-why`, or `cursor-architect` as named sibling skills | Exact symbol/call, rejected finding, accepted scope, or constraint-encoding approval gate | One rerun after rejection; `cursor-architect` is a sketch only when the accepted set crosses a shape boundary | Return report/diff for coordinator review; a second rejection fails the flow | Coordinator's current task and explicitly assigned files |
| `pstack/skills/poteto-mode/SKILL.md`, Subagents section | a playbook needs a code-writing or bounded helper delegate | named `poteto-agent` | Full bounded brief, file pointers, selected model/effort, ownership and proof contract; no inlined bulk | Reuse the existing `poteto-agent` conversation; start a named one only when no suitable instance exists | Native asynchronous delegation replaces Cursor `is_background`; coordinator drains and reviews the result | Current task's native delegate result, with coordinator authority retained |
| `cursor-poteto-mode/playbooks/multi-phase-plan.md` and other playbooks | playbook-specific exploration or execution step | `poteto-agent` for ordinary playbook delegates | Playbook step, exact paths, conventions, tests and entry points; the selected leaf `cursor-principle-*` is read when applied | Reuse within the bounded conversation; after an interrupt-chained resume, start a fresh consolidated delegate rather than trusting a dropped directive | Native return to the coordinator; no recursive delegation is implied by the profile | Current task, selected project/worktree, and the coordinator's proof ledger |
| Routed `cursor-how`, `cursor-why`, `cursor-interrogate`, `cursor-reflect`, `cursor-swarm`, and `cursor-arena` paths | their own trigger, not generic poteto style | Their own bounded explorer, evidence, reviewer, candidate or cross-judge contract | Keep their role-specific payload, file pointers, reviewer count, cross-judge family and evidence category | Do not flatten these routes into `poteto-agent`; reuse only where that skill's contract permits | Native parallelism is conditional on host capability; missing delegates are labeled, not fabricated | Their caller's current task and declared output surface |
| `cursor-setup-pstack` | role/model override request | model-capability-router's selected native models and efforts | Operator-selected role map, detected availability, panel fan-out, `inherit-parent`/`auto` aliases and cross-judge family rule | Preserve explicit selections; do not replace a configured role with a default profile | Selection/configuration is returned as a bounded plan or approved config change; no automatic profile activation | Explicit project/global destination only after the workflow's approval gate |

The matrix describes routing contracts and output destinations. A separate
[bounded probe](../reports/cursor-native-profile-live-probe-20260914.md)
observed two native named delegates returning in this host; it did not exercise
the full matrix, background completion, or top-level task profile loading.

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
