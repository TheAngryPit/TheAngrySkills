# TheAngrySkills

[![Skill stack CI](https://github.com/TheAngryPit/TheAngrySkills/actions/workflows/skill-stack-ci.yml/badge.svg)](https://github.com/TheAngryPit/TheAngrySkills/actions/workflows/skill-stack-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![npx skills](https://img.shields.io/badge/npx%20skills-TheAngrySkills-111111)](https://www.skills.sh/theangrypit/theangryskills)

My public skill stack for Codex, `npx skills`, and agent workflows that need
more discipline than a giant prompt.

This is not a universal skill registry. It is the installable public surface for
skills I actually use, maintain, or curate. Drafts, risky experiments, generated
docs, raw upstream mirrors, and operator-specific material are kept out of this
public repo unless they have been reviewed and deliberately promoted.

## The Short Version

This is my agent operating stack:

- **execution discipline** so long work does not dissolve into noisy chat
- **proof discipline** so "done" means something specific
- **skill hygiene** so useful workflows become reusable capability instead of
  one-off conversation residue
- **design operators** for frontend, visual systems, Penpot, and
  Illustrator-style work
- **curated external mirrors** when outside skills are useful but need prefixes,
  provenance, and install hygiene before sharing

The folder structure is part of the product. It keeps my owned workflow skills,
design/operator skills, knowledge packs, generated docs, and external mirrors
separate so they can be installed, reviewed, and updated without collisions.

## Why This Exists

Agents get better when useful workflow knowledge becomes durable:

- repeated failures become rules, scripts, or skills
- repeated checks become deterministic tools
- long work gets checkpoints instead of noisy chat
- skill catalogs stay reviewable instead of becoming a junk drawer
- public installs stay narrow, attributed, and security-reviewed

The point is not to collect every skill. The point is to keep a working stack
that can be installed, audited, and improved without losing provenance.

## How The Stack Is Organized

TheAngrySkills is organized by how a skill behaves in real work, not just by who
wrote it.

| Style | What it means | Examples |
|---|---|---|
| Operating core | Default agent discipline: checkpoints, proof, install hygiene | `proof-orchestrator`, `aegis-*` |
| Engineering workflow | Skills that shape code work, docs, or skill quality | `skill-catalog-curator`, `theangry-ai-code-audit`, `docs-skill-builder` |
| Design/operator | Skills for visual tooling and creative execution | `adobe-illustrator-operator`, `penpot-mcp-operator` |
| Curated mirrors | External skills kept source-prefixed so multiple packs can coexist | `openclaw-*`, `taste-*`, `vercel-agent-*`, `marketing-*` |

This matters because skill repos collide fast. Many packs eventually contain
their own `handoff`, `review`, `browser`, `plan`, or `ingest` skill. Prefixes
and categories make it clear what is mine, what is mirrored, what is generated,
and what is safe to install by default.

## Quickstart

### 1. Browse the public stack

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --list
```

Include nested mirror packs:

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --list --full-depth
```

### 2. Install one skill

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --skill skill-catalog-curator
```

### 3. Install one skill globally for Codex

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --skill skill-catalog-curator -g -a codex
```

## Wizard-Style Install Discipline

Use this repo like a guided setup, not like a blind package install:

| Stage | Human action | Gate |
|---|---|---|
| Choose | Pick one skill, a nested pack, or a curated skillset | Do not install everything by default |
| Inspect | Read the skill description, scripts, and install path | Stop if it touches secrets, host state, hooks, or network access |
| Dry-run | Use `--list`, `--full-depth`, or bootstrap dry-run scripts first | Confirm the exact commands before applying |
| Install | Install the narrowest useful set | Prefer local/project scope unless global is intentional |
| Verify | Run the skill once on a low-risk task | Promote to daily workflow only after it behaves correctly |

The workflow is simple: stage the procedure, show what will happen, confirm the
risky step, then make the result durable.

## What Is Inside

| Area | Path | What it is for |
|---|---|---|
| Core workflow | `skills/core/` | execution discipline, routing, proof, communication, skill hygiene |
| Engineering | `skills/engineering/` | code-facing helpers, skill authoring, docs and goal workflows |
| Design/operator | `skills/design/` | visual, Penpot, Illustrator, and creative operator skills |
| Founder GTM | `skills/founder-gtm/` | founder sales and outreach templates with human-gated use |

See [`docs/skill-categories.md`](docs/skill-categories.md) for category rules.

## Mirrors And Documentation Skills

Documentation skills are not published here by default. They are still part of
the operating model: when a tool or project matters, turn its docs into a
searchable, attributed reference pack instead of forcing an agent to improvise
from memory. Public documentation packs should be promoted deliberately, with
clear provenance and safety review.

External mirrors are different. They are curated external skills, not generated
docs. Only selected mirror families are promoted for public install. The public
stack should not become a blind dump of every mirrored skill from every source.

Operator-specific packs, unpublished workflow experiments, private knowledge
workflows, personal voice machinery, company/client strategy, and local
maintenance helpers stay out of this public repo unless a sanitized public
rewrite is reviewed and promoted deliberately.

The currently accepted mirror families for public curation are:

- OpenClaw skills, with `openclaw-` prefixes
- Taste skills, with `taste-` prefixes
- Vercel Agent Skills, with `vercel-agent-` prefixes
- Marketing skills, with `marketing-` prefixes
- Looper skills, with `looper-` prefixes
- Effective HTML skills, with `effective-` prefixes

When mirrors are published here, they should:

- keep source-specific prefixes such as `openclaw-`, `taste-`, or `vercel-`
- preserve upstream README, license, copyright, and notices
- avoid mixing owned TheAngrySkills workflow logic into upstream material
- stay clearly marked as curated mirrors, not original work

This matters because different skill packs often collide on names like
`handoff`, `review`, or `browser`. Prefixes keep installs legible.

## Contributing

This repo is open source, but still curated.

Good issues and pull requests usually:

- fix a broken `npx skills` install or update path
- improve one existing skill without changing its role
- add missing provenance, license, or safety notes
- improve tests, CI, scanner behavior, or docs
- propose a new skill with clear scope and no private/local leakage

`main` is protected. Community PRs are welcome as review inputs, but arbitrary
skills, mirrors, generated docs, and install surfaces will not be merged just
because they pass CI.

Every PR must clear the minimum safety gate in
[`docs/pr-safety-minimums.md`](docs/pr-safety-minimums.md).

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before proposing changes.

Use [Discussions](https://github.com/TheAngryPit/TheAngrySkills/discussions)
for broader questions, setup feedback, and ideas that are not yet concrete
issues or PRs.

## Security

Skills are executable instructions for agents. Scripts, workflows, install
commands, mirrors, generated docs, lifecycle hooks, and package managers are
supply-chain surfaces.

Before trusting a skill, check:

- what files it asks an agent to read or write
- whether it runs scripts or shell commands
- whether it changes host/global state
- whether it touches secrets, credentials, hooks, MCP servers, or CI
- whether its source and license are clear

Read [`SECURITY.md`](SECURITY.md) before reporting security-sensitive findings.

## License

Owned TheAngrySkills content is released under the [MIT License](LICENSE).

Future mirrored or generated third-party content must preserve its upstream
copyright, license, notices, and provenance. The MIT license for this repo does
not relicense third-party material.
