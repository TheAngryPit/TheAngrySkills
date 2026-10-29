---
name: cursor-review-plugin-submission
description: Audit a Cursor plugin for marketplace readiness. Use when validating manifests, component metadata, discovery paths, and submission quality before publishing.
---

## Reference path base

Shell commands, bare/backticked paths and prose use the original skill root (two directories above this reference). References to the original file mean that root, including sibling skills and playbooks. Markdown link destinations are file-relative and have already been relocated; do not apply the command base to those links.


# Review a Cursor plugin submission

Perform a read-only structural audit of an explicitly supplied local Cursor plugin.

## Workflow

1. Run `python3 scripts/cursor_plugin_submission_audit.py <plugin-root>`.
2. Review manifest parsing and metadata, bounded relative component paths, component discovery, required frontmatter fields, and README presence.
3. Report `STRUCTURAL_PASS`, `REVIEW_REQUIRED`, `BLOCKED`, or `ERROR` exactly as returned, with the concrete issues.
4. Escalate hooks, MCP server declarations, active components, marketplace uniqueness, runtime behavior, and external publication for separate human review. Never execute them during this audit.
5. State that `STRUCTURAL_PASS` is a local structural result, not a marketplace acceptance or publication recommendation.

The adapter performs no activation, installation, network access, credential use, or external write. The upstream `needs_human_review` finding remains recorded for active submission surfaces.
