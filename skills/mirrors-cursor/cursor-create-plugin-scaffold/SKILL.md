---
name: cursor-create-plugin-scaffold
description: Create a new Cursor plugin scaffold with a valid manifest, component directories, and marketplace wiring. Use when starting a new plugin or adding a plugin to a multi-plugin repository.
---

# Create a bounded Cursor plugin scaffold

Create a static Cursor-format scaffold only inside an explicitly supplied project-local disposable root.

## Workflow

1. Require a lowercase kebab-case plugin name, purpose, target users, component set, license text, and destination.
2. Require the destination root to exist, be empty except for the adapter's marker, and remain inside the explicit project boundary.
3. Run the bundled `scripts/cursor_plugin_scaffold_fixture.py` adapter. It may create a manifest, README, supplied LICENSE, and static placeholders for rules, skills, agents, or commands.
4. Pass the generated plugin directly to `cursor-review-plugin-submission` or `scripts/cursor_plugin_submission_audit.py` and report the structural result.
5. Treat hook, MCP server, marketplace wiring, global plugin-home, installation, activation, and publication requests as `REVIEW_REQUIRED` before any write.

Never default to `~/.cursor`, install the plugin, enable active components, or claim that the scaffold is ready for marketplace submission. The source security finding remains retained for those active surfaces.
