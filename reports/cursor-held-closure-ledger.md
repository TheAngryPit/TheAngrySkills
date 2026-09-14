# Cursor held-skill closure ledger

Date: 2026-09-14. Source pin: `cursor/plugins` commit
`889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`.

The pinned manifest contains 91 physical skills. It has 33 `publish:false`
entries: 30 active entries below plus the three dormant Benny entries
(`cursor-reproduce-and-fix-issues`, `cursor-setup-benny`, and
`cursor-triage-issue-reports`). This ledger does not count dormant Benny as
active and does not claim 88/88 functional. “Held” means absent from the
published catalog. Published guide-only and local-renderer surfaces are not
silently recounted as held here.

| Skill | Exact upstream requirement | Current Codex adaptation and proof | Proof still needed | Concrete blocker | Next executable step |
| --- | --- | --- | --- | --- | --- |
| `cursor-advisor` | On explicit `/advisor` or second-opinion request, consult a stronger/different model at decision/error/done checkpoints; never self-enable; advisor does not edit. | Delegated-native adapter; task-bound synthetic `PostToolUse`/`SubagentStop`/`Stop` lifecycle and pinned role reference checked. | Fresh task profile selection, native model/effort selection, trusted hook, live consult and role/verdict correlation. | No trusted project hook or live named advisor consult is proven. | Run one explicitly authorized, read-only native advisor consult and capture the bounded verdict. |
| `cursor-check-agent-compatibility` | Run four separate checks: scanner score, startup, validation loop, and docs reliability, one subagent per task, then preserve the score contract. | Four reviewer roles bundled; invalid frontmatter corrected; structural preview only. | Scanner package/version review, cold startup, four real checks, separate evidence and combined score. | Scanner package and startup prerequisites have not been executed or reviewed. | Review/pin the scanner package, then run the four checks against a disposable repository. |
| `cursor-continual-learning` | Delegate transcript mining and `AGENTS.md` updates to `agents-memory-updater`; parent remains orchestration-only. | Native write-gated adapter; synthetic Stop thresholds/mtime/duplicate tests and one synthetic updater fixture pass. | Real scoped transcript, trusted hook, authorized `AGENTS.md` diff, updater failure and duplicate handling. | No real transcript boundary or trusted automatic updater hook is proven. | Use an explicitly authorized project transcript and bounded updater delegate; capture before/after diff. |
| `cursor-create-plugin-scaffold` | Given kebab-case name, purpose/users, component set, and repository style, create valid manifest, component directories, and marketplace wiring; source defaults to `~/.cursor/plugins/local/`. | Disposable marked-root fixture writes static manifest/README/LICENSE/four components and passes structural audit. | Native destination, active component semantics, hooks/MCP and marketplace behavior, installation and publication review. | Source global `~/.cursor` default and active hooks/MCP/marketplace components remain unsafe/unadapted. | Repeat only in an explicit disposable project root with hooks/MCP disabled, then review each active component separately. |
| `cursor-review-plugin-submission` | Audit manifest metadata, component paths/discovery, documentation, quality and marketplace readiness before publishing. | Read-only local auditor fixture checks manifest/path/frontmatter/README and passive hook/MCP detection. | Full YAML validation, uniqueness/marketplace checks, runtime behavior and human submission review. | Marketplace submission and active hook/MCP behavior are unproven; scanner verdict remains `needs_human_review`. | Run the complete static audit on a supplied disposable plugin and resolve every `REVIEW_REQUIRED` finding. |
| `cursor-cursor-sdk` | Guide code against `@cursor/sdk`, `Agent.create/prompt/resume`, streaming, cancellation/errors, local/cloud choice and MCP configuration. | Reference-only reader identifies SDK symbols; no install, execution or authentication. | Safe contextual credential/MCP review and an authorized external SDK behavior proof. | Upstream `blocked_malicious` credential/MCP findings and absent Cursor SDK runtime. | Keep reference-only; if needed, review a pinned SDK package and run a no-credential documentation fixture. |
| `cursor-workflow-from-chats` | Extract durable preferences from recent Cursor parent/subagent chats (default seven days), cite parent evidence, redact secrets, and propose skills/rules/docs. | History-gated scoped reader/preference extractor; no durable write without approval. | Bounded parent transcript selection, subagent evidence handling, redaction and artifact proposal fixture. | Native task list/read exists, but a bounded parent/subagent transcript reconstruction and redaction proof is absent. | Supply an explicitly scoped transcript export and produce a proposed project-local artifact with provenance. |
| `cursor-docs-canvas` | Render architecture/API/how-to documentation as an interactive navigable Cursor Canvas with sections, TOC and cross-references. | Local Markdown reader/renderer with linked-document fallback; no product config. | Canvas SDK/primitive, component/hook contract and interactive output. | Pinned source calls itself a placeholder and requires `~/.cursor/skills-cursor/canvas/SKILL.md`; no native Canvas equivalent is proven. | Keep conditional: render a local linked Markdown/HTML artifact and label the Canvas parity gap. |
| `cursor-add-dictation` | On `/add-dictation`/transcribe intent, wire an app mic or uploaded audio to Grok STT with captions/timestamps/diarization/subtitles. | External-voice adapter expects server-side HTTP/multipart client; missing endpoint/auth is typed and key-free. | Authorized xAI endpoint/key handling and safe audio success/error fixture. | Active source `curl` sends audio with `XAI_API_KEY`; external network and credential handling are unproven (`blocked_malicious`). | Keep held; review server-only credential flow, then run an authorized safe audio fixture. |
| `cursor-add-read-aloud` | On `/add-read-aloud`/TTS intent, add app speaker/auto-speak/narration using Grok TTS. | External-voice adapter expects server-side HTTP plus playback; missing auth leaves playback idle. | Authorized xAI endpoint/key handling and safe text/audio success/error fixture. | Active source `curl` sends reply text with `XAI_API_KEY` and writes audio; external network/credential handling is unproven (`blocked_malicious`). | Keep held; review server-only credential flow, then run an authorized safe text fixture. |
| `cursor-add-voice` | On `/add-voice`/Voice Mode, wire app mic to duplex Grok realtime speech with safe auth; reserve mic for dictation and waveform for voice. | External realtime adapter expects server relay/WebSocket; malformed events close a diagnostic mock session. | Authorized relay, server credential isolation, microphone/audio integration and realtime error fixture. | xAI realtime endpoint and network/credential path are not proven in this host. | Prove a mock relay first, then request explicit network authorization for a safe provider test. |
| `cursor-debug-voice` | On `/debug-voice`, install dev-only client-to-local-NDJSON logs, match report to signatures, fix one issue and re-test; never audio/tokens/prod. | Local log reader/redaction adapter; missing logs or failed redaction is `INCONCLUSIVE` and write-free. | App-specific log fixture, redaction, one bounded fix/retest and no-production proof. | No current voice integration/log source has been exercised. | Provide a scoped synthetic NDJSON log and run the redaction/diagnosis fixture. |
| `cursor-orchestrate` | Only explicit `/orchestrate <goal>` may decompose work into cloud planners/workers/verifiers with structured handoffs, state, cancellation and recovery. The pinned implementation uses Cursor SDK/scripts. | The [Work cloud contract](cursor-orchestrate-work-cloud-contract-20260914.md) maps the operator-selected ChatGPT Work destination to documented native task creation and existing list/read surfaces; local delegation and Cursor scripts are not substitutes. The source/security finding remains held. | Explicit Work root dispatch, child fan-out/drain, structured handoffs, repository artifacts, cancellation and recovery readback. | Auto-review rejected a bounded Work task creation for lack of specific user authorization; no task was created. The current available tools do not document Work child/drain/cancel/artifact parity. | Obtain approval for the exact read-only Work PR #64 proof task in the contract report; then observe task ID/result and separately prove tree/artifact/recovery operations. |
| `cursor-pr-review-canvas-pr-review-canvas` | Render a PR diff in Cursor Canvas grouped by reviewer importance, boilerplate/core logic and tricky changes; read Canvas prerequisites first. | Local diff reader/document renderer; Canvas absence returns artifact plus parity gap. | Canvas SDK/component contract and live PR metadata/render behavior. | No Canvas primitive or pinned Canvas SDK is available. | Retain conditional local Markdown/HTML review artifact and label Canvas unavailable. |
| `cursor-architect` | For `/architect` or non-trivial work, ground, sketch types/signatures/modules, agree across perspectives, implement, and scrap a disproven sketch. | Delegated-native bounded design delegate plus local reader; missing delegate has labeled sequential fallback. | Trigger, todolist phases, delegated design result, ownership and redesign behavior on a disposable task. | Native delegated design invocation is unobserved. | Run one bounded read-only architecture pass and retain the sketch/result handoff. |
| `cursor-arena` | Fan out N parallel candidates, read every candidate, cross-judge, pick a base, graft strongest loser ideas, and verify. | Delegated-native candidate adapter records unavailable candidates rather than fabricating a winner. | Real N-way native fan-out, independent candidate artifacts, cross-judge/graft and verification. | Native parallel subagent capability exists, but an Arena candidate/cross-judge/graft run is unobserved; one fallback cannot establish competition. | Run a bounded two-candidate read-only arena when native fan-out is available; otherwise record sequential fallback. |
| `cursor-automate-me` | Capture corroborated working preferences, then sequence mining, Cursor `create-skill`, and `unslop` to draft/update one `-mode` skill. | History-gated adapter defaults to project-local `.agents/skills`; fixture updates from two bounded evidence slices and preserves uncontradicted sections. | Authorized transcript scope, native skill-creator, `cursor-unslop`, user preference loop and destination writeback. | Native history and skill-creator invocation are not proven in the current host. | Use supplied bounded evidence and run a project-local draft through `cursor-unslop`, with approval before write. |
| `cursor-create-verification-skill` | Generate `.cursor/skills/verify-<app>/` that launches the real app, drives each feature as a user, captures evidence and cleanup. | Native-write adapter maps to project-local `.agents/skills/verify-<app>/`; disposable notes CLI captures subprocess evidence and drift. | Live target/harness, syntax/version Doctor, native activation, all features and permission proof. | No live target application or native verification runner is supplied. | Run against an explicitly authorized disposable app, then verify launch/doctor/drive/evidence/cleanup and second pass. |
| `cursor-figure-it-out` | When no narrower playbook fits, design an auditable hypothesis loop before code, scale rigor, and log decisions with show-me-your-work. | Native procedure adapter uses local reader/check runner/decision log; failed or ungrounded check blocks done. A [post-change real-case audit](cursor-figure-it-out-real-case-20260914.md) verified the held renderer mapping and bounded trail guard. | Prospective pre-change baseline, native trigger, full task phases, real product result, and independent review. | The mapping fix predates the audit; its runtime behavior cannot be proved retrospectively. | Activate on a disposable Codex project before an actual bounded change; record the hypothesis, failed branch, real-product outcome, and reviewer result. |
| `cursor-interrogate` | Spawn one reviewer per configured model over the same scope/rubric, synthesize adversarial findings, and never auto-apply. | Delegated-native read-only reviewers with missing-reviewer accounting; no repair PR from unavailable model. | Multi-model fan-out, independent same-diff review, deduplication and synthesis. | Native multi-review behavior and model routing remain unproven. | Run two bounded read-only reviewers on one disposable diff and preserve separate reports. |
| `cursor-maintain-verification-skill` | For every feature, read source in parallel, drive every feature live, reconcile feature map and make at most one PR of proven corrections. | Project-local maintenance adapter and fixture create `.agents/skills/verify-*`, capture drift and clean second execution. | Live app, source-wave delegation, native runner, failed Doctor, cleanup ownership and PR boundary. | No live target/native runner path is supplied. | Run a disposable feature-map maintenance pass, then prove live feature coverage before any PR. |
| `cursor-make-bot-ui` | Build a UI whose server POSTs untrusted JSON to a Grok Bot webhook; keep sender key server-side; optionally expose through Tailscale. | External-product/security adapter is reference-only; no webhook or installer execution. | Authorized webhook routine, sender-key handling, UI/error path and Tailscale exposure review. | Quarantine retains active `curl ...` to `sudo sh` privilege-escalation commands (source lines 89/95). | Do not execute installer; design a local mock webhook and separately review a pinned, non-privileged Tailscale path. |
| `cursor-no-comments` | Spawn Comment Sicko on current scope/diff, inspect findings, reject bad flags, act on accepted findings, and offer constraint encodings. | Named `comment-sicko` profile asset and bounded role contract; native session selection remains conditional. | Fresh task profile selection, live reviewer output, accepted-finding application and optional constraint approval. | Named `comment-sicko` subagent selection and a bounded output were observed; fresh top-level loading, complete role compliance, and the first-output marker remain unproven. | Run an explicitly selected named reviewer on a disposable diff and capture coordinator-owned findings. |
| `cursor-poteto-mode` | Apply Poteto style, all 23 playbooks/principles, deliberate bounded subagents, unslopped prose, simple code and verified work; no silent scope widening. | Native governed-style adapter; all 23 playbooks rendered, notes bug-fix fixture and bounded Bun/CLI/scratch checks recorded. | Live playbook application, profile loading/selection, native session, script security/egress, polling/stack and real PR behavior. | Bundled executable/dependency surface and native session/cloud parity remain unproven. | Keep unpublished; review scripts/egress, then run one explicitly selected playbook in a disposable project. |
| `cursor-recall` | Reconstruct recent context from exact chat history, live state and shared record; preserve missing exports and return a tight current-state brief. | History-gated scoped reader preserves workspace/topic/time mismatch as partial and write-free. | Exact task-history selection, live repository/shared-record reconciliation and missing-export evidence. | Native bounded history reconstruction is unobserved. | Supply a scoped export plus repository state and produce a provenance-tagged brief. |
| `cursor-reflect` | Spawn three parallel reviewers over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. | Delegated-native judgment/tooling/divergent lenses; missing transcript/lens remains incomplete and write-free. | Three native reviewers, transcript scope, synthesis and explicit edit authorization. | Native task read tools exist; exact scoped transcript access and a three-reviewer run remain unproven. | Run three bounded read-only lenses over a supplied synthetic transcript; propose edits without applying them. |
| `cursor-setup-pstack` | Detect available Task model slugs and write an always-applied per-role model rule, preserving explicit choices and aliases. | Native config-gated dry-run fixture covers 17 roles/four panels, aliases, malformed input and no-write behavior. [Current-channel inventory](cursor-setup-pstack-native-inventory-20260914.md) reads advertised subagent models/efforts and Sol-medium turn context, with a candidate map under the standing router. | User-owned task/Work channel entitlement, actual role dispatch, parent alias behavior, persistent destination/write and new-session readback. | The live inventory is scoped to this subagent channel; no persistent policy change was requested or tested. Installed router lacks the source's later profile-distribution section. | Use the observed inventory for a reviewed project-local role diff if the operator requests changed choices; then exercise selected roles and read back a new session before promotion. |
| `cursor-swarm` | Open a four-phase todolist before launch; fan out N parallel workers, require each to report `PASS`/`ISSUES`/`BLOCKED`, drain them, and aggregate one report with gaps. | Delegated-native adapter now preserves the source's phase order and worker verdicts; the prior two-worker run produced an aggregate but lacked the prelaunch todolist and source-format verdicts. | Source-faithful native N-worker fan-out, terminal drain, aggregation, and dropout handling. | The first parallel run does not prove the full source workflow. | Run a bounded two-worker read-only swarm on the current head with a prelaunch todolist, source-format worker verdicts, and one evidenced aggregate. |
| `cursor-cancel-ralph` | On cancel request, inspect `.cursor/ralph/scratchpad.md`, report iteration, and remove `.cursor/ralph` state. | Native state-gated adapter restricts cancellation to matching project/task state; synthetic wrong-session/symlink tests pass. | Trusted live hook state, exact task/session correlation and actual cancellation readback. | No trusted project hook or live loop state is installed. | Inspect one explicitly scoped project state and perform only a matching bounded cancellation proof. |
| `cursor-ralph-loop` | Start iterative self-referential development loop with completion promise/max iterations, storing `.cursor/ralph` state and feeding prompt after each turn. | Native persistent-loop adapter arms task-bound state and returns Codex continuation in synthetic Stop tests. | Trusted project hook, live continuation, user interruption, scheduler, idempotency and completion readback. | No project hook is trusted and no live automatic continuation is observed. | Prove a bounded max-iteration loop in a disposable project with explicit hook trust and cancellation. |
## Newly published bounded workflows

