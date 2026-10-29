---
name: cursor-sharpen
description: "Use when the user explicitly requests $cursor-sharpen to frame a task through expert methods, intended outcome and appropriate constraints, then execute the authorized work."
---

## Runtime selection

Before runtime-dependent work, read [execution selection](references/runtime/selection.md). In a verified T3 host follow [the T3 contract](references/runtime/t3.md) and its method reference; the inline section below is the native Codex branch, not literal T3 dispatch. Outside T3, native Codex follows that inline branch unchanged. If the host is ambiguous or a required capability is unavailable, report the gap; a permission refusal never authorizes switching branches.

## Native Codex branch

Before starting, ask how a top expert would approach this task (their raw sources, their real methods, an outside check that the result is right), what the user is really after, and whether the task is over- or underspecified. Loosen constraints that don't serve the goal as readily as you add ones that do, and leave choices that are the user's to make open instead of deciding them. Fold in only what makes the work better, not bigger, but always keep one outside check that the result is right, without narrating the framing, then do the work.

## Codex boundaries

Respect explicit operator constraints and the requested tool or outcome. Loosening a proposed implementation detail does not authorize changing scope, access, cost, privacy or security. The outside check must be supported evidence (for example a focused test, source comparison or rendered inspection), not automatic external contact or delegation. Use native agents only when the task or governing workflow authorizes delegation, with model selection owned by `model-capability-router`.
