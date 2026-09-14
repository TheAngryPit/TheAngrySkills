# Real `how` / `why` workflow evidence

Date: 2026-09-14
Branch: `codex/pstack-how-why-real-20260914`
HEAD: `0479ea88374bcb9d3843eedb60d4631c63599bb4`
Authority clone: `/private/tmp/theangryskills-pstack-20260913-xcCoXg/repo`

Scope: exercise the real Cursor mirror workflow for the held `cursor-how` and
`cursor-why` candidates. This report records source traversal and read-only
evidence. It does not add a classifier, preview helper, runtime adapter,
published output, global installation, merge, push, or external mutation.

## Decision under review

Both candidates remain held. The manifest records `publish: false` and
`Codex workflow not demonstrated` for `cursor-how` at
`sources/cursor-plugins/manifest.json:1032-1049` and for `cursor-why` at
`sources/cursor-plugins/manifest.json:1985-1992`.

The `cursor-how` overlay records `not_proven_in_current_codex_session` and
`held_until_behavior_proof_and_permission_gate` at
`sources/cursor-plugins/overlays/cursor-how.json:20-37`. The `cursor-why`
overlay has the same availability/promotion hold and retains a contextual
`mcp-plugin-hook-install` finding: active connector discovery, external
evidence queries, and connector/MCP authentication are part of the behavior
at `sources/cursor-plugins/overlays/cursor-why.json:44-60`.

## `how`: real subsystem walkthrough

### Question and source contract

The question was: how does this repository render a declared-but-held skill
into a disposable candidate preview while keeping the published mirror and
catalog unchanged?

The pinned upstream `how` contract is explicit-only at
`sources/cursor-plugins/snapshot/pstack/skills/how/SKILL.md:1-4`. It chooses a
simple/direct path for a narrow question and a 2–4-angle parallel exploration
for a subsystem at lines 11–18, then requires evidence-backed synthesis and
the sections Overview, Key Concepts, How It Works, Where Things Live, and
Gotchas at lines 20–56. Its support prompts are the actual files under
`pstack/skills/how/references/`, not invented replacements.

### Entry point and flow

The real call chain is:

`main` → `preview_candidates` → `verify_snapshot` → `validate_manifest` →
candidate selection → `render_skill` → `rewrite_sibling_links` → staged rename.

- `main` dispatches `--preview-candidates` at
  `scripts/sync-cursor-plugin-skills.py:465-477`.
- `preview_candidates` loads the ledger, verifies the complete source snapshot,
  selects every `declared_for_distribution` entry (including held candidates),
  renders into temporary staging, and renames only into the caller-selected
  destination at `scripts/sync-cursor-plugin-skills.py:413-433`.
- `verify_snapshot` fail-closes on manifest schema/path errors, symlinks,
  physical inventory drift, per-skill file/license hashes, plugin-level support
  files, and native support hashes at
  `scripts/sync-cursor-plugin-skills.py:66-140`.
- `render_skill` copies the source directory, checks overlay source path/SHA,
  renames frontmatter, applies exact-count replacements, copies only ledger-
  approved support files, normalizes descriptions, translates explicit-only
  metadata, inserts the Codex note, rewrites links, copies license evidence,
  and writes `MIRROR.md` at `scripts/sync-cursor-plugin-skills.py:213-309`.
- `rewrite_sibling_links` maps declared preview siblings to local relative
  links and held/dormant siblings to pinned upstream URLs at
  `scripts/sync-cursor-plugin-skills.py:192-210`.
- `codex_invocation_policy` translates Cursor's
  `disable-model-invocation: true` into
  `agents/openai.yaml` with
  `policy.allow_implicit_invocation: false` at
  `scripts/sync-cursor-plugin-skills.py:174-189`.

### Real execution

Executed in the clean authority clone:

```text
python3 scripts/sync-cursor-plugin-skills.py --preview-candidates <disposable destination>
rendered 88 active skills, including held candidates, at <disposable destination>
```

