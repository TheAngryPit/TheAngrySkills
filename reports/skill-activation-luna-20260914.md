# Skill activation fixture — Luna bounded proof

Date: 2026-09-14

## Scope

This report covers only the disposable Git project at
`/private/tmp/skill-activation-luna.0xFjUr`. The project contains two
synthetic skills under `.agents/skills/` and an exact byte copy of the project
`model-capability-router` skill. No global skill, config, Doctor, PR, Sol
checkout, or user-owned Codex task was changed.

## Independent fixture proof

- Project-local discovery root: `.agents/skills/`.
- Catalogue entries: `fixture-explicit-only`, `fixture-implicit-eligible`, and
  `model-capability-router`.
- `fixture-explicit-only` has `policy.allow_implicit_invocation: false`.
- `fixture-implicit-eligible` has the default implicit policy.
- `model-capability-router/SKILL.md` matches the Luna source byte-for-byte:
  `e2867ae60d8e2234681056543888c5b4ae2f9249158cf6bc1ecfa9982d1e33cb`.
- The fixture classifier keeps catalogue discovery separate from selected full
  `SKILL.md` reads; the name-only router check remains before a full read.

## Runtime boundary

The runtime probe used `codex-cli 0.154.0` with `--ephemeral`,
`--ignore-user-config`, `--ignore-rules`, `--sandbox read-only`, `--json`, an
isolated temporary home/config, and `-C` pointing at the fixture. The first
attempt was blocked by the sandbox's DNS failure. The approved network retry
reached the API but returned:

`401 Unauthorized: Missing bearer or basic authentication`

The explicit-only, unmentioned, implicit-trigger, and delegated-agent cases
therefore have no live model result. They remain `NOT_OBSERVED`; no activation
marker is claimed. In particular, a local catalogue hit is not evidence that
an agent or delegated agent read the full `SKILL.md`.

## Commands and verification

```text
python3 -m unittest -v tests.test_skill_activation_fixture
python3 scripts/skill_activation_fixture.py /private/tmp/skill-activation-luna.0xFjUr --full-read fixture-explicit-only
```

No push, merge, global installation, or external publication was performed.
