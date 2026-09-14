# Benny automation pack: separate conditional native plan

Date: 2026-09-14
Upstream pin: `cursor/plugins` commit `889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`
Scope: the three retained Benny automation sources under `pstack/automations/benny`.

This is a separate automation pack. It is not part of the 88 active slash-skill
sources and none of its three entries is published or indexed as a slash skill.
The manifest currently reconciles 88 non-Benny physical skills plus these three
dormant Benny entries. The published/held split is owned by the sibling mirror
work; the invariant relevant here is that all 88 non-Benny sources remain in the
slash-skill scope and all three Benny sources remain outside it. This report
does not change that manifest, the marketplace, the sync generator, the existing
broad reports, or PR #66. No automation was created, scheduled, enabled, or
activated.

## Physical source and provenance ledger

The repository's pinned skills-only snapshot contains seven Benny files: three
operational skill sources and four references. A complete local clone of the
same pinned upstream commit is also available for this run and contains the
full 12-file pack. The vendored snapshot is therefore incomplete, while the
pinned upstream source itself is available for a future reviewed import. This
distinction is a deployment blocker for the current repository tree, not a
reason to count the three retained sources as removed.

| Source | Pinned path | SHA-256 | Manifest state |
| --- | --- | --- | --- |
| Setup | `sources/cursor-plugins/snapshot/pstack/automations/benny/skills/setup-benny/SKILL.md` | `5a3cbe63360c9f6373b6cb6c79a1eaf7e0eba181bfaa1577e2e6431af3407282` | `publish: false`, `declared_for_distribution: false`, availability `external connector or routing not demonstrated` |
| Triage | `sources/cursor-plugins/snapshot/pstack/automations/benny/skills/triage-issue-reports/SKILL.md` | `216a758b8711e64d19a55e6032c496527daac6364d010611040f3c04ef1a448f` | `publish: false`, `declared_for_distribution: false`, availability `external connector or routing not demonstrated` |
| Reproduce/fix | `sources/cursor-plugins/snapshot/pstack/automations/benny/skills/reproduce-and-fix-issues/SKILL.md` | `1363cc07343fe86aab42853b1bd4563288cbcbdf12f1c265b3b3b1afa25c09cb` | `publish: false`, `declared_for_distribution: false`, availability `external connector or routing not demonstrated` |

Supporting reference hashes recorded by the manifest and rechecked here:

- `control-adapter.md`: `58b0615d2fca895f9a20df83266e280042b0d585b5f2fd324e2094a682fd846b`
- `feature-map.example.md`: `1e5c7c8522daec3e43fcc2e73ceb97289ded65b552949ce65a11cc8eb3d2b6ee`
- `verify-existing-fix.md`: `c90eae00abcdec71a58fa8d60f2c495b082a526ad50b8e8e494837609129bf29`
- `routing.example.md`: `e5e53013692568cf69da8e8b302fff929fe2fbc9aec1a4651fd7997e2c7a4025`

The complete pinned clone supplies the five files omitted from the vendored
skills-only snapshot. Their hashes are:

- `FOR_AGENTS.md`: `a125e317dec1b8731fdc71f404c669f1127a73af932f7a7b8b8744a5542328a7`
- `README.md`: `ca3c42cbb7f0bf7068f7407eb355815e6c234d5c2786942f3cbe751a3690024b`
- `templates/configuration.example.yaml`: `13e24b4ce9b9a0913916e85fe3b080b88d45f8e55dccfe8ae38e0751a997b6f5`
- `templates/reproduce-automation-prompt.md`: `71ec574f1844e379394ae4ef14c48d7df10afbaa319d395c788d7f856f0e6899`
- `templates/triage-automation-prompt.md`: `e0bba594547834f013ec805915610eb597e7929efe3ffbe85ae00339ee16d474`

The complete clone's `FOR_AGENTS.md` confirms the intended two-automation
relationship, its shared rules, configuration placeholders, and explicit
editor handoff. `README.md` independently confirms that the files are dormant
setup/automation sources and do not appear as slash skills. These full-pack
files were read for planning only; none was copied into this repository.

All three entries use the pinned `pstack/LICENSE`, whose recorded and observed
hash is `bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e`.
The existing overlays preserve the source hashes and semantics. The triage and
repro overlays add only a Codex boundary note; the setup overlay records the
contextual security hold.

## What each source does

`setup-benny` is a control-plane procedure. It copies a complete pack into a
target repository's `.cursor/automations/benny/`, merges
`.cursor/settings.json` with `plugins.pstack.enabled: true`, checks project
scope resolution for ten named pstack dependencies, gathers secret-free
configuration, validates routing and the control adapter, and hands creation or
editing of two live automations to the built-in Automations workflow. It
explicitly says to ask before creating or updating an automation, keep secrets
out of files and prompts, and never put the Benny directory in the slash-skill
manifest (`setup-benny/SKILL.md:9-15,21-69,94-116,151-165`).

