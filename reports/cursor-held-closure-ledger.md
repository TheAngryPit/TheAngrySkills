# Cursor held-skill closure ledger

Date: 2026-09-14. This is the pre-worker held queue. The current successor
decision for the nine pstack batch is in
[`reports/pstack-nine-closure-20260914.md`](pstack-nine-closure-20260914.md).
Source pin: `cursor/plugins` commit
`889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`.

The pinned manifest at queue creation contained 91 physical skills. It had 28
`publish:false` entries: 25 active entries below plus the three Benny automation entries
(`cursor-reproduce-and-fix-issues`, `cursor-setup-benny`, and
`cursor-triage-issue-reports`). The three Benny sources still exist upstream
under `pstack/automations/benny`; they are installed through Benny's project
automation setup and are outside the slash-skill catalog. The pinned manifest
does not distribute them as ordinary slash skills. This ledger does not count
them as active slash skills or claim 88/88 functional. “Held” means absent from the
published catalog. Published guide-only and local-renderer surfaces are not
silently recounted as held here.

## Pstack first

The pre-worker queue had 9 held pstack slash skills before the other 16 active
held skills. The current successor promoted bounded explicit-only
`cursor-create-verification-skill`, `cursor-maintain-verification-skill`,
`cursor-no-comments`, `cursor-automate-me`, `cursor-figure-it-out`,
`cursor-poteto-mode`, `cursor-recall`, and `cursor-setup-pstack`; the remaining
pstack gate stays in the same coherent groups. Sol owns integration and the
setup/poteto/router link; Luna high owns
bounded execution in a separate checkout. The existing UI cleanup gate remains
preserved.

1. **Core selection and safe execution:** `cursor-setup-pstack`,
   `cursor-poteto-mode`, `cursor-no-comments`. Prove native role selection,
   companion availability, exact source routing and readback; avoid
   unapproved persistent home changes.
2. **User-surface proof:** `cursor-create-verification-skill` and
   `cursor-maintain-verification-skill`. Keep the CLI input-only source-wave
   distinct from the two native web source readers. The disposable UI run is
   real for that target; Reset fixture still needs action-time confirmation.
3. **Delegated reasoning and review:** Published bounded `cursor-interrogate` and
   `cursor-reflect` provide separate review and reflection paths; effective
   backend model identity and live transcript selection remain open.
4. **Context and learning:** `cursor-recall`, `cursor-figure-it-out`,
   `cursor-automate-me`. Require source-scoped history, a prospective real
   case, and a reviewed project-local skill edit respectively.
5. **External product branch:** `cursor-make-bot-ui`. Preserve the source
   security finding and use a local mock before credentials, installer, or
   network exposure.

