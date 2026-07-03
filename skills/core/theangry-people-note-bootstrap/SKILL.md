---
name: theangry-people-note-bootstrap
description: "Use when creating or updating public-safe people or agent notes for TheAngryPit, Echo, TheHive, or project lead threads. Avoids secrets, sensitive private memory, and unsupported claims."
---

# TheAngry People Note Bootstrap

Create durable, public-safe notes about humans, collaborators, partners, and agents.

This skill is inspired by `new-person` from `jxnl/personal-monorepo-template`, but adapted to Echo and TheAngryPit privacy boundaries.

## Use When

Use when Vitor asks to:

- add a collaborator;
- create a person profile;
- remember how someone works;
- create a project agent note;
- document a specialist thread;
- prepare a public-safe handoff note for a person or agent.

## Target Files

Default locations:

- Echo vault: `PEOPLE/<slug>.md`
- Standalone project: `people/<slug>.md` or the project's accepted people/agents folder
- Agent note: use the agent-note template where available

Use existing project conventions when they exist.

## Required Templates

Prefer:

- `WORKFLOWS/templates/person-note.template.md`
- `WORKFLOWS/templates/agent-note.template.md`

If the target repo has its own templates, inspect those first.

## Privacy Rules

Do not store:

- secrets, credentials, tokens, private contact details, or account data;
- sensitive health, family, legal, or financial details;
- raw private transcripts or copied private messages;
- unsupported speculation presented as fact;
- anything unsafe or unfair to expose in a project handoff.

Mark inferred context as inference.
Add `Last verified` when facts can drift.

## Workflow

1. Identify whether this is a person note or agent note.
2. Inspect the target repo's existing people/agent conventions.
3. Choose a lowercase hyphenated slug.
4. Create or update only the smallest useful note.
5. Include role, working context, preferences, ongoing threads, boundaries, source notes, and last verified date.
6. If useful context would require sensitive material, stop and say the note is not safe for this public-safe layer.

## Output

Report:

- created or updated file;
- what source/context was used;
- what was intentionally excluded for privacy;
- what still needs Vitor confirmation.
