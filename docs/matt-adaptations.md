# Approved Matt skill adaptations

The public repository owns these adaptations; no Workbench copy is needed.
Batch 01 was individually presented and approved by the operator on 2026-09-12.
The exact approved patches are beside each skill, with rationale and Astra links
in PROVENANCE.md. Roots keep their original workflow structure and line counts.

| Skill | Root before → after | Approved scope |
| --- | --- | --- |
| code-review | 87 → 87 | Include WIP; shorten description; preserve the two reviewers |
| diagnosing-bugs | 138 → 138 | Provisional hypotheses and evidence-based phase decisions |
| tdd | 38 → 38 | Reuse agreed test seams; preserve red-green workflow |
| resolving-merge-conflicts | 14 → 14 | Stage only operation changes; operator-authorized cancellation |
| AskPit | 90 → 90 | Native context decisions; preserve workflow map and writer route |

No content moved behind new disclosure in this batch. AskPit retains its existing
PHASE-BOUNDARIES.md (55 → 55 lines). No other Matt skill is silently adapted.
Writing for Astra remains the previously approved separate authoring skill.

## Review updates

The daily upstream alert covers these five skills plus Writing for Astra.
It opens or updates GitHub issues; it does not rewrite or merge content.
Notifications follow the repository's GitHub subscription settings.

For an approved update, use an inspected upstream checkout:

```sh
python scripts/sync-matt-adaptations.py --upstream /path/to/upstream --skill code-review
python scripts/sync-matt-adaptations.py --check
```

Omit --skill to rebuild the approved batch. Each skill is staged and validated
before replacement; a conflict preserves that skill's current package. A batch
is per-skill, not a transaction across all five: inspect the whole working diff
if a later skill fails. Do not accept unrelated upstream behavior automatically.
The AskPit command is a compatibility entry point to the same approved pipeline.

Validation checks generated hashes, reverses the approved patch and verifies
that the reconstructed files match the recorded upstream hashes (including the
AskPit packaging transform). Tests cover patch conflicts, changed support files,
retained adaptations and unchanged alert baselines.

Source publication is separate from deployment to Codex homes. Other Matt skills
remain pending individual review; this batch is not a claim of full-family migration.
