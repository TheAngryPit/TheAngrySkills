# Cursor skill mirror

Source: https://github.com/cursor/plugins.git
Commit: c1c0a32802223f4be824112dd83d33ad29a8b26c
Physical source path: pstack/skills/create-verification-skill/SKILL.md
Upstream family README: https://github.com/cursor/plugins/blob/c1c0a32802223f4be824112dd83d33ad29a8b26c/pstack/README.md
Source SHA-256: 644f2551403c1bca01a2855b34611b6e7be0ce0dc5b204514c376c0f6a6e6ac4
Published name: cursor-create-verification-skill
Decision class: adaptação funcional
Availability: bounded explicit-only native adapter proven by an isolated CLI verification fixture and a disposable web target driven through the native in-app browser; project-local .agents/skills/verify-<app>/ generation, Doctor, feature drives, evidence preservation, cleanup ownership, controlled drift and second-run readback are observed; production target parity, reusable host activation and action-time reset remain unproven
License evidence: pstack/LICENSE

The raw source is in `sources/cursor-plugins/snapshot/`. This directory is
generated from that source and its exact per-skill overlay. External
products, connectors, credentials and automation runtimes remain external.
The decision class does not establish runtime availability.
