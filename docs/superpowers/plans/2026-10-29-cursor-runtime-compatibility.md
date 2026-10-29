# Cursor Runtime Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add demonstrable T3 execution to the existing Cursor adaptations while preserving native Codex, install identity, reviewed provenance and upstream automation behavior.

**Architecture:** Extend the existing renderer with runtime-scoped references generated from one reviewed adapter source. Preserve the existing Codex content as an exact separately addressable contract; select the appropriate operation contract from actual host capabilities. Maintain one operation-level compatibility ledger for the complete published Cursor family, without introducing another model policy, installer or updater.

**Tech Stack:** Existing Python standard-library generator/validators; JSON provenance and compatibility ledgers; Markdown skills; pytest 9.1.1 and current repository checks. No new runtime dependency or daemon.

**Spec:** `docs/superpowers/specs/2026-10-29-cursor-runtime-compatibility-design.md` (approved by Vítor on 2026-10-29).

## Global Constraints

- Preserve the 107 published `cursor-*` names, five held adaptations, explicit invocation policy, source snapshots, accepted pins and 14 mapped source agents.
- Keep the current pstack revision `d457567332aa6989e753ea289f30ea2bfbc80bc0` (0.15.28). Upstream refresh is a separate change.
- Extend `scripts/sync-cursor-plugin-skills.py`; never hand-edit generated skill output or add a second updater.
- Keep `model-capability-router` as the sole model/effort policy and `proof-orchestrator` as the proof-path authority. No automatic model/provider substitution or new paid route.
- Preserve native Codex semantics; no session hooks, sticky activation, schedules, credentials, installed homes or active user sessions are changed by this implementation.
- Retain all existing automation schedules, tokens/permissions, family/batch markers, report-only detection, canonical PR ownership, exact-head review/finalization and curated/adapted separation.
- Hermes and the distinct OpenClaw native-subagent/native-Codex/ACP contexts are future adapter identities, explicitly unavailable until their own proofs exist.
- No merge, publication or fleet deployment in this implementation plan. Prepare a local review branch and exact evidence; missing live proof blocks release rather than lowering acceptance.

## Review Focus

1. An individually installed skill must carry every runtime/persona reference it needs; source-repository-relative links must not become required execution dependencies. Task 2 pins standalone packaging.
2. A permission refusal must not be treated as absence and rerouted through another host/tool. Task 1 pins refusal versus missing-capability results.
3. A Codex provider inside T3 must receive T3 lifecycle rules while retaining its allowed native same-provider behavior; missing T3 tools must not silently select another runtime. Task 1 pins hosted identity and ambiguous selection.
4. A future source refresh must preserve locally owned adapter contracts and trigger review of affected operation coverage. Tasks 2 and 4 pin deterministic generation and detector behavior.
5. An output that is discoverable or passes fixtures must not become a live-support claim, and an inherited or unavailable target must not silently change policy. Tasks 1 and 5 pin evidence levels and live acceptance.

## File and responsibility map

- `sources/cursor-plugins/runtime-adapters/compatibility.json`: authored operation-level coverage and evidence status for every published skill and planned future runtime identity.
- `sources/cursor-plugins/runtime-adapters/t3.md`: canonical T3 operation/lifecycle guidance; copied into affected installed skill packages by the existing renderer.
- `scripts/cursor_runtime_contracts.py`: pure validation, deterministic package rendering, host-operation selection and selected-target mapping; no external execution or implicit policy.
- `scripts/sync-cursor-plugin-skills.py`: call the runtime rendering extension after the existing reviewed Codex rendering, before final generated hashes/state are calculated.
- `scripts/check-cursor-adaptations.py`: validate runtime ledger coverage and packaged runtime file integrity without changing its existing successful return contract.
- `sources/cursor-plugins/overlays/*.json`: only reviewed per-skill runtime declarations, where applicable; original Codex overlay fields remain intact.
- `skills/mirrors-cursor/**/references/runtime/`: generated adapter/persona/retained-Codex material; never authored by hand.
- `reports/cursor-plugin-skills-state.json`: existing generated state, extended compatibly only where needed; all generated changes explained.
- `tests/test_cursor_runtime_contracts.py`, `tests/test_cursor_runtime_packaging.py`, `tests/test_cursor_runtime_automation.py`: new operation, packaging and automation regression tests.
- `tests/test_cursor_plugin_mirror.py`: include the new renderer dependency in copied test repositories, retaining every existing assertion.
- `skills/core/model-capability-router/references/t3-runtime.md`: reviewed T3 transport mapping, conditional on T3; existing Codex profiles remain unchanged.
- `docs/cursor-runtime-compatibility.md`: supported operation/evidence matrix and execution/rollback guidance.

