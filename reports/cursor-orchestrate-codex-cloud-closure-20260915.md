# Cursor orchestrate: native Codex Cloud closure

Date: 2026-09-15  
Scope: read-only capability discovery, bounded adapter implementation, deterministic mirror generation, and local verification.

## Documented native surface

Official OpenAI developer-command documentation defines these Codex Cloud CLI operations:

- `codex cloud exec --env ENV_ID [QUERY]`, with one to four attempts and an optional branch;
- `codex cloud list --json`, including task identity, URL, status, environment identity, summary, and attempt count;
- `codex cloud status TASK_ID`;
- `codex cloud diff TASK_ID`;
- `codex cloud apply TASK_ID --attempt N`.

Sources:

- <https://learn.chatgpt.com/docs/developer-commands?surface=cli>
- <https://learn.chatgpt.com/docs/codex/cli>

The documented CLI surface has no cancellation command. A bounded stop therefore means dispatching no further dependency-ready tasks while retaining confirmed task identities and readback. Applying a diff remains a separate mutation after inspection.

## Local readback

The installed binary reported `codex-cli 0.154.0`. Its `codex cloud --help` output exposed `exec`, `status`, `list`, `diff`, and `apply`.

Read-only command:

```text
codex cloud list --json --limit 20
```

Observed result: exit code 0 and zero tasks. The interactive environment selector showed only `All Environments (Global)` and no concrete environment. That selector is not an executable `ENV_ID`, so no cloud task was created.

## Native adaptation

The published mirror keeps explicit `/orchestrate <goal>` invocation and replaces the Cursor runtime with a coordinator-owned dependency graph:

1. validate one planner, bounded children, dependency existence, and acyclicity;
2. compute only dependency-ready task IDs;
3. build shell-free `codex cloud exec` argument tuples after out-of-band creation authorization and exact environment/branch selection;
4. normalize documented list readback and derive status/diff commands;
5. reconcile structured handoffs with artifact identity for passing work;
6. build an apply command only after separate authorization.

This preserves planner, worker, verifier, dependency, drain, and handoff intent. It does not claim access to Cursor's private internal agent tree.

## Security boundary

All pinned upstream `blocked_malicious` findings remain recorded in the overlay. The rendered bundle excludes upstream prompts, references, schemas, TypeScript/Bun scripts, dependency manifests, measurement shell execution, Slack adapters, and credential paths. It contains only the rewritten native skill, the reviewed Python adapter, provenance, and license.

The earlier provisional ChatGPT Work client ID belongs to a separate experiment with unknown final state. This Codex Cloud adaptation neither retries nor resolves that request.

## Proof and residual gap

Focused tests cover graph validation, ready batches, authorization gates, exact argv construction, unsafe identifier and private-marker rejection, list parsing, apply separation, handoff aggregation, cycles, missing dependencies, and child bounds.

Live Codex Cloud dispatch, cloud runtime handoffs, and diff readback remain unproved because this host currently exposes no concrete `ENV_ID`. Publication is conditional on that explicit runtime prerequisite and does not claim live execution.
