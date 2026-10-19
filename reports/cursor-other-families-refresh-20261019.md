# Cursor non-pstack adaptation refresh — 19 October 2026

Compared all 53 existing non-pstack skill directories, including support files, with official cursor/plugins main d457567332aa6989e753ea289f30ea2bfbc80bc0. Fifty-two are byte-identical. The X MCP guide and its pricing reference changed; no other existing skill package needs a source refresh.

The preserved new source covers built-in public reads, X Chat unread pagination, unsigned/plain events, message-request list/open/accept semantics, persistent-key consent, scheduled calls and pricing. The native overlay preserves actual connector discovery and host pricing, task-scoped reads, approved helper provisioning, secret-input requirements and authorization for state-changing operations. It does not activate X, install a helper, read credentials or perform account operations.

The two refreshed raw files are hash-pinned independently in reviewed-file-updates.json; the historical full-tree baseline remains unchanged. Complete-tree verification checks the historical Git inventory, current pstack family and each reviewed non-pstack blob against its source commit. No new skill or held source is admitted. Alternate Claude harness copies and the previously excluded Tailscale source remain outside the published catalog.

Generation and static adaptation checks pass: 112 physical skill sources, 107 published, five held, 14 mapped agents, zero unresolved links. Focused and full regression results are recorded in the completion checkpoint. Live connector operation and fresh-session selection remain unproven.

Verification: full repository suite 396 passed, 2 skipped, 11 subtests passed; focused suite 59 passed and 6 subtests passed. Five real-Git provenance cases pass after the schema guard. Generation and exact upstream Git validation pass. The X package security scan is safe_to_install with zero findings. Test audit/deslop found no remaining issue. Named Comment Sicko review returned no flags and made no edits. Independent isolated Codex review returned scoped-clean through P2; no live connector execution is claimed.
