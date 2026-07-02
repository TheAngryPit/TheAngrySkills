# Artifact States

Use explicit states instead of vague completion language.

| State | Meaning |
| --- | --- |
| `raw_created` | Raw artifact or source pointer exists. |
| `manifest_created` | Source manifest exists with provenance and sensitivity. |
| `normalized_created` | Normalized Markdown exists. |
| `strategy_packet_created` | Prompt packet or strategy run input exists. |
| `ready_for_codex_execution` | Codex execution is prepared but not run. |
| `needs_review` | Output exists and needs operator or Echo review. |
| `accepted` | Reviewed material can be promoted. |
| `needs_edit` | Output is useful but needs correction. |
| `rejected` | Output should not be promoted. |
| `blocked` | Required source, extraction, proof, or approval is missing. |
