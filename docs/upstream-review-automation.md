# Matt and Cursor pstack upstream review automation

The `Review Matt and Cursor pstack upstreams` workflow runs on its schedule or
through `workflow_dispatch`. It checks the reviewed Matt adaptations, including
`writing-for-astra`, and the Cursor `pstack` plugin against their accepted
revisions. It creates or updates one review-only pull request for each changed
family and batch:

- `matt / adapted`
- `cursor / pstack`

The detector records source skill changes, supporting-file and license changes,
new or removed skills, and plugin-level support inventory drift. It scopes the
Cursor lane to `pstack`; the existing Emil/OpenClaw adapted-upstream workflow
continues to own those families.

The pull request contains a stable family/batch marker and the observed source
commit. Its only repository artifact is the detector evidence under
`reports/upstream-updates/`. The workflow never rewrites snapshots, overlays,
generated skills, manifests, catalogs, installed homes, accepted hashes or
baselines. It never merges or force-pushes. A diverged review branch or more
than one open PR with the same marker fails closed.

The bounded handoff included in each report and PR is:

```text
@codex update Review only the reported <family> / <batch> upstream delta at <source-head>. Preserve the repository's pins, exclusions, provenance, patches, hashes, global installs and homes. Propose or implement only bounded adaptation changes supported by the PR evidence. Do not publish new skills, accept a baseline, install anything, merge, force-push, or broaden scope. Leave the branch reviewable and report changed files and checks.
```

Posting this prompt is a human review action after the PR comment is visibly
available. The resulting task, changed files, branch SHA and checks must be
recorded before a human accepts any adaptation or advances a baseline.

For deterministic offline checks, point the detector at local git fixtures:

```sh
python scripts/detect-upstream-updates.py \
  --family matt \
  --family cursor \
  --upstream matt=/path/to/matt-checkout \
  --upstream cursor=/path/to/cursor-plugins-checkout \
  --report-dir /tmp/upstream-reports
```

Exit status `0` means no relevant drift, `1` means one or more review reports
were written, and higher statuses indicate an operational failure.
