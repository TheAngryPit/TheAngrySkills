# Matt Pocock skill integrations

The public repository contains 30 curated Matt Pocock skills under
`skills/mirrors-mattpocock/`, plus the separately packaged AskPit adaptation.
The upstream source is [Matt Pocock's skills repository](https://github.com/mattpocock/skills),
reviewed at `3cca18b368ae95cdbdebbff572ccafa662551015`.

`ask-matt` and `writing-for-agents` are not copied into the mirror. AskPit and
Writing for Astra are the repository's separate packages and retain their
explicit identity and routing decisions.

## Approved surface

Batch 01 was already integrated and remains unchanged: `code-review`,
`diagnosing-bugs`, `tdd`, and `resolving-merge-conflicts`. AskPit is tracked by
the same pipeline but remains under `skills/core/ask-pit`.

The final approved integration adds 15 adapted Matt packages:

- `retro`, `setup-matt-pocock-skills`, `scaffold-exercises`
- `codebase-design`, `prototype`, `to-spec`, `to-tickets`, `wayfinder`
- `implement-spec`, `loop-me`, `writing-beats`, `writing-fragments`, `writing-shape`
- `grilling`, `teach`

It also adds 11 maintained packages with an intentional empty overlay:

- `domain-modeling`, `grill-with-docs`, `implement`, `improve-codebase-architecture`
- `research`, `triage`, `wizard`, `grill-me`, `handoff`
- `to-questionnaire`, `wait-what`

The 15 approved changes are recorded byte-for-byte in each package's
`ADAPTATIONS.patch`. The 11 maintained packages contain a zero-byte
`ADAPTATIONS.patch`; this is an explicit no-change decision, not a missing or
ignored patch. Every package carries its complete upstream support files,
`LICENSE`, `PROVENANCE.md`, and `UPSTREAM.json` hashes.

## Update and reverse proof

The adapted package generator reads the tracked `scripts/matt-adaptations.json`
manifest. It stages each package in a temporary directory, applies its overlay,
validates the generated hashes, and replaces an existing destination only after
validation succeeds. Empty overlays are skipped explicitly by the adapter and
are still checked by the same reverse-proof path.

Use a reviewed upstream checkout:

```sh
python scripts/sync-matt-adaptations.py --upstream /path/to/upstream --skill code-review
python scripts/sync-matt-adaptations.py --check
```

The daily `Review adapted skill upstreams` workflow derives its package list
from the manifest and includes Writing for Astra as a separate monitored
package. It reports changed upstream support files and licenses without
rewriting packages, accepting a new baseline, or opening real issues during
tests. A future update requires a fresh inspection and human approval.

The adapter's `--proposals-root` option is only for first creation from an
already approved local proposal set. Normal refreshes use the accepted
`ADAPTATIONS.patch` and `PROVENANCE.md` stored beside each package.

## Scope boundaries

These are curated external mirrors, not new TheAngrySkills workflow logic.
Do not silently add local policy, rename upstream skills, or copy the excluded
`claude-handoff`, `git-guardrails-claude-code`, `migrate-to-shoehorn`,
`setup-pre-commit`, or `setup-ts-deep-modules` sources. Do not treat a passing
hash check as proof that an upstream update is approved.
