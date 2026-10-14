# OpenClaw core Codex adaptations

Twelve selected OpenClaw core workflows adapted for Codex, distinct from the nine shared `openclaw/agent-skills` prefix-only mirrors. Each package preserves its source identity, MIT notice, supporting resources and adaptation record. This is an explicitly selected adaptation pack, not a blanket mirror of upstream maintainer workflows.

## Install

Use full-depth discovery for the nested pack and select only desired names. Example:

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --full-depth -g -a codex -y -s openclaw-diagnose-gateway
```

## Selective installation and companion skills

The Skills CLI installs only the names explicitly selected with `-s`; it does not resolve this pack's `manifest.json`. Required companions must be selected in the same install or already be present.

| Requested workflow | Required additional selections |
|---|---|
| openclaw-debugging | openclaw-testing |
| openclaw-test-performance | openclaw-testing |
| openclaw-test-heap-leaks | openclaw-test-performance, openclaw-testing |
| openclaw-release-plugin-testing | openclaw-testing |

The other eight workflows have no mandatory installed companion from this pack. Their checkout-owned prerequisites and on-demand upstream source references still apply. Documentation-refactoring includes its documentation dependency and license as packaged resources.

For a complete heap-investigation install:

```bash
npx skills add https://github.com/TheAngryPit/TheAngrySkills.git --full-depth -g -a codex -y -s openclaw-test-heap-leaks openclaw-test-performance openclaw-testing
```

Conditional branches also need the relevant companion: test-performance uses openclaw-test-heap-leaks for memory investigations and openclaw-release-plugin-testing for artifact-sensitive plugin proof. A selected remote-proof route uses the separate shared openclaw-crabbox package; include it only when that route is requested and authorized. These selections do not install runtime CLIs, cloud profiles or credentials.

To install the complete twelve-skill pack, list all twelve names from the manifest explicitly; this also satisfies every in-pack required companion. The manifest records required and conditional dependencies for review, not as a claim of automatic installation.

`manifest.json` lists the exact twelve names and invocation policies. Diagnostics and debugger workflows use available CLIs; repository workflows resolve the selected OpenClaw checkout. Update and connection repair require explicit Codex invocation and preserve the actual target owner's authority.

## Sources and scope

The public `sources/openclaw-core` archive retains the original selected upstream directories at the recorded commit, with native entrypoints renamed `SKILL.source.md` for non-discovery. Installable references retain upstream resources; two executable recipe examples are replaced with scoped guidance while originals stay in provenance. Refactor-docs additionally contains technical-documentation as reference resources, not a thirteenth installable skill.

No Gateway, provider, account, credential, live service or model is installed/configured by this pack. Native Codex tools and current project permissions remain the execution authority. Package/security/discovery proof is distinct from live Gateway proof and fresh model routing. No automatic refresh is enabled; future updates must preserve the adaptation contract and provenance.
