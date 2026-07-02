---
name: aegis-communication-discipline
description: 'Use when project execution is drifting into noisy chat. USE FOR: "sparse project status", "proof-aware progress updates", "chat-not-ledger execution". DO NOT USE FOR: "general code review", "one-line answers", "pure HTML styling".'
disable-model-invocation: true
---

# Aegis Communication Discipline

Use this skill to keep project execution quiet, structured, and operationally honest.

## Contract

- Send one short start update before substantial work.
- During work, report only when operator-relevant state changes: blocker, scope change, proof-level change, durable checkpoint update, or operator decision needed.
- Put routine step detail into the active project ledger instead of chat.
- Use exact status terms: `validated`, `partial`, `canonical`, `superseded`, `unresolved`, `gated`, `drift`.
- Avoid filler, apologies, speculative narration, and repeated "still working" updates.

## Completion Criteria

The work is compliant when chat contains only operator-relevant updates and the durable project state contains the checkpoint detail needed for resume or review.

## Red Flags

- Chat is becoming the ledger.
- Status repeats without new operator-relevant information.
- The agent says "probably", "looks fine", or "should be good" where proof vocabulary is needed.
- The agent hides uncertainty instead of marking `unresolved`, `gated`, or `drift`.

## Boundary

This skill governs communication behavior. For the persistent checkpoint surface, pair it with `aegis-html-ledger` or the repo's existing ledger convention.
