# TheAngrySkills

[![Skill stack CI](https://github.com/TheAngryPit/TheAngrySkills/actions/workflows/skill-stack-ci.yml/badge.svg)](https://github.com/TheAngryPit/TheAngrySkills/actions/workflows/skill-stack-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![skills.sh](https://skills.sh/b/TheAngryPit/TheAngrySkills)](https://skills.sh/TheAngryPit/TheAngrySkills)

My public skill stack for Codex, `npx skills`, and agent workflows that need
more discipline than a giant prompt.

This is not a universal skill registry. It is the installable public surface for
skills I actually use, maintain, or curate. Drafts, risky experiments, generated
docs, private reports, and raw upstream mirrors are reviewed in a private
Workbench before anything is exported here.

## Why This Exists

Agents get better when useful workflow knowledge becomes durable:

- repeated failures become rules, scripts, or skills
- repeated checks become deterministic tools
- long work gets checkpoints instead of noisy chat
- skill catalogs stay reviewable instead of becoming a junk drawer
- public installs stay narrow, attributed, and security-reviewed

The point is not to collect every skill. The point is to keep a working stack
that can be installed, audited, and improved without losing provenance.

## Quickstart

### 1. Browse the public stack

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --list
```

Include nested packs such as `themindshift` and `echo-ingest-knowledge`:

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

### 4. Bootstrap a curated set

Install the bootstrap skill first:

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --skill theangrypit-skillset-bootstrap -g -a codex
```

Then dry-run a curated skillset before applying it:

```bash
./skills/core/theangrypit-skillset-bootstrap/scripts/list-skillset.sh theangrypit-core.tsv
```

Apply only after reviewing the printed commands:

```bash
./skills/core/theangrypit-skillset-bootstrap/scripts/install-skillset.sh theangrypit-core.tsv --apply
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

This mirrors how the private Workbench operates: stage the procedure, show what
will happen, confirm the risky step, then make the result durable.

## What Is Inside

| Area | Path | What it is for |
|---|---|---|
| Core workflow | `skills/core/` | execution discipline, routing, proof, communication, skill hygiene |
| Engineering | `skills/engineering/` | code-facing helpers, skill authoring, docs and goal workflows |
| Design/operator | `skills/design/` | visual, brand, Penpot, Illustrator, and creative operator skills |
| Knowledge packs | `skills/knowledge/` | ingest, synthesis, editorial, PRD, and publishing loops |

See [`docs/skill-categories.md`](docs/skill-categories.md) for category rules.

## Mirrors And Generated Docs

External mirrors and generated documentation skills are not part of the initial
public export. They stay in the private Workbench until their license,
provenance, prefix, prompt-injection risk, local-path risk, and scanner findings
are reviewed.

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

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before proposing changes.

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
