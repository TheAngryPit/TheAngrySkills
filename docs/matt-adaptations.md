## Refresh — 6 October 2026

Latest reviewed upstream: `4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d`. Existing reviewed overlays from PR100 remain the base for package refresh. AskPit retains its own identity and Writing for Astra route, incorporates current implement-spec/pr/retro flows, and uses native context decisions. Writing for Astra integrates useful pointer, information-structure, completion and source-of-truth guidance while retaining the documented Astra decisions. Vanilla ask-matt and writing-for-agents remain excluded from the emitted catalog.

The new portable, explicit-only `chief-of-staff` guidance is curated with an intentional empty overlay. It suggests schedules subject to harness support; it creates no schedule or delegated run during source publication. `pr` was already curated in PR100 and is refreshed rather than duplicated. These packages need manual installation where absent. The removed resolving-merge-conflicts source remains preserved as a legacy package; it is not silently replaced by a docs page or deleted.

# Matt Pocock skill integrations

The public repository contains 32 curated packages from Matt Pocock's skills
repository under
`skills/mirrors-mattpocock/`, plus the separately packaged AskPit adaptation.
The upstream source is [Matt Pocock's skills repository](https://github.com/mattpocock/skills),
originally reviewed at `3cca18b368ae95cdbdebbff572ccafa662551015`;
current source review is recorded below.

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

## Upstream review on 2026-10-05

The reviewed upstream head is `24fe0ef7737efae15c87225755e9f6f5965e4888`.
The existing mirror destinations for `implement-spec` and `retro` remain
unchanged; their source paths moved from `skills/in-progress/` to
`skills/engineering/`.

The `pr` package is a new, verbatim source inclusion with an explicit empty
overlay. Its upstream frontmatter credits Dex Horthy and Humanlayer; the
package is sourced from Matt Pocock's repository without implying Matt authored
that skill. This makes 19 curated packages with patches and 12 with explicit
empty overlays, plus AskPit's separate patch.

Upstream removed `skills/engineering/resolving-merge-conflicts`. Its existing
mirror and Codex adaptation remain intact at their reviewed source pin and are
held for legacy conflict-resolution use. The new `pr` skill drafts pull request
bodies and is not an equivalent replacement. The removal is recorded at the
reviewed head above; no new source was assigned to the legacy destination.

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