`triage-issue-reports` is the issue intake path. It reads one top-level Slack
report and current replies, freezes the source channel and root timestamp,
reviews attachments, performs bounded source/history cause tracing, classifies
the report, applies an optional routing map, searches and deduplicates through a
configured tracker adapter, and creates a ticket only when all fail-closed gates
pass. It then posts exactly one substantive reply in the same source thread with
one configured marker (`[benny:bug]`, `[benny:performance]`, or
`[benny:other]`) and optionally a tracker URL. It never cross-posts, sends a DM,
posts a root message, or lets a worker post (`triage-issue-reports/SKILL.md:9-28,30-81,109-142,144-183,200-238`).

`reproduce-and-fix-issues` is the evidence and optional fix path. It waits for a
marker from the configured triage identity in the frozen source thread, stops
for an untrusted/missing/conflicting marker, checks human ownership and existing
fix artifacts, then uses a configured control adapter to drive the real UI.
The discriminating symptom must be observed twice; state inspection cannot
inject it. An existing pull request or commit switches to baseline/patched
verification and forbids a competing fix. A new fix is allowed only after
confirmed repro, media review, no human owner, root-cause evidence, scope/budget
fit, and baseline/patched adapter support. A code worker is allowed to edit only
when Slack credentials and every Slack write are provably absent; the
coordinator owns all Slack posts, the final diff, commits, and any draft PR
(`reproduce-and-fix-issues/SKILL.md:9-32,34-103,218-240,242-280`).

The supporting `control-adapter.md` requires app identity and environment
confirmation, user-visible actions, mapped feature/state coverage, read-only
inspection, screenshots, start/stop recording, cleanup, bounded retries, and a
fresh state for the second attempt. `verify-existing-fix.md` requires twice on
the baseline and twice on the patched build, with the same UI path, state check,
screenshot, and recording; compilation or tests alone do not prove the fix
(`control-adapter.md:1-165`; `verify-existing-fix.md:1-93`).

## Conditional native plan

The feasible native shape is a project-local, explicit, two-runner adapter. The
three sources remain read directly from a committed
`.cursor/automations/benny/` tree after the complete upstream pack is supplied.
They stay outside `.agents/skills`, `skills/mirrors-cursor`, and the marketplace.
An event runner may pass a new top-level Slack report to both configured runs,
but it must not infer a schedule, create an automation, or activate either run.
Creation/update remains an explicit human action in the native Automations
editor.

The pack needs one secret-free project configuration outside the source-managed
directory, for example `.cursor/benny/configuration.yaml`, plus a completed
feature map and optional routing map. The configuration must resolve all of the
following before a run can write anything:

1. Source Slack channel ID, optional operations channel ID, triage identity user
   ID, marker strings, and polling/follow-up budgets.
2. Repository URL, default branch, PR URL format, and isolated worktree policy.
3. Tracker adapter and its team/project/labels/intake status, including search,
   read, create, update, and compensation operations.
4. Control skill/adapter, completed feature-map path, target app/environment,
   artifact directory, and all screenshot/recording/readback capabilities.
5. Caller-supplied model slugs and effort budgets for triage, repro/code, and
   media review. No private or guessed model slug is acceptable.

Secrets such as `BENNY_SLACK_BOT_TOKEN` belong in the host secret manager or
environment only. They must never be placed in YAML, the copied pack, prompts,
logs, screenshots, recordings, or commits.

The native runner should expose these bounded stages:

| Stage | Required behavior | Safe result when unavailable |
| --- | --- | --- |
| Intake preflight | Verify trigger channel, immutable root `thread_ts`, parent existence, source permalink, and attachment access. | `BLOCKED`; zero Slack/tracker writes. |
| Triage | Read the full report, classify, trace cause, dedupe, and create/update only through the configured tracker adapter. | `NO_TICKET` or `BLOCKED`; never guess a route. |
| Verdict | Re-read the parent, post one reply with one marker, then read back the same thread. | `BLOCKED`; if a ticket was created and compensation cannot be verified, report the failure only in run output. |
| Repro gate | Accept only the configured identity's reply marker; verify ownership, artifacts, control adapter, feature map, and real UI capabilities. | `WAIT`, `STOP`, or `BLOCKED`; no source post and no fix. |
| Repro evidence | Run the mapped UI path twice from reset state, capture screenshot/recording, and perform the named read-only cross-check. | `COULD_NOT_REPRODUCE` or `BLOCKED`; no authored fix. |
| Existing fix | Run the same path twice on baseline and twice on patched artifact. | `INCONCLUSIVE` or `INSUFFICIENT_FIX`; no competing PR. |
| New fix | Only after all gates, use an isolated credential-free code environment, run an appropriate test, review the diff, repeat patched UI evidence, and open a draft PR if explicitly configured. | Keep the repro report; no PR. |

The bounded no-write fixture added in this pass does not need external
connectors. It feeds fake events and asserts that the adapter:

- rejects a wrong channel, missing root, deleted parent, reply timestamp, or
  second marker without any write;
- accepts exactly one configured marker only from the configured triage identity
  and only as a reply under the frozen root;
- refuses ticket creation for feature/question/duplicate/uncertain outcomes and
  refuses it when compensation is unavailable;
