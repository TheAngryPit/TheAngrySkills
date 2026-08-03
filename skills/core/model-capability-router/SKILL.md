---
name: model-capability-router
description: Use when a task needs a model, reasoning effort, agent role, skill or tool capability chain, fallback, proof bar, or escalation selected from an approved routing preset and the capabilities currently available in the environment.
---

# Model Capability Router

Route from task requirements and current availability, not from model prestige.
The preset is policy; fresh inventory is runtime truth.

## Route

1. Locate the nearest operator-approved preset. Use an explicit path when more
   than one exists. Do not silently treat a bundled example as approved policy.
2. Classify the task into one route. If classification is ambiguous, state the
   two candidates and ask before choosing the more expensive one.
3. Discover relevant skill names from the current session or run `inventory`
   with explicit skill roots. Never infer a capability from an old catalog.
4. Run:

```bash
python3 scripts/route.py resolve \
  --preset <preset.toml> \
  --route <route> \
  --available-model <model> \
  --skill-root <skills-root>
```

5. Use the first available primary/fallback model. Attach the named agent role,
   required capability chain, gate, and proof bar.
6. If no valid model or required capability exists, return `blocked`; do not
   substitute an unlisted model or generic skill.

For a route whose preset sets `operator_authorization_required = true`, resolve
it only after explicit authorization in the current task and pass
`--operator-authorized`. Without that flag the router must return `blocked`.

## Escalation

Escalate one route at a time when fresh evidence shows the current route cannot
meet the proof bar. `max` and `ultra` require explicit operator authorization in
the current task and never expand permissions, targets, credentials, or scope.
The preset must also mark every route that can select either effort with
`operator_authorization_required = true`.

## Output Contract

Return:

- selected route, model, effort, and agent role;
- fallback used and why;
- capability chain with available/missing status;
- sandbox, approval, and human gates;
- proof bar and escalation trigger;
- preset name/version and availability evidence.