`cursor-how`, `cursor-why`, `cursor-show-me-your-work`, and `cursor-thermos`
moved from this held ledger to the published catalog after their bounded
native cases. The scope is read-only `how`/`why` execution, a bounded local TSV
writer with an independently reviewed trail, and a two-lens Thermos review
with a labeled missing-lens result. Automatic skill selection, other hosts,
and guaranteed access to every evidence connector remain unproven. The `why`
connector-security finding remains in its overlay with the review decision.

## Group dependency order

1. **Foundational local readers:** `cursor-figure-it-out` and `cursor-recall`
   (with published `cursor-how`, `cursor-show-me-your-work`, and guide-only
   principles available under their documented limits).
   Establish bounded paths, evidence, and wording before orchestration.
2. **Delegated review and style:** `cursor-advisor`, `cursor-architect`,
   `cursor-arena`, `cursor-interrogate`, `cursor-reflect`, `cursor-swarm`,
   `cursor-no-comments`, and `cursor-poteto-mode`. Prove
   native named/bounded delegation and coordinator ownership first; Poteto's
   `cursor-deslop`, `cursor-control-cli`, and `cursor-control-ui` dependencies
   are conditional and must be checked per playbook.
3. **History and learning:** `cursor-workflow-from-chats`, `cursor-automate-me`,
   and `cursor-continual-learning`. Prove exact transcript scope and redaction
   before any preference or `AGENTS.md` write.
