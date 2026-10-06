# Benny native Codex adaptation — 6 October 2026

Base: c4be1f96a8fac6c8280bc81182cfa334109ebc4e. Upstream: cursor/plugins df581122cde17e6e27686b5a448bde23e4ad4318. The operator selected the three formerly excluded Benny workflows; the five other exclusions remain unchanged. Original exclusion reasons are preserved as history in the manifest.

The three explicit-only packages preserve triage, trusted-marker waiting, ownership and existing-fix gates, two independent real-UI reproductions, tracker compensation, coordinator-only Slack posting, bounded code edits, draft-only PRs and cleanup. Setup carries a complete portable native pack. Its three direct instruction files use instructions.md rather than SKILL.md to avoid nested skill discovery. Project-owned configuration remains outside managed resources; live prompts use committed target-relative paths, not source-repository or plugin-cache locations.

The support bundler's exact hash ledger now covers the 12-file Benny subtree. Raw upstream files and all 14 agent mappings are unchanged. Preview includes explicitly published source-dormant packages while the upstream distribution declaration remains factual. Generated catalog: 102 emitted, 5 held, 107 physical skills.

Trigger normalization accepts message_ts or ts only when supplied aliases agree, rejects child events and freezes the original root. Its regressions failed before repair; the portable-package regression failed against the merged base. The helper still performs no external writes or activation and is not a live automation runner.

The exposed Codex scheduling API lacks Slack message-event triggers. Source delivery does not silently convert event semantics to polling. Actual event delivery, connector authentication, parent preflight, dedupe, compensation, worker isolation and real-UI baseline/patched operation remain runtime setup requirements. This source update installs nothing, creates no automation and uses no credentials or external integration actions.

Validation: full repository suite 360 passed plus 5 subtests; deterministic generation passes (490 output files), complete upstream tree passes (903 files), adaptation coverage passes with zero unresolved links, catalog checks and JavaScript syntax pass, and git diff --check passes. Independent native Astra review found two setup wording defects; both were corrected and the reviewer cleared the final source. Detailed security findings of existing packages are unchanged; all three new packages have zero findings. See cursor-benny-security-20261006.json. Live runtime proof is not claimed. Agent-assisted adaptation and review preserve upstream attribution and license.

## Remote Codex review corrections

Both P2 findings at candidate4fafd2e were reproduced and fixed at the generator boundary. compare-upstream now checks every admitted support-ledger hash, reporting modified, missing or symlinked support files with a nonzero result. The detached pack receives LICENSE.upstream and MIRROR.md from the already-pinned generated package; directory/path/collision checks protect that copy. Both regression paths failed before repair and pass afterward (2 tests plus 2 subtests). Independent native Astra review cleared these corrections. Final deterministic output is492files; the raw903file upstream tree remains unchanged. No runtime activation or installation is performed.

Final correction verification:361tests and7subtests pass; focused2tests and2subtests pass. Deterministic492-file build, full upstream integrity, adaptation coverage, catalog, JavaScript syntax, Matt reverse proofs and git diff --check pass. The changed setup package still has zero scanner findings.
