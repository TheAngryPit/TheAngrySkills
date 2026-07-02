# Thread Metadata Bloat

Codex Desktop can become slow when display metadata stores prompt-sized content
instead of compact titles/previews.

This document describes the existing bloat signal and compatibility context.
The accepted next title-repair direction is narrower and is specified in:

- `thread-title-repair-spec.md`
- `thread-title-repair-prd.md`

Legacy combined repair context:

- `--apply --repair-thread-metadata-bloat` and `--repair-thread-metadata-only`
  are the existing compatibility path
- that legacy path may compact `threads.first_user_message` for oversized
  automatic metadata
- title-only repair is separate and must not reuse this path

## Legacy Compatibility Path

The commands above are the current compatibility behavior.

- `--repair-thread-metadata-only` is the legacy metadata repair entrypoint
- `--apply --repair-thread-metadata-bloat` also runs the normal apply pipeline
- legacy repair may compact `threads.first_user_message` for oversized
  automatic metadata when the compatibility path is invoked
- legacy repair does not change the title-only contract; it remains a
  compatibility path only

Legacy path rules:

- preserve manual titles by default
- replace `threads.title` only when it equals oversized `first_user_message`
- only replace that automatic prompt/title bloat when `session_index.jsonl`
  already contains a short, safe, operator-facing name for the same thread
- if no safe `session_index.jsonl` name exists, preserve the oversized title and
  report `thread_metadata_title_repair_unavailable`
- do not rewrite `preview`, transcripts, or `session_index.jsonl`
- preserve the rollout transcript
- write a private repair manifest
- write a restore helper

## Title-Only Repair

This section documents the separate title-only repair workflow. It does not
describe the legacy combined metadata command.

Implemented command shape:

```bash
python3 scripts/keep_codex_fast.py --repair-thread-titles-dry-run --codex-home <codex-home>
python3 scripts/keep_codex_fast.py --repair-thread-titles-apply --confirm-thread-title-repair APPLY_THREAD_TITLE_REPAIR --codex-home <codex-home>
```

For title-only repair:

- `dry-run` is read-only
- `apply` is explicit and backup-first
- manual titles are preserved
- `threads.title` is the only mutable thread field in scope
- `threads.first_user_message`, `threads.preview`, transcripts, and
  `session_index.jsonl` are not rewritten
- replacements come only from an existing safe short
  `session_index.jsonl.thread_name` for the same thread
- candidates without safe names are reported as `needs_human`
- subagent/system-owned threads are excluded from automatic repair

Relevant fields:

- `threads.title`
- `threads.first_user_message`

Report mode should count:

- active thread rows
- total title characters
- total preview characters
- max title length
- max preview length
- title values over the configured title limit
- title values that duplicate `first_user_message`
- oversized titles that differ from `first_user_message` and must be preserved
- preview values over the configured preview limit
- previews over 10k characters

Normal apply mode only reports candidates. It must not shorten title/preview
metadata.

Title-only repair is a separate operation. The first command is always the
read-only classifier `--repair-thread-titles-dry-run`; apply uses
`--repair-thread-titles-apply` with the explicit confirmation phrase and must
not be confused with the legacy compatibility entrypoint above.

Title-only repair policy:

- backup first
- require Codex not to be writing state
- preserve manual thread names by default
- do not rewrite `first_user_message`, `preview`, transcripts, or
  `session_index.jsonl` for the title-repair slice
- never append or rewrite `session_index.jsonl`; it may contain operator-owned
  manual thread names

Do not describe metadata repair as deleting chat history. It is display metadata
repair, not transcript deletion.

Manual-name preservation rule:

- if `title` is different from `first_user_message`, treat it as operator-owned
  and do not rewrite it
- if `title` equals `first_user_message` and is oversized, treat it as automatic
  prompt/title bloat, but only replace it with a safe existing
  `session_index.jsonl` name for that exact thread
- never synthesize a replacement name from prompt text, cwd, transcript content,
  or model summaries
- title repair must not change transcript JSONL files
- compacting `title` must not create replacement names in `session_index.jsonl`

Compatibility note: the legacy command remains available for compatibility and
may compact `first_user_message`. Do not expand or rely on legacy
first-message compaction for title-only repair without updating the PRD, spec,
and tests first.