- routes a missing config, missing tracker operation, missing feature map, or
  missing control capability to a typed `BLOCKED` result;
- rejects a first-attempt-only repro, state injection, absent recording, or
  mismatched baseline/patch state;
- preserves the existing-artifact rule and never emits a competing PR request;
- keeps secrets out of emitted records and never invokes scheduling or activation.

That fixture would prove adapter decisions and no-write boundaries only. It would
not prove a live Slack thread, tracker, Cursor Automations editor, target UI,
native model selection, or PR operation, so it must remain labeled fixture-only.
The complete pinned pack now supplies the source-side configuration and prompt
contract, so this pass adds a smaller no-write event/marker gate fixture in
`scripts/cursor_benny_adapters.py` with focused tests. It still does not close
the external runtime gap: the fixture has no connectors and never performs a
write.

## Exact external permissions and blockers

The current source and Codex task prove provenance and static contracts only. A
conditional native implementation remains blocked on these concrete inputs:

- The complete source-side pack is available in the pinned upstream clone, but
  its `FOR_AGENTS.md`, README, configuration example, and prompt templates are
  not vendored in this skills-only repository snapshot. A reviewed import would
  need to preserve their hashes and scope; this pass deliberately did not copy
  them.
- Explicit human approval to copy/commit `.cursor/automations/benny/`, merge
  `.cursor/settings.json`, create or update `benny-triage` and
  `benny-reproduce`, and later enable them. This pass took none of those actions.
- A native Automations editor/create-update path. The repository has no proof
  that a Codex automation backend or direct protocol endpoint is an allowed
  substitute; the source explicitly requires the reviewed editor handoff.
- Slack permissions: read the configured source channel and thread replies;
  read attachment metadata/downloads; reply in the source thread; and, only if
  configured, post/edit one operations-thread status. The triage identity and
  channel IDs must be supplied. Cross-post, DM, root-post, and worker-post
  permissions are intentionally not requested.
- Tracker permissions and resolved identifiers for search, read, create,
  update, source-link/recurrence, and cancel/close/delete compensation.
- A named control adapter with a completed user-facing feature map and the nine
  setup-check capabilities: bring-up, stable app marker, one mapped feature,
  disposable state, read-only inspection, screenshot, recording, and cleanup.
- Repository history/read access plus an isolated worktree and a draft pull
  request action for the optional fix phase. No write/PR permission is needed to
  classify or report a blocked run.
- Explicit model slugs, effort budgets, tracker/routing values, and retention
  policy. The source forbids carrying over a private default or guessing a slug.

The existing contextual security finding for `setup-benny` is retained: the
scanner flagged `mcp-plugin-hook-install` at source `SKILL.md:63`, classified as
`guardrail_reference_in_dormant_workflow`. The line is a fail-closed dependency
guard, but the surrounding setup flow can copy files, write
`.cursor/settings.json`, and enable live automations. The overlay therefore
keeps `setup-benny` dormant and unindexed with no installation or enablement
authorization (`sources/cursor-plugins/overlays/cursor-setup-benny.json:50-69`).

The triage and repro overlays are `safe_docs_only` in the manifest, but that is a
static source verdict. Slack, tracker, app-control, repository, PR, model,
recording, and automation-editor behavior remain unproven. This report makes no
runtime parity, scheduling, activation, or 88/88 functional claim.

## Verification performed

- Read all three pinned `SKILL.md` files end to end.
- Read all four available Benny references, including the existing-fix branch.
- Recomputed all seven snapshot file hashes and the pstack license hash; they
  match the manifest.
- Confirmed the manifest has 88 non-Benny skills plus exactly three Benny
  entries; all three Benny entries are `publish: false` and dormant, while the
  non-Benny preview count remains 88. At the time this separate pack was
  drafted, the concurrent local mirror check reported 91 physical and 62
  published outputs; later successor promotions are outside this pack and not part of this
  pack.
- Confirmed the current mirror test explicitly expects 88 candidates and
  excludes `cursor-setup-benny` from the candidate output
  (`tests/test_cursor_plugin_mirror.py:333-352`).
- Read the complete pinned `FOR_AGENTS.md`, README, configuration example, and
  both automation prompt templates. Recomputed all 12 full-pack file hashes;
  the five omitted files are recorded above.
- Added and tested the no-write intake/triage event gate fixture; it returns
  explicit `BLOCKED`, `WAITING_FOR_TRIAGE`, `TRIAGE_STOPPED`, or
  `TRIAGE_ACCEPTED` decisions and never schedules, activates, or writes.
- Focused proof: `pytest -q tests/test_cursor_benny_adapters.py` passed 8 tests;
  `python3 -m py_compile scripts/cursor_benny_adapters.py` and `git diff
  --check` passed.
- No shared code, manifest, marketplace, generator, existing report, PR,
  external connector, automation, schedule, secret, or runtime state was
  changed. The only code additions are the owned event-gate script and its
  focused tests listed above.

Result: `PASS — separate pack accounted for; conditional native plan complete;
runtime blocked on missing pack material and explicit external permissions.`
