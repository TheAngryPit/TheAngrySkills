# writing-fragments: approved adaptation

Source: [https://github.com/mattpocock/skills.git](https://github.com/mattpocock/skills.git).
Original integration source revision: 3cca18b368ae95cdbdebbff572ccafa662551015.
Operator approved the final Matt Pocock integration on 2026-09-12. MIT attribution is retained in LICENSE.

## What changed and why

Use collaborative naming and make the leading-word coinage optional when it clarifies a recurring idea.

The exact approved difference is [ADAPTATIONS.patch](ADAPTATIONS.patch). The patch file contains only the approved overlay.
Basis: [OpenAI Astra guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).
No additional behavior was invented during integration.

Historical upstream review: `24fe0ef7737efae15c87225755e9f6f5965e4888` on 2026-10-05. Per-file source hashes are recorded in UPSTREAM.json.

Current upstream review: `4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d` on 2026-10-06. Per-file source hashes are recorded in UPSTREAM.json.

## Upstream review

The daily Review adapted skill upstreams workflow alerts through a GitHub issue
when source files, supporting files or license change. It does not overwrite this
skill or accept a new baseline. UPSTREAM.json records reviewed hashes and commit.
During an approved review, scripts/sync-matt-adaptations.py builds in a temporary
directory, reapplies this overlay and validates it. A patch conflict preserves the
published version. Review every new upstream change before merging.
