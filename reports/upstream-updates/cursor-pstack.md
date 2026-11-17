<!-- upstream-update:family=cursor:batch=pstack -->
<!-- codex-handoff:family=cursor:batch=pstack:head=e1cc03121a0e71129a4fb730d7c5528a0a3e43c8 -->
# Reviewed Cursor / Pstack adaptation refresh

| Identity | Revision or disposition |
| --- | --- |
| Accepted PR166 baseline | `8ecfb19f844b67a4bc7af7f66c366d57bc7b6d2b` |
| Candidate Pstack family | `e1cc03121a0e71129a4fb730d7c5528a0a3e43c8` |
| Lifecycle | `family=cursor`, `batch=pstack`, `latest=e1cc03121a0e71129a4fb730d7c5528a0a3e43c8` |
| Disposition | Existing admitted packages refreshed through explicit native overlays; acceptance into main remains with the coordinator |
| Raw source | Global tree remains at 8ecfb19; only Pstack advances to e1cc031 |
| Install surface | 108 published adapters, six held adapters; no new admission |
| Runtime evidence | Source, deterministic generation and regression fixtures; no new live runtime certification |

This replaces the earlier detector-only report. Its old `df581122` baseline and
`candidate_content_promoted=false` disposition no longer describe this candidate.
The source comparison is now the accepted PR166 baseline against the pinned
Pstack update. The complete path inventory and native support provenance are in
[the review receipt](../pstack-refresh-20261117.json).

## Native adaptation decisions

- Existing full-file overlays preserve accepted Codex methods, routing and permission boundaries while their source anchors and README pins advance.
- Fourteen principle bodies, technical-writing, unslop, teach and blast-radius receive the compatible upstream changes. No model or provider default is imported from Cursor.
- Twenty-three support files removed upstream remain reviewed native support through the existing hash-ledgered `bundled_native_files` mechanism. They preserve How, Why, Reflect and Architect prompts, the native Orchestrate playbook and plan checker. Their origin stays pinned to 8ecfb19, distinct from the new raw source.
- The new `worker.md` receives a native parent/scope/refusal contract. It does not import upstream blanket bans on questions or authorize extra delegation, publishing or deployment.
- Comment Sicko explicitly maps the changed trace/why sentence. Poteto's new model frontmatter is discarded; its native profile bytes and binding keys remain unchanged. GPT-6.2/Fable routing stays with the existing model-capability-router.
- All six held adapters remain held, including Statechart. Its updated scripts remain quarantined source; no upstream script was executed. Claude harness records remain reference-only and Tailscale remains pending.

## Scope and verification

Full raw Git verification covers 2,051 files, 173 skill paths and 16 source-agent
paths. These include parallel harness references, not 16 installed roles. The
native role inventory remains 14. Mirror and adapter checks cover 114 entries,
108 published packages, six held packages and 1,207 generated output files.
The coordinator records the final exact-head CI and security comparison before
publication. No installed home, credentials, schedules or native configuration
was changed by this refresh.

## Upstream Pstack paths reviewed

