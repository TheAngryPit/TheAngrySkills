---
name: model-routing-preset-builder
description: Use when someone wants to create, clone, explain, or customize a portable Codex model-routing preset based on their available models, preferred quality, speed, usage budget, agent roles, capabilities, fallbacks, and human gates.
---

# Model Routing Preset Builder

Build a complete, reviewable routing preset instead of scattering model choices
across prompts and agent files. Start from an example, then make every deviation
explicit.

## Build

1. Inventory the models, reasoning efforts, agent roles, skills, tools, and
   compute modes actually available. Mark unverified entries unavailable.
2. Ask for preferences on speed, quality, cost/usage, coordination, planning,
   implementation, review, memory work, and exceptional compute.
3. Copy either `assets/vitor-opinionated.toml` or
   `assets/neutral-balanced.toml`. Never edit the bundled example in place.
4. Adjust routes and fallbacks. Keep reader-facing `Light` mapped to TOML
   `low`. Preserve at least one available fallback for every optional model.
5. Record capability requirements by stable names, not local filesystem paths.
6. Validate with the sibling `model-capability-router` script:

```bash
python3 <model-capability-router>/scripts/route.py validate --preset <preset.toml>
```

7. Show a route matrix and ask the operator to approve the preset before it
   becomes a default.

## Required Routes

Cover `micro`, `exploration`, `bounded_worker`, `coordination`, `debugging`,
`planning`, `hard_implementation`, `review`, `audit`, `release`,
`memory_worker`, and `memory_curator`. A custom preset may add routes but should
not silently remove these branches.

## Gates

`max` and `ultra` remain operator-authorized modes. A preset may describe when
they help, but must not select them automatically. Capabilities that mutate the
host, access secrets, deploy, publish, spend money, or cross accounts require an
explicit gate independent of model choice.

## Completion Contract

Return the preset path, its base example, every changed route, unavailable
models and fallbacks, capability gaps, validation result, and approval status.
