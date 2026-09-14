# Verification-skill UI and source-wave proof

Date: 2026-09-14

## Repository and change boundary

- Canonical repository: `TheAngrySkills` (the configured local remote is
  `/private/tmp/cursor-theangryskills-mirror-20260912`).
- Local task checkout: `/private/tmp/theangryskills-pstack-20260913-xcCoXg/repo`.
- Branch: `codex/verification-ui-delta-20260914`.
- Authority base: `ea6099fa5b9c80251cfe82467738e133aee17c35`.
- Current carried commit before this delta: `b3a9046e` (`test(pstack):
  strengthen verification skill fixture proof`).
- This delta changes only the two held overlay descriptions and this report.
  It does not alter the manifest, pinned source, global skills, product code,
  PR state, or push any branch.

The name `TheAngry-Workflows` is the local project context from the original
task, not the canonical repository identity for this verification-skill
delta. The report uses `TheAngrySkills` for repository provenance and names the
checkout path separately.

## Source-wave input

Native bounded readers were used independently, one per mapped feature. Their
receipts are separate from the CLI fixture's caller-supplied input:

- Cicero, task `01a0a090-f43a-7853-9604-421ee99f847c`, read the create feature.
  It cited the form and visible status in
  `/private/tmp/pstack-web-verify-20260914/index.html:27-38`, persistence in
  `app.js:10-16`, rendering and save behavior in `app.js:18-57`, and the
  feature map in `features/create-note.md:6-32`. It found no behavior drift;
  it did flag that the map's `Doctor passes` wording is not implemented by the
  static fixture and that the empty-list precondition depends on reset.
- Aristotle, task `01a0a090-f356-7df2-ac27-9dcc7acdf4b9`, read the search
  feature. It cited the search controls in
  `/private/tmp/pstack-web-verify-20260914/index.html:40-48`, filtering and
  empty state in `app.js:18-41`, query and clear behavior in `app.js:59-63`,
  and the feature map in `features/search-notes.md:6-32`. It found no behavior
  drift; it flagged only the wording mismatch between “Notes page” and the
  single static page and the need to confirm persistence after clear.

The earlier CLI fixture report remains fixture-only. Its `OBSERVED` source-wave
field was caller-supplied and must be read as `OBSERVED_INPUT_ONLY` unless
paired with native-reader receipts. This report records the two native reader
receipts above separately and does not promote the earlier field.

## Disposable UI proof

The generated project-local skill is at
`/private/tmp/pstack-web-verify-20260914/.agents/skills/verify-notes-web/`.
Its launch, Doctor, drive, evidence, and cleanup contract is in `SKILL.md:12-50`.
The disposable app exposes the visible version/health identity, labelled create
controls, search controls, and the explicit `Reset fixture` cleanup control in
`index.html:27-51`; create, persistence, filtering, empty-state, clear, and
reset behavior are implemented in `app.js:10-72`.

Doctor evidence:

- `node --check app.js` passed.
- HTML parsing passed with `syntax:html-ok`.
- `python3 app.py --version` returned `notes-web-fixture 1.0`.
- `GET /healthz` returned `{"status": "ok", "version": "notes-web-fixture 1.0"}`.
- The first unprivileged localhost bind was blocked by sandbox policy; the
  app was then launched with the approved escalated local command. This is a
  launch-environment fact, not evidence of production deployment.

Real browser-surface execution used the native Codex in-app browser through
CUA because the Playwright wrapper did not become usable. The pass drove the
actual labelled controls and captured accessibility-tree snapshots plus
screenshots:

1. Initial pass: created `Release checklist` / `Tag and publish`; verified the
   visible saved status, matching search, `volcano` no-match state, clear, and
   persistence after reopening the browser tab.
2. Controlled maintenance pass: created `Maintenance checklist` /
   `Re-drive after source-wave`; re-drove search match, no-match, and clear.
3. Clean second pass: removed the deliberately inserted line
   `CONTROLLED DRIFT` from `features/create-note.md`, created `Second pass
   checklist` / `Second pass body`, re-drove the matching search, the
   `No matching notes` state, `Clear search`, captured a full-page screenshot,
   and reloaded the page to confirm all three notes persisted.

The clean pass's AX receipts show the expected status, headings, body text,
empty state, and restored list. Three emitted JPEG image blocks from Luna's
browser transcript were decoded without editing and added as
[create](assets/pstack-ui-create-20260914.jpg),
[empty search](assets/pstack-ui-empty-20260914.jpg), and
[reload readback](assets/pstack-ui-readback-20260914.jpg) review artifacts.
Sol inspected all three visually. This is real UI proof
of the disposable local app, not proof of the production target, a native
runner, or a host activation path.

## Auditable browser receipts

