# Real `thermos` / `swarm` behavior evidence

Date: 2026-09-14
Branch: `codex/thermos-swarm-real-20260914`
Authority head: `c3ecb26184994071da56e6aacd04682a760fad0e`
Diff case: `c0561f382d0e07a28810cef73c72e20beebe2e42..c3ecb26184994071da56e6aacd04682a760fad0e`
Clone: `/private/tmp/theangryskills-pstack-20260913-xcCoXg/repo`

Scope was read-only native role evidence for the real PR #64 head diff. No
renderer, build helper, tests, generated tree, source/manifest edits, hooks,
secrets, global install, push, merge, or PR edit was performed.

## Source contract read first

The complete pinned source and support material was read before delegation:

- `sources/cursor-plugins/snapshot/thermos/skills/thermos/SKILL.md`
- `sources/cursor-plugins/snapshot/thermos/agents/thermo-nuclear-review-subagent.md`
- `sources/cursor-plugins/snapshot/thermos/agents/thermo-nuclear-code-quality-review-subagent.md`
- `sources/cursor-plugins/snapshot/pstack/skills/swarm/SKILL.md`
- `sources/cursor-plugins/overlays/cursor-thermos.json:10-38`
- `sources/cursor-plugins/overlays/cursor-swarm.json:10-34`
- mirrored rubrics `skills/mirrors-cursor/cursor-thermo-nuclear-review/SKILL.md` and
  `skills/mirrors-cursor/cursor-thermos-thermo-nuclear-code-quality-review/SKILL.md`

The real diff scope was the publication/accounting change in
`.claude-plugin/marketplace.json`, the `cursor-how`/`cursor-why` manifest and
overlays, and the changed evidence reports. The Thermos lenses received the
same scoped diff. The Swarm workers received disjoint slices of that same diff.

## Source-step matrix

| Workflow | Required source step | Observed result | Status |
|---|---|---|---|
| Thermos | Gather one scoped diff and pass it to two distinct lenses | Both reviewers received the same real PR #64 diff and separate role prompts | Complete |
| Thermos | Run bug/security and code-quality lenses in parallel | Kierkegaard and Sagan completed independently | Complete |
| Thermos | Preserve separate reports | Each lens returned its own verdict/findings below | Complete |
| Thermos | Coordinator deduplicates and synthesizes | Coordinator verdict: `ISSUES`; three P2 themes retained | Complete |
| Swarm | Frame explicit worker count and disjoint slices | N=2; Boole owned catalog/manifest/overlays, Singer owned ledger/matrix | Complete |
| Swarm | Fan out in one parallel launch | Both workers launched together | Complete |
| Swarm | Drain workers and aggregate one report | Both returned `PARTIAL`; aggregate below preserves both results | Complete |
| Swarm | Preserve missing/partial outcome | Missing current CI artifact and out-of-slice policy proof remain explicit | Complete |

## Thermos: two independent lenses

### Lens 1 — bug/security/devex

Agent: Kierkegaard `01a0a055-dc99-7b51-8c3e-4f81c57a0a57`.

Verdict: `ISSUES`.

1. **P2 — Promotion evidence is stale and internally contradictory.** The
   changed report claims publication while retaining old authority HEAD
   `0479ea...`, old held-state wording, and pre-promotion `54/201` counts
   (`reports/pstack-how-why-real-20260914.md:5,15-26,177-198`; current
   publication is manifest/catalog state at `sources/cursor-plugins/manifest.json:1028-1049,1961-1992`).
2. **P2 — `cursor-how` negative-path proof is overstated.** The overlay calls
   the missing/error cases behavioral evidence, while the report admits that
   only `sed` failures were observed and native `Read`/Task errors remain
   unproven (`sources/cursor-plugins/overlays/cursor-how.json:32-34`;
   `reports/pstack-how-why-real-20260914.md:370-374`).
3. **P2 — `cursor-why` remains a permission-boundary gap while published.**
   Its scanner verdict is `needs_human_review`, the connector/authentication
   finding remains, and the marketplace now exposes it
   (`sources/cursor-plugins/manifest.json:1961-1992`;
   `sources/cursor-plugins/overlays/cursor-why.json:44-59`;
   `.claude-plugin/marketplace.json:303`). The lens did not claim an exploit;
   it identified operator/tool permission dependence.

No reviewer dropout occurred. The lens reported code/catalog consistency and
no tests/builds/runtime were rerun.

### Lens 2 — maintainability/code quality

