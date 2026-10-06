# Native requirements

Resolve each dependency by its exact exposed name or read its available SKILL.md. Distribution is not runtime activation. Missing dependencies stop their dependent step and must be reported. Do not install or substitute a product automatically.

| Workflow | Required capability |
|---|---|
| Shared Pstack | `cursor-poteto-mode`, its 23 playbooks, `cursor-principle-*` leaves, `cursor-bro`, `cursor-unslop` |
| Controls and cleanup | `cursor-control-ui`, `cursor-control-cli`, `cursor-verify-this`, `cursor-deslop` |
| Dylan delegates | Native `agent_type: "dyl-agent"`; source asset distributed through `model-capability-router`, separately installed and loaded by the host |
| Deep review | `cursor-thermos` and its independent bug/security and code-quality roles; separately available native Bugbot reviewer |
| Figma | Connected Figma MCP plus the exposed Figma design-to-code skill; inspect actual tool schemas |

Use the exposed `cursor-poteto-mode` directory for `playbooks/<name>.md`. Its siblings use exact `cursor-*` names. Routed workflow skills retain their role contracts. Native asynchronous completion replaces Cursor background tasks. If Bugbot is absent, report deep review incomplete; do not impersonate it with a generic reviewer.
