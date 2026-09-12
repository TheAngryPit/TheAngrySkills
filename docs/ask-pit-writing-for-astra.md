# AskPit and Writing for Astra

AskPit is the public replacement for the retired ask-pit/ask-theangrypit router
variants in the private Workbench. Its source is Matt Pocock's Ask Matt; the
only workflow adaptation routes /writing-for-agents to /writing-for-astra.
The skill name and UI display name identify AskPit without colliding with Ask Matt.

Writing for Astra is our separately maintained authoring reference, based on
OpenAI's Astra guidance and the useful editorial principles of Writing for Agents.
Its provenance and included upstream MIT license explain the adaptation.

## Updating

The existing scheduled Sync Curated Mirrors workflow also runs
`python scripts/sync-ask-pit.py`. It fetches current upstream Ask Matt, includes
its supporting files, reapplies the approved identity and route, validates the
result and includes it in the existing update PR. The workflow's existing
required-check and auto-merge path applies. No full Matt Pocock mirror exists.

A changed/missing writer route or identity fails before replacing AskPit. Review
the change instead of silently publishing an unpatched router. Writing for Astra
is outside the generated AskPit directory and is never overwritten by refresh.
New Matt Pocock skills are not imported: the full-family mirror was cancelled.

For a deterministic local refresh use `--upstream /path/to/checkout`.
For offline integrity validation use `--check`. UPSTREAM.json records the exact
source commit and original/generated hashes; tests cover compatible updates,
missing routes, support additions/removals and preservation of the writer skill.

## Installation

Install the public skills by their distinct names: `ask-pit` and
`writing-for-astra`. AskPit retains explicit-only invocation; it is not a mandatory
coordinator or global workflow. Installing a source is separate from publishing it.
Existing installed aliases must be reconciled per home; source replacement alone
does not remove an old runtime installation.
