---
name: ask-pit
description: "Router for PIT/Hive workflow skills. WHEN: \"Ask PIT\", \"which skill should I use\", \"choose a workflow\", \"start a design task\", \"plan proof\", \"handoff flow\"."
disable-model-invocation: true
---

# Ask PIT

Ask PIT chooses the next skill or short skill chain for the PIT/Hive workflow.

It is based on the idea of Ask Matt, but it routes across the full selected skill set for Helio:

- Plannotator / effective-html: 3 skills
- Taste Skill Pack: 13 skills
- Matt Pocock: 30 skills
- Cursor plugins: 2 skills
- TheAngryPit / Angry Skills: 75 skills
- shadcn / improve: 1 skills
- shadcn / ui: 1 skills

The full catalog lives in [references/catalog.md](references/catalog.md). Read it only when the user asks for the full list or when the common routing rules below are not enough.

## Output contract

When the user asks what to run, answer with:

1. The next skill, or at most three skills in order.
2. Why that route fits the job.
3. The exact first prompt the user should paste into Codex.
4. What proof or handoff to ask for at the end.

Do not list the whole catalog unless the user asks for the catalog. Pick a route.

## Routing rules

### Starting a new project or client job

Use `setup-matt-pocock-skills` only when a repo needs the Matt Pocock workflow setup.

Use `grill-with-docs` when there is an existing repo, folder, brief, or source material and the first job is to clarify the work.

Use `grill-me` when the idea is still conversational and there is no project folder yet.

Use `to-prd` after the goal is clear and the work needs a durable product/spec document.

Use `to-issues` after a PRD exists and the work needs executable issues.

Use `implement` only when the task is already specific enough to build.

### Learning and course work

Use `teach` when Helio is learning a workflow over multiple sessions.

Use `scaffold-exercises` when the lesson needs hands-on exercises rather than explanation.

Use `writing-great-skills` when the task is to improve a skill or understand skill-writing quality.

### Design, UI and visual work

Use `design-taste-frontend`, `gpt-taste`, `stitch-design-taste`, `high-end-visual-design`, or `taste-skill` when the decision is visual quality, interface direction, or taste.

Use `html`, `html-plan`, or `html-diagram` when the deliverable should be a local browser artifact, visual explainer, diagram, or plan.

Use `shadcn` when the project uses shadcn/ui components or the user asks to add/search/fix shadcn components.

Use `improve` when the user wants an advisor-style audit and implementation plans for another agent, not direct implementation.

### Writing cleanup and quality pass

Use `unslop` for prose, prompts, specs, PRDs, documentation, course text, or final summaries that feel AI-generated.

Use `deslop` for code diffs and generated implementation artifacts that need cleanup without changing behavior.

### Documentation and repo-specific knowledge

Use the relevant TheAngryPit docs skill when the user asks about a tool or internal technical area, for example `openclaw-docs`, `gbrain-docs`, `litellm-docs`, `n8n-docs`, `openbao-docs`, or `shadcn-ui-docs`.

Use `skills-sh-docs`, `docs-skill-builder`, `skill-catalog-curator`, or `theangry-refresh-docs-skills` when the work is about maintaining the skill catalog itself.

### Proof, review and handoff

Use `review` when the user asks for code review.

Use `proof-orchestrator` when the user needs evidence that something works.

Use `handoff` when work must move to another thread, another person, or another machine.

Use `openclaw-handoff`, `openclaw-agent-transcript`, `openclaw-autoreview`, or `openclaw-session-viewer` only for OpenClaw-specific work.

## Default first prompts

If the user is starting from a vague idea:

```text
Ask PIT: escolhe o melhor skill ou sequência curta para transformar esta ideia em trabalho claro. Quero primeiro perguntas, depois um plano pequeno, e só depois execução.
```

If the user is starting from a client/design task:

```text
Ask PIT: tenho esta tarefa de design/cliente. Escolhe a sequência de skills certa para clarificar, decidir direção visual, produzir o artefacto e pedir prova no fim.
```

If the user is blocked:

```text
Ask PIT: estou bloqueado neste ponto. Diz-me que skill devo correr, que informação falta, e qual é o próximo passo mais pequeno que desbloqueia isto.
```

## Safety

Do not approve installs, network access, secrets, or destructive commands. If the route needs one of those, say what is needed and ask for explicit approval.
