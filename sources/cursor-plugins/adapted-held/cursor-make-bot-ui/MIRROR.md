# Cursor skill mirror

Source: https://github.com/cursor/plugins.git
Commit: 4dd1d05818d19792e7cd6e818f1667f95f7e1dbe
Physical source path: pstack/skills/make-bot-ui/SKILL.md
Upstream family README: https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/README.md
Source SHA-256: ad19d0bc6764287ec08c2521701974e7dac941f72e4d0fe81a24f4614494586f
Published name: cursor-make-bot-ui
Decision class: adaptação nominal
Availability: safe local mock webhook adapter proves server-side key redaction, required headers, one-attempt timeout/error handling, and local payload validation; external connector, sender-key retrieval, routine wake, Tailscale state, and privileged install path remain unproven Reviewed source refresh; prior runtime and fixture evidence predates this refresh.
License evidence: pstack/LICENSE

The raw source is in `sources/cursor-plugins/snapshot/`. This directory is
generated from that source and its exact per-skill overlay. External
products, connectors, credentials and automation runtimes remain external.
The decision class does not establish runtime availability.
