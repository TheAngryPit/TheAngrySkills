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
