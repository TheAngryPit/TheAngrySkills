## Benny native distribution — 6 October 2026

The operator selected all three Benny workflows for native Codex adaptation, superseding only the prior Benny exclusion. The current catalog emits 102 of 107 source skills; the five remaining exclusions are Grok Voice and make-bot-ui. Historical notes below retain their original counts and decisions.

`cursor-setup-benny`, `cursor-triage-issue-reports` and `cursor-reproduce-and-fix-issues` are explicit-only packages. Setup bundles the complete, hash-pinned 12-file pack with native intent/configuration/templates and direct `instructions.md` operational files. This avoids nested skill auto-discovery; committed project workflows read those files directly. No installation or activation is performed. The Codex schedule API does not provide Slack message-event delivery: that capability must be established separately, without silently substituting polling.

The native event boundary normalizes consistent `message_ts`/`ts` aliases and rejects conflicting timestamps and child events. Local fixture results are not live Slack, tracker compensation, worker-isolation or real-UI proof. See [Benny source review](../../reports/cursor-benny-native-20261006.md).

## Current source review — 6 October 2026

The complete raw tree is pinned to `df581122cde17e6e27686b5a448bde23e4ad4318`, pstack0.15.15:903files,107physical skills and14agent sources. All107skills have native adapters:99are emitted and8existing operator exclusions stay dormant. The historical global/per-skill pins below retain provenance; refreshed pstack entries and the three additions carry the current per-skill pin. See [refresh evidence](../../reports/cursor-refresh-20261006.md).

`cursor-poteto-help` preserves the help/prompting map using native Codex roles, invocation and requested scheduling. `cursor-origin-api` and `cursor-port-github-app-to-origin` preserve current-spec lookup and planning-only behavior. No installation or runtime activation is implied.

# Complete Cursor source and Codex adapters

Current full upstream pin: `e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a`.

- `upstream-tree/` preserves all 890 tracked files byte for byte, including 104 skills, all 14 agents, plugin manifests, full Benny automation pack, docs, scripts, hooks, assets and licenses. `full-tree.json` records every Git blob, mode and SHA-256. These are inert source files, not registered plugins or executable instructions for Codex.
- `snapshot/` is the reviewed input to the adapter generator. All 104 skill snapshots match the full-tree pin. Historical per-entry provenance remains explicit. It also includes the complete Pstack README and guide, with all ten chapters, index and six images hash-checked in `manifest.json`.
- `overlays/` adapts all 104 skills. The generated catalog contains 96. `adapted-held/` contains the eight adapted but unindexed operator exclusions: four Grok Voice skills, three Benny workflows and make-bot-ui. None is installed or activated by source generation.
- `agent-coverage.json` maps all 14 upstream agents to native TOML source profiles in `skills/core/model-capability-router/assets/agents/`. Pstack itself owns two, and Dylan owns one. Profile distribution does not prove installation, fresh-session loading, model selection or execution.

Poteto retains its 23 playbooks and 24 principle leaves. Its inline index owns principle routing after that workflow is selected. The global principle router remains unchanged. Dylan layers on those exact adapted dependencies; it does not create another principles tree.

The full guide is preserved as upstream reference, including Cursor-specific examples. The operational adapters govern native execution. Read the adapter and actual host capabilities before attempting any referenced setup, credential access, scheduling or external action.

Run the source checks:

```sh
python3 scripts/sync-cursor-plugin-skills.py --check
python3 scripts/check-cursor-full-tree.py --upstream /path/to/full/cursor-plugins
python3 scripts/check-cursor-adaptations.py
```

After editing a held adapter, regenerate its review copy with `python3 scripts/check-cursor-adaptations.py --write-held`. That command never indexes the held copies. The existing `cursor/pstack` upstream-review batch now checks the whole Cursor tree against `full-tree.json`; its identity, approval and publication gates are unchanged. Historical fixtures without that ledger retain the older Pstack-only comparison.

Source completeness, native adaptation, distribution, installation and runtime proof are different claims. Figma/Google/X/X Money connectors, Bugbot, authorized secrets input, Benny's Slack event trigger, voice devices/providers, and bot wake endpoints require actual host proof. Current source work performs no installs, credentials, connector operations, automated runs or external writes.

The report is [Cursor full parity review](../../reports/cursor-full-parity-20261005.md).

## Earlier review history

The following notes document earlier increments and their proof limits. Their counts describe those increments, not the current inventory.

# Cursor plugin skills mirror

This is a pinned, reviewable native Codex adaptation of the skills in `cursor/plugins` at
`c1c0a32802223f4be824112dd83d33ad29a8b26c`. The pinned `snapshot/`
contains the 94 physical `SKILL.md` files, their 169 files of in-skill support,
and the nearest physical license evidence. It also pins 27 plugin-level agent, hook, and rule dependencies in a hash-checked support ledger. Reviewed native adapters are bundled only into the published skills that use them; the old hook adapter and make-bot-ui adapter remain repository evidence and are not rendered. No adapter is registered as a hook. The raw support files are not registered or executed by the mirror. Nothing is installed globally. `manifest.json` is keyed by physical
upstream path; it retains the three Benny automation sources for historical
provenance, but Vítor excluded them from this mirror and its previews.

