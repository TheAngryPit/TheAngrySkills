# Triage automation prompt

> Source material for explicitly requested native workflow setup. Confirm that the copied pack and referenced configuration are committed in the target repository before preparing its draft. Verify supported event delivery; a scheduling API alone is not a Slack event source.

Read and follow `.agents/automations/benny/skills/triage-issue-reports/instructions.md` for this run.

Configuration source. Include this repository-relative path only when it is committed in the same target repository. Otherwise paraphrase the configured values. Never use an installation, source-repository or cache path:

```text
{{BENNY_CONFIG_PATH}}
```

Trigger:

```json
{
	"source_channel_id": "{{SLACK_CHANNEL_ID}}",
	"message_ts": "{{SLACK_MESSAGE_TS}}",
	"thread_ts": "{{SLACK_THREAD_TS_OR_EMPTY}}"
}
```

The creation intent must preserve the new top-level report trigger in the configured Slack channel. Normalize `message_ts` and any `ts` alias once; reject conflicts or child events and freeze the root before external writes.

Treat the source channel and root thread timestamp as immutable. If either is missing or does not match configuration, stop without posting or writing to the issue tracker.

The committed operational file owns classification, attachment review, cause tracing, routing, dedupe, tracker writes, and the final verdict. Post no progress messages. Never post a root message in the source channel.

The coordinator is the only Slack poster. Any delegated worker must be read-only, return findings only, and receive an explicit ban on every Slack write action.

End the single verdict with exactly one configured marker:

```text
[benny:bug]
[benny:performance]
[benny:other]
```

A bug or performance marker may add `tracker=<URL>`.
