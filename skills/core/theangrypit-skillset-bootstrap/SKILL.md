---
name: theangrypit-skillset-bootstrap
description: Install or update TheAngryPit skillsets on a new machine using the native npx skills CLI. Use when setting up Codex skills across devices, reinstalling TheAngryPit-owned skills, or bootstrapping known external skills through npx skills add.
---

# TheAngryPit Skillset Bootstrap

Use this skill to reproduce a known Codex skills setup on another device through
the native `npx skills` CLI.

This skill does not replace the native installer. It wraps it with small
manifests so the operator can install the same skillsets repeatedly.

## Install This Bootstrap Skill

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --skill theangrypit-skillset-bootstrap -g -a codex
```

## Dry-Run First

Dry-run is the default. It prints the exact `npx skills add` commands without
running them.

```bash
./scripts/install-skillset.sh skillsets/codex-main.tsv
```

## Apply

```bash
./scripts/install-skillset.sh skillsets/codex-main.tsv --apply
```

## Skillsets

- `skillsets/theangrypit-core.tsv`: default TheAngryPit operator workflow
  baseline for Codex.
- `skillsets/theangrypit-codex.tsv`: all TheAngryPit-owned operator workflow
  skills for Codex.
- `skillsets/external-known.tsv`: known external skills that are not copied into
  this repo.
- `skillsets/codex-main.tsv`: TheAngryPit core skills plus known external
  daily-use skills.

## Rules

- The scripts call `npx skills add`; they do not copy installed skill folders.
- HTTPS repo URLs are preferred for private repos unless SSH has been tested.
- The default mode is dry-run to avoid surprise installs.
- External skills stay external; this repo stores only the source URL and skill
  name.
- Avoid wildcard repo installs for mixed catalogs. Install named skills or a
  curated manifest instead.
- Use `scope=wizard` and `agent=wizard` when you want the native installer to
  ask its normal questions.
- Use `scope=global` and `agent=codex` when you want non-interactive global
  Codex install.

## Commands

List planned install commands:

```bash
./scripts/list-skillset.sh skillsets/codex-main.tsv
```

Install planned commands:

```bash
./scripts/install-skillset.sh skillsets/codex-main.tsv --apply
```

Update named installed skills from a manifest:

```bash
./scripts/update-skillset.sh skillsets/external-known.tsv --apply
```

Rows with `skill=*` are install-only. Native `skills update` updates installed
skills by name, so wildcard install rows are skipped by the update script.