The generated `cursor-how` tree contained six files, including its transformed
`SKILL.md`, support prompts, `MIRROR.md`, and
`agents/openai.yaml`. The generated `cursor-why` tree contained 16 files,
including the seven-category source playbooks and its explicit-only policy.
Both generated policies were:

```yaml
policy:
  allow_implicit_invocation: false
```

The rendered `cursor-how` frontmatter preserved the trigger wording and
removed the Cursor-only flag. Its Codex note preserved native read-only
delegation, coordinator ownership, and sequential fallback language. The
rendered `cursor-why` frontmatter preserved the evidence-category wording and
its Codex note retained the seven-category coverage map, actual connector
availability rule, null results, epistemic separation, and read-only scope.

The committed tree was then checked with:

```text
python3 scripts/sync-cursor-plugin-skills.py --check
mirror check passed: 91 physical, 54 published, 201 output files
```

The clone remained clean. The preview did not change `skills/mirrors-cursor`,
`reports/cursor-plugin-skills-state.json`, or
`.claude-plugin/marketplace.json`. The preview itself is not mutation-free:
it writes the explicitly supplied destination, so the destination was created
under `/private/tmp` and removed after inspection.

### `how` source steps achieved and not achieved

Achieved:

- real local entrypoint, calls, ownership, data boundaries, support files, and
  tests traced with paths and line numbers;
- read-only native explorer used against the exact authority clone and returned
  the same flow and boundaries;
- real candidate preview executed and inspected for both held skills;
- explicit-only policy conversion and held/published boundary observed;
- existing mirror suite exercised the preview, link, hash, catalog, and policy
  guards.

Not achieved:

- no live Codex skill discovery, automatic trigger, model response, or full
  `how` answer was executed through the Codex runtime;
- no claim of native Cursor runtime parity;
- existing tests do not directly assert every generated `cursor-how` support
  file; the direct output inspection above is the new evidence for this pass.

## `why`: rationale and evidence ledger

### Code anchor and source-control evidence

The code anchor is the two held manifest entries and overlays above, plus the
renderer boundary at `scripts/sync-cursor-plugin-skills.py:343-381` and the
explicit-only correction at `scripts/sync-cursor-plugin-skills.py:174-189`.

Local history shows:

- `fd69d184` — `Mirror selected Cursor plugin skills with pinned source and
  Codex proof gates (#61)`, which introduced both overlays and their held
  proof contracts;
- `06164f98`, `16eaa41c`, and `39bf581d`, which refined the pstack source
  mapping and sibling references;
- `0479ea88` — `fix(cursor): preserve explicit-only skill invocation in Codex`,
  which proves deterministic policy generation for published and held previews,
  but does not prove live activation.

GitHub PR #61 is merged and its body states that the mirror is a pinned,
reviewable source snapshot with deterministic overlays, that the renderer and
read-only fixture exist, and that the complete PR workflow remains unproven.
PR #64 is open and explicitly frames the 88-skill expansion as staged native
adapters: held candidates still require live behavioral proof, fresh top-level
task loading and automatic skill invocation remain unobserved, and global
installation/merge/cloud parity are outside demonstrated proof.

### What the available external sources returned

| Category | Source and query | Result |
|---|---|---|
| Source control / forge | Local Git; GitHub PR reads for `TheAngryPit/TheAngrySkills` #61 and #64 | Direct evidence above; no PR comments returned for either PR. |
| Issue tracker | Linear searches `cursor-how`, `cursor-why`, `TheAngrySkills` | No direct matching rationale. Returned unrelated/general records only; no ticket was used to infer the hold. |
| Long-form docs | Notion AI searches `cursor-how`, `cursor-why` | No results. |
| Team chat | Public Slack searches `cursor-how`, `cursor-why` | No results. Private/DM search was not used. |
| Infrastructure observability | Tool inventory | No Datadog/New Relic/Honeycomb/Grafana/Splunk read-only connector was exposed. Not searched. |
| Error tracking | Tool inventory | No Sentry/Rollbar/Bugsnag/Airbrake read-only connector was exposed. Not searched. |
| Product analytics | Tool inventory | No Databricks/Snowflake/BigQuery/ClickHouse/dbt/Redshift read-only connector was exposed. Not searched. |

