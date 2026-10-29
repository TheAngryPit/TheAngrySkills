---
name: cursor-how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
---

## Reference path base

Shell commands, bare/backticked paths and prose use the original skill root (two directories above this reference). References to the original file mean that root, including sibling skills and playbooks. Markdown link destinations are file-relative and have already been relocated; do not apply the command base to those links.


## Codex runtime mapping

Use native read-only subagents only when authorized; the standing `model-capability-router` owns model and effort. Preserve simple versus complex paths, distinct exploration angles, cited synthesis and coordinator verification.

# How

Explore the codebase to answer how a subsystem works. Give a senior engineer enough of a mental model to start changing it without turning the explanation into annotated source.

Choose model and effort through the standing `model-capability-router` and the native Codex inventory. Respect the operator's selection. If a requested model is unavailable, report that exact gap without substituting another model.

## 1. Assess complexity

If scope is ambiguous, state the interpretation and explore. The user can redirect.

- **Simple:** one module, small utility, or narrow question. Do not spawn explorers. If native delegation is authorized and useful, use one read-only explainer with `references/explainer-prompt.md`; otherwise inspect and explain directly. Then go to step 4.
- **Complex:** a subsystem spanning files or services, a cross-cutting feature, or a full architecture overview. Continue to step 2.

When in doubt, take the simple path.

## 2. Explore complex questions

When native delegation is authorized, investigate two to four distinct angles in parallel with read-only delegates. Choose model and effort through `model-capability-router`. Give each delegate a bounded angle and the explorer prompt in `references/explorer-prompt.md`. If delegation is unavailable, investigate the same angles sequentially and keep their evidence separate. Do not ask one explainer to repeat exploration after these findings exist.

## 3. Synthesize complex questions

After explorers return, combine their cited findings in the coordinator or one read-only native synthesizer selected through `model-capability-router`. Give it every finding and `references/explainer-prompt.md`. Resolve contradictions by checking the source. The coordinator owns the explanation and verifies its source paths. Simple questions skip this synthesis step because their one explainer already produced the account.

## 4. Present

Check the cited source paths and explain the result in the requested scope. Correct factual errors before presenting it. Use only the applicable sections from `references/explainer-prompt.md`: Overview, Key Concepts, How It Works, Where Things Live, and Gotchas.