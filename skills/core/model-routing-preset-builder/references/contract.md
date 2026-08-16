# Preset Contract

Presets use TOML and `schema_version = 3`. Top-level fields identify the preset;
`policy` defines operator gates and Fleet capacity; `profiles.<name>` defines
stable orchestration defaults; `roles.<name>` defines default compute and proof
for a functional role; and `routes.<name>` defines topology and lifecycle.
Optional `capabilities.<name>` entries define required skill names and a gate.

Effort values are technical config values. Write `Light` in explanatory prose
and `low` in TOML. Treat model identifiers as runtime-specific strings whose
availability must be proven at routing time.

Role and compute are independent. Role TOML should normally omit `model` and
`model_reasoning_effort`; explicit route selection or the runtime default then
applies. A pinned role file is valid only when its pins match the selected route.
Proof-bearing roles such as planner, reviewer, auditor, and release checker
should set `compute_override_allowed = false` unless the preset defines an
equally strong explicit constraint. A user override must not downgrade compute
while retaining the stronger proof requirement.

Every native task is a user-owned platform peer. Record whether it is logically
a `delegated_subtask` with a parent or an `independent_parallel_task` without
one. Never infer logical independence from the platform peer relationship.
Fleet ceilings are not runtime availability. A resolver must fail closed
without live capacity and active-child evidence. A field Fleet additionally
requires an existing verified coordinator and capability evidence collected in
that coordinator, not inherited from the master.
The preset must bound `coordinator_receipt_max_age_seconds`; callers may tighten
but never enlarge that window. Receipt claims remain structured attestation,
not independent proof.
