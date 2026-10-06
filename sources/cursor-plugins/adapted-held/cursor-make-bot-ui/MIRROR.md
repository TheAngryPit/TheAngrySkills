# Cursor skill mirror

Source: https://github.com/cursor/plugins.git
Commit: c1c0a32802223f4be824112dd83d33ad29a8b26c
Physical source path: pstack/skills/make-bot-ui/SKILL.md
Upstream family README: https://github.com/cursor/plugins/blob/c1c0a32802223f4be824112dd83d33ad29a8b26c/pstack/README.md
Source SHA-256: 3624c8ef16cf2e48deb2a4049e72c6962a9431c8d6c6af90e7bd7ea0375224ec
Published name: cursor-make-bot-ui
Decision class: adaptação nominal
Availability: safe local mock webhook adapter proves server-side key redaction, required headers, one-attempt timeout/error handling, and local payload validation; external connector, sender-key retrieval, routine wake, Tailscale state, and privileged install path remain unproven
License evidence: pstack/LICENSE

The raw source is in `sources/cursor-plugins/snapshot/`. This directory is
generated from that source and its exact per-skill overlay. External
products, connectors, credentials and automation runtimes remain external.
The decision class does not establish runtime availability.
