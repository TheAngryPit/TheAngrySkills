# Add runtime support without replacing the Cursor adaptation

Status: proposed design, awaiting operator approval before implementation.

## Intent

Vítor selected improving TheAngrySkills' existing Cursor adaptations rather than replacing them with a third-party T3 port. Each addition must compound the existing work: preserve native Codex behavior, names, source provenance, proof requirements and automation, while adding a verified T3 execution path. Hermes and OpenClaw are subsequent runtime adapters, not implementations or compatibility claims in this change.

The target is a maintainable, reusable pstack adaptation. Being the de facto adaptation is an ambition, not an acceptance test or a claim of universal support.

## Verified baseline

- Repository main: `ecd94d59f67ad39c33f53a88b04a4c9d092cde4b`.
- Cursor inventory: 112 physical entries, 107 published skills, five held adaptations and 14 mapped source agents. The pstack source family is pinned at `d457567332aa6989e753ea289f30ea2bfbc80bc0` (0.15.28).
- `sources/cursor-plugins/snapshot/` and its ledgers preserve reviewed upstream content. Per-skill JSON overlays are authored input. `scripts/sync-cursor-plugin-skills.py` generates `skills/mirrors-cursor/`, the state ledger and the Cursor marketplace entry. Generated output must not be edited by hand.
- The renderer presently supports `codex_note`, `codex_native_body`, exact replacements, reviewed support-file bundling and native profile assets. It checks source hashes, safe paths and unexpected local output changes before replacement.
- The installed `cursor-poteto-mode` body matches this canonical source. Its contracts are native Codex contracts; this does not establish provider-neutral T3 orchestration.
- Existing adaptation checks pass. Previous focused checks passed seven setup and 19 core tests. Fresh automation tests passed 49 cases across `test_upstream_pr_automation.py`, `test_adapted_upstream_watch.py` and `test_cursor_addition_detector.py` using pytest 9.1.1. An initial unittest invocation collected zero pytest-style cases and was not counted as a pass.
- The full unchanged repository baseline passed: 424 tests passed, two skipped and 13 subtests passed in 57.30 seconds. This is pre-implementation evidence, not proof that the proposed adapter works.

## Existing automation and ownership

| Lane | Current behavior that must survive |
| --- | --- |
| Adapted upstream detector | `review-matt-cursor-upstreams.yml`, scheduled and manually dispatchable, calls `detect-upstream-updates.py` for Matt and Cursor/pstack. Creates or updates one evidence-only PR per family/batch; it does not promote a pin or regenerate/install a skill. |
| Reviewed adaptation work | Existing source/overlay/pin changes remain reviewable on the appropriate branch. Historical `@codex update`, execution-candidate syntax, connector receipt, actual task execution and delivery are distinct proof levels. No new agent trigger is introduced here. |
| Finalizer | Explicit manual dispatch, exact expected adaptation SHA and reviewed-ready confirmation. Trusted control code, canonical branch/family checks, reviewed manifest/generated output, authenticated exact-head review and explicit CI precede the bot readiness record and protected auto-merge path. No recorded live run was found during this audit. |
| Curated mirror refresh | `sync-curated-mirrors.yml` owns accepted one-to-one mirror refreshes. It is separate from reviewed Cursor functional adaptation and has its own existing PR/auto-merge behavior. Its scope must not absorb new runtime policy by accident. |
| Observer/CI | `codex-review-gate.yml` observes authenticated exact-head review; `skill-stack-ci.yml` checks syntax, tests, catalog and security signals. Passing CI does not grant acceptance authority. |

Read-only GitHub inspection found successful scheduled runs for the adapted upstream detector and curated mirror refresh on 2026-10-29. This is evidence of those runs, not proof of every downstream stage. No repository-matching local Codex automation definition was found in the inspected automation folder. Hosted Cursor automations outside this repository were not enumerated; their absence is not claimed.

## Approaches considered and decision

1. Replace the mirror with a public T3 port. Declined: replaces existing Codex contracts, introduces another updater and may change model policy, hooks and workflow semantics.
2. Maintain a separate full T3 fork beside the Codex fork. Declined: duplicates methodology and makes fixes diverge. Installing identical skill names from both forks into one home also creates discovery ambiguity.
3. Extend the existing source/overlay/generator system with conditional runtime contracts. Selected direction: one reviewed upstream source and one named skill family, with common methodology and explicit execution adapters. This is the user's selected direction; exact file layout below is the implementer's proposal.

## Architecture

