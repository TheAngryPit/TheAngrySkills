---
name: echo-ingest-result-review
description: Review echo-ingest knowledge outputs before promotion. Use when generated notes, pattern outputs, strategy results, summaries, or extracted claims need acceptance, edits, rejection, promotion, or cockpit review status updates.
---

# Echo Ingest Result Review

Use this skill to decide what can move from generated output into a durable vault note.

## Review Order

1. Read the source manifest first.
2. Read the generated output second.
3. Check whether claims are traceable to source evidence.
4. Separate facts, interpretation, recommendations, and open questions.
5. Mark each output as one of:
   - `accepted`
   - `needs_edit`
   - `rejected`
   - `manual_only_reference`
6. Promote only accepted material into final notes.
7. Keep raw artifacts and private transcript material out of final notes unless the operator explicitly approves quoting.

## Acceptance Criteria

An output can be accepted when:

- the source is identified;
- private content is not overexposed;
- factual claims are supported;
- the note has a clear purpose in the vault;
- generated interpretation is labeled as interpretation;
- next action, if any, is explicit.

## Common Fixes

- Replace long excerpts with short summaries.
- Split source facts from strategy recommendations.
- Move uncertain claims into open questions.
- Mark high-sensitivity material as review-only.
- Keep noisy pattern output as a side artifact instead of promoting it.

## Output

Report:

- accepted items;
- items needing edits;
- rejected items and why;
- exact final-note files changed or proposed;
- cockpit/status updates needed;
- remaining review questions for the operator.
