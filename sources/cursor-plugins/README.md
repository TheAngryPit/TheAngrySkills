# Cursor plugin skills mirror

This is a skills-only mirror of `cursor/plugins` at
`889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`. The pinned `snapshot/`
contains the 91 physical `SKILL.md` files, their 169 files of in-skill support,
and the nearest physical license evidence. It does not import independent
plugin components or install anything. `manifest.json` is keyed by physical
upstream path; it retains the three non-distributed Benny skills as dormant.

Each `overlays/<published-name>.json` declares the exact source hash, optional
exact-text changes and a Codex boundary note. The build rewrites the frontmatter
name, fixes sibling Markdown links to a published sibling or to the pinned
upstream source when that sibling is held, and writes provenance and license
evidence beside each published skill. The upstream skill text otherwise stays
in place. The decision class is editorial; it does not establish live tool,
connector, model, hook or cloud availability.

This first reviewable batch publishes 48 content or naming candidates under
`skills/mirrors-cursor/`. It holds 37 functional adaptations until their Codex
workflow and permission behavior are proven. It also holds `cursor-cursor-sdk`,
`cursor-make-bot-ui` and `cursor-review-plugin-submission` for contextual
security review. All 91 remain traceable in the manifest and snapshot. No held
skill is indexed for installation by this batch. There is no new plugin or
marketplace entry.

To verify the committed build:

```sh
python3 scripts/sync-cursor-plugin-skills.py --check
```

To compare a fresh checkout without accepting changes:

```sh
python3 scripts/sync-cursor-plugin-skills.py --compare-upstream /path/to/cursor-plugins
```

The comparison reports new, removed and modified physical skills and exits
nonzero if any need review. Build refuses to overwrite local changes in the
generated tree. To adopt a new upstream commit, review its inventory, license,
behavior and security delta per skill, update the snapshot and manifest, rebase
exact overlays, then rebuild and review the resulting diff. New skills are never
activated automatically. Reverting this mirror means reverting only its
snapshot, overlays, generator, report and `skills/mirrors-cursor/` tree; global
installation is a separate operator decision.

`orchestrate`, `cursor-sdk`, Grok voice and X MCP continue to describe their
named external products. A native Codex implementation or ChatGPT Work backend
needs separate behavioral proof. The source classifications and static scans
must never be presented as equivalent runtime proof.
