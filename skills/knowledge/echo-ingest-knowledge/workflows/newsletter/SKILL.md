---
name: echo-ingest-workflow-newsletter
description: Prepare newsletter knowledge from echo-ingest sources. Use when source material should feed an editor-in-chief workflow, newsletter issue, content pipeline, segment, angle list, reading queue, or publishing decision without publishing automatically.
---

# Echo Ingest Newsletter Workflow

Use this skill to turn ingested sources into newsletter-ready knowledge without confusing research with final copy.

## Workflow

1. Confirm source intake artifacts exist. If not, use `$echo-ingest-source-intake`.
2. Classify the source role:
   - signal;
   - source link;
   - argument fuel;
   - example;
   - counterpoint;
   - future issue candidate.
3. Extract concise editorial value:
   - why it matters;
   - what claim it supports;
   - what audience would care;
   - what angle it suggests;
   - what should not be overstated.
4. Use `$echo-ingest-pattern-runner` only for selected patterns that help editorial judgment.
5. Send generated outputs to `$echo-ingest-result-review` before they become durable issue notes.

## Boundaries

- Do not publish.
- Do not write as if the issue is approved.
- Do not flatten Vitor's voice into generic tech commentary.
- Preserve source links and uncertainty.
- Keep personal/private material out of public drafts unless explicitly approved.

## Output

Return:

- issue or queue candidate;
- editorial angle;
- source role;
- usable bullets;
- risks or claim limits;
- next review action.