- `M pstack/.cursor-plugin/plugin.json`
- `M pstack/README.md`
- `M pstack/agents/comment-sicko.md`
- `M pstack/agents/poteto-agent.md`
- `M pstack/automations/benny/FOR_AGENTS.md`
- `M pstack/automations/benny/skills/reproduce-and-fix-issues/SKILL.md`
- `M pstack/automations/benny/skills/setup-benny/SKILL.md`
- `M pstack/automations/benny/skills/triage-issue-reports/SKILL.md`
- `M pstack/docs/guide/01-setup.md`
- `M pstack/docs/guide/02-poteto-mode.md`
- `M pstack/docs/guide/03-understand.md`
- `M pstack/docs/guide/04-design.md`
- `M pstack/docs/guide/05-build-and-clean.md`
- `M pstack/docs/guide/06-verify-and-ship.md`
- `M pstack/docs/guide/07-overnight.md`
- `M pstack/docs/guide/09-make-it-yours.md`
- `M pstack/docs/guide/10-recipes-and-pitfalls.md`
- `M pstack/docs/harness/claude-code.md`
- `M pstack/plugin.json`
- `M pstack/skills/architect/SKILL.md`
- `D pstack/skills/architect/references/design-red-flags.md`
- `D pstack/skills/architect/references/rationale-template.md`
- `D pstack/skills/architect/references/runner-prompt.md`
- `M pstack/skills/arena/SKILL.md`
- `M pstack/skills/automate-me/SKILL.md`
- `M pstack/skills/benchmark-checklist/SKILL.md`
- `M pstack/skills/blast-radius/SKILL.md`
- `M pstack/skills/figure-it-out/SKILL.md`
- `M pstack/skills/how/SKILL.md`
- `D pstack/skills/how/references/explainer-prompt.md`
- `D pstack/skills/how/references/explorer-prompt.md`
- `M pstack/skills/no-comments/SKILL.md`
- `M pstack/skills/poteto-help/SKILL.md`
- `M pstack/skills/poteto-mode/SKILL.md`
- `M pstack/skills/poteto-mode/playbooks/autonomous-run.md`
- `M pstack/skills/poteto-mode/playbooks/autopilot-full.md`
- `M pstack/skills/poteto-mode/playbooks/autopilot-stack.md`
- `M pstack/skills/poteto-mode/playbooks/babysit.md`
- `M pstack/skills/poteto-mode/playbooks/bug-fix.md`
- `M pstack/skills/poteto-mode/playbooks/eval.md`
- `M pstack/skills/poteto-mode/playbooks/feature.md`
- `M pstack/skills/poteto-mode/playbooks/hillclimb.md`
- `M pstack/skills/poteto-mode/playbooks/investigation.md`
- `M pstack/skills/poteto-mode/playbooks/multi-phase-plan.md`
- `M pstack/skills/poteto-mode/playbooks/opening-a-pr.md`
- `D pstack/skills/poteto-mode/playbooks/orchestrate.md`
- `M pstack/skills/poteto-mode/playbooks/perf-issue.md`
- `M pstack/skills/poteto-mode/playbooks/refactoring.md`
- `M pstack/skills/poteto-mode/playbooks/runtime-forensics.md`
- `M pstack/skills/poteto-mode/playbooks/session-pickup.md`
- `M pstack/skills/poteto-mode/playbooks/shipping.md`
- `M pstack/skills/poteto-mode/playbooks/trace-forensics.md`
- `M pstack/skills/poteto-mode/playbooks/worktree-cleanup.md`
- `D pstack/skills/poteto-mode/scripts/check-plan.mjs`
- `D pstack/skills/poteto-mode/scripts/check-plan.test.ts`
- `M pstack/skills/poteto-mode/scripts/package.json`
- `A pstack/skills/poteto-mode/worker.md`
- `M pstack/skills/principle-attack-the-premise/SKILL.md`
- `M pstack/skills/principle-boundary-discipline/SKILL.md`
- `M pstack/skills/principle-build-the-lever/SKILL.md`
- `M pstack/skills/principle-explain-the-number/SKILL.md`
- `M pstack/skills/principle-fix-root-causes/SKILL.md`
- `M pstack/skills/principle-foundational-thinking/SKILL.md`
- `M pstack/skills/principle-make-operations-idempotent/SKILL.md`
- `M pstack/skills/principle-minimize-reader-load/SKILL.md`
- `M pstack/skills/principle-model-the-domain/SKILL.md`
- `M pstack/skills/principle-prove-it-works/SKILL.md`
- `M pstack/skills/principle-separate-before-serializing-shared-state/SKILL.md`
- `M pstack/skills/principle-sequence-verifiable-units/SKILL.md`
- `M pstack/skills/principle-test-behavior-not-implementation/SKILL.md`
- `M pstack/skills/principle-type-system-discipline/SKILL.md`
- `M pstack/skills/recall/SKILL.md`
- `M pstack/skills/reflect/SKILL.md`
- `D pstack/skills/reflect/references/divergent-reviewer.md`
- `D pstack/skills/reflect/references/judgment-reviewer.md`
- `D pstack/skills/reflect/references/synthesizer.md`
- `D pstack/skills/reflect/references/tooling-reviewer.md`
- `M pstack/skills/setup-pstack/SKILL.md`
- `M pstack/skills/sharpen/SKILL.md`
- `M pstack/skills/show-me-your-work/SKILL.md`
- `M pstack/skills/statechart/scripts/backends/mermaid.ts`
- `M pstack/skills/statechart/scripts/run.ts`
- `M pstack/skills/statechart/scripts/test/chart.test.ts`
- `M pstack/skills/statechart/scripts/test/cli.test.ts`
- `M pstack/skills/statechart/scripts/test/corpus.test.ts`
- `M pstack/skills/statechart/scripts/test/corpus/Login/chart.mmd`
- `A pstack/skills/statechart/scripts/test/drawn.ts`
- `M pstack/skills/statechart/scripts/test/labels.ts`
- `M pstack/skills/statechart/scripts/test/render.test.ts`
- `M pstack/skills/swarm/SKILL.md`
- `M pstack/skills/teach/SKILL.md`
- `M pstack/skills/technical-writing/SKILL.md`
- `M pstack/skills/unslop/SKILL.md`
- `M pstack/skills/why/SKILL.md`
- `D pstack/skills/why/references/epistemics.md`
- `D pstack/skills/why/references/investigator-prompt.md`
- `D pstack/skills/why/references/source-playbook.md`
- `D pstack/skills/why/references/sources/code-archaeology.md`
- `D pstack/skills/why/references/sources/databricks.md`
- `D pstack/skills/why/references/sources/datadog.md`
- `D pstack/skills/why/references/sources/incident-postmortem.md`
- `D pstack/skills/why/references/sources/linear.md`
- `D pstack/skills/why/references/sources/notion.md`
- `D pstack/skills/why/references/sources/sentry.md`
- `D pstack/skills/why/references/sources/slack.md`
- `D pstack/skills/why/references/synthesizer-prompt.md`
