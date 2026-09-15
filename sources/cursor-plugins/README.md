# Cursor plugin skills mirror

This is a pinned, reviewable native Codex adaptation of the skills in `cursor/plugins` at
`889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`. The pinned `snapshot/`
contains the 91 physical `SKILL.md` files, their 169 files of in-skill support,
and the nearest physical license evidence. It also pins 27 plugin-level agent, hook, and rule dependencies in a hash-checked support ledger. Separate hash-checked native adapters are bundled only into the held Advisor, Ralph, and continual-learning previews; the make-bot-ui adapter remains historical evidence and is not rendered. They are not registered as hooks. The raw support files are not registered or executed by the mirror. Nothing is installed globally. `manifest.json` is keyed by physical
upstream path; it retains the three Benny automation sources for historical
provenance, but Vítor excluded them from this mirror and its previews.

Each `overlays/<published-name>.json` declares the exact source hash, optional
exact-text changes and a Codex boundary note. The build rewrites the frontmatter
name, fixes sibling Markdown links to a published sibling or to the pinned
upstream source when that sibling is held, and writes provenance and license
evidence beside each published skill. The upstream skill text otherwise stays
in place. The decision class is editorial; it does not establish live tool,
connector, model, hook or cloud availability.

PR #64 merged 59 emitted mirrors under `skills/mirrors-cursor/`, including
bounded explicit-only `cursor-how`, `cursor-why`, `cursor-show-me-your-work`,
`cursor-thermos`, and local-computer `cursor-swarm`. PR #66 adds bounded explicit-only local `cursor-arena` and `cursor-architect`
workflows. This isolated successor branch adds bounded explicit-only
`cursor-interrogate` and `cursor-reflect`, then promotes the bounded native
`cursor-create-verification-skill`, `cursor-maintain-verification-skill`, and
`cursor-no-comments`, `cursor-automate-me`, `cursor-figure-it-out`,
`cursor-poteto-mode`, `cursor-recall`, and `cursor-setup-pstack` paths, bringing
the catalog to 71 published mirrors. Vítor selected the remaining 12 active
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
redaction limits. The remaining held functional
adaptations stay held with a per-skill Codex contract recording native mapping,
permission gates, and positive, missing-capability/input, and error scenarios
still to prove.
It also holds `cursor-cursor-sdk` and `cursor-review-plugin-submission` for
contextual security review. The current eight-source exclusion and twelve-skill
selection are recorded in the [scope decision](../../reports/cursor-scope-selection-20260914.md).
The verification pair is published only for the bounded explicit-only local
CLI/UI paths. Production target parity, reusable host activation, action-time
Reset cleanup, and changed-outcome PR publication remain separate gaps. The
`cursor-no-comments` path is published only for the bounded named
`comment-sicko` review with coordinator-owned integration. All 91 physical
skills remain traceable in the manifest and snapshot. The `cursor-poteto-mode`
candidate renders all 23 playbooks and bundles its role reference, but its
bundled script security review, cloud task parity, and full live playbook
behavior remain unproven.
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
