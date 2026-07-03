---
name: theangry-write-like-vitor-bootstrap
description: "Use when Vitor asks to bootstrap or update a writing-style skill from his authored messages, posts, emails, drafts, or project voice examples. Privacy-gated and split by personal, TheHive, BEE, and project voice lanes."
---

# TheAngry Write Like Vitor Bootstrap

Create or update a durable writing-style skill from Vitor's own authored material without storing raw private messages.

This skill is inspired by `write-like-me-bootstrap` from `jxnl/personal-monorepo-template`, but adapted to Vitor's separate voice lanes.

## Voice Lanes

Do not collapse all writing into one voice.

Default lanes:

- Vitor personal;
- TheHive public/company;
- BEE / TheHive signal operator;
- project-specific voice when explicitly needed;
- private relationship or repair tone only if explicitly approved.

## Approval Gates

Ask before:

- reading email, Slack, Telegram, WhatsApp, DMs, private docs, or private transcripts;
- writing any generated skill or style profile;
- using examples from sensitive contexts;
- promoting any generated profile into TheAngrySkills or installed skills.

No connector scan is implied by this skill alone.

## Privacy Rules

- Do not store raw private excerpts in durable files.
- Use synthetic examples that preserve style without exposing private facts.
- Keep source evidence as compact descriptors such as `sent email follow-ups, March-June 2026`.
- Separate channel and posture. Do not flatten email, social posts, Slack-style replies, and brand copy.
- Do not infer sensitive personal details from writing samples.

## Workflow

1. Identify requested voice lane and target channel.
2. Identify approved source material and date range.
3. Cluster by posture:
   - quick reply;
   - pushback;
   - delegation;
   - status update;
   - public post;
   - email reply;
   - partner/client note;
   - correction or repair.
4. Extract style rules, pacing, directness, humor, warmth, and forbidden tells.
5. Produce a preview before writing files.
6. Ask for approval.
7. Only after approval, create or update the generated writing-style skill/profile.

## Generated Skill Requirements

The generated skill should:

- route by lane, channel, and posture before drafting;
- ask only when audience, channel, goal, or risk changes the draft;
- default to useful drafts, not style lectures;
- include critique mode: what does not sound like Vitor;
- preserve privacy and source boundaries;
- update when Vitor corrects voice assumptions.

## Output Before Approval

```text
Voice lane:
Sources allowed:
Postures found:
Draft style rules:
Synthetic example quality:
Privacy exclusions:
Needs Vitor:
```
