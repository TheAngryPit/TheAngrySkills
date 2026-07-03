# Upstream Penpot AI Kit

Source: `https://github.com/penpot/penpot-ai-kit`

Status: official Penpot-adjacent AI workflow kit, useful as reference material. Do not install or copy blindly into live brand workflows without review.

## What It Adds

The kit is not just MCP setup. It adds an agent operating layer around Penpot MCP:

- an `AGENTS.md` style rule surface;
- a catalog of Penpot skills;
- workflows that chain skills;
- prompt templates for better briefs;
- install/update/verify/uninstall lifecycle guidance;
- safety posture around MCP keys and client config;
- checkpoint behavior where the assistant previews or reports before continuing.

## Useful Skill Categories

The upstream catalog includes patterns worth adapting:

- `penpot-foundations`: create token systems for color, spacing, type and themes.
- `penpot-component-factory`: create tokenized components with variants and states.
- `penpot-build-screen`: design screens from structured briefs.
- `penpot-build-from-code`: rebuild app screens/components into Penpot.
- `penpot-document-handoff`: add handoff annotations without touching the design.
- `penpot-audit-accessibility`: WCAG-style audit.
- `penpot-audit-tokens`: find hardcoded/off-system values.
- `penpot-design-to-code-review`: compare design with real implementation.
- `penpot-migrate`: Figma to Penpot migration pattern.
- `penpot-rename-layers`: safe housekeeping.
- `penpot-router`: route unclear requests to one workflow.

## Adaptation Rule

Use the upstream kit as structure and vocabulary, not as automatic authority.

For owned brand work:

- preserve brand canon and visual DNA;
- keep product, lab, company, and community surfaces distinct;
- keep public/internal boundaries;
- do not expose MCP keys or private source material;
- do not install the kit or mutate client config without explicit approval;
- use the kit's review/checkpoint model for live Penpot edits.

## Practical Decision

The local `penpot-mcp-operator` skill should remain the thin low-level operator skill.

If Penpot becomes a main workflow, create or import a second layer later:

- `penpot-foundations-brand`
- `penpot-brandbook-builder`
- `penpot-screen-builder`
- `penpot-audit-and-handoff`

Do this after validating that the upstream kit's skill format is compatible with the local Codex skill loader and the target repo conventions.
