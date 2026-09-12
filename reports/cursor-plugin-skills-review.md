# Cursor plugin skills mirror — implementation review

Base: TheAngrySkills `main` at `0706a19a4aac46a8db0a01e48dfe9ddc76768ca8`.
Source: `cursor/plugins` at `889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`.
Scope: skills and their support files only; no plugin, global install, push or merge.

The manifest has 91 physical skills and 169 support files. Three Benny skills
are source-dormant. The first build indexes 48 skills: 35 content-intact and
13 nominal adaptations. It retains 40 declared skills as unindexed candidates:
37 functional adaptations awaiting Codex behavior proof, plus `cursor-sdk`,
`make-bot-ui` and `review-plugin-submission` pending contextual security review.
No editorial classification is presented as a tested runtime capability.

The first-pass security scan of all 88 declared candidates reported 77
`safe_to_install`, five `blocked_malicious`, five `needs_human_review` and one
`quarantine`. These are scanner verdicts, not conclusions about upstream
intent. For example, `add-dictation` was flagged for an xAI STT request carrying
`$XAI_API_KEY`; `cursor-sdk` was flagged for credential/MCP reference material;
and `make-bot-ui` contains an actual `curl ... | sudo sh` Tailscale install
instruction. All 11 non-safe candidates are unindexed in this batch. A
per-finding reading and approved adaptation are required before promotion.

Static checks passed for the 48 indexed candidates: 48/48 frontmatter parsed
with no errors (32 A, 16 B from the Codex profile); the security scanner
returned `safe_to_install` for 48/48; relative Markdown links in generated
output resolved; rebuild produced the committed bytes; and comparison with
the pinned upstream checkout reported no new, removed or changed skills or
licenses. Three tests cover reproducibility, local-edit preservation and
source-drift rejection. These checks do not establish live routing or
end-to-end workflow behavior.

The pstack cross-skill links are mapped to published sibling names where those
skills exist in this batch; held siblings point to the pinned upstream source.
The Poteto Mode index's 23 `principle-*` IDs remain in the unindexed source and
will need explicit name mapping when its functional port is reviewed. Benny's
external automation files remain out of distribution, and the exact scope of
its ancestor license is still a promotion gate. The `debug-voice` `../x` path
is an unresolved fixture, not a missing vendored dependency.

The Codex Work Cloud surface has no demonstrated substitute for Cursor
orchestrate's Git isolation, model routing, worker hierarchy, cancellation,
recovery, artifact or PR contract. A cloud proof must be a separate synthetic
task after an authorized dispatch path and a concrete closure mechanism are
established; no cloud task was created in this batch.

Review order: validate this source/overlay format and 48-content batch;
resolve the 11 security findings in context; port and behavior-test the 37
functional skills in bounded lots; only then consider promoting held skills.
The reverse path is removal of this mirror's generated skills, source snapshot,
overlays, report and generator. There is no installed state to roll back.
