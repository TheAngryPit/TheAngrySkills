# ask-pit: approved adaptation

Source: [Matt Pocock skills](https://github.com/mattpocock/skills).
Reviewed source revision: 3cca18b368ae95cdbdebbff572ccafa662551015.
Operator approved batch 01 on 2026-09-12. MIT attribution is retained in LICENSE.

## What changed and why

Retain the AskPit identity and Writing for Astra route. Replace fixed context limits, mandatory context clearing and zero-cost claims with native context decisions. Preserve the workflow map and intentional orchestration.

The exact approved difference is [ADAPTATIONS.patch](ADAPTATIONS.patch).
Basis: [OpenAI Astra guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).
These changes preserve the selected workflow; no measured performance or allowance improvement is claimed.

## Upstream review

The daily Review adapted skill upstreams workflow alerts through a GitHub issue
when source files, supporting files or license change. It does not overwrite this
skill or accept a new baseline. UPSTREAM.json records reviewed hashes and commit.
During an approved review, scripts/sync-matt-adaptations.py builds in a temporary
directory, reapplies this patch and validates it. A patch conflict preserves the
published version. Review every new upstream change before merging.
