# OpenClaw core Codex adaptations

Twelve selected OpenClaw core workflows adapted for Codex, distinct from the nine shared `openclaw/agent-skills` prefix-only mirrors. Each package preserves its source identity, MIT notice, supporting resources and adaptation record. This is an explicitly selected adaptation pack, not a blanket mirror of upstream maintainer workflows.

## Install

Use full-depth discovery for the nested pack and select only desired names. Example:

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --full-depth -g -a codex -y -s openclaw-diagnose-gateway
```

`manifest.json` lists the exact twelve names and invocation policies. Diagnostics and debugger workflows use available CLIs; repository workflows resolve the selected OpenClaw checkout. Update and connection repair require explicit Codex invocation and preserve the actual target owner's authority.

## Sources and scope

The public `sources/openclaw-core` archive retains the original selected upstream directories at the recorded commit, with native entrypoints renamed `SKILL.source.md` for non-discovery. Installable references retain upstream resources; two executable recipe examples are replaced with scoped guidance while originals stay in provenance. Refactor-docs additionally contains technical-documentation as reference resources, not a thirteenth installable skill.

No Gateway, provider, account, credential, live service or model is installed/configured by this pack. Native Codex tools and current project permissions remain the execution authority. Package/security/discovery proof is distinct from live Gateway proof and fresh model routing. No automatic refresh is enabled; future updates must preserve the adaptation contract and provenance.
