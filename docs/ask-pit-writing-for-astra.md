# AskPit and Writing for Astra

AskPit is the public replacement for the retired ask-pit/ask-theangrypit router
variants in the private Workbench. Its source is Matt Pocock's Ask Matt; the
writer adaptation routes /writing-for-agents to /writing-for-astra. Approved
batch 01 also adapts context management to the current harness; the workflow
map and intentional orchestration remain. See its PROVENANCE.md and ADAPTATIONS.patch.
The skill name and UI display name identify AskPit without colliding with Ask Matt.

Writing for Astra is our separately maintained authoring reference, based on
OpenAI's Astra guidance and the useful editorial principles of Writing for Agents.
Its provenance and included upstream MIT license explain the adaptation.

## Updating

The daily **Review adapted skill upstreams** workflow checks Ask Matt, Writing for Agents and
the four approved batch-01 skills, including supporting files and the upstream license. It
opens or updates one GitHub issue per affected skill with changed paths, a
commit comparison and links to the adjacent PROVENANCE.md rationale.

It does not modify skills, accept a new baseline or auto-merge adaptations.
Unchanged source files produce no alert even if unrelated upstream commits exist.
GitHub notification delivery follows the repository's notification settings.

Each skill keeps its reviewed source revision and hashes in UPSTREAM.json.
After reviewing a change, preserve the documented modifications, port or
explicitly skip upstream differences, and advance the baseline in the reviewed PR.
Closing the issue alone does not update that baseline.

AskPit's generator remains available for an approved review:
`python scripts/sync-ask-pit.py --upstream /path/to/checkout`.
`--check` validates generated integrity offline. Writing for Astra is never
rewritten by that generator. The generic mirror updater no longer refreshes
AskPit automatically. The full Matt mirror is being reviewed in approval-sized batches; unapproved
adaptations and new skills are not imported by this generator.

## Installation

Install the public skills by their distinct names: `ask-pit` and
`writing-for-astra`. AskPit retains explicit-only invocation; it is not a mandatory
coordinator or global workflow. Installing a source is separate from publishing it.
Existing installed aliases must be reconciled per home; source replacement alone
does not remove an old runtime installation.
