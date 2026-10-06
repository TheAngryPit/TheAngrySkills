# Benny for Codex

This complete native pack preserves the two upstream workflows: triage a Slack report, then reproduce/verify/fix a trusted verdict. Read [FOR_AGENTS.md](FOR_AGENTS.md) and [setup](skills/setup-benny/instructions.md) directly. The catalog packages are explicit-only distribution; the committed automation files are direct workflow instructions.

Project setup, installation, event delivery, credentials and activation are separate. Merge into a requested target at `.agents/automations/benny/`, preserve local changes, keep user config outside that directory, and verify shared native dependencies in a fresh session. Event-driven activation remains incomplete without an authorized Slack event source; never silently schedule polling. No live workflow is activated by reading this pack.
