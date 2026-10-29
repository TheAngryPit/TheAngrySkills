---
name: cursor-principle-migrate-callers-then-delete-legacy-apis
description: "Apply when introducing a new internal API while old callers still exist. Migrate callers and delete the old API in the same wave instead of preserving compatibility layers."
---

## Reference path base

Shell commands, bare/backticked paths and prose use the original skill root (two directories above this reference). References to the original file mean that root, including sibling skills and playbooks. Markdown link destinations are file-relative and have already been relocated; do not apply the command base to those links.


# Migrate Callers Then Delete Legacy APIs

- Update tests to assert the new contract, and delete tests that only protect pre-refactor implementation details

**When this applies:**
- No external users depend on backward compatibility
- The project can absorb coordinated breaking changes
- The new API is part of a simplification or refactor initiative
