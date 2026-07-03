# Founder GTM Pack

This package preserves the locally installed `founder-gtm` skills that were
historically sourced from `cursor/plugins`.

The upstream path recorded by the local inventory was:

```text
cursor/plugins :: founder-gtm/skills/<skill-name>/SKILL.md
```

The current `cursor/plugins` mirror no longer contains `founder-gtm`, so this is
not treated as a live mirror. It is a curated local preservation pack inside the
TheAngrySkills Workbench.

## Included Skills

- `gtm-setup`
- `gtm-sales-pack`
- `gtm-cold-email`
- `gtm-linkedin-outreach`
- `gtm-x-outreach`
- `gtm-warm-intro`
- `gtm-get-better`
- `gtm-design-play`
- `gtm-playbook`

## Known Gap

Several preserved skills reference `gtm-find-prospects`, but no local installed
copy of that skill was found under `~/.agents/skills` or `~/.codex/skills`, and
the current Cursor mirror does not contain the historical `founder-gtm` source.
Treat prospect generation as missing until the source is recovered or a new
TheAngrySkills-native replacement is explicitly designed.

## Operating Notes

- Keep the copied `SKILL.md` files source-faithful unless a later review pass
  explicitly accepts a fork.
- Treat outbound, email, LinkedIn, X/Twitter, Gmail, credential, and API actions
  as human-review-required.
- Do not install this pack globally by default. Review, select, and install only
  after the operator confirms the intended GTM workflow.
- If an upstream source is recovered later, compare before replacing this pack.
