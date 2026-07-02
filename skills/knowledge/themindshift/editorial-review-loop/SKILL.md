---
name: themindshift-editorial-review-loop
description: Run the TheMindShift editorial review loop for draft critique, revision direction, voice fit, evidence integrity, no-em-dash compliance, and publishing-risk checks. Use when a draft needs review before Vitor gives final language approval.
---

# TheMindShift Editorial Review Loop

Use this skill to protect editorial quality before Vitor reviews a draft. It can propose or apply bounded revisions, but it cannot approve voice fit for Vitor.

TheMindShift project files and `TheAngry_Editor-inChief` remain authority. This skill is procedural support for a repeated editorial loop.

## Required Reads

1. Read TheMindShift `AGENTS.md`, `ACTIVE_STATE.md`, `NEWSLETTER_DOCTRINE.md`, and `MODES/editorial-review-loop.md` if present.
2. Read the active draft, approved research synthesis, issue brief, and any previous Vitor feedback on voice or structure.
3. Inspect the draft review artifact if one already exists.

If the TheMindShift project root is missing, ask for it. Do not run this loop from memory alone.

## Loop Steps

1. Confirm the draft version, current gate, and whether the task is critique-only or revision allowed.
2. Review thesis, opening force, section flow, source grounding, specificity, Vitor voice, and reader payoff.
3. Check for generic AI writing, false polish, over-broad claims, unsupported assertions, repetition, and em dash usage.
4. Produce a prioritized editorial review with must-fix issues, optional improvements, and preserve-as-is calls.
5. Revise if authorized and the fix is bounded, then rerun the review against the changed draft.
6. Hand back a draft review artifact target or review notes with exact Vitor decision points.

## Hard Stops

- Stop before final voice approval.
- Stop before declaring the draft publication-ready.
- Stop before publication, posting, emailing, contacting anyone, or changing external systems.

## Output

Return the review verdict, must-fix list, revision status, remaining voice risks, blocker status, and next action.
