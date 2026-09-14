# `cursor-make-bot-ui` local adapter proof

Date: 2026-09-14. Scope: the nine-skill pstack closure batch.

The source requires a browser UI, a server-owned sender key, a POST to a
webhook, a wake path, and optional Tailscale exposure. The safe native slice in
this branch is deliberately local and offline. It is implemented in
`scripts/cursor_bot_ui_adapters.py` and bundled through the held overlay. It
does not contact a webhook, read a credential, install Tailscale, or run sudo.

## Observed local contract

`run_bot_ui_fixture` returned `FIXTURE_ONLY`. The successful mock request had
one attempt, HTTP 200, JSON content type, `Authorization` and
`X-Automation-Key` headers, and an eight-second timeout. Evidence redacted both
key headers. The request body contained only the fixture payload.

The timeout branch returned `FAILED`, wrote one payload-only JSONL record, and
did not retry. The non-200 branch has the same one-attempt behavior. A list
payload was rejected before dispatch, and a remote HTTPS webhook URL was
rejected before dispatch. The mock received exactly one successful request.

Focused proof passed with five tests in
`tests/test_cursor_bot_ui_adapters.py`. No network, secret, Tailscale state,
privileged command, routine creation, wake turn, or browser surface was
observed. Those source subflows remain conditional and are not represented as
available native behavior.

## Decision

Keep `cursor-make-bot-ui` unpublished under `security_hold_quarantine`.
The local adapter closes the safe request-boundary slice without weakening the
source scanner finding. External webhook credentials, routine wake handling,
and Tailnet exposure require separate authorization and proof.
