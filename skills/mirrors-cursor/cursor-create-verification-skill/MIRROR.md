# Cursor skill mirror

Source: https://github.com/cursor/plugins.git
Commit: d457567332aa6989e753ea289f30ea2bfbc80bc0
Physical source path: pstack/skills/create-verification-skill/SKILL.md
Upstream family README: https://github.com/cursor/plugins/blob/d457567332aa6989e753ea289f30ea2bfbc80bc0/pstack/README.md
Source SHA-256: d353973547bf8ad8977eca645f4cd4feaed0d32f4b43d1448f906b0a76c4d694
Published name: cursor-create-verification-skill
Decision class: adaptação funcional
Availability: bounded explicit-only native adapter proven by an isolated CLI verification fixture and a disposable web target driven through the native in-app browser; project-local .agents/skills/verify-<app>/ generation, Doctor, feature drives, evidence preservation, cleanup ownership, controlled drift and second-run readback are observed; production target parity, reusable host activation and action-time reset remain unproven 0.15.28 source refresh; prior runtime and fixture evidence predates this refresh.
License evidence: pstack/LICENSE

The raw source is in `sources/cursor-plugins/snapshot/`. This directory is
generated from that source and its exact per-skill overlay. External
products, connectors, credentials and automation runtimes remain external.
The decision class does not establish runtime availability.
