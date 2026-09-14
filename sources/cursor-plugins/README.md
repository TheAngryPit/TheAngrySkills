# Cursor plugin skills mirror

This is a pinned, reviewable native Codex adaptation of the skills in `cursor/plugins` at
`889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`. The pinned `snapshot/`
contains the 91 physical `SKILL.md` files, their 169 files of in-skill support,
and the nearest physical license evidence. It also pins 27 plugin-level agent, hook, and rule dependencies in a hash-checked support ledger. A separate hash-checked native adapter is bundled only into the held Advisor, Ralph and continual-learning previews; it is not registered as a hook. The raw support files are not registered or executed by the mirror. Nothing is installed globally. `manifest.json` is keyed by physical
upstream path; it retains the three non-distributed Benny skills as dormant.

Each `overlays/<published-name>.json` declares the exact source hash, optional
exact-text changes and a Codex boundary note. The build rewrites the frontmatter
name, fixes sibling Markdown links to a published sibling or to the pinned
upstream source when that sibling is held, and writes provenance and license
evidence beside each published skill. The upstream skill text otherwise stays
in place. The decision class is editorial; it does not establish live tool,
connector, model, hook or cloud availability.

The merged baseline indexes 53 candidates under `skills/mirrors-cursor/`. This branch adds `cursor-ralph-loop-help` as guide-only and `cursor-how`/`cursor-why` as bounded explicit-only native workflows, for 56 emitted mirrors. The other 32 active skills have contracts and pinned sources but remain held and unindexed; all 88 active skills are in scope. The three Benny skills remain dormant. Public availability of this branch requires PR review and merge.
The cursor-team-kit PR review canvas is published for a read-only local artifact
path with executable renderer proof. Six instruction-only candidates are
`guide_only`: the four principles, technical writing, and Ralph help. The
`how`/`why` role-flow [evidence](../../reports/pstack-how-why-real-20260914.md)
supports bounded read-only publication while automatic skill selection remains
unobserved. The remaining held functional
adaptations stay held with a per-skill Codex contract recording native mapping,
permission gates, and positive, missing-capability/input, and error scenarios
still to prove.
It also holds `cursor-cursor-sdk`, `cursor-make-bot-ui` and
`cursor-review-plugin-submission` for contextual security review.
`cursor-maintain-verification-skill` is held after source review showed a
Cursor-local path, parallel workers, live driving, and PR publication that need
a Codex-specific proof. All 91 physical skills remain traceable in the manifest and snapshot. The pstack candidate renders all 23 playbooks and bundles its role reference, but application in a live Codex session, cloud task parity, and bundled script safety are still unproven.
No held skill is indexed for installation by this batch. The generator keeps
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
