# TheAngrySkills

The Angry Pit personal skill stack for Codex, `npx skills`, and agent workflow
experiments that survived enough review to be installable.

This is not a universal skill registry. It is the public install surface for the
skills I actually use or curate. The private Workbench remains the place where
drafts, generated docs, mirrors, reports, and risky experiments are reviewed
before anything is exported here.

## What This Repo Is

TheAngrySkills gives my agent workflow a controlled shape:

- owned workflow skills for execution, proof, communication, and skill hygiene
- engineering skills for creating, reviewing, and improving agent-facing work
- design/operator skills for visual and creative tooling
- knowledge workflow packs for ingest, synthesis, and publishing loops
- public contribution and security rules that keep the install surface narrow

The public repo is deliberately smaller than the private Workbench. If a skill,
mirror, or generated docs pack is not here, it has not been accepted into the
public install surface yet.

## Install

List available skills:

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --list
```

List nested skill packs too:

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --list --full-depth
```

Install one skill:

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --skill skill-catalog-curator
```

Install one skill globally for Codex:

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --skill skill-catalog-curator -g -a codex
```

Install the bootstrap skill:

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --skill theangrypit-skillset-bootstrap -g -a codex
```

Then dry-run a curated skillset:

```bash
./skills/core/theangrypit-skillset-bootstrap/scripts/list-skillset.sh theangrypit-core.tsv
```

Apply only after reviewing the printed commands:

```bash
./skills/core/theangrypit-skillset-bootstrap/scripts/install-skillset.sh theangrypit-core.tsv --apply
```

## Categories

- `skills/core/`: default TheAngryPit workflow layer.
- `skills/engineering/`: code-facing workflow and skill-building helpers.
- `skills/design/`: visual, design, and creative-tool operator skills.
- `skills/knowledge/`: source ingest, synthesis, and publishing workflow packs.

See [`docs/skill-categories.md`](docs/skill-categories.md) for category rules.

## Mirrors And Generated Docs

External mirrors and generated documentation skills are not part of the initial
public export. They are curated in the private Workbench first because they can
carry upstream licensing, provenance, prompt-injection, local-path, or
secret-scanner risk.

When mirrors are published here, they should keep source-specific prefixes such
as `openclaw-`, `taste-`, or `vercel-` so installed skills do not collide.

## Contributing

This is an operator-owned stack, not an open marketplace. Issues are useful for
broken installs, unsafe behavior, provenance problems, and focused proposals.
Pull requests may be restricted to collaborators.

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before proposing changes.

## Security

Skills are executable instructions for agents. Scripts, workflows, install
commands, mirrors, generated docs, lifecycle hooks, and package managers are
supply-chain surfaces.

Read [`SECURITY.md`](SECURITY.md) before reporting security-sensitive findings.
