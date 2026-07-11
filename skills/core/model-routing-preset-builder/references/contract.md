# Preset Contract

Presets use TOML and `schema_version = 1`. Top-level fields identify the preset;
`policy` defines global gates; `routes.<name>` defines model, effort, role,
fallback, and proof; optional `capabilities.<name>` entries define required
skill names and a gate.

Effort values are technical config values. Write `Light` in explanatory prose
and `low` in TOML. Treat model identifiers as runtime-specific strings whose
availability must be proven at routing time.
