# Selected ClawHub skills

`config/clawhub-skills.json` records the owned publisher, public source paths,
ClawHub slugs, and explicit catalog categories for the selected skill releases.
These browse labels supplement the repository's Core/Engineering organization;
they do not rename installed skills or replace the install catalog.

Publish the exact reviewed Git commit, using canonical Git file bytes rather
than platform checkout newline conversions. Pass each entry's `categories` as
the comma-separated `--categories` value and retain `--source-repo`,
`--source-commit`, `--source-ref`, and `--source-path` provenance. The manifest is
reviewable metadata; the ClawHub website does not automatically consume it.

The `openclaw-` URL prefix is reserved by ClawHub. The validation skill therefore
uses `custom-build-validation` there, while its installed skill name and source
directory remain `openclaw-custom-build-validation`.

For category-only edits, use the owned skill's Catalog metadata settings and
verify persistence after reloading. For a new release, pass the categories
explicitly so pending-release promotion cannot restore the original empty
classification. Do not republish unchanged files merely to retry a pending scan.

`existingExternalListings` records category choices for owned ClawHub listings
whose source is not exported from this repository. It does not import those
files or authorize publishing private Workbench content.

## Security review follow-through

The 1.0.0 ClawHub reviews identified two concrete source problems:

- The Aegis ledger and structured execution skills required an iCloud copy of
  project records without a destination/content grant or a local-only path.
  Local ledgers are now sufficient; a cloud copy requires authorization for
  the project, account/folder, and content scope. Existing valid authorization
  remains reusable. Credentials, private conversations, personal records, and
  restricted project content are excluded from implied transfers.
- The docs generator preserved source symlinks and then wrote its index
  through one of those links. It also followed a symlinked output parent while
  replacing a generated tree. Generation now rejects these links and escaping
  paths, preserves upstream reserved filenames under a `.source` name, and
  makes GitHub publication dependent on the operator's destination, visibility,
  and exact-file authorization.
- The subsequent 1.0.1 scan identified newline-containing source filenames
  splitting into separate copy inputs, allowing an unrelated local file to be
  included. A fourth actual-generator regression reproduced that leak. Source
  names containing TSV control characters are now refused before output changes;
  enumeration uses NUL delimiters and every copy input must belong to the source
  root.
- The 1.0.2 scan then identified metadata inserted directly into Bash source.
  Tool-name command substitution and URL quote breakouts were reproduced with
  harmless temporary marker files. The scaffold now quotes constants with
  `shlex.quote` in one substitution pass; generated Markdown is rendered as data
  with a separately JSON-quoted YAML description. Regressions verify neither
  metadata field executes commands and that punctuation, Unicode, literal
  placeholder text and documentation paths still round-trip.

The offline generator regressions exercise the actual scaffold and generator:
ordinary document bytes and upstream index preservation, an external-file
sentinel behind a source-index symlink, and an external-directory sentinel
behind a symlinked output parent. They failed against the old Git blobs and
passed against the corrected source.
The additional newline-path case failed against 1.0.1 while the earlier three
passed; all four pass after the follow-up repair. Run them on POSIX with:

```bash
python3 tests/test_docs_skill_builder_security.py
```

The fixture uses only temporary synthetic files and a local Git repository;
it fetches no documentation and performs no installation or publication.
Windows skips these tests because they require POSIX symlink semantics.

A scanner failure with no verdict is an incomplete scan, not a demonstrated
skill defect. Keep it distinct from an actionable review finding. Upload,
security approval, public version availability, and install verification are
separate results; never label a pending submission approved.
