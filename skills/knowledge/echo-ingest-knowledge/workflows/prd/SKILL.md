---
name: echo-ingest-workflow-prd
description: Prepare PRD and implementation context from echo-ingest sources. Use when source packs, conversations, specs, articles, videos, or notes need to become a product brief, PRD input, issue context, implementation plan, or engineering handoff.
---

# Echo Ingest PRD Workflow

Use this skill to turn messy source material into product and engineering context without pretending decisions are already made.

## Workflow

1. Confirm intake artifacts exist. If not, use `$echo-ingest-source-intake`.
2. Extract:
   - user problem;
   - operator intent;
   - explicit requirements;
   - non-goals;
   - constraints;
   - proof bar;
   - open decisions;
   - implementation risks.
3. Classify each item as source-derived fact, inference, recommendation, or unresolved question.
4. Use selected patterns only when they clarify requirements, risks, alternatives, or test strategy.
5. Send generated PRD material to `$echo-ingest-result-review` before promoting it into repo docs.

## Handoff Shape

For engineering handoffs, include:

- context;
- goal;
- files or modules likely involved;
- constraints;
- exact acceptance criteria;
- proof required;
- what not to do;
- first safe implementation slice.

## Boundaries

- Do not create fake completeness from broad source dumps.
- Do not collapse operator taste into generic requirements.
- Do not skip human gates.
- Do not rewrite doctrine or project canon unless explicitly asked.

## Output

Return:

- PRD-ready summary;
- requirement table;
- open decisions;
- recommended first slice;
- proof plan;
- review status.
