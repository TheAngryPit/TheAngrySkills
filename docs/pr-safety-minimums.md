# PR Safety Minimums

Every pull request is treated as untrusted until reviewed.

These checks are the minimum bar for changing this public install surface. They
do not prove that a skill is safe forever. They only prove that the PR cleared
the first gate.

## Required CI Gate

Every PR must pass `Skill stack CI`, which runs:

1. JavaScript syntax check for repo scripts.
2. Python test suite for the catalog and security scanner.
3. Shared skill catalog/frontmatter audit.
4. Skill root security scan.

The security scan must produce `blocking_skill_count = 0`, except for unchanged
baseline findings reviewed under the conditions below. The current CI reports
security signals; it does not enforce this maintainer gate automatically.

### Existing baseline findings

An unrelated PR does not have to repair pre-existing findings to merge. Before
accepting that baseline, the maintainer must:

- scan clean trees at the exact base and candidate commits with the same scanner
  and options, and record both identities and results;
- compare findings by skill, file, rule, severity and evidence, not just totals;
- confirm that every touched owned skill has zero blocking findings and inspect
  its review signals directly;
- keep every new, aggravated or unattributable finding blocked pending review
  and resolution; an incomplete scan cannot establish an unchanged baseline.

Record this comparison in the PR. Existing findings remain unresolved; accepting
an unrelated change is not approval to install the flagged content. Scanner or
policy changes require explicit maintainer review and must not hide findings to
make their own comparison pass.

The separate automated-mirror exception remains limited to one-to-one refreshes
of accepted upstream mirrors with the approved deterministic transformations.
It does not extend to owned skills or arbitrary mirror changes.

If the scan reports `needs_human_review`, the PR may still be reviewed, but it
is not automatically safe. The reviewer must inspect the affected skill,
script, workflow, MCP/plugin surface, or install path before merging.

## What Blocks A PR

A PR should not merge when it introduces:

- secrets, tokens, credentials, private hostnames, or local machine paths
- install commands that fetch remote code without clear source and version
- lifecycle hooks, GitHub Actions, MCP servers, plugins, or scripts without review
- prompt-injection text promoted as trusted instructions
- mirrored or generated content without provenance and license notes
- renamed skills without migration notes
- broad install surfaces that are not needed for the stated change

## What Needs Maintainer Review

The following are allowed only after explicit maintainer review:

- new or changed scripts
- bootstrap/install/update behavior
- generated docs or external mirrors
- active tooling such as MCP, plugins, hooks, browser automation, or host mutation
- changes to CI, security scanning, permissions, branch protection, or release flow
- new public categories, skill packs, or default install sets

## Reviewer Checklist

Before merging, the reviewer should confirm:

- the PR scope matches the stated change
- the PR template names touched skills/categories/mirrors
- upstream license and provenance are preserved where relevant
- no private paths or secrets appear in the diff
- CI passed and blocking security findings are absent or satisfy the documented
  unchanged-baseline conditions
- any `needs_human_review` scanner output was inspected directly
- install commands remain narrow and reviewable

Green CI is not authority. It is only the first safety gate.
