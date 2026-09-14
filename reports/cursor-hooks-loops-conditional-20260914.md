# Conditional proof: advisor, continual learning, and Ralph hooks

Date: 2026-09-14  
Scope: `cursor-advisor`, `cursor-continual-learning`, `cursor-ralph-loop`, and `cursor-cancel-ralph`  
Upstream pin: `cursor/plugins@889ec4b68fa5aab0e867dad71ec3fdf386ae48f3`

## Decision

All four overlays remain `publish: false` and `promotion_status: held`. The
fixtures below prove bounded project-local state transitions and degraded
behavior. They do not prove that a Codex project hook is installed, trusted,
or invoked automatically, so publishing or indexing these workflows would
overstate parity.

The existing `scripts/cursor_native_hook_adapters.py` is the implementation
under test. `scripts/cursor_hooks_loops_adapters.py` is a disposable harness
that builds only synthetic events and fixture state. It does not register a
hook, launch a scheduler, read a real transcript, call a model, use a
credential, or write outside the project supplied by each test.

## Source inventory and preserved behavior

| Overlay | Pinned source | Source behavior | Conditional boundary |
| --- | --- | --- | --- |
| `cursor-advisor` | `advisor/skills/advisor/SKILL.md`; `advisor/agents/advisor-subagent.md`; `advisor/hooks/*.sh`; `advisor/hooks/hooks.json`; `advisor/skills/advisor/references/briefing-template.md` | Explicit advisor enable/disable/status and model selection; pending edits; expected advisor subagent; verdict recording; one pre-completion nudge | Native model/effort selection, trusted hook, live named advisor consult, and role/verdict correlation remain unproven |
| `cursor-continual-learning` | `continual-learning/skills/continual-learning/SKILL.md`; `continual-learning/agents/agents-memory-updater.md`; `continual-learning/hooks/continual-learning-stop.ts`; `continual-learning/hooks/hooks.json` | Parent delegates transcript mining and `AGENTS.md` updates; stop threshold uses turn count, elapsed time, transcript mtime, and duplicate generation guard | Real scoped transcript, live native delegate, authorized `AGENTS.md` diff, and trusted automatic hook remain unproven |
| `cursor-ralph-loop` | `ralph-loop/skills/ralph-loop/SKILL.md`; `ralph-loop/hooks/capture-response.sh`; `ralph-loop/hooks/stop-hook.sh`; `ralph-loop/hooks/hooks.json` | Explicit prompt, completion promise, max iterations, project-local state, and continuation after Stop | Trusted project Stop hook, live continuation, scheduler, interruption, and completion readback remain unproven |
| `cursor-cancel-ralph` | `ralph-loop/skills/cancel-ralph/SKILL.md`; shared Ralph hooks and state | Cancel an active loop and report its iteration | Live task/session state and hook readback remain unproven; fixture never uses recursive deletion |

The source text is preserved in the snapshot. The Codex overlays already
record the pinned source hashes, native mapping, fallback, security verdict,
and `held` promotion state. This batch does not alter the manifest, generator,
marketplace, or shared catalog.

## Fixture proof

`tests/test_cursor_hooks_loops_adapters.py` runs six local tests:

1. Advisor: explicit enable, `apply_patch` edit sensor, one-time Stop nudge,
   expected advisor registration, and accepted verdict.
2. Advisor degraded path: another session is ignored and an invalid verdict
   returns a diagnostic while pending work remains.
3. Ralph: task-bound arm, two distinct Stop iterations, exact completion
   promise cleanup, and idempotent post-completion cancel.
4. Ralph degraded path: another session cannot continue or cancel the loop;
   matching cancel removes only the state and a second cancel is inactive.
5. Continual learning: a one-turn threshold triggers only for a transcript
   inside the explicitly armed fixture root.
6. Continual learning degraded path: an out-of-scope transcript is ignored
   and is not created as a side effect.

The tests assert the adapter's actual result values, including
`BOUND_HOOK_TRUST_UNVERIFIED`, `ARMED_HOOK_TRUST_UNVERIFIED`, `OTHER_SESSION`,
`INACTIVE`, and the bounded `decision: block` responses. Repeated Ralph events
with the same turn id are idempotently ignored by the underlying adapter.

## Security and operational boundaries

The manifest's baseline security verdict for all four entries is
`safe_docs_only`, with the finding retained. The fixture adds no permission
or trust: before calling the adapter it rejects lexical symlink components in
the supplied project and transcript root. The underlying adapter additionally
validates its state descendants, absolute transcript root, exact turn ids,
and wrong-session no-op behavior. The symlink guarantee belongs to this
fixture boundary and is not a claim about a live host. No hooks are installed,
no global Cursor or Codex state is touched, no process is started or killed,
and no external network or secret is used.

## Remaining promotion evidence

Promotion requires a separately authorized disposable-host exercise that
records the actual selected native model/effort where relevant, verifies the
exact project hook hash and trust, observes a live bounded Stop/SubagentStop
event, and captures cancellation or updater readback. Continual learning also
needs an explicitly authorized transcript path and a before/after `AGENTS.md`
diff. Synthetic payloads and fixture state alone must remain conditional.
