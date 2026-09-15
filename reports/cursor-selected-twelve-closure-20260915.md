# Cursor selected-twelve closure

Date: 2026-09-15. This report reconciles the twelve candidates selected after
PR #68 against their Codex adaptations, behavior proof, security findings, and
publication state. It does not install skills globally, trust hooks, contact an
external provider, create a pull request, or merge a branch.

## Published bounded adaptations

| Skill | Demonstrated Codex behavior | Preserved gap |
| --- | --- | --- |
| `cursor-workflow-from-chats` | An explicit project-local JSONL export is limited to one parent and its linked children, filtered by time, reduced to corroborated preference atoms, redacted, and written as a reviewable proposal plus receipt. Local artifact writes and durable writeback are reported separately. | Automatic native task-history acquisition, automatic routing, and durable skill/rule/memory writeback remain unavailable. |
| `cursor-docs-canvas` | Explicit project-local Markdown produces linked Markdown/HTML with navigation, stable anchors, safe cross-references, escaped content, and inspected responsive output. | Cursor Canvas SDK and primitive parity remain unavailable. |
| `cursor-pr-review-canvas-pr-review-canvas` | An explicit project-local unified diff produces linked Markdown/HTML grouped by reviewer value with changed-line attention callouts and compact mechanical summaries. | Live PR metadata, `gh` retrieval, publication, and Cursor Canvas parity remain unavailable. |

Each published skill bundles the reviewed `scripts/cursor_canvas_adapters.py`.
The manifest pins its SHA-256 and restricts the native-support relationship to
these three skills. The generated marketplace and state now contain 74
published skills, 9 held candidates, and 8 operator exclusions across 91
physical sources.

## Converted but retained

| Skill | Delivered adaptation | Reason it remains held |
| --- | --- | --- |
| `cursor-advisor` | Explicit task-bound adapter, bundled advisor role reference, identity/verdict checks, and symlink-safe local state. | Native bounded consultation is supported only on hosts exposing delegation, but a live explicit advisor consult and its correlated result were not demonstrated for this candidate. A trusted hook is optional automation, not a prerequisite for an explicit consult. |
| `cursor-continual-learning` | Bundled updater role, bounded synthetic transcript/index/`AGENTS.md` behavior, threshold logic, and symlink-safe transcript roots. | A verified real transcript source, live updater delegation, reviewed project diff, and any trusted automatic hook remain unproven. |
| `cursor-orchestrate` | Explicit-only native mapping, reviewed plan and handoff contracts, and preserved Cursor security findings without executing the bundled runtime. | Local collaboration can supply bounded child dispatch where exposed, while ChatGPT Work creation is a separate user-owned task action. Full fan-out, drain, artifact identity, cancellation, and recovery were not demonstrated as one workflow; the upstream executable bundle remains security-held. |
| `cursor-ralph-loop` | Task/session-bound local state, maximum/promise/cancellation decisions, and safe project boundaries. | Codex exposes follow-up, interruption, and scheduled-heartbeat primitives in applicable hosts, but no supported automatic Stop continuation matching the preserved loop contract was demonstrated. |
| `cursor-cancel-ralph` | Matching-session cancellation removes only the state file; unknown and other sessions remain unchanged. | No live Ralph continuation exists to cancel and correlate end to end. |
| `cursor-check-agent-compatibility` | Four-role evidence inventory with an explicitly withheld score when the scanner is absent. | Published scanner startup, behavioral checks, and combined score remain unproven. |
| `cursor-create-plugin-scaffold` | A marked disposable root generates a static Cursor-format scaffold and feeds it to the structural auditor. | Plugin activation, hooks/MCP behavior, marketplace wiring, installation, and publication remain unproven. |
| `cursor-review-plugin-submission` | Read-only structural audit covers manifest paths, required metadata, component discovery, README, symlink escapes, and active-surface escalation. | Full YAML, marketplace uniqueness, submission policy, runtime behavior, and human submission review remain unproven. |
| `cursor-cursor-sdk` | A non-executing reference reader identifies the pinned SDK contract and fails closed on credentials, authentication, execution, network, and MCP requests. | The source `blocked_malicious` verdict is retained. No Cursor SDK runtime or Codex parity is claimed. |

The retained set is not counted as published or installed. Missing Cursor names
or exact SDK identity are not treated as blockers by themselves; each hold is
based on the preserved behavior or security boundary that still lacks proof.

## Verification

- `pytest -q tests` — **261 passed, 2 subtests passed**.
- `python3 scripts/sync-cursor-plugin-skills.py --check` — **91 physical, 74 published, 357 output files**.
- `git diff --check` — passed.
- Focused context/Canvas, native-hook, plugin scaffold/audit, scanner, and mirror tests — **70 passed** in the integration pass.
- Local deterministic security scans classified each newly published skill as `needs_human_review` solely because it bundles the Python adapter. The adapter and every generated copy were then covered by the Codex Security diff review.
- Codex Security scan `b0225539-32dc-4ac5-8368-b58524d15666` completed with **0 reportable findings**. One same-user concurrent pathname race hypothesis was suppressed because the required process already has equivalent direct filesystem authority; a privileged cross-user deployment would require reassessment.

The repository-wide `pytest -q` command also discovers vendored
`openclaw-autoreview` tests as top-level modules and stops on two pre-existing
relative-import collection errors. The repository-owned `tests/` suite above
is green.