`upstream_commit` is the default revision for entries without a `source_commit`.
`pstack_upstream_commit` is the separate reviewed baseline for the pstack drift
detector; it prevents the same reviewed plugin changes from reopening a report.
The 24 reviewed Pstack skill entries use per-skill provenance at
`e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a`; the global snapshot baseline stays
at `c1c0a32802223f4be824112dd83d33ad29a8b26c` for all other entries (including the unchanged operator exclusions). This mixed
pin keeps the newer Pstack source review bounded to 21 existing entries and
three reviewed additions: `cursor-benchmark-checklist`, `cursor-correct`, and
`cursor-principle-explain-the-number`. It does not advance X MCP or the
operator-excluded voice and Benny skills. Each rendered
`MIRROR.md` and held-sibling link uses the applicable skill revision, and the
generated state records only the overrides from the global default.

Each `overlays/<published-name>.json` declares the exact source hash, optional
exact-text changes and a Codex boundary note. The build rewrites the frontmatter
name, fixes sibling Markdown links to a published sibling or to the pinned
upstream source when that sibling is held, and writes provenance and license
evidence beside each published skill. A reviewed `codex_native_body` may replace
an incompatible operational body while the pinned source and hashes remain as
provenance. Without that field, the upstream body stays in place. The decision class is editorial; it does not establish live tool,
connector, model, hook or cloud availability.

PR #64 merged 59 emitted mirrors under `skills/mirrors-cursor/`, including
bounded explicit-only `cursor-how`, `cursor-why`, `cursor-show-me-your-work`,
`cursor-thermos`, and local-computer `cursor-swarm`. PR #66 adds bounded explicit-only local `cursor-arena` and `cursor-architect`
workflows. This isolated successor branch adds bounded explicit-only
`cursor-interrogate` and `cursor-reflect`, then promotes the bounded native
`cursor-create-verification-skill`, `cursor-maintain-verification-skill`, and
`cursor-no-comments`, `cursor-automate-me`, `cursor-figure-it-out`,
`cursor-poteto-mode`, `cursor-recall`, and `cursor-setup-pstack` paths, bringing
the catalog to 71 published mirrors. The `cursor-setup-pstack` adaptation also
maps the reviewed pstack reasoning-budget labels to native model/effort choices
in a fixture-only dry run. Vítor selected the remaining 12 active
candidates for conversion and excluded eight sources from this mirror: the
three Benny automations, four Grok Voice skills, and `cursor-make-bot-ui`.
The excluded sources are neither published nor rendered in candidate previews;
their pinned upstream files stay in the historical snapshot. Publication is
not proof of full native execution.
The cursor-team-kit PR review canvas is published for a read-only local artifact
path with executable renderer proof. Six instruction-only candidates are
`guide_only`: the four principles, technical writing, and Ralph help. The
`how`/`why` role-flow [evidence](../../reports/pstack-how-why-real-20260914.md)
supports bounded read-only publication while automatic skill selection remains
unobserved. The `show-me-your-work` [audit](../../reports/cursor-show-work-review-20260914.md)
supports a bounded local decision writer and independent review with explicit
redaction limits. Eight of the final nine candidates now publish bounded native adaptations:
advisor, compatibility scanning, continual-learning proposals, static plugin
scaffolding and review, Ralph continuation, and exact-child cancellation. Their
incompatible Cursor operational bodies are not emitted. `cursor-cursor-sdk` now
publishes a bounded native migration guide and read-only adapter while excluding
all seven upstream credential/MCP reference files from its rendered bundle.
The current generated catalog has 86 published skills after the reviewed
additions; operator exclusions are unchanged. Earlier Work-cloud proof limits
remain as recorded in their owning overlays. The current eight-source exclusion and twelve-skill
selection are recorded in the [scope decision](../../reports/cursor-scope-selection-20260914.md).
The verification pair is published only for the bounded explicit-only local
CLI/UI paths. Production target parity, reusable host activation, action-time
Reset cleanup, and changed-outcome PR publication remain separate gaps. The
`cursor-no-comments` path is published only for the bounded named
`comment-sicko` review with coordinator-owned integration. All 94 physical
skills remain traceable in the manifest and snapshot. The `cursor-poteto-mode`
candidate renders all 23 playbooks and bundles its role reference, but its
bundled script security review, cloud task parity, and full live playbook
behavior remain unproven.
No held skill is indexed for installation. The generator keeps
the repository's `.claude-plugin/marketplace.json` catalog entry
`mirrors-cursor` aligned with the emitted paths. This is catalog registration;
it does not import or activate an independent Cursor plugin.

To verify the committed build:

```sh
python3 scripts/sync-cursor-plugin-skills.py --check
```

To compare a fresh checkout without accepting changes:

```sh
python3 scripts/sync-cursor-plugin-skills.py --compare-upstream /path/to/cursor-plugins
```

The check also verifies that the marketplace catalog lists exactly the
reviewed, emitted Cursor skills. The comparison reports new, removed and
modified physical skills and exits
nonzero if any need review. Build refuses to overwrite local changes in the
generated tree. To adopt a new upstream commit, review its inventory, license,
behavior and security delta per skill, update the snapshot and manifest, rebase
exact overlays, then rebuild and review the resulting diff. New skills are never
activated automatically. Reverting this mirror means reverting its snapshot,
overlays, generator, report, catalog entry and `skills/mirrors-cursor/` tree; global
installation is a separate operator decision.

`orchestrate`, `cursor-sdk`, Grok voice and X MCP continue to describe their
named external products. A native Codex implementation or ChatGPT Work backend
needs separate behavioral proof. The source classifications and static scans
must never be presented as equivalent runtime proof.
