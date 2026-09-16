# Matt editorial audit

Date: 2026-09-16
Audited upstream revision: `3cca18b368ae95cdbdebbff572ccafa662551015`
Audit branch: `codex/editorial-closure-20260916`

## Scope and count reconciliation

This pass reviewed every `SKILL.md` in the 30 `skills/mirrors-mattpocock/*`
directories, the separately packaged `skills/core/ask-pit`, the separately
maintained `skills/engineering/writing-for-astra`, and all relevant support
files in those packages. The original Matt source was read from the physical
checkout at `/private/tmp/matt-skills-upstream-20260915`; its HEAD and every
Matt `UPSTREAM.json` record the revision above.

The requested phrase “30 adaptations including AskPit and Writing for Astra”
does not match the physical or manifest inventory. The repository currently
contains:

- 30 Matt mirror packages under `skills/mirrors-mattpocock/`;
- 1 additional manifest item, `ask-pit`, for 31 manifest items total;
- 1 separately maintained Writing for Astra package, making 32 monitored
  packages in `scripts/matt-adaptations-detector.py`.

The manifest tests codify 31 items, 30 mirror names, and `ask-pit` as the extra
item. The detector appends Writing for Astra separately. No count-changing
edit is proposed: changing either source would alter the established manifest
or monitoring contract.

## Review method

The semantic review applied the following criteria to roots and relevant
support files:

- **Astra** — narrow trigger, minimal root router, progressive disclosure,
  contextual pointers, preserved multimodel and native compatibility,
  explicit safe-work permission, and a bounded result plus evidence;
- **WA** — Matt's original Writing for Agents guidance: one trigger per branch,
  useful context pointers, in-file completion criteria, canonical sources, and
  no-op pruning;
- **Curator** — `scan_skill_catalog.py` and `audit_skill_frontmatter.py`, with
  warnings treated as leads rather than findings;
- **H** — Humanizer: factual fidelity, plain prose, no fabricated authority,
  inflated significance, chatbot residue, or decorative rewriting;
- **K** — Karpathy Q8: explicit outcomes, invariants, scope, bounded autonomy,
  human review surfaces, and reproducible verification.

The 30 mirror packages retain intentional model-invoked versus explicit-only
profiles, orchestration, tracker commands, templates, ordered procedures,
security gates, and native model/permission boundaries. Those are behavior, not
generic recipe padding.

## Nominal matrix

The source hash is the exact `UPSTREAM.json["upstream_sha256"]["SKILL.md"]` for
the original Matt root. All rows use the reviewed upstream commit above.

