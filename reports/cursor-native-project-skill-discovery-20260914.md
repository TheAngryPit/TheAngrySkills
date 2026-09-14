# Project-local Codex skill discovery probe

Date: 2026-09-14. The [Codex skill contract](https://learn.chatgpt.com/docs/build-skills)
documents project-local `.agents/skills`, explicit `$name` invocation, and
`agents/openai.yaml` with `allow_implicit_invocation: false` for an explicit-only
skill. The [Cursor skill contract](https://prod.cursor.com/docs/skills) gives
`disable-model-invocation: true` the corresponding explicit-only intent.

An authorized disposable Codex project worktree started from a commit already
containing three project-local skills: `fixture-explicit-only`,
`fixture-implicit-eligible`, and `model-capability-router`. The isolated task's
session-start `Available skills` catalog contained the implicit-eligible skill
and router from that project, but did not list the explicit-only skill. The
three directories and metadata were present on disk. Thus the task observed
project-local catalog discovery for two skills; it did not observe why the
explicit-only skill was omitted from that catalog.

A follow-up message containing the literal `$fixture-explicit-only` supplied no
native skill-selection token or resolution trace. The task did not read that
skill's body or produce its private marker. Its result is `NOT_OBSERVED`, not a
failure or success of explicit invocation. A separate CLI attempt with an
isolated home reached the API but returned `401 Unauthorized` before model
output; the CLI and desktop app are distinct runtime surfaces. The native app
skill picker could not be automated because the available computer-use tool
disallows control of the Codex app. No home, credential, global installation,
main checkout, or project trust setting was changed.

The generated `agents/openai.yaml` policy in this PR is source- and
documentation-grounded. This probe establishes a narrower runtime fact:
project-local implicit-eligible skills and the router appeared in one fresh
task catalog. Explicit-only selection, full `SKILL.md` loading, implicit
triggering, and delegated router use remain unobserved.