The one remaining pstack skill is `cursor-make-bot-ui`; its local request
boundary is proven but its external webhook/Tailnet path remains quarantined.
The other 17 held skills remain in scope after pstack and may advance on
independent safe evidence, but they do not displace this gate.

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
| `cursor-automate-me` | Capture corroborated working preferences, then sequence mining, Cursor `create-skill`, and `unslop` to draft/update one `-mode` skill. | History-gated adapter defaults to project-local `.agents/skills`; fixture updates from two bounded evidence slices and preserves uncontradicted sections. | Authorized transcript scope, native skill-creator, `cursor-unslop`, user preference loop and destination writeback. | Native history and skill-creator invocation are not proven in the current host. | Use supplied bounded evidence and run a project-local draft through `cursor-unslop`, with approval before write. |
| `cursor-create-verification-skill` | Generate `.cursor/skills/verify-<app>/` that launches the real app, drives each feature as a user, captures evidence and cleanup. | Native-write adapter maps to project-local `.agents/skills/verify-<app>/`; disposable notes CLI observes Doctor, actions, protected cleanup and evidence. A separate disposable web app was driven by CUA for create/search/reload with visual receipts. | UI cleanup, native activation and reusable-run permission proof. | The `Reset fixture` UI action that clears localStorage awaits action-time confirmation; no production target parity is claimed. | After confirmation, reset only fixture-owned browser state, inspect post-reset UI, and reconcile the generated skill/feature map. |
| `cursor-figure-it-out` | When no narrower playbook fits, design an auditable hypothesis loop before code, scale rigor, and log decisions with show-me-your-work. | Native procedure adapter uses local reader/check runner/decision log; failed or ungrounded check blocks done. A [post-change real-case audit](cursor-figure-it-out-real-case-20260914.md) verified the held renderer mapping and bounded trail guard. | Prospective pre-change baseline, native trigger, full task phases, real product result, and independent review. | The mapping fix predates the audit; its runtime behavior cannot be proved retrospectively. | Activate on a disposable Codex project before an actual bounded change; record the hypothesis, failed branch, real-product outcome, and reviewer result. |
| `cursor-maintain-verification-skill` | For every feature, read source in parallel, drive every feature live, reconcile feature map and make at most one PR of proven corrections. | CLI fixture captures Doctor, caller-provided source-wave input, drift/re-drives and cleanup. Separately, two native read-only source readers inspected create/search web features, then the coordinator re-drove both in the disposable UI and read back a clean feature map. | UI cleanup, native activation and changed-outcome PR boundary. | The UI reset awaits confirmation; no product bug was found, so a corrective PR is not indicated. | Complete the owned UI cleanup after confirmation, then preserve the clean no-PR maintenance verdict. |
| `cursor-make-bot-ui` | Build a UI whose server POSTs untrusted JSON to a Grok Bot webhook; keep sender key server-side; optionally expose through Tailscale. | Safe local adapter proves server-only key headers/redaction, JSON POST shape, local endpoint gating, malformed nested credential rejection, one-attempt timeout/non-200 handling and payload-only failure evidence. | Authorized webhook routine, sender-key handling, UI/error path and Tailscale exposure review. | Quarantine retains active `curl ...` to `sudo sh` privilege-escalation commands (source lines 89/95). | Keep fixture-only; do not execute installer or network path. Separately review a pinned, non-privileged Tailscale path if explicitly authorized. |
| `cursor-no-comments` | Spawn Comment Sicko on current scope/diff, inspect findings, reject bad flags, act on accepted findings, and offer constraint encodings. | Generated held skill was read, then its exact `agent_type: "comment-sicko"` dispatched on a disposable JS scope; reviewer deleted one redundant comment, kept SPDX, and Sol accepted after syntax/runtime readback. [Receipt](cursor-no-comments-role-fixture.md) and [chain](../docs/native-agent-profiles.md). | Fresh top-level load, exact first-output marker, ambiguous/constraint comments, rejected-report rerun, architect branch, optional encoding and automatic skill trigger. | The simplest read-and-dispatch and accepted-finding path works in this task; full source workflow and installed skill activation remain unproven. | Run a bounded ambiguous-comment/rejected-report case with conditional `cursor-how`/`cursor-why`, then verify a fresh task's named profile load. |
| `cursor-poteto-mode` | Apply Poteto style, all 23 playbooks/principles, deliberate bounded subagents, unslopped prose, simple code and verified work; no silent scope widening. | Native adapter renders all 23 playbooks; generated skill now names exact `agent_type: "poteto-agent"` and follow-up reuse. Existing named agent was reused for a setup Investigation and reported reading full mode, selected playbook and an applied principle leaf. [Chain](../docs/native-agent-profiles.md). Notes bug-fix and Bun/CLI checks remain bounded fixtures. | Independently observed profile loading/skill read, full playbook application, script egress, polling/stack and real PR behavior. | Agent self-report of full skill read is not host tool metadata; executable/dependency and cloud parity remain unproven. | Exercise one end-to-end selected playbook with native trace and coordinator verification; retain security hold on active scripts. |
| `cursor-recall` | Reconstruct recent context from exact chat history, live state and shared record; preserve missing exports and return a tight current-state brief. | History-gated scoped reader preserves workspace/topic/time mismatch as partial and write-free. | Exact task-history selection, live repository/shared-record reconciliation and missing-export evidence. | Native bounded history reconstruction is unobserved. | Supply a scoped export plus repository state and produce a provenance-tagged brief. |
| `cursor-setup-pstack` | Detect available Task model slugs and write an always-applied per-role model rule, preserving explicit choices and aliases. | Native config-gated dry-run fixture covers 17 roles/four panels, aliases, malformed input and no-write behavior. [Current-channel inventory](cursor-setup-pstack-native-inventory-20260914.md) reads advertised subagent models/efforts and Sol-medium turn context, with a candidate map under the standing router. | User-owned task/Work channel entitlement, actual role dispatch, parent alias behavior, persistent destination/write and new-session readback. | The live inventory is scoped to this subagent channel; no persistent policy change was requested or tested. Installed router lacks the source's later profile-distribution section. | Use the observed inventory for a reviewed project-local role diff if the operator requests changed choices; then exercise selected roles and read back a new session before promotion. |
| `cursor-cancel-ralph` | On cancel request, inspect `.cursor/ralph/scratchpad.md`, report iteration, and remove `.cursor/ralph` state. | Native state-gated adapter restricts cancellation to matching project/task state; synthetic wrong-session/symlink tests pass. | Trusted live hook state, exact task/session correlation and actual cancellation readback. | No trusted project hook or live loop state is installed. | Inspect one explicitly scoped project state and perform only a matching bounded cancellation proof. |
| `cursor-ralph-loop` | Start iterative self-referential development loop with completion promise/max iterations, storing `.cursor/ralph` state and feeding prompt after each turn. | Native persistent-loop adapter arms task-bound state and returns Codex continuation in synthetic Stop tests. | Trusted project hook, live continuation, user interruption, scheduler, idempotency and completion readback. | No project hook is trusted and no live automatic continuation is observed. | Prove a bounded max-iteration loop in a disposable project with explicit hook trust and cancellation. |
## Newly published bounded workflows

