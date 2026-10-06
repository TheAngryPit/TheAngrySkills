# Prompts worth copying

Swap in the real paths, skills, and done checks. Informal wording works.

## Understand

- `$cursor-poteto-mode read <thread>. restate the underlying issue in your own words, in plain english.`
- `$cursor-poteto-mode investigate why <symptom>. give me what we know, what data you used, and your best hypotheses. don't change any code yet.`
- `use $cursor-how to understand <subsystem>. then use $cursor-why to find out why it broke recently.`
- `$cursor-recall my work on <topic> from last week, then read <issue>.`
- `$cursor-teach me why you implemented it this way and not <other way>. what did you trade off?`
- `$cursor-poteto-mode take over this branch. read the decision log, find what's done, and continue. don't redo finished work.`

## Build

- Bug: `$cursor-poteto-mode <symptom>. repro first, then fix and verify.`
- Bug in an app: `$cursor-poteto-mode repro this with /verify-<app>. if it repros on main, fix it and show me a video as proof.`
- Bug with a cheap test: `$cursor-poteto-mode repro <bug> first. if there's a cheap test path, $cursor-tdd it. then fix and rerun.`
- Feature: `$cursor-poteto-mode add <behavior>. <current output> stays byte-identical. verify both.`
- Refactor: `$cursor-poteto-mode move <code> into one module, zero behavior change. record the current output first and prove it's unchanged after.`
- Perf: `$cursor-poteto-mode <operation> takes <time> on <fixture>. trace it, fix the measured cause, show me before and after.`

## Design and plan

- `$cursor-poteto-mode prototype a few options for <feature>. take screenshots or videos for me to compare.`
- `$cursor-poteto-mode we need <feature>. $cursor-architect it first, and answer open questions with prototypes. let me review before proceeding.`
- `$cursor-poteto-mode write a tutorial for how i would use <new package> first. then $cursor-teach me why it beats the current one.`
- `ask $cursor-arena for a second opinion on this thread and our approach.`
- `$cursor-poteto-mode turn this design into a plan. small verifiable PRs, each with its own verification steps.`
- `$cursor-poteto-mode plan the migration of <library> to <target>. small verifiable PRs. the result must match the original exactly, bugs included.`

## Review and ship

- `$cursor-interrogate the whole branch, but skeptically. don't change anything yet. no nitpicks unless it's a real bug or regression.` Read the dismissals too.
- `$cursor-swarm check every package under <dir> against its check script. one worker per package. one report.`
- `$cursor-poteto-mode open the pr. small ordered commits, evidence in the description.`
- `$cursor-poteto-mode babysit this pr. get it green.` For status only: `$cursor-poteto-mode check on pr <number>. anything outstanding?`
- `$cursor-poteto-mode land the stack.`

## Away and back

- `$cursor-poteto-mode im going to bed. <goal> in a fresh worktree off <base>. done means <checks>. keep a decision log. don't ask me before committing. continue until done with supported native continuation; schedule a follow-up only if explicitly requested. if you're truly stuck after a few hours, stop and write up why.`
- `$cursor-show-me-your-work catch me up on what you did last night.` Read its Attention section first.
- `$cursor-poteto-mode full autopilot on this queue. each item is independent.`
- `$cursor-poteto-mode autopilot these changes but stack them, don't ship. i'll land the stack.`
- `$cursor-reflect capture what we learned so the next run doesn't repeat it.` Approve only edits that change a future decision.
- `$cursor-bro` restates the last reply in plain words.
