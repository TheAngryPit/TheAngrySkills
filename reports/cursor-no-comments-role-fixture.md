# `cursor-no-comments` bounded role fixture

The pinned `pstack/agents/comment-sicko.md` is bundled by the mirror preview as `cursor-no-comments/references/comment-sicko-agent.md`. An existing native Codex reviewer was assigned only `/private/tmp/codex-comment-sicko-fixture-20260913/src/total.js` and instructed to apply that role. The input contained a legal SPDX header and a redundant function-body comment.

Observed output: the reviewer deleted exactly one redundant comment, retained `// SPDX-License-Identifier: MIT`, changed no application code, reported no `MUST KILL` flag, and reported no restored comments. The final file still has `total(values)` returning the same `reduce()` expression. The coordinator read the final file and ran `node --check /private/tmp/codex-comment-sicko-fixture-20260913/src/total.js` successfully.

This proves one bounded native role execution and the legal-header exception. It does not prove automatic skill trigger, Codex model selection, handling of ambiguous comments, rerun-on-rejection, architect integration, optional constraint encoding, or installation of a named agent profile.