`cursor-how`, `cursor-why`, `cursor-show-me-your-work`, `cursor-thermos`,
`cursor-swarm`, `cursor-arena`, `cursor-architect`, `cursor-interrogate`, and `cursor-reflect`
moved from this held ledger to the published catalog after their bounded
native cases. The scope is read-only `how`/`why` execution, a bounded local TSV
writer with an independently reviewed trail, a two-lens Thermos review with a
labeled missing-lens result, and a local-computer Swarm with a visible
four-phase checklist and two independent workers. Automatic skill selection, other hosts,
and guaranteed access to every evidence connector remain unproven. The `why`
connector-security finding remains in its overlay with the review decision.
The bounded Arena case used two isolated local design candidates, an independent
cross-judge, a selected base and grafts, a redesign after a failed hypothesis,
and a disposable implementation whose first drift test failed and was fixed.
[Arena proof](pstack-architect-arena-native-20260914.md) does not establish
automatic invocation, Work cloud, other hosts, or production behavior.
The [Interrogate proof](pstack-interrogate-native-20260914.md) records two
read-only native reviews of one scope/rubric, a separate PR #66 same-diff case,
deduplication, lead judgment and no auto-apply. Its explicit-only publication
retains PARTIAL for missing configured reviewers and does not claim effective
backend model attestation.
The [Reflect fixture](cursor-reflect-disposable-20260914.md) records three read-only
lenses and one synthesizer on a scoped transcript with embedded prompt injection
ignored. It publishes the bounded explicit-only path; actual native transcript
selection and an approved skill edit remain unproven. Source security findings
remain recorded; the generated mirror scans safe.
The [Architect proof](pstack-architect-arena-native-20260914.md) records a later
prospective Ground-before-Sketch case with how/why before two distinct designs,
an independent judge, base/grafts and disposable runtime probes. It supports
only bounded explicit local design publication, not production or automatic use.

## Group dependency order

1. **Foundational local readers:** `cursor-figure-it-out` and `cursor-recall`
   (with published `cursor-how`, `cursor-show-me-your-work`, and guide-only
   principles available under their documented limits).
   Establish bounded paths, evidence, and wording before orchestration.
2. **Delegated review and style:** `cursor-advisor`,
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

The pre-worker table below retained 25 rows. Eight pstack rows are now
published as bounded explicit-only paths; the current manifest has 17 active
held rows. The already-published guide-only principles and local PR renderer
are outside this held count and retain their own conditional/native-parity
labels.

`cursor-advisor`, `cursor-check-agent-compatibility`,
`cursor-continual-learning`, `cursor-create-plugin-scaffold`,
`cursor-review-plugin-submission`, `cursor-cursor-sdk`,
`cursor-workflow-from-chats`, `cursor-docs-canvas`, `cursor-add-dictation`,
`cursor-add-read-aloud`, `cursor-add-voice`, `cursor-debug-voice`,
`cursor-orchestrate`, `cursor-pr-review-canvas-pr-review-canvas`,
`cursor-automate-me`,
`cursor-create-verification-skill`, `cursor-figure-it-out`,
`cursor-maintain-verification-skill`,
`cursor-make-bot-ui`, `cursor-no-comments`, `cursor-poteto-mode`,
`cursor-recall`, `cursor-setup-pstack`,
`cursor-cancel-ralph`, and `cursor-ralph-loop`.

The pre-worker list below contained the 25 active `publish:false` names and
excluded the three dormant Benny skills. The current manifest contains 17
active held names after removing the eight bounded pstack promotions, which
are recorded in `reports/pstack-nine-closure-20260914.md`. Optional
external-service branches may be
distributed conditionally only with the local fallback,
credential boundary, and unavailable-capability result preserved.

## Evidence checks

- Queue baseline: `jq` reported 91 physical skills, 28 `publish:false`, and 25
  active `publish:false` before the eight bounded pstack promotions. The
  current successor reports 91 physical skills, 20 `publish:false`, and 17
  active held skills after excluding `pstack/automations/benny`.
- Every row was reconciled against its pinned
  `sources/cursor-plugins/snapshot/**/SKILL.md`, matching overlay JSON under
  `sources/cursor-plugins/overlays/`, and
  `reports/cursor-native-capability-matrix.md`.
- Hook-specific boundaries and synthetic proof limits are recorded in
  `reports/cursor-native-hooks-crosswalk.md`; this ledger does not promote
  synthetic fixtures to native runtime parity.
- Historical PR #64 checkpoint after Swarm promotion: local validation reported `pytest -q tests` 197
  tests plus two subtests and mirror `--check` at 91 physical/59 emitted/239
  output files. Bundled Bun tests 52/52 and strict typecheck passed in scratch;
  CI validation for published PR #64 head `ab038461` completed successfully.
  PR #66 publishes Arena and bounded Architect at 91/61/250; the isolated
  full-catalog successor adds bounded Interrogate and Reflect at 91/63/266,
  and this pstack closure reaches 91/71/344. Their distinct validation
  receipts are recorded in the capability matrix.
- No credentials, global home, fixtures, source files, or code were changed by
  this ledger pass.