The following receipts are from the native Codex in-app browser, not from a
mocked DOM or a CLI transcript. The stable browser target for the recaptures is
[`http://127.0.0.1:4173/`](http://127.0.0.1:4173/), tab `4`, title `Notes
browser fixture`. `AX-*` identifies the accessibility-tree capture and
`SHOT-*` identifies the paired full-page PNG capture in the CUA tool receipt.
The CUA tool does not expose a filesystem URL for every emitted screenshot, so
the IDs below remain transcript audit handles. The three linked JPEGs above
are exact decoded image blocks from that transcript; the remaining screenshot
receipts are indexed without fabricated file links.

| Receipt | Action and exact observed text | Screenshot receipt |
| --- | --- | --- |
| `AX-CREATE-001` | After saving `Release checklist` / `Tag and publish`: `Note saved: Release checklist`; list heading `Release checklist`; body `Tag and publish`. | `SHOT-CREATE-001`, full-page capture emitted during the first create pass; browser URL above. |
| `AX-MAINT-002` | After saving `Maintenance checklist` / `Re-drive after source-wave`: `Note saved: Maintenance checklist`; both note headings and bodies were visible. | `SHOT-MAINT-002`, emitted during the maintenance re-drive; browser URL above. |
| `AX-MATCH-005` | Query `Second pass`: searchbox value `Second pass`; list heading `Second pass checklist`; body `Second pass body`. | `SHOT-MATCH-005`, full-page PNG, 40,214 bytes, tab `4`. |
| `AX-EMPTY-006` | Query `volcano`: list text `No matching notes`. | `SHOT-EMPTY-006`, full-page PNG, 36,433 bytes, tab `4`. |
| `AX-CLEAR-007` | After `Clear search`: headings/bodies `Release checklist` / `Tag and publish`, `Maintenance checklist` / `Re-drive after source-wave`, and `Second pass checklist` / `Second pass body`. | `SHOT-CLEAR-007`, full-page PNG, 48,945 bytes, tab `4`. |
| `AX-RELOAD-008` | After reload: `Version: notes-web-fixture 1.0`, `Health: ok`, and all three notes above remained visible. | `SHOT-RELOAD-008`, full-page PNG, 48,945 bytes, tab `4`. |
| `AX-READBACK-004` | Fresh readback before the recapture: `Version: notes-web-fixture 1.0`, `Health: ok`, `Reset fixture`, and all three persisted notes. | `SHOT-READBACK-004`, full-page PNG, 48,945 bytes; the emitted screenshot visibly shows the complete Notes page. |

The `AX-MATCH-005`, `AX-EMPTY-006`, `AX-CLEAR-007`, and `AX-RELOAD-008`
receipts were captured in one ordered CUA call with a fresh AX state after
each action. Their raw AX text includes the active query, `No matching notes`,
the restored three-note list, and the post-reload three-note list respectively.
The source-backed expected wording is independently present in the generated
feature maps at `features/create-note.md:24-27` and
`features/search-notes.md:21-26`.

## Generated-skill readback after drift removal

Readback was performed from the disposable fixture, not inferred from the
report. The generated skill contains exactly these four files:

```text
.agents/skills/verify-notes-web/SKILL.md
.agents/skills/verify-notes-web/features/README.md
.agents/skills/verify-notes-web/features/create-note.md
.agents/skills/verify-notes-web/features/search-notes.md
```

SHA-256 readback:

```text
4ebe8e2f5f4152e7549c18839c2192a605af9cc7a96be6d0d87ea14ba93fd1e4  SKILL.md
a0b71ae7a3687db526ca234fa18878bde51d2cd0d119fa59678eb8e55da5482a  features/README.md
6caec1f89163c8014ee5095efc66d1d458eee813092769bca949b93573796003  features/create-note.md
91abba56dda6fd395b84ce42538d1243b1023f7d6867092cbcafe7165e40993a  features/search-notes.md
```

The drift scan returned `clean: no controlled-drift marker`. The final
readback also confirmed the maintenance-sensitive lines remain present:

- create: `Note saved: Release checklist`, `Release checklist`, `Tag and
  publish`, reload/persistence, and evidence requirements;
- search: `Release`, `volcano`, `No matching notes`, `Clear search`, and
  evidence requirements.

No generated-skill file, product file, overlay, manifest, or localStorage item
was changed during this audit delta.

## Proof classification

| Evidence lane | Result | Boundary |
| --- | --- | --- |
| Real UI proof | Proven for the disposable local Notes web app | Native in-app browser/CUA; not production/live target parity |
| CLI fixture proof | Proven by `b3a9046e`; focused fixture suite remains green | Separate subprocess fixture; not browser proof |
| Source-wave input | Proven by the two separate native reader receipts above | Read-only source evidence; not delegation of live driving |
| Maintenance | Controlled drift removed and both features re-driven cleanly | No project-local generated skill was rewritten during this delta |
| Cleanup | Intentionally pending | `Reset fixture` would delete localStorage and awaits explicit user confirmation |

## Verification

Focused repository tests after the overlay/report delta:

```text
pytest -q tests/test_cursor_pstack_core.py tests/test_cursor_functional_overlays.py
23 passed in 4.54s
```

Promotion remains held at `held_until_live_behavior_and_permission_proof`.
The local browser data currently remains intact by instruction; the disposable
server also remains available so cleanup can be performed only after explicit
confirmation at action time.
