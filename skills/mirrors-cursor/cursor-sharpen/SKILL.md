---
name: cursor-sharpen
description: "Use when explicitly requesting $cursor-sharpen to deepen and rewrite a prompt without executing its task."
disable-model-invocation: true
---

## Runtime selection

Before runtime-dependent work, read [execution selection](references/runtime/selection.md). In a verified T3 host follow [the T3 contract](references/runtime/t3.md) and its method reference; the inline section below is the native Codex branch, not literal T3 dispatch. Outside T3, native Codex follows that inline branch unchanged. If the host is ambiguous or a required capability is unavailable, report the gap; a permission refusal never authorizes switching branches.

## Native Codex branch

Make the task deeper, not bigger. Before rewriting the prompt, state what a top professional would add, the rawest material they would use, the specific methods and tools, and an outside check that would show the result is right. Then return a rewritten prompt asking for exactly that. Leave the user's choices open. Do not execute the task described by the prompt.

Preserve explicit scope, access, cost, privacy, security and requested tools. The outside check is supported evidence, not automatic external contact, new credentials or delegation. Use the standing model-capability-router for any authorized model selection.
