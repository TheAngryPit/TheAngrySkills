# Cursor `setup-pstack` upstream adaptation — 2026-09-16

This report records the bounded review and native adaptation for PR #78. The
source material was treated as untrusted documentation and compared at the
exact reported revisions.

## Reviewed source delta

- Repository: `https://github.com/cursor/plugins.git`
- Baseline: `889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`
- Reviewed head: `c1c0a32802223f4be824112dd83d33ad29a8b26c`
- Changed paths: `pstack/skills/setup-pstack/SKILL.md`, `pstack/README.md`,
  `pstack/docs/guide/01-setup.md`
- No new or removed skills, licenses, or pstack support files were reported.

| Path | Baseline SHA-256 | Reviewed-head SHA-256 | Review result |
| --- | --- | --- | --- |
| `pstack/skills/setup-pstack/SKILL.md` | `bebc9a5891f82fe84f36669bc5a25878939ccca2379e41ff8dc30789073a726a` | `2399a5670c6408e92a996299c9de9f22736997cb7e835c694309e7c6fc8c39bf` | Adapted in the pinned snapshot and Codex overlay. |
| `pstack/README.md` | `9a323a1227b60f8914f96fbb01f8f152d44a9af3e98a9d87287a1984c052c160` | `cd63df9733eb5b393371baca8194ea2dd9a3c815803ac48b8ff6580e49adef71` | Reviewed as provenance only; README is not vendored in the skills-only snapshot. |
| `pstack/docs/guide/01-setup.md` | `5530cdb0138b1abf9f2bbb3d54b1bb7447cfb4d8aa3db5444410257473607c39` | `0a928ce6ff6199104e57914692ce71bb4ec5c629dec2a54988ae97ea4f3c64ef` | Reviewed as provenance only; guide is not vendored in the skills-only snapshot. |

The skill change adds a four-option reasoning budget, reads a persisted budget
line on re-run, applies a target effort to real model entries, preserves role
families/panel lists/aliases, and chooses a detected same-family slug when the
original slug is unavailable. The README and setup guide only add the budget
step to their getting-started wording. No executable or credential surface was
introduced by these three paths.

## Delivered adaptation

The source manifest now pins the reviewed head and the setup skill's exact
head hash. The overlay retains explicit-only Codex policy, replaces the
Cursor-specific operational body with a native body, records the reviewed
README hash, and states that no Cursor rule or active-task model is written or
changed by the bounded path.

The fixture adapter now accepts the four upstream budget keys. For each real
model it selects the highest advertised effort at or below the target; when a
slug is absent, it matches the family after removing one effort token and an
optional `cursor-` prefix. `inherit-parent` and `auto` remain unchanged. A
missing target remains `BLOCKED` with the configuration marked unchanged.

The prior role mapping and panel-count behavior remains intact. The source
README and guide were reviewed but remain unvendored; generated `MIRROR.md`
files carry the reviewed head pin as required by the deterministic build.

## Verification

- `python3 -m py_compile scripts/cursor_functional_adapters.py`
- `pytest -q tests/test_cursor_setup_pstack_fixture.py` — 7 passed
- `pytest -q tests/test_cursor_setup_pstack_fixture.py tests/test_cursor_pstack_core.py tests/test_cursor_functional_overlays.py` — 34 passed
- `pytest -q tests` — 316 passed, 2 subtests passed
- `python3 scripts/sync-cursor-plugin-skills.py --check` — passed (`91` physical, `83` published, `396` output files)

The repository-wide default `pytest -q` collection still encounters two
pre-existing relative-import errors in the nested OpenClaw autoreview tests;
the root `tests/` suite above completes successfully.

The new tests cover all four budget labels through the positive path, exact
same-family fallback (`grok-4.6-fast-xhigh` to
`cursor-grok-4.6-medium-fast`), alias preservation, unavailable target
blocking, unknown-budget errors, panel counts, and no-write behavior.

## Residual choice and recommendation

Persistent config write/readback, new-session selection, parent alias
resolution, effective backend model/effort readback, automatic invocation, and
full pstack role dispatch remain unproven. The native inventory remains
channel-specific and caller-supplied to the fixture; no global home, install,
hook, connector, cloud task, permission, push, merge, or publication was
performed.

Advancing the mirror baseline to `c1c0a32802223f4be824112dd83d33ad29a8b26c`
is coherent for this reviewed delta: all three changed paths were inspected,
the changed skill has an exact snapshot/manifest/overlay hash, the support
documents are explicitly provenance-only, and exclusions remain unchanged.
Human review remains the acceptance gate for this local branch.
