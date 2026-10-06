# Reproduce automation prompt

> Source material for explicitly requested native workflow setup. Confirm that the copied pack and referenced configuration are committed in the target repository before preparing its draft. Verify supported event delivery; a scheduling API alone is not a Slack event source.

Read and follow `.agents/automations/benny/skills/reproduce-and-fix-issues/instructions.md` for this run.

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

The creation intent must preserve the new top-level report trigger in the configured Slack channel. Normalize `message_ts` and any `ts` alias once; reject conflicts or child events and freeze the root before external writes. It should include the configured repository, default branch, issue tracker, control adapter, feature map, and draft pull request capability.

Treat the source channel and root thread timestamp as immutable. If either is missing or does not match configuration, stop without posting.

Wait for a configured triage marker from the configured triage identity in this exact thread. Proceed only for `[benny:bug]` or `[benny:performance]`.

Require the configured control-adapter skill before attempting a repro. Reproduce the exact discriminating symptom twice through the real UI. Verify existing pull requests or commits without authoring over them. Attempt a bounded fix only after a confirmed repro and the operational file's fix gate.

The coordinator is the only Slack poster. Every child prompt must forbid `SendSlackMessage`, `PostToSlack`, `chat.postMessage`, and all other Slack writes. Children return findings only.

Never post a root message in the source channel.