| Skill | Source path | Source `SKILL.md` SHA-256 | Criteria | Finding and disposition | Changed paths |
| --- | --- | --- | --- | --- | --- |
| `code-review` | `skills/engineering/code-review` | `47f4e52c21694def9c7c11cbfbf891ca35eac7a93e395797515be3c8a409ae50` | A/WA/C/H/K | Narrow review trigger; WIP scope and two-axis reviewer contract are intentional. Pass. | none |
| `diagnosing-bugs` | `skills/engineering/diagnosing-bugs` | `77f3cf31bc99b2f49af943222526531fcc9fc41d047626d3640e875e85af3e84` | A/WA/C/H/K | Approved adaptation still retained fixed `100×` and `1000` fuzz counts. Replaced both with resource-bounded repetitions while preserving the diagnostic loop. | `ADAPTATIONS.patch`, `PROVENANCE.md`, `SKILL.md`, `UPSTREAM.json` |
| `tdd` | `skills/engineering/tdd` | `cb01f66bebfaa25fa1f88e6b7e769cd9fd9f35b1120b8563749820738814c927` | A/WA/C/H/K | Agreed seams, red-green loop, and interface behavior remain explicit. Pass. | none |
| `resolving-merge-conflicts` | `skills/engineering/resolving-merge-conflicts` | `9d8114f8ef0b31f535a265fc05c364bd8cf2e2895a830040e06c22acb11f54b0` | A/WA/C/H/K | Primary-source resolution, cancellation authorization, and finish checks encode correctness. Pass. | none |
| `ask-pit` | `skills/engineering/ask-matt` | `b25d86fb36b1d294eeead5d7db529f86135f9671f2afcd607579a63bb2213769` | A/WA/C/H/K | Minimal router keeps the AskPit identity, Writing for Astra route, phase choices, orchestration, and native context decisions. Pass. | none |
| `retro` | `skills/in-progress/retro` | `264f3330f1e2382af89610ed048ba0ed6d08883eb69f596a8f1df3f1e1a4c6a1` | A/WA/C/H/K | Explicit-only retrospective trigger and Writing for Astra pointer are contextual. Pass. | none |
| `setup-matt-pocock-skills` | `skills/engineering/setup-matt-pocock-skills` | `2bcd89e97777cdb705914424e39c97d5db524c8eb4eafac8120778a07774f0ec` | A/WA/C/H/K | Setup questions now skip choices already determined by repo/harness; tracker and domain support docs retain concrete branches. Pass. | none |
| `scaffold-exercises` | `skills/misc/scaffold-exercises` | `75f5c9d771606fb9762f16522efc954df11c324f87148d8ff069bce166257de9` | A/WA/C/H/K | Lint command, file requirements, solution-only proof, and commit boundary are observable contracts. Pass. | none |
| `codebase-design` | `skills/engineering/codebase-design` | `2c20617f87ec8af6a434859f381b2f061a69b530444e74eb39e78bb016a6d1e2` | A/WA/C/H/K | Approved vocabulary exception, evidence-based seam rule, and replacement-test condition are coherent. Pass. | none |
| `domain-modeling` | `skills/engineering/domain-modeling` | `327a2b50620e2fd70abc6893cd6965e76b20f8d0adb0dc2c8d5eb3845efb643e` | A/WA/C/H/K | Root and `ADR-FORMAT.md`/`CONTEXT-FORMAT.md` separate glossary terms from implementation decisions. Pass. | none |
| `grill-with-docs` | `skills/engineering/grill-with-docs` | `7de372c13488f1ee96cc11cd8907b56b6809cc93eef776eeddd37de6b6cbe3fe` | A/WA/C/H/K | Two-skill on-ramp is the intentional stateful workflow. Pass. | none |
| `implement` | `skills/engineering/implement` | `6d3fd9e83b8f36e5213854779db49b256a457a7ebb4a503e53fa7dcff696adc3` | A/WA/C/H/K | Explicit-only implementation keeps TDD, regular checks, review, and commit bounds. Pass. | none |
| `improve-codebase-architecture` | `skills/engineering/improve-codebase-architecture` | `d1ac25511a936ff4250a48dbcefda363837d6bb9321b3cba73df99fa37270a75` | A/WA/C/H/K | Root and `HTML-REPORT.md` still state the old one-adapter rule and prohibit established `boundary` terms, conflicting with approved `codebase-design`. Held as a new behavior proposal because this package has an intentional empty overlay. | none |
| `prototype` | `skills/engineering/prototype` | `714de632d116bb73f65cdb5a882db15b9369a6713b9a47c0fad827848f0bfbe3` | A/WA/C/H/K | Root and UI support said “no tests” while approved `LOGIC.md` permits a focused assertion. Aligned all three surfaces to “no production test suite; focused assertion allowed.” | `ADAPTATIONS.patch`, `SKILL.md`, `UI.md`, `UPSTREAM.json` |
| `research` | `skills/engineering/research` | `985569f15739c713d6784887c3d186d4ef9ac85bec5ad9c068d25bf0739928e4` | A/WA/C/H/K | Primary-source requirement, single cited output, and explicit background delegation are intentional. Pass. | none |
| `to-spec` | `skills/engineering/to-spec` | `43ad9cf318e5e7d3d1fa360253a37021796dc87a0c2e595ad262661a10f85088` | A/WA/C/H/K | Settled seams can continue; publishing, user stories, edge cases, and out-of-scope sections remain bounded. Pass. | none |
| `to-tickets` | `skills/engineering/to-tickets` | `5c9fba69845c2519b9b35b9af42ae5142c21f8ca15ac2123dc2722002c8058ae` | A/WA/C/H/K | Demonstrated-blocker prefactoring, vertical slices, blocking edges, and tracker-specific paths are correctness contracts. Pass. | none |
| `triage` | `skills/engineering/triage` | `623a2ed692bdc77d2090e2a3dea3b627dd722ad3bbaca0be83aada75292c8fc4` | A/WA/C/H/K | State machine, human approval points, redaction, and `AGENT-BRIEF.md`/`OUT-OF-SCOPE.md` support contracts are explicit. Pass. | none |
| `wayfinder` | `skills/engineering/wayfinder` | `fee6e1d0c50f0e736b4ef8a599060c959afae904c9a97d82c97f049fcc3aa0f1` | A/WA/C/H/K | Approved bounded ticket sizing and native research fallback preserve the map and context pointers. Pass. | none |
| `wizard` | `skills/engineering/wizard` | `bdf31d48211ea559878f95a4f344aeabf8d85897488ba564382bab0b000daac1` | A/WA/C/H/K | Human-only steps, exact UI/command provenance, confirmation gates, and reusable `template.sh` are correctness-critical. Pass. | none |
| `implement-spec` | `skills/in-progress/implement-spec` | `f703b5f41df9c2202e19540d203e0d5fc32613572a838a070136cc22e712b129` | A/WA/C/H/K | Explicit workflow authorization, branch-only fallback, role preservation, review, and cleanup are bounded. Pass. | none |
| `loop-me` | `skills/in-progress/loop-me` | `e44d1cc3e760fb86ac42964c2a5f1fcac511715db50fb375f3f7be814de1eaa7` | A/WA/C/H/K | Workflow vocabulary and completion contract now allow explicit human checkpoints without open-ended interviewing. Pass. | none |
| `writing-beats` | `skills/in-progress/writing-beats` | `a96abafa2372eede8267d770138b322d6125da8adaa7ccf0a5e08e4ee13ee71e` | A/WA/C/H/K | Explicit-only trigger and 3–5 beat loop are authorial workflow controls, with natural-end completion. Pass. | none |
| `writing-fragments` | `skills/in-progress/writing-fragments` | `298b0edd23df229183630de592ed8aa4289233560f2040691f6eb77caeaad4ea` | A/WA/C/H/K | Optional leading-word coinage removes forced jargon while preserving fragment capture and append-only safety. Pass. | none |
| `writing-shape` | `skills/in-progress/writing-shape` | `f5e6c57bdd85178ace4a260c92f46da6b64ddee18215b461d875739c68976f72` | A/WA/C/H/K | Format tradeoffs are discussed only when they affect meaning or review; raw material remains read-only. Pass. | none |
| `grill-me` | `skills/productivity/grill-me` | `caaf8b8de1684f96e26b28f3c29189db5c89cce4b73e1c93d86164f66ef88637` | A/WA/C/H/K | Small explicit-only wrapper with a precise delegation pointer. Pass. | none |
| `grilling` | `skills/productivity/grilling` | `10ff989e7498b23b5acb49d5048f11dcd906757d2f79c5cdf8a00001381296f2` | A/WA/C/H/K | Native fact lookup or bounded delegation is allowed; decisions remain with the user. Pass. | none |
| `handoff` | `skills/productivity/handoff` | `7c62de979fdc7ac32fb5ddb2146156c917f80ee070d30fadc9d40343c4b6ed25` | A/WA/C/H/K | Temp-directory destination, artifact pointers, and redaction are explicit. Pass. | none |
| `teach` | `skills/productivity/teach` | `a32df9dcdfc0c4fdc1c98e1ed3940c5f56b84c1aa90ff60346f32b8b53915b43` | A/WA/C/H/K | Trust-source claim grounding, stateful lesson records, and mission confirmation are concrete. Pass. | none |
| `to-questionnaire` | `skills/productivity/to-questionnaire` | `b5eb929842ee0e93d867c5e906d183d350f2f2d149eaeaa86967d94d8eda1d3b` | A/WA/C/H/K | Questions target the recipient knowledge gap; one-idea questions and answer stubs are output contracts. Pass. | none |
| `wait-what` | `skills/productivity/wait-what` | `e3f44e3ccbc0e7b62f20ba70b295fc9c9f4aa3f96c77168faee1c71bacbf4215` | A/WA/C/H/K | Narrow corrective trigger and contextual language pointer are sufficient. Pass. | none |
| `writing-for-astra` | `skills/productivity/writing-for-agents` | `551adca942227b44192edba88acd4e8db911f0121ce58ad16944ccf6a896a74a` | A/WA/C/H/K | Maintained adaptation has a minimal root, contextual Codex reference, completion bounds, native permission boundary, and preserved multimodel/orchestration requirements. Pass. | none |