### Task 1: Validate compatibility and host-operation selection

**Files:** Create `scripts/cursor_runtime_contracts.py`, `sources/cursor-plugins/runtime-adapters/compatibility.json`, `tests/test_cursor_runtime_contracts.py`.

**Interfaces:** `load_contracts(path: Path, entries: list[dict]) -> dict` validates authored coverage; `select_runtime(explicit: str | None, capabilities: dict) -> dict` returns `runtime`, `status` and `reason`; `resolve_operation(runtime: str, operation: str, capabilities: dict, denied: bool = False) -> dict` returns `route`, `status`, `reason`; `t3_target(binding: dict, catalog: dict) -> dict` returns exactly a valid selected `target` or an explicit unresolved result. These are offline validators, not a mandatory agent command wrapper.

Selection result statuses are `selected`, `blocked`, `unsupported` or `deferred`. Runtime identities are `native-codex`, `t3`, `hermes`, `openclaw-subagent`, `openclaw-codex` and `openclaw-acp`. Capability fixtures identify advertised host operations separately from provider and denial state. They do not treat an SDK error as an absent tool. Bindings use the current T3 target keys `providerInstanceId`, `model` and `options` unchanged; catalog fixtures must match a captured current tool-result shape, not an invented universal model schema.

Pin these test names and assertions (fixture values below are synthetic):

```python
def test_permission_denial_never_falls_through(t3_capabilities):
    result = resolve_operation("t3", "delegate", t3_capabilities, denied=True)
    assert result["status"] == "blocked"
    assert result["route"] is None

def test_ambiguous_context_needs_selection(ambiguous_capabilities):
    result = select_runtime(None, ambiguous_capabilities)
    assert result["status"] == "blocked"
    assert result["runtime"] is None

def test_exact_selected_t3_binding_is_preserved(selected_binding, live_shape_catalog):
    result = t3_target(selected_binding, live_shape_catalog)
    assert result["target"] == selected_binding
```

- [ ] Write failing tests for complete coverage of the exact published manifest names, unknown/duplicate entries, missing per-operation evidence and future-runtime unavailable status. Check selected supported/unsupported operations rather than one global flag.
- [ ] Write table tests for explicit native Codex; T3 plus Codex; T3 plus another provider; ambiguous host; missing required tool; permission denial; unavailable selected model/options. Assert denial never falls through and target mapping never substitutes a model, changes effort, or invents inheritance.
- [ ] Run `pytest -q tests/test_cursor_runtime_contracts.py`; verify failures identify missing new behavior.
- [ ] Implement the pure interfaces and the authored runtime/operation schema. Catalogue all 107 published skills: affected orchestration/support closure, unaffected methodology, explicitly unsupported and deferred capabilities. Do not claim full T3 support for the family.
- [ ] Run the new tests and the existing seven setup/profile fixture tests. Commit only validated source/schema/tests.

### Task 2: Generate self-contained packages while retaining Codex contracts

**Files:** Modify the existing renderer and checker; create `tests/test_cursor_runtime_packaging.py`; update copied-fixture dependencies in `tests/test_cursor_plugin_mirror.py`; generate runtime references and state only through the renderer.

**Interfaces:** `render_runtime_package(target: Path, entry: dict, rendered_codex: str, contracts: dict) -> None` receives the exact previously rendered Codex SKILL text and writes the conditional entry and bundled references. No inputs outside validated reviewed roots. Existing no-runtime callers retain their current bytes. `verify_runtime_packages(root: Path, contracts: dict) -> None` rejects missing, modified, orphaned or escaping files.

Name the new regressions `test_no_runtime_declaration_preserves_bytes`, `test_retained_codex_resolves_original_targets`, `test_single_skill_package_is_self_contained`, `test_unsafe_adapter_path_leaves_output_unchanged` and `test_two_renders_and_check_mode_match`. The last test compares complete file sets and SHA-256 values, not only a success message; unsafe-path cases compare the pre/post output tree.

