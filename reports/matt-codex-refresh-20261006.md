# Matt, AskPit and Writing for Astra refresh — 6 October 2026

Reviewed source:4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d. Integration is based on existing PR100 exactfff88c970dd09d17cd989d5798c9ce16137025e5, preserving its earlier curated pr package, source-path migrations, generator provenance history and native workflow overlays.

## Result

Eleven existing Matt mirror packages, AskPit and Writing for Astra were reviewed/refreshed. AskPit retains its identity and Writing for Astra route, native context judgment and intentional orchestration while incorporating the current implement-spec/pr/retro flow. The pr route is catalog-backed and remains dependent on actual installation. Writing for Astra incorporates useful pointer, information-structure, completion and source-of-truth guidance. Its provenance explains why forced context splits, leading-word heuristics and unsupported negation rules were not adopted.

The new portable chief-of-staff source is curated with an empty overlay and upstream explicit-only metadata. Its first provenance review is this October6source inclusion, not the September12integration. It suggests schedules subject to harness support; this task creates no schedules or agent runs from that skill. Existing package original-review history is preserved separately from the refreshed source pin.

Vanilla ask-matt and writing-for-agents are absent from the emitted package inventory and catalog. They remain upstream provenance, not duplicate installable variants. The removed upstream resolving-merge-conflicts skill remains the existing legacy package; its explanatory docs page does not replace its behavior. No live skill folder was changed and no installation was performed.

## Verification

Generator reverse proof and hashes pass for33manifest packages (32mirrors plus AskPit). Package source review and Writing for Astra decisions are code-proven; live agent invocation is not claimed. Complete repository pytest: 353 passed and 2 subtests passed; final focused generator/watch/automation suite: 87 passed. Shared catalog:zeroerrors. Security comparison against exactPR100base:existinggrillingblockingfinding anddiagnosing-bugsreviewfinding unchanged byte-for-byte in detailednormalizedcomparison;0new/aggravated findings,0findings onAskPit,WritingforAstraandchief-of-staff. See matt-security-refresh-20261006.json. Git diff --check passes. Remote exact-headCI/review remain the final merge gate. Source publication is separate from manual installation.

## Files in this refresh

- `.claude-plugin/marketplace.json`
- `docs/ask-pit-writing-for-astra.md`
- `docs/matt-adaptations.md`
- `scripts/matt-adaptations.json`
- `skills/core/ask-pit/ADAPTATIONS.patch`
- `skills/core/ask-pit/PROVENANCE.md`
- `skills/core/ask-pit/SKILL.md`
- `skills/core/ask-pit/UPSTREAM.json`
- `skills/engineering/writing-for-astra/PROVENANCE.md`
- `skills/engineering/writing-for-astra/SKILL.md`
- `skills/engineering/writing-for-astra/UPSTREAM.json`
- `skills/mirrors-mattpocock/codebase-design/PROVENANCE.md`
- `skills/mirrors-mattpocock/codebase-design/UPSTREAM.json`
- `skills/mirrors-mattpocock/diagnosing-bugs/PROVENANCE.md`
- `skills/mirrors-mattpocock/diagnosing-bugs/UPSTREAM.json`
- `skills/mirrors-mattpocock/domain-modeling/PROVENANCE.md`
- `skills/mirrors-mattpocock/domain-modeling/UPSTREAM.json`
- `skills/mirrors-mattpocock/implement-spec/PROVENANCE.md`
- `skills/mirrors-mattpocock/implement-spec/UPSTREAM.json`
- `skills/mirrors-mattpocock/improve-codebase-architecture/PROVENANCE.md`
- `skills/mirrors-mattpocock/improve-codebase-architecture/UPSTREAM.json`
- `skills/mirrors-mattpocock/pr/PROVENANCE.md`
- `skills/mirrors-mattpocock/pr/UPSTREAM.json`
- `skills/mirrors-mattpocock/retro/PROVENANCE.md`
- `skills/mirrors-mattpocock/retro/UPSTREAM.json`
- `skills/mirrors-mattpocock/setup-matt-pocock-skills/PROVENANCE.md`
- `skills/mirrors-mattpocock/setup-matt-pocock-skills/UPSTREAM.json`
- `skills/mirrors-mattpocock/tdd/PROVENANCE.md`
- `skills/mirrors-mattpocock/tdd/UPSTREAM.json`
- `skills/mirrors-mattpocock/triage/PROVENANCE.md`
- `skills/mirrors-mattpocock/triage/UPSTREAM.json`
- `skills/mirrors-mattpocock/wait-what/PROVENANCE.md`
- `skills/mirrors-mattpocock/wait-what/UPSTREAM.json`
- `tests/test_matt_adaptations.py`

New chief-of-staff package files are included in addition to this tracked diff list. Generator and upstream-watch changes preserve historical provenance and explicitly retained legacy packages.

Remote Codex review found that Writing for Astra original integration hash had been replaced. The correction restores3cca18b368ae95cdbdebbff572ccafa662551015 as originalintegration and records4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d separately as currentreview. The added provenance regression failed before the current-review line was supplied and passed after the correction.

Two further remote review findings were corrected at their owner: repeated refreshes now preserve prior reviews as history with one current revision; batch refresh validates/skips the explicitly pinned legacy package and reaches later packages. Both real regressions fail against8c390ef and pass after the fix. Read-only watchers likewise distinguish accepted source retirement from source return/license drift, without touching retained package data. Full batch refresh and reverse proofs pass; focused 87 tests pass. The native detector against the full upstream history reports changed:false at revision 4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d. This proves the CLI detection path, not a scheduled execution.
