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
