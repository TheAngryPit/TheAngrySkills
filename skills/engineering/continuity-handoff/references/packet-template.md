---
type: Continuity Handoff
title: "<human task title>: compact continuation"
description: Continue accepted work without inheriting the legacy transcript.
tags: [continuity, handoff]
status: active
generated:
  by: "<agent or operator>"
  at: "<ISO-8601 timestamp>"
sources:
  - id: source-task
    resource: "urn:codex:thread:<thread-id>"
    title: "<human source title>"
  - id: decision-anchor
    resource: "<commit, issue, URL, or document title>"
    title: "<human anchor title>"
continuity:
  schema_version: "0.1"
  source_mode: legacy-task
  destination_mode: fresh-native-task
  transcript_inherited: false
  acknowledgement_required: true
  historical_recall: bounded-read-only-question-driven
---

# Mission

<One paragraph describing the current outcome, not the whole project history.>

# Current Goal And Resume Checkpoint

- Active goal: <goal or explicitly none>.
- Completed checkpoint: <last proven checkpoint>.
- Resume point: <one exact next action>.
- Authorization boundary: <what this packet does and does not authorize>.

# Orientation

- Product/project: <name>.
- Repository: <portable owner/name or verified local checkout>.
- Branch: `<branch>`.
- HEAD: `<commit>`.
- Source task: **<title>** (`<id>`), <profile>, <device>, <project/CWD>.
- This is semantic continuation, not transcript migration.

# Accepted Decisions

- <Decision and rationale.>

# Failures And Do Not Repeat

- <Rejected action, measured consequence, and required invariant.>

# Ledger Snapshot And Canonical References

- <Reference authoritative files, commits, issues, tests, and ledgers.>
- <Include only the current checkpoint and strongest proof.>
- Live repository and runtime truth override stale references.

# Protected State

- <Exact source task and unrelated user-owned state that must remain untouched.>

# Historical Recall Handle

```yaml
title: "<human source title>"
thread_id: "<source task id>"
profile: "<profile>"
device: "<device>"
project: "<project>"
cwd: "<source cwd>"
codex_home: "<source CODEX_HOME>"
rollout_path: "<verified rollout path>"
access_policy: "bounded-read-only-question-driven"
```

# Known Historical Gaps

- <Facts deliberately omitted or not verified.>
- Absence from this packet means unknown, not false.

# Independent Review Before Implementation

Read repo instructions and verify branch, HEAD, dirty state, cited canon, and
the smallest relevant implementation surface. Stop on contradiction.

# Validation

- <Exact proof required before continuation is accepted.>

# Suggested Skills

- <Only capabilities relevant to the next bounded action.>

# Required Acknowledgement

Reply first with:

1. mission and resume checkpoint;
2. accepted versus unverified facts;
3. exact next read-only action;
4. protected state;
5. confirmation that implementation has not started.