- [ ] Write failing tests that no-runtime rendering is byte-identical; the retained Codex contract is byte-identical to the old renderer's content; standalone packages resolve all references; malformed/absolute/parent-traversal/symlink inputs fail before output replacement; two renders and check mode agree.
- [ ] Preserve relative-link meaning when moving Codex content under `references/runtime/`: rewrite destination-relative links deterministically and assert each resolves to the same installed target as before. Compare normalized semantic body to the original rather than accepting missing instructions.
- [ ] Add the extension at the existing generator boundary before output hashes and state are calculated. Leave raw source, source hashes and codex overlay input intact. Use existing manifest/state ownership and preserve the checker's existing success response.
- [ ] Keep legacy invocation metadata and names unchanged. Do not create duplicate runtime variants or implicit activation. Generate the required references for an individually installed skill from canonical input.
- [ ] Run `pytest -q tests/test_cursor_runtime_packaging.py tests/test_cursor_plugin_mirror.py tests/test_cursor_full_parity.py`; run `python3 scripts/sync-cursor-plugin-skills.py --check` and `python3 scripts/check-cursor-adaptations.py`. Commit generator, fixtures and exact generated artifacts together.

### Task 3: Add T3 contracts across the pstack execution closure

**Files:** Create canonical `runtime-adapters/t3.md`; update runtime declarations for `cursor-poteto-mode`, `cursor-setup-pstack`, `cursor-how`, `cursor-why`, `cursor-interrogate`, `cursor-architect`, `cursor-arena`, `cursor-swarm`, `cursor-no-comments`, `cursor-reflect`, and every impacted playbook/support dependency identified by Task 1. Add the conditional model-router reference; generate agent-facing files.

**Interfaces:** Consume Task 1's operation keys and Task 2's packaging API. Each migrated skill explicitly selects its runtime contract before following runtime-dependent instructions. Native Codex reads the preserved Codex contract. T3 reads host-neutral workflow plus T3 operation guidance; unconditional Codex dispatch must not remain active on its T3 branch.

Name the operation regressions `test_t3_writer_uses_tool_isolation`, `test_native_codex_keeps_named_agent_contract`, `test_t3_persona_does_not_claim_native_registration`, `test_review_round_is_a_fresh_task`, `test_pr_wait_has_one_owner` and `test_unavailable_binding_is_not_substituted`. Exercise selection and generated instructions together, and reject missing required workflow steps rather than relying on a keyword-absence scan alone.

- [ ] Write failing contract tests for child context/persona loading, current `delegate_task` isolation/target/options, no shell-created delegate worktrees, no top-level-thread worker fallback, task cancellation/collection, fresh review tasks, PR linking/watching ownership and no second timer watcher.
- [ ] Pin proof-surface and unsupported-operation tests: no universal preview-tool fallback; no assertion of native specialist registration from a persona brief; no automatic schedule/merge authority; missing named roles and unsupported cloud execution remain explicit.
- [ ] Map the selected model policy into the current live T3 catalog without creating another persistent role sheet. Keep explicit bindings and current Codex profile values unchanged. A selected unavailable binding yields an unresolved choice.
- [ ] Derive needed portable persona instructions from the pinned source through reviewed adapter inputs. Preserve the native Codex named profile path; record adapted persona execution as a different proof level.
- [ ] Inventory all 23 playbooks and their support links. Every runtime-specific call site must use a selected operation contract or carry an explicit unsupported status; do not remove steps to pass a scan.
- [ ] Run all Cursor-family tests and relevant router/profile tests; regenerate/check all packages and inspect the authored plus generated diff. Commit in coherent runtime-path slices, retaining any incomplete operation as unreleased.

### Task 4: Prove that upstream automation and admission boundaries survive

**Files:** Create `tests/test_cursor_runtime_automation.py`; update `docs/cursor-runtime-compatibility.md`. No `.github/workflows/`, detector or finalizer behavior change is planned. A necessary control-plane change must be split and reviewed independently.

