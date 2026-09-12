# Writing for Astra provenance

Operator-owned adaptation inspired by Matt Pocock's writing-for-agents.
Upstream: https://github.com/mattpocock/skills
Source path: skills/productivity/writing-for-agents
Reviewed revision: 3cca18b368ae95cdbdebbff572ccafa662551015
License: MIT; upstream attribution is retained in LICENSE.

Basis: [OpenAI guidance for Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).

This is a separate maintained skill, not a one-to-one mirror. Upstream updates
do not overwrite it automatically. New semantic changes need owner review.

Retained: narrow context pointers, conditional disclosure, grouped concepts,
canonical sources, meaningful completion and model-relative evaluation of rules.
Changed: outcome-led guidance instead of prioritizing ordered recipes; no hidden
sequence through forced context boundaries, adjective escalation, speculative
negation rule or compression of technical criteria into vague keywords.
Codex-specific invocation guidance lives in a conditional reference.
Intentional orchestration and multi-model correctness remain requirements.

Root line counts at creation: upstream 81; adapted root 63.
No measured performance or allowance improvement is claimed by this rewrite.

## Adaptation rationale

| Adaptation | Reason |
| --- | --- |
| Prefer purpose, constraints and completion over mandatory recipes | Give Astra freedom to select an approach while preserving correctness requirements. |
| Split conditional reference material, not sequential steps hidden behind context resets | Load guidance when relevant without forcing orchestration merely to reduce context. |
| Remove adjective escalation and speculative negation advice | Use concrete requirements rather than unsupported prompting heuristics. |
| Preserve technical criteria instead of compressing them into vague keywords | Optimize useful context, not minimum line count. |
| Put Codex invocation mechanics in references/codex-skill-mechanics.md | Harness-specific details should be loaded only when applicable. |
| Preserve safety, compatibility and intentional orchestration | These encode requirements, not compensation for older models. |

The rationale follows [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).
These are editorial choices, not measured performance claims.

## Update review

UPSTREAM.json stores the reviewed Writing for Agents files and license hashes.
The daily Review adapted skill upstreams workflow opens or updates a GitHub issue
on additions, changes or removals. It leaves our version and baseline untouched.
Review each relevant upstream change against the rationale above; port or skip it
explicitly, then update the reviewed commit/hashes in the approved change.
Closing an issue without updating the baseline does not acknowledge that update.
