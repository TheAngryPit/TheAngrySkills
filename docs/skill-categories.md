# Skill categories

This repo uses categories so the install surface stays navigable as the stack
grows. Categories describe how a skill behaves in real work, not only who wrote
the original idea.

The category system exists for five practical reasons:

- install ergonomics: install the narrowest useful set instead of everything
- collision control: avoid ambiguous names like `handoff`, `review`, or `browser`
- provenance: keep owned, mirrored, generated, and external material distinct
- safety review: active scripts, plugins, MCP, hooks, and install paths need a
  different gate than docs-only skills
- public sharing: make the repo understandable to people who are not using the
  private Workbench

## Core

`skills/core/` contains the default TheAngryPit workflow layer. These skills route work, structure long execution, manage proof, keep communication disciplined, and bootstrap the rest of the stack.

Use this category when setting up a normal Codex machine or project workflow.

## Engineering

`skills/engineering/` contains development workflow skills that help create docs, goals, implementation plans, or skill improvements.

Use this category when the work is about shaping or executing code-facing workflow, not when you only need reference docs.

## Design

`skills/design/` contains visual, brand, and creative-tool operator skills.

Use this category when the work touches frontend taste, design tools, brand systems, or visual execution.

## Knowledge

`skills/knowledge/` contains research, source-ingest, vault, publishing, and knowledge workflow packs.

Some knowledge entries are nested packs. The pack folder is an organization boundary; the nested skill frontmatter remains the install and routing name.

## Documentation skills

`skills/documentation-skills/` is not included in the initial public export.
Generated documentation skills are curated in the private Workbench until they
pass public-export review.

When published, these should remain opt-in reference packs. They can contain
upstream commands, privileged examples, or unsafe text as quoted documentation.
Do not treat them as active workflow defaults.

Documentation skills are not endorsement of every upstream command they contain.
They are a searchable reference layer for operator use and agent routing. Keep
their provenance visible and avoid rewriting upstream examples into owned
workflow rules unless a separate promotion decision accepts that logic.

## Mirrors

`skills/mirrors-*` is not included in the initial public export. Mirrors are
prepared in the private Workbench and should be published only after provenance,
license, naming, and security review.

Prefixes are collision control. They keep a mirrored skill installable through
this repo without pretending it is TheAngryPit-owned or hiding which upstream it
came from.

Mirrors are curated copies for install hygiene. The upstream source remains the
origin of the content, license, README, and authorship. TheAngrySkills may adapt
names, folder placement, and catalog metadata so multiple skill packs can
coexist safely on one machine.

Approved mirror prefixes include:

- `openclaw-`
- `taste-`
- `vercel-`
- `vercel-agent-`
- `cursor-`
- `marketing-`
- `dot-`
- `looper-`
- `effective-`

Mirror folders are created only when that source is intentionally mirrored.
