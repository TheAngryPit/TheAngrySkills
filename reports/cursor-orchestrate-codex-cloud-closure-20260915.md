# Cursor orchestrate: native Codex Cloud closure

Date: 2026-09-15  
Scope: bounded adapter implementation, one authorized read-only Codex Cloud audit, runtime defect correction, deterministic generation, and verification.

## Native surface

Official OpenAI documentation describes `codex cloud exec --env ENV_ID [QUERY]` with one to four attempts and an optional branch, plus `list --json`, `status`, `diff`, and separately mutating `apply`. The CLI documentation does not expose cancellation. The native task UI did expose a cancellation button during this proof; it was not used.

Sources:

- <https://learn.chatgpt.com/docs/developer-commands?surface=cli>
- <https://learn.chatgpt.com/docs/codex/cli>

## Authorized runtime proof

The existing GitHub installation already covered all repositories. Direct search in the Codex environment form found `TheAngryPit/TheAngrySkills`, so no repository-access mutation was performed.

Exactly one environment was created:

- name: `TheAngrySkills orchestrate proof`
- ID: `6aa9136795d0819186c67d8b812e7a70`
- repository: `TheAngryPit/TheAngrySkills`
- image: universal
- setup: automatic
- environment variables and secrets: none
- agent internet: off

Exactly one task was executed with one attempt:

- task: `task_e_6aa91395baf483268a13e1a5cd9db403`
- URL: <https://chatgpt.com/codex/tasks/task_e_6aa91395baf483268a13e1a5cd9db403>
- branch: `main`
- required and observed commit: `124c985348e79cec1a17cfc4ccd73e461e1efdc6`
- final status: `READY`
- task result: read-only audit `FAIL` with three adapter findings
- diff summary: zero files and zero lines changed
- apply: not used
- cancellation: not used

`codex cloud diff` reported that no diff was available, consistent with the zero-change audit. No additional attempt or task was created.

## Runtime payload corrections

The actual `list --json` payload differed from the initial fixture in two ways:

- `environment_id` was `null` while `environment_label` identified the environment;
- pagination was returned as `cursor`, not `next_cursor`.

The parser now accepts an environment ID, label, or both; requires at least one identity; reads `cursor`; and keeps a normalized `next_cursor` compatibility alias. The exact real task shape is a regression fixture.

## Audit findings and fixes

The cloud audit found that bare caller-supplied completed IDs could unlock descendants. Readiness now comes only from validated `PASS` handoffs. Each passing completion must carry the associated cloud task and attempt, proof that status and diff were inspected, and a structured artifact URI with a SHA-256 digest. Bare IDs, `BLOCKED` or `ISSUES` handoffs, uninspected results, textual artifact references, and malformed digests do not unlock descendants.

The adapter now represents the native command range with attempts from one through four and an optional branch. This does not change the completed proof: that task intentionally used one attempt and a fixed branch/commit for reproducibility.

Goal and acceptance text are copied into the cloud prompt. Task creation authorization and prompt-content transmission authorization are therefore separate explicit gates. Private-path and high-confidence credential-pattern checks remain limited defensive detection; they are not described as proof that arbitrary text contains no private data.

## Security and publication boundary

All pinned upstream `blocked_malicious` findings remain recorded. The rendered bundle excludes upstream prompts, references, schemas, TypeScript/Bun scripts, dependency manifests, measurement shell execution, Slack adapters, and credential paths. Only the rewritten native skill, reviewed Python adapter, provenance, agent metadata, and license are published.

The historical provisional ChatGPT Work client ID remains separate with unknown state. It was not retried or treated as Codex Cloud evidence.

## Proof boundary

The runtime proves environment discovery, a single fixed-commit read-only task, one attempt, result readback, the real list payload shape, and zero repository changes. It does not prove a multi-task dependency drain, diff application, or cancellation. The adapter prepares reviewable argv and validates supplied records; it does not execute commands or authenticate the provenance of arbitrary caller-created mappings.
