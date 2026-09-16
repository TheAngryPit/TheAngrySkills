# Owned and global editorial audit

Date: 2026-09-16
Audited commit: `c2901d0f0da0f6ce9855f196b493af005ba3583c`
Branch: `codex/editorial-closure-20260916`

## Scope and source of truth

The source-controlled marketplace lists 28 first-party skills in `the-angry-core`,
`the-angry-engineering`, `the-angry-design`, and `founder-gtm`. Physical
occurrence checks found the same 28 `SKILL.md` directories. This audit covers 26
of them: all first-party directories outside `skills/mirrors-*`, excluding
`skills/core/ask-pit` and `skills/engineering/writing-for-astra` because those
are owned by separate editorial passes.

The inventory was reconstructed from:

- `.claude-plugin/marketplace.json` (sha256
  `e09e39ccf5e17904cfc75efbc2b6a8782911d26f69e8e89e907a386aa988b7ff`)
- `README.md` (sha256
  `c4e35454f07bcf6eb251edc70a0ad611b8824b5eaaeced9757514aa76f167dc2`)
- `docs/skill-categories.md` (sha256
  `c390161edd9df08e9f0a1c33c60d317bc4ddd351a618af1f74304d494604fd1e`)
- the physical `SKILL.md` occurrences and their hashes below.

The private source-controlled Workbench was reconciled separately because it is
a curation source, not a public mirror cache. Its detailed inventory, paths,
hashes, and per-skill dispositions are retained only in a task-local private
ledger. This public report records the method and aggregate conclusion without
disclosing that private inventory.

The review applied Writing for Astra's purpose, context, constraints, canonical
pointers, freedom, boundaries, completion, and intentional orchestration rules;
the curator's shared catalog/frontmatter checks; Humanizer's prose-tell checks;
and Karpathy Q8's outcome, assumption, human-review, scope, simplicity, and
verification rules. Templates, quoted examples, explicit safety boundaries,
and operational contrasts were retained when they carry behavior.

## Nominal matrix

`unchanged` means the source already satisfies the approved behavior and no
approved recommendation authorizes an edit. `proposal` records a curator
warning that needs a separate owner decision. No skill file is modified by this
pass.