Agent: Sagan `01a0a055-db34-71e3-9368-4bc7d9130737`.

Verdict: `ISSUES`.

1. **P2 — Promotion classification is growing as name-based test special
   cases.** The changed tests add `cursor-how`/`cursor-why` exclusions and
   dedicated name branches, while fixed counts also change from `34/19` to
   `36/17` (`tests/test_cursor_functional_overlays.py:84-92,131-134`;
   `tests/test_cursor_plugin_mirror.py:78,101`). The lens recommends deriving
   assertions/counts from explicit promotion metadata rather than synchronized
   name literals.
2. No other high-confidence maintainability regression was found; the lens
   observed no file-size breach or hidden orchestration wrapper.

### Coordinator synthesis

The two lenses agree on `ISSUES`, but identify different failure modes:

- Evidence correctness: current publication claims are not fully reproducible
  because the promotion report still carries historical authority/counts.
- Proof honesty: the `how` negative path is bounded `sed` evidence, not native
  Read/Task behavior.
- Permission boundary: publishing `why` does not enforce connector scopes;
  future runs remain bounded by actual host permissions.
- Maintainability: promotion classes are encoded in multiple name/count test
  branches rather than one authoritative metadata-derived model.

No Thermos `missing reviewer` branch was needed because both lenses completed;
no success was invented—the combined verdict remains `ISSUES`.

## Swarm: two disjoint workers, drain, aggregate

### Frame and slices

Worker count was explicitly N=2. The slices were disjoint:

- **Slice A — Boole:** `.claude-plugin/marketplace.json`, the two manifest
  entries, and both overlays. Focus: publication/proof/permission consistency.
- **Slice B — Singer:** `reports/cursor-held-closure-ledger.md` and
  `reports/cursor-native-capability-matrix.md`. Focus: evidence accounting and
  validation/gap claims.

### Worker 1 — Slice A

Agent: Boole `01a0a055-ddb2-7f33-900a-0083be811904`.

Result: `PARTIAL`.

Observed:

- Marketplace paths for `cursor-how` and `cursor-why` are present.
- Both manifest entries are `publish: true` and
  `declared_for_distribution: true`.
- Proof claims remain bounded and automatic trigger selection remains
  explicitly unobserved.
- Permission limits, unavailable evidence categories, read-only scope, and
  the `cursor-why` security finding remain retained.

Missing inputs:

- Explicit-only `agents/openai.yaml` policy was outside the assigned slice.
- No automatic-selection, renderer, build, or test proof was performed.

### Worker 2 — Slice B

Agent: Singer `01a0a055-dbcf-7a12-8b17-2b027a814941`.

Result: `PARTIAL`.

Observed:

- The ledger records local validation but explicitly says CI validation for
  the new published head remains unread (`reports/cursor-held-closure-ledger.md:123-126`).
- The capability matrix says CI passed only on prior head `9e76c597` and
  requires current-head readback (`reports/cursor-native-capability-matrix.md:32-36`).
- Published `how`/`why` retain bounded-scope and runtime-parity gaps
  (`reports/cursor-native-capability-matrix.md:14`).

Missing input:

- Current GitHub `Validate skill stack` status/artifact for head `c3ecb261`.
  No success was inferred.

### Swarm aggregate

`PARTIAL`: both disjoint workers completed, but neither can be upgraded to
`PASS` without the missing inputs they named. Their results are preserved
separately above and combined here; no worker was silently dropped and no
missing-worker success was invented.

No worker error/dropout branch occurred in this run. The explicit partial
branch is the observed missing-input outcome required by the swarm contract.

## Validation and limits

- Source/support/overlay reads completed before delegation.
- Real PR #64 head and parent diff were used as the review case.
- Thermos had two independent reviewer outputs plus coordinator synthesis.
- Swarm had two parallel workers, disjoint ownership, drain, and aggregate.
- No renderer, build helper, test suite, CI query, or external PR mutation was
  performed in this lot.
- No automatic Thermos/Swarm skill trigger, cloud-worker parity, or external
  runtime equivalence is claimed.

## Final bounded verdict

Thermos behavior is **observed as two-lens native review plus coordinator
synthesis**, but the real diff receives `ISSUES`, not approval. Swarm behavior
is **observed as two-worker fan-out/drain/aggregation with explicit partial
handling**, but the real diff receives `PARTIAL` because current CI and other
slice-limited evidence are missing. Neither result justifies promotion of
`cursor-thermos` or `cursor-swarm`.