## Applied edits

These edits are limited to already-approved adaptation intent and preserve the
observable workflow.

### `prototype`

Before, `SKILL.md` rule 4 said:

> No tests, no error handling beyond what makes the prototype runnable, no abstractions.

After:

> No production test suite, no error handling beyond what makes the prototype runnable, and no abstractions. A focused assertion is allowed when it is the cheapest proof of the question; keep it separate from production code.

The same boundary is now stated in `UI.md`, and the existing approved
`LOGIC.md` wording remains canonical. This removes an internal contradiction
without authorizing production code or a production test suite.

### `diagnosing-bugs`

Before, the non-deterministic branch required `Loop the trigger 100×`, and the
property/fuzz branch required `run 1000 random inputs`.

After, both say to repeat or generate enough varied inputs to distinguish the
failure from noise within available time and resources, and to report
uncertainty when the failure remains rare. The diagnostic phases, feedback-loop
completion criterion, regression test seam, and cleanup remain unchanged.

## Held new behavior proposal

`improve-codebase-architecture` has an empty overlay, so changing it would
create a new adaptation choice. The current text is:

- `SKILL.md:13`: “one adapter = hypothetical seam, two = real” and “don't drift
  into ... boundary”;
- `HTML-REPORT.md:112`: “Never substitute ... boundary (for seam)”.

