---
name: continuity-handoff
description: Create a compact fresh-task continuity packet that preserves goals, decisions, proof, protected state, and a bounded read-only handle to legacy Codex history. Use when replacing a bloated or legacy task without forking its transcript, handing work to a fresh task, or retrieving one missing historical fact without loading the full conversation.
---

# Continuity Handoff

Continue work in a fresh task without duplicating the legacy transcript.

The default path is fast and packet-only. Historical recall is exceptional,
question-driven, read-only, and bounded.

## Modes

- **Create**: produce a continuity packet for a fresh task.
- **Acknowledge**: verify a received packet before implementation.
- **Recall**: recover one missing historical fact from the legacy Codex rollout.

Do not use native task fork as a desbloat mechanism unless a fresh measurement
proves that the destination does not inherit material transcript weight.

## Create

1. Read the current repo instructions and current task state.
2. Identify the source task by human title, task ID, profile, device, project,
   CWD, and `CODEX_HOME`. Never identify it by ID alone.
3. Capture the current goal or explicitly state that no active goal exists.
4. Reference existing commits, specs, ledgers, issues, and proof artefacts. Do
   not paste their full contents.
5. Record accepted decisions, rejected directions with reasons, protected
   state, open gates, known historical gaps, and the exact resume point.
6. Resolve the source `rollout_path` from a quiescent `state_5.sqlite` opened
   with immutable read-only semantics when local access is authorized. If a
   `-wal` or `-shm` sidecar exists, close Codex and retry. Never include
   credentials or secret-bearing files.
7. Fill [the packet template](references/packet-template.md). Save it in the OS
   temporary directory unless the operator requests a durable project file.
8. If the operator explicitly asks to create a new task, deliver the packet to
   a fresh native task. Do not fork the source task.
9. Require acknowledgement before implementation.

The packet must remain compact. A large transcript summary is a failed handoff.

## Acknowledge

Before changing anything, state:

1. the mission and resume checkpoint;
2. accepted facts versus unverified claims;
3. the next read-only action;
4. protected state that will remain untouched;
5. whether implementation has started.

Live repo and runtime truth outrank the packet. Stop and report contradictions.

## Recall

Use recall only when one explicit question cannot be answered by the packet,
current repo, referenced canon, or current runtime evidence.

1. State the unanswered question.
2. Derive a narrow literal search term and optional ISO date.
3. Run the bundled reader:

```bash
node scripts/recall-codex-history.mjs \
  --codex-home <source-code-home> \
  --thread-id <source-task-id> \
  --query <literal-term> \
  --date YYYY-MM-DD \
  --match-role user \
  --before 1 \
  --after 5 \
  --max-matches 3
```

Run the script from this skill directory. It refuses non-quiescent SQLite,
opens the database with `mode=ro&immutable=1`, validates the rollout identity,
streams JSONL, sanitizes every returned message, and caps output. It never
writes source state.

Use `--match-role user` for an operator report and `--match-role assistant` for
an earlier agent conclusion. Internal system/developer messages are never
returned. If no narrow literal exists, ask the operator for a better locator
rather than loading or summarizing the full transcript. A second query is
allowed only when the first query and its failure are reported.

Return a compact evidence capsule:

- question;
- finding;
- task title, ID, profile, device, and project;
- evidence line/timestamp locator;
- retrieval scope;
- confidence;
- unresolved gap;
- confirmation that no state changed.

Do not paste raw tool output into the destination when the capsule is enough.

## Safety

- Source and destination tasks are immutable during packet generation and recall.
- Never copy `auth.json`, credentials, cookies, passwords, tokens, Keychain
  material, or unrelated conversation.
- Never query another profile or device by guessing a nearby path.
- Never rewrite SQLite, JSONL, titles, indexes, goals, or project bindings.
- Never treat packet absence as proof that an event did not happen.
- Never claim historical completeness from a compact packet.
- Any destructive cleanup, archive, pruning, or source deletion is a separate
  operator decision after the successor is validated.

## Validation

A handoff passes only when:

- the destination has a fresh native identity and no inherited transcript;
- mission, decisions, negative knowledge, anchors, and protected state survive;
- repository contradictions stop execution;
- unsupported historical claims are refused;
- recall, when needed, is bounded and evidence-located;
- source and repo state remain unchanged;
- destination persisted size stays materially below the source.
