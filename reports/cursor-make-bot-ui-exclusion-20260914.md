# Cursor make-bot-ui scope decision

Date: 2026-09-14. Vítor explicitly excluded `cursor-make-bot-ui` from the
Codex mirror. This supersedes the earlier plan to close its webhook workflow.
No further bot UI adapter, queue, webhook, secret, Tailnet, or install work is
authorized by that plan.

The manifest retains the pinned upstream path, file hash, license evidence,
security finding, and historical local adapter evidence. The new
`excluded_from_mirror` flag prevents publication and candidate-preview
rendering, including after a source refresh. It does not classify the source
as one of the three upstream-dormant Benny automations.

Current accounting: 91 physical upstream sources, including 88 active slash
skills and three Benny automation sources; 71 Codex mirrors published, 16
active candidates held pending Vítor's scope choice, and one active source
intentionally excluded. The other 16 are paused for a selection decision,
not permanently cancelled. No global installation or external operation was
performed for this exclusion.