4. **Verification and configuration:** `cursor-create-verification-skill`,
   `cursor-maintain-verification-skill`, `cursor-check-agent-compatibility`,
   and `cursor-setup-pstack`. Require a real disposable target, live inventory,
   and explicit write/readback boundaries.
5. **Hooks and loops:** `cursor-ralph-loop`, `cursor-cancel-ralph`. Establish
   trusted project hook payloads and task/session state before continuation or
   cancellation.
6. **Local review artifacts:** `cursor-pr-review-canvas-pr-review-canvas` and
   `cursor-cursor-team-kit-pr-review-canvas`. The local Markdown/HTML renderer
   may be used conditionally; Canvas parity stays a separate claim.
7. **External product/service surfaces:** voice skills, `cursor-orchestrate`,
   `cursor-make-bot-ui`, `cursor-cursor-sdk`, `cursor-docs-canvas`, and plugin
   scaffold/submission skills. Review credentials, endpoints, hooks/MCP,
   installers, egress, and publication separately before any live branch.

## Remaining unavailable skills

All 30 rows remain absent from the published catalog and unavailable for a
claimed native functional invocation until their row's proof and blocker are
closed. The already-published guide-only principles and local PR renderer are
outside this held count and retain their own conditional/native-parity labels.

`cursor-advisor`, `cursor-check-agent-compatibility`,
`cursor-continual-learning`, `cursor-create-plugin-scaffold`,
`cursor-review-plugin-submission`, `cursor-cursor-sdk`,
`cursor-workflow-from-chats`, `cursor-docs-canvas`, `cursor-add-dictation`,
`cursor-add-read-aloud`, `cursor-add-voice`, `cursor-debug-voice`,
`cursor-orchestrate`, `cursor-pr-review-canvas-pr-review-canvas`,
`cursor-architect`, `cursor-arena`, `cursor-automate-me`,
`cursor-create-verification-skill`, `cursor-figure-it-out`,
`cursor-interrogate`, `cursor-maintain-verification-skill`,
`cursor-make-bot-ui`, `cursor-no-comments`, `cursor-poteto-mode`,
`cursor-recall`, `cursor-reflect`, `cursor-setup-pstack`,
`cursor-swarm`,
`cursor-cancel-ralph`, and `cursor-ralph-loop`.

The list contains exactly the 30 active `publish:false` names and excludes the
three dormant Benny skills. Optional external-service branches may be
distributed conditionally only with the local fallback,
credential boundary, and unavailable-capability result preserved.

## Evidence checks

- Manifest count: `jq` reports 91 physical skills, 33 `publish:false`, and 30
  active `publish:false` after excluding `pstack/automations/benny`.
- Every row was reconciled against its pinned
  `sources/cursor-plugins/snapshot/**/SKILL.md`, matching overlay JSON under
  `sources/cursor-plugins/overlays/`, and
  `reports/cursor-native-capability-matrix.md`.
- Hook-specific boundaries and synthetic proof limits are recorded in
  `reports/cursor-native-hooks-crosswalk.md`; this ledger does not promote
  synthetic fixtures to native runtime parity.
- After the Thermos promotion, local validation reported `pytest -q tests` 197
  tests plus two subtests and mirror `--check` at 91 physical/58 emitted/235
  output files. Bundled Bun tests 52/52 and strict typecheck passed in scratch;
  CI validation for published head `ab038461` completed successfully.
- No credentials, global home, fixtures, source files, or code were changed by
  this ledger pass.
