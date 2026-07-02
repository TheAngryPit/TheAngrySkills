## Karpathy Skill Eval Summary

Date: 2026-04-17

### Goal

Evaluate and tighten the `karpathy-agentic-guidelines` skill using:
- Agent Skills best practices
- an autoresearch-style frozen-harness loop
- a quantized `q8` variant for lower always-loaded cost

### Phases

#### Phase 1: Harness setup

- Built a fixed 3-case harness:
  - `small-change`
  - `delegation`
  - `research-loop`
- Locked the output contract to a required heading schema in the fixture README.
- Added a local runner that installs each skill variant into an isolated `CODEX_HOME` and runs `codex exec`.

#### Phase 2: First iterations

- Compared:
  - `without_skill`
  - `current_skill`
  - `q8`
- Found the main weakness was not `small-change` or `delegation`.
- The real gap was `research-loop`, especially wording around:
  - `frozen harness`
  - `fixed measuring stick`
  - `measure and record the baseline current version`
  - explicit keep/discard phrasing

#### Phase 3: Skill revision

The `current_skill` gained:
- stronger defaults over menus
- clearer validation-loop wording
- more explicit research-loop template language

The `q8` variant gained:
- tighter default-mode guidance
- explicit research-loop phrasing in the quick reference
- stronger `research-loop.md` reference wording

#### Phase 4: Rerun with corrected token capture

The runner was updated to read usage from `turn.completed.usage`, which made token comparisons reliable.

### Stable methodology

- Keep `without_skill` as the frozen baseline.
- Let `current_skill` and `q8` evolve, but never change the case files or heading contract mid-comparison.
- Compare:
  - pass rate
  - wall-clock time
  - token usage
- Prefer the variant that improves pass rate without paying avoidable cost or fragility.

### Best benchmark results on GPT-5.4 Mini

Best read:
- `q8` is the strongest ship candidate.
- It matched or beat the `current_skill` on pass rate.
- It was materially cheaper in tokens than both `without_skill` and `current_skill`.
- It was also faster than the richer `current_skill`.

Key numbers:
- `without_skill`
  - mean pass rate: `0.72`
  - mean time: `53.8s`
  - mean tokens: `731,872`
- `current_skill`
  - mean pass rate: `1.00`
  - mean time: `64.2s`
  - mean tokens: `747,771`
- `q8`
  - mean pass rate: `1.00`
  - mean time: `46.6s`
  - mean tokens: `493,584`

### Main keep/discard decisions

Keep:
- defaults over menus
- explicit heading-contract obedience
- explicit `frozen harness` / `fixed measuring stick` wording
- `measure and record the baseline current version`
- concise keep/discard rules

Discard:
- vague research-loop language
- wording that implies the harness is fixed without naming it clearly
- verbose always-loaded content when the same guidance can live in a reference

### Current conclusion

- Keep the fuller `current_skill` as the rich reference version.
- Prefer `q8` when shipping the default operational variant.
- If further work continues, focus on:
  - robustness to output-contract drift
  - token reduction without weakening research-loop specificity

### Spark final spot check

Single-round result on `gpt-5.3-codex-spark`:
- `without_skill`
  - mean pass rate: `0.78`
  - mean time: `24.2s`
  - mean tokens: `595,354`
- `current_skill`
  - mean pass rate: `0.78`
  - mean time: `21.5s`
  - mean tokens: `382,609`
- `q8`
  - mean pass rate: `0.89`
  - mean time: `18.6s`
  - mean tokens: `350,385`

Read:
- On Spark, `q8` still wins.
- It is the fastest variant.
- It is also the cheapest in tokens.
- The fuller `current_skill` still reduces token cost heavily versus baseline, but it does not beat `q8`.
