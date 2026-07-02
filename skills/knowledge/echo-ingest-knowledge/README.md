# Echo Ingest Knowledge Skill Pack

This pack groups the reusable skills for the echo-ingest-knowledge workflow.

The folder `echo-ingest-knowledge` is a repo organization boundary. The
frontmatter `name` in each nested `SKILL.md` remains the skill routing name.

## Skills

| Skill name | Folder | Purpose |
| --- | --- | --- |
| `echo-ingest-source-intake` | `source-intake/` | Convert source material into raw artifact, manifest, normalized Markdown, and reviewable notes. |
| `echo-ingest-codex-runner` | `codex-runner/` | Execute strategy packets through Codex or prepare explicit Codex execution packets. |
| `echo-ingest-pattern-runner` | `pattern-runner/` | Run selected Fabric-style patterns under activation governance. |
| `echo-ingest-result-review` | `result-review/` | Review generated outputs before vault note promotion. |
| `echo-ingest-workflow-newsletter` | `workflows/newsletter/` | Prepare source material for newsletter/editorial workflows. |
| `echo-ingest-workflow-research` | `workflows/research/` | Prepare evidence-linked research notes and synthesis. |
| `echo-ingest-workflow-prd` | `workflows/prd/` | Prepare PRD, issue, and engineering handoff context. |

## Install Note

This pack uses nested skill folders. Use full-depth discovery when listing or
installing from the repository:

```bash
skills add /path/to/TheAngrySkills --list --full-depth
```

Named installs should target the frontmatter skill names, not the nested folder
names.

## Boundaries

- Do not install globally from this pack until source-repo validation passes.
- Do not edit live installed skill folders directly.
- Keep Fabric patterns in catalog/config data, not as hundreds of skill folders.
- Keep raw source material out of promoted vault notes unless explicitly approved.
