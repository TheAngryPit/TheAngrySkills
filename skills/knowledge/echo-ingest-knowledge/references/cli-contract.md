# CLI Contract

Use the owning project's `echo_ingest_knowledge.py` CLI when available.

Expected responsibilities:

- create raw artifacts;
- create manifests;
- normalize Markdown;
- create reviewable final notes;
- import or review pattern catalogs;
- prepare strategy-run prompt packets;
- capture status without silently calling model providers.

If a project lacks the CLI or the command is unavailable, do not invent a
replacement. Create a clear blocker and provide the exact missing command or
artifact.

LLM execution should use Codex explicitly: current session, approved subagent,
or an explicitly configured Codex CLI run. Do not silently fall back to an
external provider.
