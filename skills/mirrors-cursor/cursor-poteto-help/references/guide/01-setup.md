> Native Codex guide adapted from the pinned pstack source. Skills, named profiles and scheduling capabilities must be verified on the actual host. Source publication is not installation. Upstream artwork is retained as original illustration.

# Set up pstack

This page covers native skill availability, model roles and the first task. Installation remains a separate operator action.

## Verify native availability

Use the operator's approved source and native Codex skill discovery. Installation is a separate operator action; this guide does not install the Cursor plugin. Verify the selected skills and named agent profiles in a fresh session before claiming availability.

## Pick your models

Run:

```text
$cursor-setup-pstack
```

[`$cursor-setup-pstack`](../../../cursor-setup-pstack/SKILL.md) detects the models you have access to, asks for a reasoning budget, shows you each role (code delegates, judgment, the review panels), and asks what you want. Answer the questions. The native adaptation follows `model-capability-router` and available session model/effort metadata; no Cursor rule is written and configured defaults are not runtime proof.

Use the standing `model-capability-router` and the actual native channel for model and effort selection. Upstream Cursor tier labels are not Codex defaults. Configured roles do not prove the selected runtime, and token savings require measured evidence.

Choose or revise native roles only within the requested setup scope. Do not write or delete Cursor rules, rewrite live Codex defaults implicitly or assume a source update changed an active session.

When supported by the native call, omitted model overrides inherit the parent selection. Verify supported models, effort, context inheritance and concurrency on that channel. Preserve independent reviewer roles without inventing Cursor model slugs.

## Accept the verification offer, or don't

At the end of setup, `$cursor-setup-pstack` looks for a way to prove app behavior in your project, either a `verify-*` skill or an existing harness. If it finds neither, it offers once to generate one with [`$cursor-create-verification-skill`](../../../cursor-create-verification-skill/SKILL.md).

Say yes and it writes the authorized source-controlled `verify-<app>/` directory, with installation and native discovery verified separately, a project-local skill that teaches agents to drive your app the way a user does. It proves the skill works once before handing it over. Say no and setup moves on. You can run `$cursor-create-verification-skill` yourself any time. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers it in depth.

If you're new to pstack, say yes. An agent that can check its own work keeps going until the check passes. An agent that can't hands every result back to you to check by hand. Of everything in this guide, the verification skill pays off the most.

Verify installed skill and named-profile discovery in a fresh native session. This guide does not establish installation or a runtime switch.

## Keep the cost in check

pstack spends extra tokens on subagents and review panels. That's the price of the rigor. To spend fewer:

- Rerun `$cursor-setup-pstack` and pick a smaller reasoning budget or cheaper models. A strong model in the main chat with cheaper, faster models in the code roles is a good split.
- Set a role to `auto` or `inherit-parent` so it runs on the chat's own model.
- Shorten a panel list. Each entry runs one subagent.
- Save `$cursor-poteto-mode` for work that needs rigor. A small, obvious edit doesn't.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
$cursor-poteto-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the todo list. Its first items are the matched playbook's steps copied in, the Feature playbook for this prompt. If `$cursor-poteto-mode` skips a step, the step stays in the list with `skip: <reason>`, so you can see what it chose not to do.

Continue the explicitly selected workflow through this task and its follow-ups. Codex does not inherit Cursor Custom Modes, Option+Enter/Alt+Enter or sticky per-turn loading; select the skill again for a new task when needed.

Next: [Route work through `$cursor-poteto-mode`](./02-poteto-mode.md).
