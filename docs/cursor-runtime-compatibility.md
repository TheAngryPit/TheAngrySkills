# Cursor adaptation runtime compatibility

This is the existing reviewed Cursor mirror with an additional conditional T3 execution contract. Names, source snapshots and accepted pstack revision remain unchanged. It is not a live workflow certificate for every provider or playbook.

## Execution

Each skill selects its host through `references/runtime/selection.md`. Native Codex continues to use its inline native branch; an exact original is retained as `original-codex.txt`. In a verified T3 host the agent reads `t3.md` and the full method reference, translating runtime operations through that explicit contract. Relative links in relocated Markdown references preserve their original destinations. A permission refusal binds every branch.

Both Codex `agents/openai.yaml` and Claude's explicit-only frontmatter are preserved in their respective supported forms. This does not enable a session hook, sticky mode, timer, provider account, installation or model policy.

## Coverage and proof

| Context | Artifact support | Execution evidence |
| --- | --- | --- |
| Native Codex | Prior complete body and named native TOML assets retained | Existing baseline plus fresh regression proof; live acceptance is recorded separately |
| T3 | Conditional execution contracts, tool-owned isolation and persona delivery | Source/fixture proof; required live checks must be attached before release |
| Hermes | Deferred adapter identity | Unimplemented |
| OpenClaw native subagent | Deferred adapter identity | Unimplemented |
| OpenClaw native Codex embedding | Deferred adapter identity | Unimplemented |
| OpenClaw ACP | Deferred external-harness adapter identity | Unimplemented |

`sources/cursor-plugins/runtime-adapters/compatibility.json` records every published skill, required operations and all 14 mapped profiles. Current `partial` statuses do not claim universal T3 workflow parity. The maintained native Codex profile assets are unchanged. Portable profiles are instruction personas read in a T3 task brief, not registration of a native named agent type. The parent still controls scope, models, authorization, acceptance and every permitted spawn.

## Maintenance

Author changes in the reviewed runtime inputs and overlays. Run the existing `sync-cursor-plugin-skills.py` renderer; never patch installed or generated copies by hand. Admission checks validate published coverage, profile identity/digests, canonical runtime references, complete generated file sets and package hashes. An individual installed skill carries its selected persona files. A missing exact dependency remains an explicit gap.

The existing adapted-upstream detector remains report-only. Its source pins, report identities, canonical branch selection, review and exact-head finalizer remain unchanged. The curated one-to-one mirror refresh remains a separate ownership lane. New runtime inputs are reviewed source, not automatically promoted upstream text. No workflow permissions, schedules or triggers are changed.

## Rollback

Restore the previous reviewed adapter input and generator revision, regenerate through the existing deterministic build and validate its complete file set before any authorized deployment. Preserve source pins, native profiles, user homes, credentials and task history. A local source change does not itself roll back or replace an installed skill; fleet deployment is separate and requires versioned readback evidence.

## Bounded live evidence, 2026-10-29

[Proof receipt](../reports/cursor-runtime-proof-20261029.json) records T3/Codex portable Poteto execution in a tool-prepared worktree and read-only Comment Sicko persona delivery, with parent content/hash/runtime verification. Native Codex discovered107/107 enabled skills in an isolated home, and native named comment-sicko dispatch returned the same fixture recommendation. All14 native profile asset bytes remain unchanged. These are bounded operation proofs; other12 personas and other providers retain source/packaging proof only, not full workflow certification. No installed home was changed.

## Review and refresh protection

The independent Astra review identified three Important issues and one malformed-target issue, regraded Important. All four were addressed in one regression-tested fix pass; no second approval verdict is claimed. The final suite passed473 tests, with2 skips and13 subtests. The corrected clean-export security comparison records13 retained-content findings, no new blocked skills, and unchanged verdicts. The earlier working-tree17-signal conclusion was withdrawn because it included four ignored bytecode files.

Coverage now binds each source identity to the reviewed effective Codex body and support-file digest. A source refresh invalidates that review until its operations and required personas are inspected and the new digest is deliberately accepted. Do not blindly recompute hashes to silence drift. Generated runtime files and generated license/provenance notices are excluded from that workflow digest; they retain separate package, source and license checks.

## Installed pilot and coding workflow

The [follow-up proof](../reports/cursor-runtime-live-20261029/proof.json) records108 exact installed-package readbacks, fresh native discovery and bounded execution for the remaining12 portable personas. All14 personas now have bounded role evidence including the earlier Poteto and Comment Sicko probes. Their instruction delivery remains separate from native named-role registration. Existing explicit-only policy remains unchanged; automatic T3 catalog advertisement and picker UI were not established.

A full read-only Investigation playbook ran through How and parent runtime verification. The later Bug fix playbook used an explicitly disposable CLI fixture, not a product defect. The original CLI lost an explicit zero to a truthiness fallback. A named Poteto delegate fixed the one existing parser after the public-CLI regression was committed. The [failing](../reports/cursor-runtime-live-20261029/bugfix-red.log) and [passing](../reports/cursor-runtime-live-20261029/bugfix-green.log) outputs preserve the observed two-case result. This does not certify all23 playbooks, cross-provider workflows or PR event continuation.

## History-independent preservation checks

The first published CI run exposed an undeclared Git-history dependency in two preservation tests. They now exercise real generation in a source-only fixture and compare the complete protected inputs before and after. Native profile bytes must also match current accepted provenance. No workflow, checkout depth or update policy changed. This avoids freezing future reviewed upstream inputs to a historical commit. The [regression failure](../reports/cursor-runtime-live-20261029/historyless-red.log) and [focused pass](../reports/cursor-runtime-live-20261029/historyless-green.log) record the correction.

After this correction, the local full suite passed474 tests, with2 skips and13 subtests. The original473-test logs describe the earlier implementation stage. GitHub CI must validate the updated PR head independently.