| Skill | Source / SKILL.md sha256 | Criteria finding | Disposition and before/after | Modified paths |
| --- | --- | --- | --- | --- |
| `skills/core/aegis-communication-discipline` | `89daa948612b2699a97c9da64bc95a32b98c0272b150978095568e67bcf070bd` | Clear trigger, status vocabulary, and completion contract. | `unchanged`; the `disable-model-invocation` field is an intentional explicit-only boundary. Before: same. After: same. | none |
| `skills/core/aegis-html-ledger` | `5839c831d4512ba3bbb595ccc1c991ea2c2cfbf73d94c212de4fcd7aa7f24f9e` | Purpose, ledger boundary, and anti-duplication rules are concrete. | `unchanged`; no decorative or inflated prose requiring correction. Before: same. After: same. | none |
| `skills/core/aegis-structured-execution` | `c0c572c825e0f5fa86b914556bb22eab982e3c331779f3932bf1d542b1d1dbc5` | Outcome, scope, proof levels, and coordinator ownership are explicit. | `unchanged`; orchestration is intentional behavior. Before: same. After: same. | none |
| `skills/core/karpathy-agentic-guidelines-full` | `2ef3c887ef451334f61be10f926f35d5ee4f3238acbdf813ef58e8368f6fa0a8` | Q8-compatible outcome and verification guidance; 240-line root and absent UI metadata are curator info findings. | `proposal`; adding `agents/openai.yaml` or splitting references changes packaging and needs approval. Before: no `agents/openai.yaml`. After: unchanged. | none |
| `skills/core/karpathy-agentic-guidelines-q8` | `1dc3dd6bb310bae3f6b2a5f89c7e49129c65350db4d7ff25365abb86a457d1ee` | Compact root keeps the high-signal rules and points exploratory work to `references/research-loop.md`. | `proposal`; curator reports missing UI metadata, but adding it is a packaging choice. Before: no `agents/openai.yaml`. After: unchanged. | none |
| `skills/core/linear-workflow-router` | `5a68d0e797423212a9a1de3218543f905543a80040a0fea5b00f232aec898636` | Trigger and mode decision tree are concrete; external tracker authority is bounded. | `unchanged`; no Humanizer or Astra edit justified. Before: same. After: same. | none |
| `skills/core/model-capability-router` | `e2867ae60d8e2234681056543888c5b4ae2f9249158cf6bc1ecfa9982d1e33cb` | Narrow trigger and explicit native routing policy preserve model and delegation boundaries. | `proposal`; shared auditor flags a 127-character description. Expanding it could alter routing, so no silent change. Before: current trigger. After: unchanged. | none |
| `skills/core/model-routing-preset-builder` | `9e26dd704f5dde24a39569f1a62696811f59f3377e28b58a09f4beceb5bc5a21` | Delegates to the single router policy and preserves approval/permission separation. | `proposal`; shared auditor flags a 100-character description. Any expansion needs owner review. Before: current trigger. After: unchanged. | none |
| `skills/core/proof-orchestrator` | `82fbd59d821476959c1ba76c116de07a8c13bdaf92a1a2240ddcd5b158fd5dd0` | Proof levels and claim calibration are explicit and non-inflationary. | `unchanged`; the wording directly meets Karpathy verification criteria. Before: same. After: same. | none |
| `skills/core/skill-catalog-curator` | `e1f70bcdf56a2946659de2a941eeec3d76b2b29e30958886aa91da4fc840b8d4` | Catalog, frontmatter, trigger, security, and reporting criteria are concrete. | `unchanged`; this is the audit authority used here. Before: same. After: same. | none |
| `skills/design/adobe-illustrator-operator` | `cad19ccb1d0947c371f13e315ff70d84db0f907f4dee330bbaec45a21c59320d` | Lane selection, source protection, probes, and visual/file verification are explicit. | `proposal`; catalog scan flags default prompt not containing literal `$adobe-illustrator-operator`; prompt names the skill and preserves the intended lane. No routing edit without approval. Before: current prompt. After: unchanged. | none |
| `skills/design/penpot-mcp-operator` | `3208e8539d2671469ef5357bb372007a53a3762d65ba1b67a002e87912d92262` | API-first, token-safe, source-aware design workflow with readback proof. | `proposal`; catalog scan flags default prompt not containing literal `$penpot-mcp-operator`; it names the operator directly. Before: current prompt. After: unchanged. | none |
| `skills/engineering/continuity-handoff` | `bb6b09b9dbb480c503661af3327aaacdd34753ec99c317578498355ae7f24b05` | Portable identity, bounded recall, protected source state, and acceptance proof are grouped correctly. | `unchanged`; long root is justified by the multi-mode contract. Before: same. After: same. | none |
| `skills/engineering/docs-skill-builder` | `ebee0607347c70ad26dc29b73e27b62087f0ddae0e0a19279c0172682b94fff4` | Source-faithful documentation generation and safety boundaries are explicit. | `proposal`; short description (114 chars) and absent `agents/openai.yaml` are catalog warnings. The literal `PLACEHOLDER` in the generator is template output behavior, not unfinished root prose. Before: current metadata. After: unchanged. | none |
| `skills/engineering/openclaw-custom-build-validation` | `4cba102beb5bf511eb0e80f4c80d4b2ca32239bc285ff019001cf1fa48938cc8` | Candidate identity, OCM ownership, proof levels, recovery, and no-release boundary are concrete. | `unchanged`; OpenClaw namespace is owned workflow guidance and remains outside mirror edits. Before: same. After: same. | none |
| `skills/engineering/theangry-ai-code-audit` | `393ec7a83ffd98b55ea2b1a1697b76513625fb981b4900ed9645172f39c5371e` | Audit lens distinguishes slop, fake safety, proof gaps, and generated residue. | `proposal`; catalog scan flags an 89-character UI short description. Shortening it is a new metadata decision. Before: current UI text. After: unchanged. | none |
| `skills/engineering/writing-ticks` | `41fd5df89f6039783cb21ee7441628225fb3bc832a3df93d6d2baa4ea08373d8` | Humanizer source reference, hard/soft finding split, and edit boundaries are explicit. | `proposal`; catalog scan flags default prompt not containing literal `$writing-ticks`; the prompt names the skill and preserves its output contract. Before: current prompt. After: unchanged. | none |
| `skills/founder-gtm/gtm-cold-email` | `55f471aa7ae3c421897f705b1c7d7678ec8bd2f3fbca903225eb708201f365ed` | Human-gated sending, domain risk, prerequisites, drafts, and reply state machine are explicit. | `proposal`; description is 98 words and root is 404 lines. Shortening/splitting could drop safety or sequence context; no approved edit exists. Before: current source-faithful pack. After: unchanged. | none |
| `skills/founder-gtm/gtm-design-play` | `f34c07ec79a03576e5df9e177f03e9cdb44654d5cefc1a1096505a8ee70f41d5` | Play structure, hypothesis backlog, and no-send boundary are concrete. | `proposal`; description is 78 words. Template triads and examples carry the play schema, so Humanizer does not remove them. Before: same. After: unchanged. | none |
| `skills/founder-gtm/gtm-get-better` | `b2e7f23ff3f478404a073f717b6cf45ca8798afb748bf44a2abc0d3e6dbc1bcd` | Metrics, retirement rules, persisted learning, and approval for skill edits are explicit. | `proposal`; description is 115 words and root is 357 lines. The dated learning records are evidence, not inflated claims. Before: same. After: unchanged. | none |
| `skills/founder-gtm/gtm-linkedin-outreach` | `1f002f3e82642a7cedfe35560c25af4fa6e6f9c7c4c045a32d862473cdf5e5c7` | Tool choice, daily limits, draft approval, and logging are concrete. | `unchanged`; the 70-word description and examples remain within the shared profile. Before: same. After: same. | none |
| `skills/founder-gtm/gtm-playbook` | `1de3426594e9eb00cc386a755d3617e9260ef5c0528b17ad14ba063af1c2b558` | Small index skill has a clear purpose and no residue. | `unchanged`; no editorial finding. Before: same. After: same. | none |
| `skills/founder-gtm/gtm-sales-pack` | `08acc7eb661de6b357a643b0ffd9cc1b63bf766232da80e9e28f965993f64d2d` | Question tree, voice-source boundary, redaction, and downstream contract are explicit. | `proposal`; description is 80 words and root is 324 lines. Placeholders are the intentional output template, not catalog residue. Before: same. After: unchanged. | none |
| `skills/founder-gtm/gtm-setup` | `ce3153a9e3f1be3336354d1b63185e5def24a64c212e9a974b8b72962baab4` | Setup dependency order, approval points, and output style are explicit. | `unchanged`; the setup sequence is intentional orchestration. Before: same. After: same. | none |
| `skills/founder-gtm/gtm-warm-intro` | `6f30b46e44d1a034ea5f5c305508cec36f5b4e05a3cbbb1849d01cecb61faae5` | Prospect/bridge matching, channel choice, approval, and logging are explicit. | `proposal`; description is 101 words and root is 247 lines. The strong opening is source-faithful GTM positioning, not a factual provenance claim. Before: same. After: unchanged. | none |
| `skills/founder-gtm/gtm-x-outreach` | `fcb52fa647fe17b8301918e730fd0bfdd043c00836ab34fcf2a8b52b498a4c37` | Prerequisites, rate limits, research grounding, and explicit send modes are concrete. | `proposal`; description is 88 words. The em dashes and options encode selectable modes and were retained. Before: same. After: unchanged. | none |

