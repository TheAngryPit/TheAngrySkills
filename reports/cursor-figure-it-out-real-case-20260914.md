# Cursor `figure-it-out` real-case behavior proof

Date: 2026-09-14
Tested head: `0479ea88374bcb9d3843eedb60d4631c63599bb4`

## Predicate and boundary

For the fixed explicit-only mapping, candidate rendering must remove Cursor's `disable-model-invocation: true`, emit `agents/openai.yaml` containing exactly `policy:\n  allow_implicit_invocation: false\n`, preserve the playbook body and overlay names, and reject malformed duplicate flags without creating policy output. This is a high-rigor activation-boundary check.

This report is a **partial post-change audit**. The fix is already committed, so the exploratory parent-renderer invocation is explicitly excluded as retrospective pre-change runtime proof. No native skill trigger or full task execution is claimed.

## Contracts and source steps

| Step | Evidence | Status |
|---|---|---|
| Read complete pinned `figure-it-out` source | [`figure-it-out/SKILL.md`](../sources/cursor-plugins/snapshot/pstack/skills/figure-it-out/SKILL.md) | Read. Phases A-E, falsifiable predicate, experiment loop, canonical TSV, and real-product check captured. |
| Read `cursor-figure-it-out` overlay | [`cursor-figure-it-out.json`](../sources/cursor-plugins/overlays/cursor-figure-it-out.json) | Read. Exact sibling mappings, positive/missing/error cases, and `not_proven_in_current_codex_session` are explicit. |
| Read complete `show-me-your-work` contract | [`show-me-your-work/SKILL.md`](../sources/cursor-plugins/snapshot/pstack/skills/show-me-your-work/SKILL.md) | Read. Append-only TSV, evidence pointers, transcript audit, and reviewer-gap rules followed. |
| Read required Principles subsection | [`poteto-mode/SKILL.md`](../sources/cursor-plugins/snapshot/pstack/skills/poteto-mode/SKILL.md) | Read. Native Codex todolist surface was unavailable, so the mandated todolist was not opened. |
| Architect/arena, native trigger, full product run | [`figure-it-out/SKILL.md`](../sources/cursor-plugins/snapshot/pstack/skills/figure-it-out/SKILL.md), [`manifest.json`](../sources/cursor-plugins/manifest.json) | Not exercised. The mapping shape is mechanical; manifest `publish` remains false and availability is unproven. |
| Cross-model trail review | [`show-me-your-work/SKILL.md`](../sources/cursor-plugins/snapshot/pstack/skills/show-me-your-work/SKILL.md) | Not assessed in this bounded subtask; no reviewer model is inferred. |

## Hypothesis/check/decision loop

1. **Current renderer hypothesis:** `0479ea88` maps the pinned source correctly. Real `--preview-candidates` rendering produced 88 candidates, including held `cursor-figure-it-out`. Direct inspection found frontmatter flag count `0`, exact native policy, all five phases, and all four overlay names (`cursor-poteto-mode`, `cursor-architect`, `cursor-arena`, `cursor-show-me-your-work`). **VERIFIED for renderer behavior.** The disposable output is reproducible with `python3 scripts/sync-cursor-plugin-skills.py --preview-candidates <destination>`; inspect `<destination>/cursor-figure-it-out/SKILL.md` and `agents/openai.yaml`. Implementation is `codex_invocation_policy` at `scripts/sync-cursor-plugin-skills.py:174`, called during `render_skill` at line 272.

2. **Malformed-input hypothesis:** duplicate explicit-only flags fail before policy creation. The fixed function returned `ValueError: duplicate explicit-only flag` and `duplicate_flag_policy_created=False`. **VERIFIED for this guard.** See `scripts/sync-cursor-plugin-skills.py:177`.

3. **Decision-log boundary hypothesis:** the held helper rejects an out-of-root logfile without mutating the canonical trail. It returned exit `1` with `log.sh: logfile path escapes the task/workspace root`; the trail hash was unchanged. **VERIFIED for this case.** The helper is reproducible in the held `cursor-show-me-your-work` preview.

4. **Repository-check hypothesis:** post-change reproducibility and held-preview behavior pass. `python3 scripts/sync-cursor-plugin-skills.py --check` returned `mirror check passed: 91 physical, 54 published, 201 output files`; focused tests (`test_held_preview_preserves_explicit_only_policy`, `test_committed_tree_is_reproducible`) returned `Ran 2 tests ... OK`. Assertions are in `tests/test_cursor_plugin_mirror.py`.

## Trail and decision

The held helper wrote the append-only [decision trail](cursor-figure-it-out-decision-trail-20260914.tsv). It records frame, mapping, verification, hold, and correction decisions. The correction rows qualify an exploratory parent-renderer row; that run is not used as pre-change runtime proof.

The explicit-only mapping is **VERIFIED** against the real post-change renderer and held-candidate output. Full skill promotion is **INCONCLUSIVE**: manifest `publish` remains false, and native Codex activation, end-to-end disposable task execution, and independent review were not demonstrated. The next prospective case must activate the skill by its published name on an authorized Codex host, execute the mapped phases, audit the TSV, and record independent review or its absence. No native trigger, external action, credential use, or PR mutation occurred.

## Attention

reviewed by not assessed

- Cross-model review was unavailable in this bounded subtask.
- The source-mandated todolist and native-host execution remain open.
