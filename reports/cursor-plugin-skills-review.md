# Cursor plugin skills mirror — implementation review

2026-09-14 PR addendum ([#64](https://github.com/TheAngryPit/TheAngrySkills/pull/64),
`codex/cursor-full-sol-20260913`): `cursor-ralph-loop-help` is emitted as a
guide to the external Cursor plugin; it never starts or cancels a Codex loop.
The branch has 54 emitted / 34 active held / 3 upstream dormant, while the
public `origin/main` baseline described below was 53 / 35 / 3. The
`--preview-candidates` path renders all 88 active skills for review without
changing the published catalog. The pstack core has 23 mapped playbooks,
fixture-only verification and a local notes-app `bug-fix` path with reproduction,
trace, prewritten correction, local Git history, and PR simulation.
`check-plan.mjs` ran on temporary plans; `worktree-audit.sh` ran with mocked
external commands. Bun exercised dependency-free `orch/store.ts` operations
and `watch-pr/github.ts` command wiring in scratch with mocked `git`/`gh`;
the exact lock dependencies then installed in scratch, and a fresh bootstrap
installed/restarted from the populated cache. Both CLI entrypoints ran against
scratch state and mocks; 52 bundled tests and strict typecheck passed. Real
GitHub status-only access to PR #64 also passed. Its `REVIEW_REQUIRED` fact
exposed a false green review cell in the source. The held preview now shows
the pending review and blocks a synthetic non-draft PR from `ready`; live
product behavior remains unproven. Advisor/Ralph/continual-learning
have inactive synthetic native hook adapters. Four agent-compatibility reviewer
roles are bundled in a held preview, whose previously invalid frontmatter now
parses. Held submission-audit and scaffold previews have bounded static fixtures
for manifest/path/frontmatter presence, passive hook/MCP detection, and explicit
disposable-destination generation; their security holds are retained.
The project-local verification fixture now drives each mapped notes CLI action
in a separate bounded subprocess, captures exit/stdout/stderr and declared
regular-file state, persists JSON evidence, reconciles controlled feature drift,
and confirms a second unchanged pass. A feature named `README` is rejected
before it can collide with the generated feature index. This remains
`FIXTURE_ONLY`: Doctor only checks source file presence/non-symlink; a real
target, per-feature source-wave delegation, changed-outcome PR, native skill
activation, and filesystem/network isolation have not been proven.
The held `cursor-show-me-your-work` preview now requires an explicit root for
its TSV helper. Ten tests exercise append and sanitization plus path escapes,
invalid roots, and parent/target symlinks, with external sentinels unchanged.
The pinned source is unchanged and the skill remains held: simultaneous writers,
durability, secret redaction, transcript audit, independent review, and live
activation are not proven.
The [47-skill pstack audit](pstack-47-skill-audit-20260914.md) compares the
installed Cursor cache with the pinned snapshot and the generated Codex
output per skill. The 47 top-level IDs match; two top-level skills and six
nested playbooks have source-version drift, with three delegate model defaults
different. This did not change the source pin. The audit found that the
published technical-writing overlay incorrectly made source-required
`unslop` optional and that the TypeScript guide used unnamespaced principle
names. The generated output now requires `cursor-unslop`, uses the two
published `cursor-principle-*` names, and retains `references/patterns.md`.
These are link/contract corrections; runtime selection is still unproven.
The public `comment-sicko` and `poteto-agent` TOML assets now provide the
named native destinations for the held `cursor-no-comments` and
`cursor-poteto-mode` workflows. Their developer-instruction bodies match exact
normalizations of the pinned agent sources, and their bytes match the already
installed global profiles. The held preview names the profiles and no longer
duplicates agent Markdown under its references. The former bounded Comment
Sicko fixture applied the role text but did not exercise the new profile
selection. Fresh-session discovery, named dispatch, and complete fix/playbook
behavior are still unproven. [Invocation matrix](../docs/native-agent-profiles.md).
The native host inspection used `codex-cli 0.154.0` help and the exposed task
tool schemas without starting a new session. `codex --profile` selects a
configuration profile, and `codex agents` browses sessions; neither is a
documented selector for these agent TOMLs. The exposed task tools accept
model and effort but no named agent profile. Exact installation bytes therefore
remain a distribution check, not discovery or dispatch proof.
The official [Subagents](https://cursor.com/docs/subagents),
[Cloud Agents API](https://cursor.com/docs/cloud-agent/api/endpoints), and
[Automations](https://cursor.com/help/ai-features/automations) contracts
separate documented runtime behavior from pstack assumptions. The held `cursor-why` preview now labels its source's
readonly-removes-MCP claim as unverified rather than granting write access.
`pytest -q tests` passed 178 tests and 2 subtests; mirror `--check`
passed at 91 physical, 54 emitted and 167 output files. CI passed on
`158c41a7` after publication.
None of these fixtures proves full native runtime parity, global installation,
or hook trust. Counts and checks below describe the earlier 53-skill baseline.

Base: TheAngrySkills `main` at `0706a19a4aac46a8db0a01e48dfe9ddc76768ca8`.
Source: `cursor/plugins` at `889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`.
Scope: skills, support files and required local catalog registration; no
independent Cursor plugin, global install or merge.

The manifest has 91 physical skills and 169 support files. Three Benny skills
are source-dormant. The current build indexes 53 skills: the original 47, one
renderer-proven read-only PR canvas path, and five `guide_only` instruction
skills. It retains 35 declared skills as unindexed candidates: 31 functional
adaptations awaiting Codex behavior proof, plus `cursor-sdk`, `make-bot-ui` and
`review-plugin-submission` pending contextual security review, and
`maintain-verification-skill` pending a Codex-local verification workflow. No
guide or renderer proof is presented as full native runtime parity.

The 169 support files count covers the full 91-skill upstream snapshot. The
164 generated files are a different measure: 53 published skills each have a
`SKILL.md`, `MIRROR.md` and copied license (159 files), plus five support files
owned by published skills. The other upstream support files remain in the
pinned snapshot for held or dormant skills; they are not installable output.
The `.claude-plugin/marketplace.json` entry `mirrors-cursor` lists exactly the
53 emitted skill paths. The generator rebuilds and checks this catalog entry
from the reviewed promotion set so future changes cannot leave it stale.

The first-pass security scan of all 88 declared candidates reported 77
`safe_to_install`, five `blocked_malicious`, five `needs_human_review` and one
`quarantine`. These are scanner verdicts, not conclusions about upstream
intent. For example, `add-dictation` was flagged for an xAI STT request carrying
`$XAI_API_KEY`; `cursor-sdk` was flagged for credential/MCP reference material;
and `make-bot-ui` contains an actual `curl ... | sudo sh` Tailscale install
instruction. All 11 non-safe candidates are unindexed in this batch. A
per-finding reading and approved adaptation are required before promotion.

The contextual second pass covers the remaining eight non-safe declared
candidates. The 11 non-safe declared candidates remain 5 `blocked_malicious`, 5
`needs_human_review`, and 1 `quarantine`; `setup-benny` is a separate dormant
snapshot finding and is not included in the 11.

| Skill | Finding and location | Context, effect, and credential surface | Decision |
|---|---|---|---|
| `add-dictation` | `network-exfiltration`, `SKILL.md:156`, critical | Active `curl` smoke instruction sends an audio file to xAI STT with `XAI_API_KEY`. | Hold until a server-side request is authorized, key handling is verified, and safe audio fixtures prove success and errors. |
| `add-read-aloud` | `network-exfiltration`, `SKILL.md:172`, critical | Active `curl` smoke instruction sends reply text to xAI TTS with `XAI_API_KEY` and writes returned audio. | Hold until a server-side request is authorized, key handling is verified, and safe text fixtures prove success and errors. |
| `orchestrate` | `persistence-mutation`, `measurements.ts:302`, critical; `policy-bypass-instruction`, `operator-boundary.test.ts:38`, critical; `persistence-mutation`, `adapters/slack/index.ts:51`, critical; 62 bundled-script warnings; one dependency-manifest warning at `scripts/package.json` | The measurement boundary executes planner-authored `bash -c` with a scratch `HOME`; the operator test is defensive despite the scanner wording; the Slack line only reads a profile field, although the adapter has external Slack access. Runtime scripts can use `CURSOR_API_KEY` and `SLACK_BOT_TOKEN`. | Retain all findings. Hold the bundled runtime for separate command-boundary, policy, dependency, egress, and side-effect review. |
| `reflect` | Four `policy-bypass-instruction` findings: `references/divergent-reviewer.md:7`, `judgment-reviewer.md:5`, `synthesizer.md:3`, `tooling-reviewer.md:5`, critical | These are defensive reference instructions that treat transcripts and reviewer output as untrusted and constrain lookups. No credential or write effect is shown at the lines. | Retain the findings as contextual defensive text. Hold until prompt-isolation behavior is reviewed. |
| `create-plugin-scaffold` | `mcp-plugin-hook-install`, `SKILL.md:16`, warning | Active workflow input includes `hooks` and `mcpServers`, followed by plugin-file creation and a `~/.cursor` default. | Hold. Static scaffolding needs an explicit destination; hooks, MCP, activation, and marketplace wiring need human approval. |
| `poteto-mode` | 20 `bundled-script-review` warnings, 4 `executable-file` warnings, and `dependency-manifest-surface` at `scripts/package.json` | The pack ships Bun/TypeScript orchestration, PR-watch, worktree-audit, and plan-check scripts. They can spawn processes, inspect GitHub/worktrees, install dependencies, or write state; no direct credential finding was emitted. | Hold. Do not run or admit bundled scripts until code, dependency, and egress behavior is reviewed. |
| `show-me-your-work` | `executable-file` and `bundled-script-review`, `scripts/log.sh`, warning | Pinned shell helper writes operator-supplied TSV. Held preview adds explicit-root, no-follow local writes; fixture rejects escapes and symlinks. No external egress is shown. | Keep held pending full workflow, concurrency, secret-handling, and installation-scope proof. |
| `why` | `mcp-plugin-hook-install`, `SKILL.md:62`, warning | Active workflow discovers MCPs and queries external evidence categories in parallel; connector authentication and data access are part of the behavior. | Hold until native connector availability, authorization, and read-only behavior are proven. |

`setup-benny` is documented separately as a dormant extra: its
`mcp-plugin-hook-install` warning at `SKILL.md:63` is a guardrail sentence, but
the surrounding workflow copies files, writes `.cursor/settings.json`, and can
enable live automations. It stays dormant and unindexed; no finding is
silenced.

`maintain-verification-skill` is held for a different reason. Its upstream
pass locates `.cursor/skills/verify-*`, launches one read-only subagent per
feature, drives the app live, and may open a PR. The earlier editorial
`intacta` classification remains preserved in the historical matrix, but
source review found a concrete Codex workflow gap. The implementation manifest
records the stricter promotion status until a native or external path is
proven without changing the requested behavior.

Static checks passed for the 53 indexed candidates: 53/53 frontmatter parsed
with no errors, including the auditor fallback without PyYAML, and the security
scanner returned `safe_to_install` for 53/53. Two descriptions use exact overlays
to preserve their words while remaining parseable in that fallback.
Fourteen focused tests cover reproducibility, local-edit preservation, source-drift
and symlink rejection, contract consistency, bounded helper fixtures, and the
real PR canvas renderer (including HTML escaping). Relative Markdown links
resolve; rebuild reproduces the generated bytes; and comparison with the
pinned upstream checkout reports no new, removed or changed skills or licenses.
The helper fixtures exercise rule shapes, not live Codex routing or runtime
effects. The canvas renderer test does not prove the full PR workflow.
The full CI-equivalent `pytest` suite passes locally after this catalog fix:
114 tests and two subtests.

The pstack cross-skill links are mapped to published sibling names where those
skills exist in this batch; held siblings point to the pinned upstream source.
The Poteto Mode index's 23 `principle-*` IDs remain in the unindexed source and
will need explicit name mapping when its functional port is reviewed. Benny's
external automation files remain out of distribution, and the exact scope of
its ancestor license is still a promotion gate. The `debug-voice` `../x` path
is an unresolved fixture, not a missing vendored dependency.

The Codex Work Cloud surface has no demonstrated substitute for Cursor
orchestrate's Git isolation, model routing, worker hierarchy, cancellation,
recovery, artifact or PR contract. A cloud proof must be a separate synthetic
task after an authorized dispatch path and a concrete closure mechanism are
established; no cloud task was created in this batch.

Review order: validate this source/overlay format and 53-skill batch; resolve
the 11 security findings in context; port and behavior-test the remaining 31
functional skills in bounded lots; only then consider promoting held skills.
The reverse path is removal of this mirror's generated skills, source snapshot,
overlays, report and generator. There is no installed state to roll back.