## Workbench reconciliation matrix

Every source-controlled private skill body and its relevant authored support
was reviewed against the same Astra, curator, Humanizer, and Karpathy criteria
used for the public matrix. The review checked trigger scope, progressive
disclosure, contextual references, authority and privacy gates, intentional
orchestration, completion bounds, and support-file consistency. Catalog and
physical-source mismatches remain private curation proposals; no private root
was copied, promoted, installed, or exposed. The detailed matrix is preserved
in the task-local private ledger and is deliberately absent from this public
artifact.

## Findings and decisions

The scoped catalog scan found 26 skills, zero errors, and eight scanner warnings:

- three default-prompt warnings for `adobe-illustrator-operator`,
  `penpot-mcp-operator`, and `writing-ticks`;
- three missing `agents/openai.yaml` warnings for the two Karpathy packages and
  `docs-skill-builder`;
- two UI short-description warnings for `aegis-communication-discipline` and
  `theangry-ai-code-audit`.

The shared frontmatter auditor found zero errors and nine warnings: short
descriptions for the two model-routing skills and `docs-skill-builder`, plus
wordy descriptions for the six GTM descriptions. All are routing or packaging
proposals. No source-controlled provenance or approval record authorizes a
metadata or behavior change in this pass, so they remain explicit proposals.

