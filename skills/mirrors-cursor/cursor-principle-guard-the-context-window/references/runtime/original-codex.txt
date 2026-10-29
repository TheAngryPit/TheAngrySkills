---
name: cursor-principle-guard-the-context-window
description: "Apply when context is filling up: large outputs, long files, repeated reads, fan-out planning. Route bulk to subagents; keep summaries in the main thread, not raw payloads."
---

## Codex adaptation

Bound reads and payloads; route only when a real delegate exists. Required native capabilities: none; this is instruction-only. No external product dependency is required by the adapted path. No tool is required; an oversized payload gets a bounded sequential fallback. This candidate is promoted for the bounded path described here; unrelated runtime parity remains unproven. This is a guide-only adaptation.

# Guard the Context Window

**Why:** Context overflow degrades reasoning quality, creates compression artifacts, and halts progress.

**Pattern:**
- **Size phases and cap scope.** Limit files per phase, set turn budgets, account for mechanism costs.