### Epistemic result

- **Direct:** both entries are `publish: false`; both state that the Codex
  workflow is not demonstrated; the `why` overlay retains the connector/
  authentication security hold; the preview rendered both held candidates and
  explicit-only native policies; PR #61 and PR #64 state the remaining proof
  boundary.
- **Supported:** the immediate reason for holding both is missing live
  behavior proof. For `cursor-why`, connector availability, authorization, and
  read-only behavior are also necessary because the workflow actively queries
  external evidence categories.
- **Inferred:** promoting either now would turn a deterministic source/render
  artifact into an implied runtime capability, which the current evidence does
  not justify.
- **Unknown:** the original product/business forcing function, any rationale
  recorded in private chat or long-form docs not returned by the connected
  searches, and runtime behavior through a fully authenticated Codex model
  task.

## Actions not taken

No implementation helper, classifier, or preview helper was added. No manifest
promotion, generated catalog change, global/home change, Doctor run, external
message, push, merge, installation, or runtime cutover was performed.

## Delta: native role-flow proof

This section records the additional role execution requested after commit
`d7aaf8a7`. It does not repeat the renderer or mirror-test evidence above.

### `how` simple-path explainer

One native read-only `general-worker` Task was launched for the narrow question
“how does `--preview-candidates` render a held `cursor-how` candidate without
indexing it?” It read the pinned `how` skill and
`references/explainer-prompt.md`, without explorer findings and without
spawning another agent. The task returned the required sections:

- `Overview`
- `Key Concepts`
- `How It Works`
- `Where Things Live`
- `Gotchas`

The explainer cited the real entrypoint and symbols, the held/published split,
the explicit-only policy conversion, and the remaining live trigger,
delegation, and result-ownership gap. This is proof that the delegated
explainer role can execute in this host; it is not proof that the held skill is
automatically discovered or activated by Codex.

### `why` investigators

Four separate native read-only investigators were launched, each reading
`references/investigator-prompt.md` and only its assigned source playbook:

| Role | Native result |
|---|---|
| Source control | Read local Git, manifest, overlays, renderer, tests, and commits `fd69d184`, `06164f98`, `16eaa41c`, `39bf581d`, `0479ea88`. Confirmed the proof-gated hold and the separate preview path. Forge access was not available inside this investigator: the local `gh` token was invalid, the remote was private/local, and direct network access failed. |
| Linear | Authorized read-only access worked. Searches for `cursor-how`, `cursor-why`, `TheAngrySkills`, `#61`, and `#64` returned only unrelated records or empty results. No ticket rationale was admissible. |
| Notion | `self` and AI search were available. Exact and wider searches returned no relevant pages. This is an empty result, not an access failure. |
| Slack | Public and exposed all-conversations read-only searches covered exact terms, URL forms, PR numbers, and broader Cursor/pstack/held/publish terms; every search returned no results. No thread or permalink existed to inspect. |

The role-specific gaps are preserved rather than filled from another source:
Linear, Notion, and Slack provide no independent rationale; observability,
error-tracking, and analytics categories have no exposed matching connectors;
and the source-control subagent could not retrieve forge discussions from its
own native access path. The coordinator's earlier GitHub read evidence remains
in the main ledger above, but it is not substituted into the investigator's
reported access path.

### Native why synthesis

The synthesizer read `references/synthesizer-prompt.md` and
`references/epistemics.md`, then returned the exact required structure below.

#### The Question

