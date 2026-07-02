# Output Paths

Use the owning project's configured paths. Typical Echo paths are:

```text
ARCHIVE/raw/echo-ingest-knowledge/
ARCHIVE/processed/echo-ingest-knowledge/
OUTPUTS/local/
OUTPUTS/committed/
WORKFLOWS/echo-ingest-knowledge/
```

General rules:

- Raw source artifacts go under raw or equivalent local-only source storage.
- Normalized extracts and manifests go under processed or equivalent derived storage.
- Review cockpits and temporary HTML surfaces go under local outputs.
- Durable workflow config belongs under the workflow directory.
- Committed outputs must be privacy-safe and review-approved.

Do not track raw archives, full transcripts, private media, or local-only review
bulk unless the operator explicitly approves.
