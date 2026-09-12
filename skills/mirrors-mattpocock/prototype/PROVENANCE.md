# prototype: approved adaptation

Source: [https://github.com/mattpocock/skills.git](https://github.com/mattpocock/skills.git).
Reviewed source revision: 3cca18b368ae95cdbdebbff572ccafa662551015.
Operator approved the final Matt Pocock integration on 2026-09-12. MIT attribution is retained in LICENSE.

## What changed and why

Allow a focused assertion as the cheapest proof of a prototype question while keeping production test suites and production code out.

The exact approved difference is [ADAPTATIONS.patch](ADAPTATIONS.patch). The patch file contains only the approved overlay.
Basis: [OpenAI Astra guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).
No additional behavior was invented during integration.

## Upstream review

The daily Review adapted skill upstreams workflow alerts through a GitHub issue
when source files, supporting files or license change. It does not overwrite this
skill or accept a new baseline. UPSTREAM.json records reviewed hashes and commit.
During an approved review, scripts/sync-matt-adaptations.py builds in a temporary
directory, reapplies this overlay and validates it. A patch conflict preserves the
published version. Review every new upstream change before merging.