**Interfaces:** Reuse existing detector/lifecycle fixtures, family/batch markers and exact-head assessment functions. Add an adapter-input mutation fixture that must be reviewed locally, not treated as automatic upstream promotion.

Name the new regressions `test_runtime_generation_preserves_upstream_ownership`, `test_detector_remains_report_only_with_runtime_inputs`, `test_runtime_input_drift_requires_review`, and `test_finalizer_keeps_exact_head_and_manifest_gate`. Assert no additional repository/home writes by comparing complete fixture trees and invoke the real existing lifecycle assessment functions for rejection cases.

- [ ] Write failing tests that adapter generation does not rewrite accepted upstream pins, excluded skills, source snapshots, mapped profile hashes, unrelated skills, workflows or installed homes.
- [ ] Preserve detector status 0/no drift, 1/review reports, operational failure >1; one canonical PR per family/batch; evidence-only detector outputs; altered license/support inventory reporting; and no second update lane.
- [ ] Pin finalizer rejection of wrong family/branch/head, detector-only candidates, missing manifest/generated evidence and changed GitHub control-plane files. Existing trusted finalizer and review-gate behavior must remain unchanged.
- [ ] Run `pytest -q tests/test_upstream_pr_automation.py tests/test_adapted_upstream_watch.py tests/test_cursor_addition_detector.py tests/test_cursor_runtime_automation.py`; require the original 49 cases to remain passing without weakened expectations.
- [ ] Run the complete repository suite and mandatory catalog/syntax/source/profile checks. Record raw outputs and exact candidate SHA. Compare security findings at exact clean base and candidate with identical scanner/options; investigate changes by finding identity, not totals. Commit reviewed compatibility docs/evidence without private paths or active session data.

### Task 5: Demonstrate live behavior and prepare the local review handoff

**Files:** Task-owned disposable fixtures and sanitized proof receipts; `docs/cursor-runtime-compatibility.md`; compatibility ledger proof statuses. No fleet install or external test PR.

**Interfaces:** Exercise the exact generated artifact from Task 3 in fresh native Codex and T3 contexts. Each receipt identifies source/adapter/artifact SHA, host/provider, operation, observed outcome and missing coverage.

- [ ] Verify fresh native Codex discovery and bounded fixture execution using the existing named role/effort semantics; compare to the approved baseline without touching active histories or installed skill homes.
- [ ] In T3, resolve current tool capabilities once before delegation and use an existing authorized route. Demonstrate one bounded child task, isolated fixture write, fresh independent read/review, artifact collection and task completion using the generated runtime contract. Isolation must be created by the host tool, not shell setup.
- [ ] If the current T3 project binding differs from the source repository, keep the proof fixture explicitly inside the tool-owned project/worktree and read the exact source artifact by approved path. This proves the transport contract, not the source project's installation or a different project binding. Never bypass a capability or permission refusal.
- [ ] Prove PR-link/watch request shape offline unless a real authorized PR is available. Do not invent a live forge proof, open a test PR, enable schedules or spend on a new model route. An unavailable required live route leaves the branch unreleased and the operation partial.
- [ ] Run the chosen independent review of the entire final change; resolve genuine findings and repeat only affected checks. Inspect source and candidate security evidence and preserve all baseline failures honestly.
- [ ] Commit the final accepted local artifacts and report exact head, proof by runtime/operation, unchanged automations, remaining gaps and rollback. Do not claim all providers or all 23 live workflows tested; no publication or deployment occurs under this plan.

## Verification baseline and completion

Approved pre-change baseline: 424 passed, two skipped and 13 subtests passed; focused automation subset 49 passed. These counts identify the baseline, not a target to imitate. The candidate must run all current tests plus the new behavior checks with raw artifacts at its final SHA.

The outcome is complete only when the supported T3 operations have their required live proof, native Codex compatibility is established, automation regressions pass, security changes are reviewed and the local handoff is verified. Missing authorization or capability produces a specific unreleased blocker, not a reduced release bar.

## Execution method

Pending operator selection required by the writing-plans workflow. Native execution is recommended: generator, overlays and admission tests share tightly coupled interfaces, and one owner can preserve them with less context duplication. One fresh independent whole-branch review follows implementation. Subagent-driven execution remains available if selected: one implementer and one fresh review gate per task, plus a whole-branch review.
