---
name: echo-ingest-pattern-runner
description: Run governed echo-ingest knowledge patterns selected from an activation config. Use when the user asks to run, apply, activate, promote, execute, or compare Fabric-style patterns against a echo-ingest source, normalized note, manifest, or strategy packet.
---

# Echo Ingest Pattern Runner

Use this skill to apply selected analysis patterns without turning the Fabric catalog into uncontrolled bulk execution.

## Workflow

1. Locate the project that owns the echo-ingest workflow.
2. Read the activation config and pattern catalog before running anything.
3. Confirm each requested pattern is selected and not pending confirmation.
4. If a pattern is `active_manual_only`, run it only when the operator explicitly named it or supplied a reviewed selection list.
5. Prefer the project's existing echo-ingest CLI for packet creation and status updates.
6. If execution requires an LLM step, route through `$echo-ingest-codex-runner` or produce a prompt packet for explicit Codex execution.
7. Write generated outputs as derived artifacts, never as raw source.
8. Mark outputs as `needs_review` unless the operator explicitly approves promotion.

## Pattern States

- `active_candidate`: allowed for normal governed runs.
- `active_manual_only`: available, but only by explicit operator request.
- `pending_review`: do not run.
- `quarantined` or `blocked`: do not run.

## Fail Closed

Stop and report the blocker if:

- the activation config is missing;
- the pattern name is not in the catalog;
- the catalog hash no longer matches the activation record;
- the source manifest is missing;
- the run would mix raw private material into a final note;
- the requested step would publish, email, post, or contact anyone.

## Output

Report:

- patterns requested;
- patterns run;
- skipped patterns and reason;
- output artifact paths;
- proof level: `implemented`, `code_proven`, `test_proven`, `runtime_proven`, or `end_to_end_proven`;
- what needs operator review next.
