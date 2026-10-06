# Cursor source parity review

The complete Cursor source tree at `e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a` is preserved. The Codex catalog now covers the ten additional skills and current X guidance. The eight existing exclusions have adapted review copies but remain unindexed.

## Evidence

| Check | Result |
|---|---|
| Full Git tree and SHA-256 census | 890 files, 104 skill files, 14 agent files |
| Adapter source coverage | All 104 skill snapshots match the complete current source pin |
| Published source catalog | 96 skills, 449 generated files |
| Dormant adapted review copies | Eight; no activation or catalog entries |
| Native agent source mappings | 14, each with source and asset hashes |
| Cross-pack skill names and Markdown links | No unresolved concrete names or links |
| Pstack guide | README, ten chapters, guide index and six images preserved and hashed |
| Poteto routing | 24 leaves and 23 playbooks retained; exact adapted principle names |
| Full repository tests | 351 passed, two subtests passed |
| Catalog validation | Zero errors, 277 informational/quality warnings across 278 skills |
| Other mirror invariants | Curated, Hyperframes and Matt checks pass |
| Full-tree live upstream comparison | Exact inventory and Git blob match |
| Current scheduled detector | No drift against current pin; full Cursor tree monitored through existing cursor/pstack batch |

The six new regression tests reject missing, changed and unexpected upstream files, check real Git inventory, prove all skill and agent mappings, and detect a new non-Pstack plugin plus a changed dormant Benny file.

## Changes and preserved boundaries

The additions are build-figma, dyl-mode, dyl-ready-pr, dyl-review, principle-the-algorithm, Google Docs/Drive/Sheets/Slides and X Money. Their upstream source, supporting files and licenses remain intact. Native adapters require real connector schemas and report missing named capabilities. Dylan uses native delegation and Poteto's shared principles. Its unavailable Bugbot step stays incomplete rather than being replaced with a generic verdict.

The X change adds encrypted-chat guidance. Its native boundary requires an authorized reviewed helper and supported secret-input surface. It does not read a Grok Bot secret store, install a helper, or use credentials merely because the skill exists. The add-dictation change now preserves upstream's current model-selection guidance in the dormant adapter; no provider call was made.

Benny's full pack remains in the raw tree. Its adapted setup describes native configuration, shared skills, connector and app-control requirements, thread-safety testing and the exact event-trigger gap. A scheduled task is not proof of a Slack-message event source. The existing local gate fixtures remain boundary evidence only.

All 14 role profiles are source assets. The original checked profile installer still selects the two Pstack profiles. The additional profiles require their own explicit host installation and fresh-session selection proof. No live homes were changed.

`principle-pack-router` was not changed. Poteto selects and reads its own principle leaves after the workflow is selected. This removes redundant routing inside Poteto without changing global operator policy.

## Security review

The repository security scan is informational and still reports 20 blocked and 57 review-needed skills across the whole existing catalog. The ten new skills and updated X guide have no scanner findings after contextual clarification. Two initial false positives were reviewed: Dylan's operator-priority sentence and X Money's warning against reconnecting to enable an account-disabled action. The wording now states the same boundaries directly. This is source review, not a claim of safe live connector execution.

Raw upstream Markdown retains its original bytes. Narrow Git whitespace attributes preserve upstream hard line breaks in raw source. The emitted X guide uses an explicit overlay for those line breaks.

## Reproduce

```sh
python3 scripts/sync-cursor-plugin-skills.py --check
python3 scripts/check-cursor-full-tree.py --upstream /path/to/cursor-plugins
python3 scripts/check-cursor-adaptations.py
python3 scripts/check-native-agent-profiles.py --require-pinned-source
python3 -m pytest -q tests
node scripts/sync-curated-mirrors.mjs --check
node scripts/sync-hyperframes-mirror.mjs --check
python3 scripts/sync-matt-adaptations.py --check
node scripts/theangry-skills.mjs check --root skills --profile shared
```

Runtime execution, connector authentication, automatic skill selection, all playbook branches, new agent loading, cloud parity and installation remain unproven by this update. No installation, activation, external posting, purchase, credential access or provider work was performed. The coordinating task owns source review and publication.
