# Sensei compatibility policy

TheAngryPit uses `skill-catalog-curator` as the operational source of truth for
skill catalog hygiene.

Sensei is useful as an external comparator, not as the authority.

## What to adopt

- Strong `description` fields with clear trigger language.
- `license` for public or shared skills.
- `version` or `metadata.version` for stable published skills and routers.
- Token/budget pressure checks.
- Frontmatter/name/directory consistency checks.
- Optional external score reports before major skillset releases.

## What not to copy blindly

- Do not make Sensei-only fields mandatory for Codex-only private skills.
- Do not add anti-triggers by default in large catalogs; they can contaminate
  routing.
- Do not let external score compliance override real routing tests.
- Do not publish local filesystem paths, installed-skill hashes, timestamps, or
  machine-specific catalog metadata.

## Profiles

- `shared`: default for TheAngryPit team/session workflows.
- `codex`: strict Codex posture.
- `agentskills`: compatibility view for Sensei/agentskills-style publication.

## Monthly check

Once a month, or before a major skillset release:

1. Check whether `@spboyer/sensei` has a newer npm version.
2. Read the upstream changelog or README changes.
3. Decide whether any new checks should become:
   - `shared` rules,
   - `agentskills` rules,
   - optional notes,
   - rejected external-only rules.
4. Update `scripts/audit_skill_frontmatter.py` only when the rule improves our
   real workflow.

Use:

```bash
python3 scripts/check_external_auditors.py
```

This command checks versions only. It does not install Sensei or mutate skills.
