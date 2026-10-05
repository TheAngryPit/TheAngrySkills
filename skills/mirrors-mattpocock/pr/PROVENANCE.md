# pr: approved adaptation

Source: [https://github.com/mattpocock/skills.git](https://github.com/mattpocock/skills.git).
Reviewed source revision: 24fe0ef7737efae15c87225755e9f6f5965e4888.
Operator approved first source inclusion on 2026-10-05. Original upstream credits are retained in SKILL.md and MIT attribution is retained in LICENSE.

## What changed and why

No content adaptation is approved for this package. The upstream files are preserved verbatim behind an explicit empty overlay.

The exact approved difference is [ADAPTATIONS.patch](ADAPTATIONS.patch). The empty file is intentional for a maintained copy.
No additional behavior was invented during integration.

## Upstream review

The daily Review adapted skill upstreams workflow alerts through a GitHub issue
when source files, supporting files or license change. It does not overwrite this
skill or accept a new baseline. UPSTREAM.json records reviewed hashes and commit.
During an approved review, scripts/sync-matt-adaptations.py builds in a temporary
directory, reapplies this overlay and validates it. A patch conflict preserves the
published version. Review every new upstream change before merging.
