# openclaw/agent-skills Skill Mirror

Mirrored skill: behavior-validator
Published skill: openclaw-behavior-validator
Source: https://github.com/openclaw/agent-skills.git
Source path: skills/behavior-validator
Branch: main
Commit: 19ebc3c689a217a85b1ca19dda8c4d0857922247

This skill is vendored from openclaw/agent-skills with a `openclaw-` prefix to avoid
global skill-name collisions. The source-controlled mirror inventory stores
`SKILL.md` as `SKILL.mirror.md` so native Skills CLI discovery does not
treat the full mirror cache as the installable stack. The mirrored
frontmatter `name` field, YAML-safe bounded `description`,
and local `mirrors/mirrors-openclaw/<name>` path examples are intentionally rewritten;
other file contents are copied from upstream.