The approved `codebase-design` root now says one adapter is evidence rather than
proof and permits an established domain or integration term such as `boundary`.
Proposed, for a later owner decision:

- `SKILL.md:13` before: “one adapter = hypothetical seam, two = real” and
  prohibit `boundary`.
- after: use the approved evidence-based seam rule and preserve `boundary` when
  it is an established domain or integration term.
- `HTML-REPORT.md:112` before: prohibit `boundary` as a seam synonym in all
  report prose.
- after: require the architecture vocabulary for architecture concepts while
  retaining established project terms where they carry domain meaning.

No edit was made for this proposal. No fixed counts in `writing-beats`, exact
1024-character triage output, or ordered setup/debug/template steps were
changed: those are workflow or output contracts and no approved recommendation
authorizes changing them.

## Catalog and provenance checks

The scoped catalog scan covered 32 skills (30 mirrors plus AskPit and Writing
for Astra), with zero errors and zero warnings. The shared frontmatter auditor
returned zero errors for all 32 roots.

`python3 scripts/sync-matt-adaptations.py --check` passed for all 31 manifest
items after the edits. Reverse provenance therefore still proves the recorded
upstream files plus only the patch overlay for every Matt package. AskPit
provenance preserves its identity and Writing for Astra route. Writing for
Astra's upstream hashes and original source path remain unchanged.

## Verification

Checks run on this branch:

```text
python3 scripts/sync-matt-adaptations.py --check
  passed: all 31 manifest items

python3 skills/core/skill-catalog-curator/scripts/scan_skill_catalog.py \
  --root skills/mirrors-mattpocock --root skills/core/ask-pit \
  --root skills/engineering/writing-for-astra --json
  32 skills scanned; 0 errors; 0 warnings

python3 skills/core/skill-catalog-curator/scripts/audit_skill_frontmatter.py \
  <each owned root> --profile shared
  0 errors across all 32 roots

pytest -q tests/test_matt_adaptations.py tests/test_ask_pit_sync.py \
  tests/test_audit_skill_frontmatter.py
  48 passed in 0.64s

git diff --check
  passed
```

No install, dispatch, publish, merge, baseline acceptance, permission change,
or external action was performed by this pass.
