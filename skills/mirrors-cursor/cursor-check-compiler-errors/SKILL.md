---
name: cursor-check-compiler-errors
description: Run compile and type-check commands and report failures
---

## Codex mirror boundary

Resolve the named skill, tool, connector, and account against what is actually available in this Codex session before following the upstream steps. Do not infer connection, authentication, credits, or runtime parity from this mirror. Preserve the external product named upstream and report a concrete missing capability when required.

# Check compiler errors

## Trigger

Compile or type-check failures are blocking local validation or CI.

## Workflow

1. Run the repo's compile and type-check commands.
2. Summarize errors by file and type.
3. Fix the highest-confidence issues first.
4. Re-run checks until clean or blocked.

## Output

- Current compile and type-check status
- Error summary grouped by file and category
- Fixes applied and remaining blockers
