---
name: theangrypit-skillset-bootstrap
description: Install or update TheAngryPit skillsets on a new machine using the native npx skills CLI. Use when setting up Codex skills across devices, reinstalling TheAngryPit-owned skills, or bootstrapping known external skills through npx skills add.
---

# TheAngryPit Skillset Bootstrap

Use this skill to reproduce a known Codex skills setup on another device through
the native `npx skills` CLI.

This skill does not replace the native installer. It wraps it with small
manifests so the operator can install the same skillsets repeatedly.

## Operator Default

For Vitor's normal setup, prefer the native interactive installer from the
public repo:

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git
```

When the wizard opens:

- Select the skills to install.
- Keep Universal `.agents/skills` targets included.
- Add the compatible additional agents Vitor uses for that machine, normally
  Codex plus compatible custom targets such as Claude Code, OpenClaw, Hermes
  Agent, and Pi when present.
- Choose global install.
- Choose symlink install.

Do not choose project-local install unless the operator explicitly asks for a
repo-local experiment.

Use this manifest to print or run the native wizard command:

```bash
./scripts/install-skillset.sh skillsets/theangrypit-native-wizard.tsv
./scripts/install-skillset.sh skillsets/theangrypit-native-wizard.tsv --apply
```

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
- `skillsets/theangrypit-native-wizard.tsv`: native interactive picker for
  Vitor's default global symlink installation flow.
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
- Use `skill=__wizard__` when you want the native installer to select skills,
  agents, global/project scope, and symlink/copy mode itself.
- The normal install source is the public `TheAngrySkills` repo. The private
  Workbench is for drafting, audits, mirrors, and promotion decisions.
- Do not manually rewrite symlinks as the normal migration path. Symlink
  surgery is only for broken installer state after a snapshot, exact path plan,
  and explicit operator approval.
- For migration, replace only installed skills whose canonical source is
  TheAngrySkills. Do not remove external/direct-upstream skills during a
  TheAngrySkills migration pass.

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
