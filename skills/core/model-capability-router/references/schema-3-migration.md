# Schema 2 to Schema 3 Migration

Schema 3 changes the route vocabulary and the authority model. Updating only
the preset or only the resolver creates an incompatible installation. Treat the
router directory, bundled preset, role assets, caller wording, and optional
external preset mirror as one release unit.

## Preflight

1. Reconcile the target Codex home and installed skill paths read-only.
2. Record hashes of the installed router, role assets, routing caller, and
   external preset mirror. Preserve their exact contents for rollback.
3. Inventory current `current_task`, `spawn_agent`, and `create_thread` model
   metadata and native controls. Do not infer support from UI badges.
4. Validate the staged schema 3 bundled preset with the staged resolver and run
   the full router tests before changing the target.
   Also bind the exact legacy and target hashes with:

   ```bash
   python3 scripts/route.py migration-preflight \
     --legacy-preset <installed-v2.toml> \
     --target-preset assets/vitor-opinionated.toml
   ```

   Continue only on `preflight_ready`; this is still not installation proof.
5. Stop if the target has local edits, an unexpected source, or an automation
   lock that cannot be reconciled.

## Staged Cutover

1. Stage the complete new router directory and updated caller in temporary
   sibling paths on the target filesystem.
2. Validate the staged resolver against its bundled preset from those paths.
3. Acquire the installation automation's normal lock or pause its writer.
4. Replace the router directory as one directory-level operation. Update the
   external preset mirror immediately afterward from the bundled preset; never
   author the mirror independently.
5. Replace the caller only after the new router and matching mirror validate.
6. Release the lock only after postflight succeeds. On any failure, restore all
   captured components rather than leaving a mixed schema installation.

The brief filesystem sequence is not permission to run concurrent routing.
The installation lock defines the maintenance window.

## Postflight

Validate all of these on the real target:

- bundled and external preset hashes match;
- schema 3 validation succeeds;
- native routing resolves without a gstack installation;
- explicit gstack mode blocks without gstack and resolves with its required
  phase artifacts when gstack is installed;
- planner resolves to Sol High;
- direct Fleet uses fresh runtime capacity and active-child evidence;
- field Fleet blocks until an existing verified Terra coordinator supplies its
  own model, tool, and capacity evidence;
- task creation, Max, and Ultra still stop at their current-user gates;
- fork and handoff remain excluded from model routing.

Classify this as `runtime_proven` only after the installed paths produce these
fresh results. Repository tests alone are `test_proven`.

## Rollback

Restore the captured router directory, caller, role assets, and external preset
as the same release unit, then rerun the previous resolver's validation. Never
roll back only the preset across a schema boundary.
