---
name: cursor-orchestrate
description: "Use only when the user explicitly types `/orchestrate <goal>` to coordinate a bounded dependency graph through native Codex Cloud tasks; requires an exact configured environment and authorization for task creation."
---

# Native Codex Cloud orchestration

Use this mirror only when the user explicitly invokes `/orchestrate <goal>`. Preserve the goal, decompose it into a bounded coordinator-owned dependency graph, and use native Codex Cloud tasks when an exact environment is configured and creation is authorized.

## Workflow

1. Validate the goal and task graph with `prepare_local_plan`. Keep exactly one planner, no cycles or unknown dependencies, and at most eight children.
2. Ask the native CLI for available tasks and environments using read-only `codex cloud list --json` or the interactive environment selector. An `All Environments` selector is not a usable environment ID.
3. When the operator has authorized cloud task creation and selected the exact environment and branch, call `build_codex_cloud_dispatch_batch`. It returns shell-free argument tuples for `codex cloud exec --env ENV_ID --attempts 1 --branch BRANCH QUERY`; the adapter never executes them.
4. Submit only dependency-ready tasks. Drain them with documented `codex cloud list --json`, `codex cloud status TASK_ID`, and `codex cloud diff TASK_ID`, then validate structured handoffs and artifact identities before marking dependencies complete.
5. Applying a cloud diff is a separate mutation. Build `codex cloud apply TASK_ID --attempt ATTEMPT` only after separate authorization.
6. The native CLI documents no cancellation command. To stop a run, dispatch no further tasks, preserve the last confirmed task identities and status, and report cancellation as unavailable.

## Boundaries

Codex Cloud coordination preserves the requested planner/worker/verifier intent without reproducing Cursor's private internal agent tree. Keep the pinned upstream `blocked_malicious` findings as provenance. Do not publish or execute the upstream TypeScript/Bun runtime, dependency manifest, measurement shell boundary, Slack adapter, or credential paths. Do not treat the earlier provisional ChatGPT Work client ID as a Codex Cloud task or create a duplicate Work task. If there is no concrete `ENV_ID`, return `ENVIRONMENT_REQUIRED` with the validated plan and do not dispatch.