Why do `cursor-how` and `cursor-why` remain held instead of published, and
what evidence supports that decision?

#### The Code in Question

The manifest entries, per-skill overlays, published-build filter, candidate
preview path, and static functional-overlay tests identified above.

#### What We Found

- **[Direct]** Both entries say `Codex workflow not demonstrated`, retain
  `publish: false`, and mark native behavior proof as pending
  (`sources/cursor-plugins/manifest.json:1028-1049,1985-1992`).
- **[Direct]** `cursor-how` requires a native reader plus bounded
  explorer/explainer behavior and remains held until behavior and permission
  proof (`sources/cursor-plugins/overlays/cursor-how.json:11-46`).
- **[Direct]** `cursor-why` requires source history plus authorized evidence
  connectors and remains held until connector availability, authorization, and
  read-only behavior are proven
  (`sources/cursor-plugins/overlays/cursor-why.json:11-37,44-60`).
- **[Supported]** The build mechanically publishes only `publish: true`, while
  preview renders declared held candidates without indexing them
  (`scripts/sync-cursor-plugin-skills.py:322-371,413-433`).
- **[Supported]** The functional tests keep both candidates outside the
  promoted set and prove static contract shapes, not native runtime behavior
  (`tests/test_cursor_functional_overlays.py:30-141`).
- **[Direct]** `fd69d184` introduced the mirror as a pinned source with Codex
  proof gates; later commits refined adaptation and explicit-only policy but
  did not promote either entry.

#### What We Can Reasonably Infer

- **[Inferred]** Publication likely waits for demonstrated native behavior,
  not static source integrity alone, because the ledger, overlays, and build
  all separate candidate review from publication.
- **[Inferred]** `cursor-how` is primarily a delegation/result-ownership proof
  gap; `cursor-why` has the higher bar because it crosses authenticated
  evidence connectors and must preserve read-only boundaries.

#### Competing Hypotheses

- **Native behavior gap:** supported by both manifest holds and proof cases;
  exact acceptance order remains unspecified.
- **Connector/security boundary:** supported specifically for `cursor-why` by
  its contextual security finding; no concrete incident was found, so this is
  preventive rather than incident-driven.
- **Packaging omission:** contradicted by the consistent manifest flags,
  overlays, tests, preview path, and multi-commit history.

#### What We Don't Know

- No direct owner statement gives final acceptance criteria, owner, or timing.
- No live `cursor-how` trigger, native explorer/explainer selection,
  unavailable-capability branch, or coordinator-owned result was run through
  automatic skill activation.
- No complete seven-category `cursor-why` run, connector authorization check,
  or end-to-end cited synthesis was run.
- Linear and Notion returned no matching rationale; Slack returned no messages
  or permalinks. Historical, archived, and private-message coverage cannot be
  inferred from empty search results.
- No observability, error-tracking, or product-analytics connector was
  exposed, so no production usage, failure, or adoption claim is possible.

#### Sources Consulted

- **Source control history:** local manifest, overlays, renderer, tests,
  reports, and five targeted commits; forge access was unavailable to the
  source-control investigator.
- **Issue / ticket tracker:** Linear exact searches for `cursor-how`,
  `cursor-why`, `TheAngrySkills`, `#61`, and `#64`; no matching rationale.
- **Long-form documents:** Notion exact and wider searches; no relevant pages.
- **Real-time team chat:** Slack exact, URL, PR-number, and broad searches;
  no results or permalinks.
- **Infrastructure observability:** not searched; no matching connector
  exposed.
- **Error / exception tracking:** not searched; no matching connector exposed.
- **Product analytics warehouse:** not searched; no matching connector
  exposed.

#### Confidence Summary

Confidence is high that the hold is intentional and proof-gated, with an
additional connector authorization/read-only gate for `cursor-why`. Confidence
is low about the final human acceptance criteria, owner decision, and any
production motivation because the relevant external sources were empty or
unavailable.
