# openclaw/agent-skills Skill Mirror

Mirrored skill: handoff
Published skill: openclaw-handoff
Source: https://github.com/openclaw/agent-skills.git
Source path: skills/handoff
Branch: main
Commit: fbc765e208061abafe8cefa31f99a179201ada67

This skill is vendored from openclaw/agent-skills with a `openclaw-` prefix to avoid
global skill-name collisions. The source-controlled mirror inventory stores
`SKILL.md` as `SKILL.mirror.md` so native Skills CLI discovery does not
treat the full mirror cache as the installable stack. The mirrored
frontmatter `name` field, YAML-safe bounded `description`,
and local `mirrors/mirrors-openclaw/<name>` path examples are intentionally rewritten;
other file contents are copied from upstream.
