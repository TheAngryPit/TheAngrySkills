---
name: theangry-project-bootstrap
description: "Use when Vitor asks to create, normalize, or prepare a project folder, Chief of Staff project home, project AGENTS.md, README, GOAL, RESULT, operating folder, or durable project scaffold."
---

# TheAngry Project Bootstrap

Bootstrap a project so Codex can find it, operate inside it, and preserve project state without asking Vitor to route every message.

This skill is inspired by `new-project` from `jxnl/personal-monorepo-template`, but adapted to Echo, Obsidian, TheAngrySkills, standalone project roots, and Chief of Staff threads.

## Use When

Use when Vitor asks to:

- create a new project folder;
- prepare a project for a Chief of Staff thread;
- normalize an existing project;
- create project README or AGENTS files;
- create `OPERATING/`, `docs/`, or `outputs/` structure;
- prepare a project handoff packet.

## First Decision

Classify the target:

- Echo-internal project under `PROJECTS/`;
- standalone code/work project outside Echo;
- experiment or spike;
- skills/workflow project;
- editorial/knowledge project.

Do not force every project into the same tree.

## Required Reads

Read the target repo or folder first:

- root `AGENTS.md`, if present;
- root `README.md`, if present;
- existing `docs/`, `OPERATING/`, `outputs/`, `PROJECT_CONTEXT.md`, or project state files;
- Echo templates if the project has no stronger local convention.

## Default Echo Templates

- `WORKFLOWS/templates/project-readme.template.md`
- `WORKFLOWS/templates/project-agents.template.md`
- `WORKFLOWS/templates/goal.template.md`
- `WORKFLOWS/templates/result.template.md`
- `WORKFLOWS/templates/implementation-notes.template.html`

## Workflow

1. Identify project name, root path, purpose, status, lane, and lead-thread role.
2. Inspect existing files before writing.
3. Propose the smallest project scaffold that makes future agents effective.
4. Create or update only approved files.
5. Preserve existing project conventions.
6. Add human gates, proof expectations, source-of-truth order, output paths, and non-goals.
7. If creating a Chief of Staff first prompt, include the loop closure card:

```text
changed:
evidence:
needs review:
next decision:
next delegation:
```

## Guardrails

- Do not overwrite existing project state without inspection.
- Do not create a brand universe or architecture just because a folder exists.
- Do not add repo-local skills unless explicitly requested.
- Do not create external accounts, install packages, or contact anyone.
- Do not store raw private archives or sensitive data in public-safe project files.

## Output

Report:

- project root;
- files created or updated;
- source-of-truth order;
- human gates;
- next concrete action;
- proof level.
