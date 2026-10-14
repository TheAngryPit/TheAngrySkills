---
name: openclaw-control-ui-e2e
description: "Use when changing or proving OpenClaw Control UI behavior with deterministic Gateway fixtures, browser flows and rendered evidence."
---

# Control Ui E2E

Codex adaptation of the pinned OpenClaw source. Repository-specific commands apply only to a verified OpenClaw checkout; portable debugger commands apply to their selected process.

## Repository and UI boundary
Use only in the selected OpenClaw checkout. Read root and scoped UI instructions, inspect current package scripts and the relevant UI owners before choosing commands. Use the packaged upstream workflow for test shape, mock patterns, Run Inspector and recording examples; resolve repository-owned imports in that checkout.

For substantial UI changes, prepare a fixture-driven state gallery covering relevant normal, empty, loading, error, permission, long-content and expanded/selected states. Label proposed/static states, preserve a baseline for comparisons, and give each example a stable feedback identifier. Keep gallery/recording output task-local unless explicitly selected for commit.

Use native Codex file/panel/browser tools for presentation and inspection; OpenClaw tools named in upstream material do not become Codex capabilities. Follow applicable effective-html/Impeccable guidance. Never replace required real interaction with a screenshot of a mock.

Run focused Vitest/Playwright proof through existing repository commands. Separate mocked-Gateway boundary evidence from real Gateway/product evidence and rendered-client evidence. Creating an isolated test state is different from touching the operator's live Gateway, account or data; preserve the applicable authorization.

Inspect the actual requested output and relevant wide/narrow states through an authorized surface, fix concrete defects and inspect again. If native rendering access is denied, preserve that refusal and report visual proof pending. Do not upload recordings without scoped publication authority and disclosure review.

## Selective installation

No mandatory installed companion from this pack is required. Checkout/runtime prerequisites and the conditional source references still apply.

## Source procedures and boundary

Read [the packaged upstream entrypoint](references/upstream/SKILL.source.md) when using this workflow; its supporting files remain beside it. This root owns Codex invocation, target resolution and authorization. Upstream examples are reference procedures, not grants of access, installation, deployment, publication or another model/provider. Use native Codex tools where capable and preserve an actual refusal. The operator's chosen model, project instructions and source-trust policy remain authoritative.

For repository-owned dependencies and original relative links, use [the source link map](references/upstream-link-map.json) against the verified checkout or its pinned GitHub reference. The pack does not claim that a linked release/channel skill or runtime is installed. Inspect the current owning source before executing a version-sensitive example.

[Provenance and adaptation record](PROVENANCE.md) identifies the source commit, retained resources and changes.
