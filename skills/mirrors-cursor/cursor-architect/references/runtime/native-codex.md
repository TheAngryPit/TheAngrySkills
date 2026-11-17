---
name: cursor-architect
description: "Sketch types, signatures, and module structure before code, then stay in the loop while implementation fills in. Use for /architect, 'architect this', 'design this', or non-trivial work where jumping to code would lock in the wrong shape."
---

## Reference path base

Shell commands, bare/backticked paths and prose use the original skill root (two directories above this reference). References to the original file mean that root, including sibling skills and playbooks. Markdown link destinations are file-relative and have already been relocated; do not apply the command base to those links.


# Architect

Before writing code, trace every system the change touches, then sketch two different shapes for it (types, signatures, module boundaries) and pick the one where each piece of state has one owner, each task has one way to do it, and callers need to know least. Redesign instead of patching if workarounds repeat.

For a large or contested design, run the **cursor-arena** skill instead of sketching alone.