```text
reviewed upstream snapshot + provenance + existing overlays
                         |
              deterministic existing renderer
                         |
       same cursor-* skill names and install locations
                         |
           common workflow and proof requirements
                         |
             explicit runtime capability selection
              /              |                 \
      native Codex       T3 execution       future adapters
      preserved          added and tested   unavailable until proven
```

Add adapter inputs under `sources/cursor-plugins/runtime-adapters/` and a runtime compatibility ledger alongside the current manifest. Extend the current renderer; do not create a second generator or updater. Keep the existing manifest schema and automation family/batch markers compatible. The ledger records supported operations and proof per skill/runtime, not a single misleading supported boolean.

Agent-facing runtime material must travel with an individually installed skill. Generate the required files under that skill's `references/runtime/` from canonical adapter input. Repeated generated copies are build output, not independently authored contracts. Validate hashes, relative links and completeness. A skill must not require the source repository's `scripts/` tree after installation.

Retain `cursor-*` names, cross-skill identity and explicit-invocation rules. Adding T3 must not enable a session hook, sticky mode, scheduler, default pack, new provider or credential path. Do not install duplicate runtime variants of the same skill into one provider home.

The methodology stays shared. Runtime-specific delegation, lifecycle, isolation, proof surfaces and PR waiting belong behind an explicit runtime pointer rather than contradictory unconditional instructions. Existing Codex-only bodies can be preserved as reviewed adapter input while their harness-neutral workflow is progressively separated; do not shorten or weaken them as a side effect.

## Runtime selection and policy

Select the execution context from the actual exposed tool contracts, not model brand, process name, directory names or a T3 citation. A Codex model inside T3 is both a provider and a hosted context. An operator selection wins; an ambiguous or unavailable context remains unselected and dependent work is reported blocked.

For a detected T3 context, use the T3 lifecycle for worktrees, PR links and watches. Same-provider native delegation remains valid only where current T3 instructions permit it. Outside T3, preserve the native Codex path. Do not reinterpret a native permission refusal as capability absence and fall through to another adapter.

`model-capability-router` remains the sole operator model/effort policy. Add an explicit T3 transport mapping to live provider instance IDs, model IDs and options; no competing model sheet, automatic provider substitution, spending route or preset replacement. Unavailable named choices remain choices needing resolution. Model recommendations are distinct from configured values and observed effective selection.

`proof-orchestrator` remains the proof-path authority. Neither installed skills, metadata discovery, fixture tests nor worker claims establish live workflow completion.

## T3 execution contract

- Bounded children on another provider/model or requiring separate isolation use `delegate_task` with the exact supported target/options and `isolation: "worktree"` where appropriate. Never create a delegate checkout in the shell or task prompt.
- Use native same-provider children only when permitted by the current host contract. Preserve specialist persona identity and ownership through supported native roles or explicit reviewed persona material; these are different proof levels, not interchangeable claims of native registration.
- New top-level threads require an explicit user request. Do not substitute `t3_thread_launch` for an ordinary worker. A workflow that would require separate top-level ownership must make the missing authorization/capability explicit rather than quietly manufacture it.
- Children get bounded briefs, file/commit pointers, permitted actions and acceptance criteria. Completion notifications govern collection. Fresh review rounds use fresh tasks. No polling loops or continued task ownership inferred from a child thread's later activity.
- Link every created, taken-over or pushed PR immediately through `link_pull_request`. Wait through the owning thread's `watch_pull_request`, and unwatch before handoff. Do not add timers as a second PR watcher. Time-based scheduling is separate and must be explicitly authorized.
- Preserve repository merge ownership and scope. No auto-merge/close/force-push authorization arises from merely installing or selecting a runtime adapter.
- Proof tools follow the actual host boundary: use the project's verification contract; browser tools only within their current authorized scope, native desktop/device tools for the surfaces they support. No universal conversion of desktop or artifact verification to `preview_*`.

## Compatibility and future runtime boundary

The first implementation covers the pstack execution paths and every supporting published skill they invoke. Inventory every reference across the 107-skill Cursor family; mark each unaffected, adapted, unsupported or deferred with a reason. Do not silently advertise all 107 as T3-certified because the entry skill works.

Hermes is a later adapter requiring native tool, skill-discovery, model-selection and lifecycle inspection. Do not call it Codex with different command names.

OpenClaw needs separate context identities: native subagent runs, native Codex app-server embedding when available, and explicitly selected external ACP harness sessions. ACP is not a universal substitute for the native runtime. Gateway/channel authority, cancellation, completion delivery, sandboxing and available tool bridges remain explicit. No OpenClaw profile, service, plugin or channel is changed in this phase.

