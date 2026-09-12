# Emil Kowalski skill mirror

This is a curated, one-to-one mirror of
[emilkowalski/skills](https://github.com/emilkowalski/skills). It follows the
same source/configuration and daily refresh path as the OpenClaw mirror.

## Current upstream inventory

| Upstream skill | Published skill | Upstream support files | Transformation |
|---|---|---|---|
| `animate-expo` | `emil-animate-expo` | `RECIPES.md` | Prefix frontmatter and concrete sibling references. |
| `animate` | `emil-animate` | `RECIPES.md` | Prefix frontmatter and concrete sibling references. |
| `animation-vocabulary` | `emil-animation-vocabulary` | — | Prefix frontmatter. |
| `apple-design` | `emil-apple-design` | — | Prefix frontmatter. |
| `ask-sonner` | `emil-ask-sonner` | `API.md` | Prefix frontmatter. |
| `emil-design-eng` | `emil-design-eng` | — | Preserve the existing `emil-` namespace; never produce `emil-emil-design-eng`. |
| `find-animation-opportunities` | `emil-find-animation-opportunities` | — | Prefix frontmatter and concrete sibling references. |
| `improve-animations` | `emil-improve-animations` | `AUDIT.md`, `PLAN-TEMPLATE.md` | Prefix frontmatter and concrete sibling references. |
| `pick-ui-library` | `emil-pick-ui-library` | — | Prefix frontmatter. |
| `prototype` | `emil-prototype` | `PICKER.md` | Prefix frontmatter and concrete sibling references. |
| `review-animations` | `emil-review-animations` | `STANDARDS.md` | Prefix frontmatter. |
| `write-swift` | `emil-write-swift` | — | Prefix frontmatter. |

The inventory above is from upstream `main` at commit
`d23d7f88a2e21c9e4b1418c7abe420f5c1052ba7`. Every published skill also carries
the upstream root `LICENSE` and a generated `MIRROR.md` containing source,
branch, commit, and published name. The upstream support files remain in their
skill package; no owned TheAngrySkills workflow logic is mixed into them.

This family exposes the complete upstream inventory for explicit project selection.
Mirror synchronization does not install or migrate local skills.

## Naming and refresh policy

The source is configured in `config/mirror-sources.json` as
`emilkowalski`, with destination `skills/mirrors-emilkowalski` and prefix
`emil-`. Generic names receive that prefix. Names that already start with
`emil-` are preserved exactly. In addition to path references, this family
rewrites exact hyphenated skill-name references so a mirrored skill such as
`emil-animate` routes to `emil-review-animations`, not to an unrelated global
`review-animations` skill. Common words such as `animate` are not rewritten.

The mirror is exposed as the separate `mirrors-emilkowalski` marketplace
plugin. It is not included in the owned `the-angry-core`,
`the-angry-engineering`, `the-angry-design`, or `founder-gtm` plugin surfaces,
and is not an owned default install set. Select it explicitly for a project.

The daily `Sync Curated Mirrors` workflow discovers new or removed upstream
skill directories and refreshes this family with the same deterministic
pipeline used for OpenClaw:

```bash
node scripts/sync-curated-mirrors.mjs --family emilkowalski
node scripts/sync-curated-mirrors.mjs --check
```

The first command requires network access and writes the mirror plus marketplace
entry in a working checkout. The second command is offline validation. Neither
command installs skills into an operator home, changes active Codex/OpenClaw
configuration, commits, pushes, or publishes a release.

## Verification record

- Upstream `main` resolved to `d23d7f88a2e21c9e4b1418c7abe420f5c1052ba7`.
- Mirror generation completed with 12 skills.
- `node scripts/sync-curated-mirrors.mjs --check` passed for all configured
  families, including OpenClaw and Emil.
- The repository pytest suite passed after the mirror-specific regression tests.
- Content verification compared upstream skill files against the deterministic
  frontmatter/path/name transformation, with LICENSE and support-file sets
  preserved.

## Security limitation

The local deterministic security scan is a separate admission gate and does not
declare this mirror safe merely because the content is upstream. The full
`skills` scan currently returns `blocked_malicious` because the repository also
contains baseline findings. In the Emil family specifically, the scanner flags
three upstream lines as `policy-bypass-instruction`: one in `emil-ask-sonner`
(the dark-mode table row), and one each in `emil-find-animation-opportunities`
and `emil-improve-animations` (their repository-content safety rule). These
lines are preserved upstream material, not silently removed or rewritten. Coordinator review classified these three findings as false positives: the
Sonner row describes a UI theme default, while both repository-content rules
explicitly reject the quoted injection attempt. None directs an agent to bypass
policy. The raw scanner result is retained; no scanner rules or upstream skill
instructions were weakened to obtain a passing verdict. This contextual review
covers these exact findings at the recorded upstream commit, not future updates.
