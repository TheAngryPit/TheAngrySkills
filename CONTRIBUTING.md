# Contributing to TheAngrySkills

TheAngrySkills is a personal skill stack with a public-facing install surface.
Contributions should make the stack safer, clearer, or easier to maintain
without turning it into a generic skill registry.

This repo is open source for installability, review, reuse, and security
analysis. Community issues and pull requests are welcome, but the stack remains
curated. A PR is a proposal for the operator-owned install surface, not a right
to add arbitrary skills.

## What fits

Good issues and pull requests usually do one of these things:

- fix a broken `npx skills` install or update path
- improve one existing skill while preserving its role
- add missing provenance, catalog metadata, or review notes
- improve security scanning, CI, or mirror hygiene
- clarify category, lifecycle, or bootstrap documentation
- propose a mirror only when the upstream source, prefix, and collision risk are clear

## What does not fit

Do not open issues or pull requests that:

- bulk-copy third-party skills without provenance and review
- add secrets, private paths, tokens, credentials, or local machine details
- rename installed skill names without migration notes
- flatten approved packs such as `themindshift` or `echo-ingest-knowledge`
- treat generated documentation skills as default workflow skills
- bypass the catalog, mirror, or security admission layers
- submit unrelated third-party skill packs for inclusion by default
- treat this repo as a general marketplace or public registry

## External mirrors and generated docs

Mirrors and generated documentation skills are curated install surfaces. They
exist so TheAngrySkills can control naming, prefixes, provenance, update paths,
and local install behavior.

When touching mirrors or generated docs:

- preserve upstream copyright, license, README, and attribution where present
- keep the source-specific prefix on mirrored skills
- do not mix owned workflow logic into mirrored upstream content
- do not promote a mirrored/generated skill into the owned core without a
  separate review decision
- classify suspicious upstream examples instead of silently deleting provenance

## Before changing files

1. Read `README.md` and `docs/skill-categories.md`.
2. Check whether the skill is owned, generated, mirrored, draft, or deprecated.
3. Keep changes narrow. One skill, one mirror family, or one docs surface per pull request is best.
4. Preserve upstream provenance for mirrored or generated content.
5. Do not edit a live installed skill folder and paste it back without checking the source-controlled version.

## Required checks

Run the focused checks that match your change:

```bash
node --check scripts/theangry-skills.mjs
python -m pytest -q tests
scripts/theangry-skills.mjs check --root skills --profile shared
```

For security-sensitive changes, also run a scan on the touched skill or mirror:

```bash
scripts/theangry-skills.mjs security scan <skill-path> --json
```

Use `scan-root` for release-style review, but do not assume every finding is malicious. Generated documentation skills can contain dangerous upstream text as inert reference material. Classify the finding instead of hiding it.

## Pull request standard

Every pull request should explain:

- what changed
- why it changed
- which skills, categories, mirrors, or catalog files were touched
- which checks passed
- what risk remains
- what was intentionally not done
- whether an agent helped create the change

Do not ask reviewers to infer safety from a green check alone. If a change affects install behavior, update behavior, external mirrors, scripts, or security scanning, spell out the path.

Pull requests from non-collaborators are not the default contribution path. If
you are proposing a new skill, mirror family, generated docs pack, or install
surface, open an issue first with the exact source, skill name, prefix, license,
and install path affected.

## License expectations

This repository uses the MIT License for owned TheAngrySkills content.

Third-party mirrors, generated docs, copied examples, upstream READMEs, and
adapted external skills must preserve upstream copyright, license, notices, and
provenance. Do not assume the repo MIT license relicenses upstream material.