Future adapters use the same compatibility ledger and contract tests. An operation with no native equivalent is unsupported or partial; it must never disappear from the workflow or be reported as completed.

## Regression and proof contract

Before changes, record the reviewed source/pins, generated file set, Codex contracts, profile hashes, invocation policy, detector output semantics and automation fixtures at the exact base SHA. Keep pre-existing failures separate.

Required candidate evidence:

1. Existing native Codex semantic contracts remain covered: selected role/effort, named agents, reuse where supported, user choices, proof steps, history and explicit unsupported branches. Retain existing tests; do not update expectations solely to fit changed behavior.
2. Deterministic render twice, check mode, provenance/hash verification, profile checks, cross-skill links, individual-skill package completeness and catalog/security scans. Unaffected output is byte-identical; explain every changed Codex artifact.
3. Table-driven runtime selection and operation mapping: native Codex, T3/Codex, T3/non-Codex, ambiguous context, missing model/tool, permission refusal and unsupported operation. Fixtures test mapping, not live model behavior.
4. Automation regressions: unchanged schedules, workflow permissions, family markers, branch selection/deduplication, source pins, detector-only reports and exit codes, exact-head finalization, separation from Matt/curated ownership, and no install/home writes. Existing automation tests plus new fixtures must survive at the final SHA.
5. Fresh native Codex discovery and bounded workflow proof on a disposable fixture. No active user threads or histories are used as fixtures.
6. Fresh T3 bounded delegation and isolated write/review proof on a disposable repository, plus the required supporting-skill invocation. The first release targets verified T3 support, not a fixture-only release. Use existing authorized execution routes and accounts within their granted scope; do not add credentials, a new paid provider/API route, test PRs or external comments. If the required live route lacks authorization or capability, keep the implementation on an unreleased review branch, report the exact proof blocker, and do not count partial status as release acceptance. A provider/runtime may be advertised as supported only for the operations its evidence actually covers.
7. Full required repository checks, exact-base/candidate security comparison, test audit and independent review before publication. Live discovery, workflow proof and deployment remain distinct receipts.

First regressions are isolated before implementation; fresh native cross-provider proof is required before claiming T3 execution support, not before documenting an unsupported operation. Preserve offline tests for every existing runtime branch.

## Delivery sequence and boundaries

1. Audit and approve this design. It changes no installed skill or live automation.
2. Implement a reviewed runtime contract and compatibility ledger at the current pinned upstream revision. Prove native Codex preservation before broadening the generated surface.
3. Add T3 to the entry/orchestration skills and their playbook/support closure in verifiable slices. Keep incomplete operations explicitly partial.
4. Review the separate upstream 0.15.28 to 0.15.36 refresh; do not mix it into the initial runtime change. Preserve the existing detector/promotion process.
5. Publish and deploy only after the corresponding proof and authorized release review. No merge, activation or fleet rollout is implied by this design document. Implementation can be prepared locally without modifying active installations.
6. After T3 acceptance, audit and implement Hermes and OpenClaw adapters as separate work, reusing the same methodology, invariants and evidence structure.

The builder may choose the internal schema and module layout, provided the public names, compatible ledgers, authored/generated boundary and one policy authority are preserved. Any required automation control-plane change is a separate reviewed change, never smuggled into an upstream detector PR.

## Acceptance

The first release adds verified T3 operations without regressing native Codex or changing the observed behavior and authority of existing automation. A compatibility report must identify source version, runtime, operation, evidence and gaps. Unverified Hermes/OpenClaw support and universal full-workflow parity remain unclaimed. Rollback restores the prior generated artifact set and adapter inputs without touching user data or task history.

## Builder review

A fresh read-only builder review asked whether missing authorization for paid cross-provider proof could make a partial implementation count as the first release. Resolution: live T3 proof is a release gate. Missing authorization leaves an unreleased review branch and a named blocker; it does not waive the gate or authorize a new paid route. This is an implementer clarification of the existing authority and evidence boundaries, not a new request for spending or access.

## References

- [Current adaptation automation contract](../../upstream-review-automation.md).
- [Successful adapted-upstream detector run, 2026-10-29](https://github.com/TheAngryPit/TheAngrySkills/actions/runs/40884819330).
- [Successful curated-mirror run, 2026-10-29](https://github.com/TheAngryPit/TheAngrySkills/actions/runs/40867238611).
- [OpenClaw ACP and native runtime distinctions](https://docs.openclaw.ai/tools/acp-agents).
