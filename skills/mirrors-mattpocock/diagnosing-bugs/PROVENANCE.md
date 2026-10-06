# diagnosing-bugs: approved adaptation

Source: [Matt Pocock skills](https://github.com/mattpocock/skills).
Original integration source revision: 3cca18b368ae95cdbdebbff572ccafa662551015.
Operator approved batch 01 on 2026-09-12. MIT attribution is retained in LICENSE.

## What changed and why

Allow explicitly provisional hypotheses to help build a reproduction, without claiming an unverified cause or fix. Remove fixed hypothesis and reproduction counts and rhetorical guarantees; preserve evidence, diagnostic phases, regression validation and cleanup.

The exact approved difference is [ADAPTATIONS.patch](ADAPTATIONS.patch).
Basis: [OpenAI Astra guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).
These changes preserve the selected workflow; no measured performance or allowance improvement is claimed.

Historical upstream review: `24fe0ef7737efae15c87225755e9f6f5965e4888` on 2026-10-05. Per-file source hashes are recorded in UPSTREAM.json.

Current upstream review: `4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d` on 2026-10-06. Per-file source hashes are recorded in UPSTREAM.json.

## Upstream review

The daily Review adapted skill upstreams workflow alerts through a GitHub issue
when source files, supporting files or license change. It does not overwrite this
skill or accept a new baseline. UPSTREAM.json records reviewed hashes and commit.
During an approved review, scripts/sync-matt-adaptations.py builds in a temporary
directory, reapplies this patch and validates it. A patch conflict preserves the
published version. Review every new upstream change before merging.
