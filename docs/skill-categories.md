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

`skills/core/` contains the public-safe TheAngryPit workflow layer. These skills structure long execution, manage proof, keep communication disciplined, and preserve install hygiene.

Use this category when setting up a normal Codex machine or project workflow.

## Engineering

`skills/engineering/` contains development workflow skills that help create docs, goals, implementation plans, or skill improvements.

Use this category when the work is about shaping or executing code-facing workflow, not when you only need reference docs.

## Design

`skills/design/` contains visual and creative-tool operator skills.

Use this category when the work touches frontend taste, design tools, or visual execution.

## Knowledge

`skills/knowledge/` is reserved for knowledge workflow packs that are explicitly public-safe.

Private source-ingest, vault, editorial, personal voice, company strategy, and publication machinery stays in the private Workbench unless Vitor explicitly approves a sanitized public rewrite. Some future public knowledge entries may be nested packs. The pack folder is an organization boundary; the nested skill frontmatter remains the install and routing name.

## Founder GTM

`skills/founder-gtm/` contains preserved founder-led outreach and sales workflow
skills. These are curated local preservation skills, not a blind external mirror.

Use this category when the work is GTM, sales copy, warm intros, LinkedIn/X
outreach, or founder sales system design. Any outbound, email, social, CRM,
credential, or automation action still requires explicit human approval before
use.

## Documentation skills

Documentation skills are generated reference packs for projects, tools,
frameworks, and docs the operator wants available to agents.

They are maintained in the private Workbench and installed from there when
needed, not published in this public install surface. They can contain upstream
commands, privileged examples, or unsafe text as quoted documentation. Do not
treat them as active workflow defaults.

Documentation skills are not endorsement of every upstream command they contain.
They are a searchable reference layer for operator use and agent routing. Keep
their provenance visible and avoid rewriting upstream examples into owned
workflow rules unless a separate promotion decision accepts that logic.

## Mirrors

Mirrors are curated external skills, not generated docs and not owned workflow
logic. Public mirror promotion is selective: only accepted mirror families and
selected skills become installable here.

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
- `vercel-agent-`
- `marketing-`
- `looper-`
- `effective-`

Cursor is intentionally excluded from this public mirror family list. Install
Cursor skills directly from Cursor's source when needed.

OpenAI and Figma remain accepted future mirror families, but they should not be
published until their source and update path are explicit, reviewable, and
separate from local plugin cache state.

Mirror folders are created only when that source is intentionally mirrored.
