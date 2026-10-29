---
name: cursor-interrogate
description: "Use for \"interrogate\", \"adversarial review\", \"multi-model review\", \"challenge this\", \"stress test this code\", \"find blind spots\", or \"tear this apart\". Multiple LLM reviewers challenge changes from independent angles."
---

## Runtime selection

Before runtime-dependent work, read [execution selection](references/runtime/selection.md). In a verified T3 host follow [the T3 contract](references/runtime/t3.md) and its method reference; the inline section below is the native Codex branch, not literal T3 dispatch. Outside T3, native Codex follows that inline branch unchanged. If the host is ambiguous or a required capability is unavailable, report the gap; a permission refusal never authorizes switching branches.

## Native Codex branch

## Codex runtime mapping

This published workflow is explicit-only through `agents/openai.yaml`. Use the native Codex subagent capability for independent read-only reviewers only when delegation is authorized. Require one immutable scope and rubric, at least two distinct model requests accepted by native spawn, separate read-only outputs, and a coordinator lead judgment before claiming a bounded review. If a configured reviewer is missing or fails, mark the aggregate PARTIAL and name the slot; never fabricate multi-model consensus or a complete configured run. Follow the standing `model-capability-router` and the operator-selected model/effort; do not force the Cursor default model table. Record requested reviewer profiles and unavailable slots, and mark effective model/effort readback unavailable unless the native surface supplies it. Keep the source rubric, lead judgment, and no-auto-apply contract.

# Interrogate

Spawn one reviewer per configured model to adversarially review code changes. The adversarial signal comes from model diversity, not assigned personas. The deliverable is a synthesized verdict. Do NOT auto-apply changes.

## Step 1, Scope

Identify what to review from context:

- If the user points at specific files or a diff, use that.
- If on a feature branch, run `git diff main...HEAD` (or the appropriate base branch) for the full changeset.
- If the user's message references recent work, gather the relevant files.

Package the diff or file contents with any surrounding context files the reviewers need to understand the code.

## Step 2, Intent

Before spawning reviewers, state the intent in one clear paragraph from the user's message, commit messages, the PR description if one exists, and the code. If you're unsure about the intent, ask the user before proceeding.

## Step 3, Spawn Reviewers

Launch independent read-only reviewers through native Codex subagents when authorized. Use the actual available reviewers under the standing `model-capability-router` and the operator-selected model/effort; extend or shrink Reviewer A/B/C/D labels to match. Record unavailable reviewer slots.

| Reviewer | Native Codex model |
|----------|--------------------|
| A/B/C/D as available | Record the requested model and effort; record effective identity only if the native surface exposes authoritative readback |

- Assign a bounded review responsibility to each native subagent.
- Use a genuinely read-only role or instructions and verify no reviewer modified the workspace.
- Use native model selection only as allowed by the standing router and operator.

If a requested model is unavailable, record that reviewer as unavailable. Continue with authorized available reviewers only when the proof bar can still be met. Do not silently substitute a model or create a repair PR.

Read `references/reviewer-prompt.md` and fill in the same template for every reviewer with the stated intent, the diff or file contents, the rubric from `references/rubric.md`, and the code-quality lens from `references/code-quality-review.md`. Pick each subagent's reasoning level and fast or standard speed for the job, per the Subagents section of the **poteto-mode** skill.

## Step 4, Synthesize

As results come back, build a unified picture:

1. **Parse all findings** from the reviewers
2. **Identify consensus**. Findings raised independently by 2+ actual reviewers are high signal; describe model diversity only when it was actually present.
3. **Identify single-reviewer findings**. Still worth reading, but weight accordingly.
4. **Deduplicate**. Different models may describe the same issue differently. Merge these and note which models raised it.
5. **Note disagreements**. If one model flags something and another explicitly says the opposite, that's useful context for the verdict.

## Step 5, Lead Judgment

You are the lead reviewer, a pragmatic senior engineer, not a neutral aggregator. Read `references/lead-judgment.md` for the full framework. Put every finding in one of four buckets, with the model(s) that raised it and a one-line rationale.

- **Act on**. Real issues affecting correctness, security, or maintainability given the actual goals. They would block a real PR.
- **Consider**. Legitimate, but you're not sure they outweigh the cost of addressing them now. Worth the user's attention.
- **Noted**. Technically valid but not actionable. Context-dependent, premature optimization, or low-impact at this stage.
- **Dismissed**. Wrong, nitpicky, or missing context, with a brief reason.

## Output Format

### Intent
> [The stated intent paragraph from Step 2]

### Reviewers
- Reviewer [label]: [model name], [N findings] (one bullet per reviewer)

### Act On
[Each: description, which models raised it, why it matters.]

### Consider
[Each: description, which models raised it, the tradeoff.]

### Noted
[Brief list.]

### Dismissed
[Each with a brief rationale.]

### Agreement Map
[Where models agreed and diverged, and what that pattern tells us.]