Humanizer review found no hard chatbot residue, fabricated authority, or
unsupported significance claim in the owned roots. It preserved operational
contrasts, quoted examples, template placeholders, dates, metrics, approval
language, and safety wording because those carry behavior or evidence. Karpathy
review found no silent authority transfer, unrelated edit, missing completion
boundary, or test-only closure claim. Writing for Astra's requirement to keep
intentional orchestration and compatibility intact rules out shortening that
would erase those constraints.

## Verification

The following checks were run against the audited tree:

```text
python3 skills/core/skill-catalog-curator/scripts/scan_skill_catalog.py \
  --root skills/core --root skills/design --root skills/engineering --root skills/founder-gtm --json
  28 skills in the full first-party roots; 0 errors; 10 warnings

python3 skills/core/skill-catalog-curator/scripts/audit_skill_frontmatter.py \
  skills/core --profile shared --json
python3 skills/core/skill-catalog-curator/scripts/audit_skill_frontmatter.py \
  skills/design --profile shared --json
python3 skills/core/skill-catalog-curator/scripts/audit_skill_frontmatter.py \
  skills/engineering --profile shared --json
python3 skills/core/skill-catalog-curator/scripts/audit_skill_frontmatter.py \
  skills/founder-gtm --profile shared --json
  0 errors across all roots; warnings are recorded above

node scripts/theangry-skills.mjs check --root skills/core --profile shared --strict
node scripts/theangry-skills.mjs check --root skills/design --profile shared --strict
node scripts/theangry-skills.mjs check --root skills/engineering --profile shared --strict
node scripts/theangry-skills.mjs check --root skills/founder-gtm --profile shared --strict
  all commands exited 0

pytest -q tests/test_audit_skill_frontmatter.py tests/test_claude_plugin_marketplace.py \
  tests/test_skill_activation_fixture.py tests/test_native_agent_profiles.py
  18 passed

git diff --check
  passed
```

The full-root counts include the two separately owned exclusions. The report
itself is the only file added by this slice. No install, propagation, dispatch,
publishing, merge, GBrain/config/app edit, permission change, or mirror rewrite
was performed.

## Gaps and follow-up proposals

The warnings need a separate approved metadata decision if they are to be
changed. The concrete proposals are: add literal skill tokens to the three
default prompts; decide whether the two Karpathy skills and `docs-skill-builder`
need UI metadata; shorten or split the three short model/docs descriptions; and
shorten the six GTM descriptions only after confirming that their trigger and
safety content remains intact. None is silently promoted here.

This report does not claim live skill selection, global installation, runtime
behavior, outbound messaging, or GTM delivery. It reports source and automated
catalog evidence only.
