#!/usr/bin/env python3
"""Inactive, project-scoped adapters for pinned Cursor Stop/SubagentStop workflows.

These handlers accept the documented Codex hook JSON on stdin. Merely shipping
this file does not register a hook or grant trust to one.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path


class HookInputError(ValueError):
    pass


def _state_path(project: Path, family: str) -> Path:
    return project / ".codex" / "cursor-mirror-state" / family / "state.json"


def _load(path: Path) -> dict | None:
    if path.is_symlink():
        raise HookInputError("hook state must not be a symlink")
    if not path.exists():
        return None
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise HookInputError("hook state must be an object")
    return value


def _save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise HookInputError("hook state must not be a symlink")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=".state-", delete=False
    ) as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def _bound_event(event: dict, project: Path, expected: str) -> bool:
    if event.get("hook_event_name") != expected:
        raise HookInputError(f"expected {expected} event")
    cwd = event.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        raise HookInputError("missing Codex hook cwd")
    return Path(cwd).resolve() == project.resolve()


def _same_session(event: dict, state: dict) -> bool:
    session = event.get("session_id")
    return isinstance(session, str) and bool(session) and session == state.get("session_id")


def _normalized_promise(message: object) -> str | None:
    if not isinstance(message, str):
        return None
    match = re.search(r"<promise>(.*?)</promise>", message, flags=re.DOTALL)
    return " ".join(match.group(1).split()) if match else None


def ralph_stop(event: dict, project: Path) -> dict:
    """Continue one bounded Ralph iteration or close only this session's state."""
    if not _bound_event(event, project, "Stop"):
        return {}
    path = _state_path(project, "ralph")
    state = _load(path)
    if state is None or not _same_session(event, state):
        return {}
    turn_id = event.get("turn_id")
    if not isinstance(turn_id, str) or not turn_id:
        raise HookInputError("missing Codex turn_id")
    if state.get("last_processed_turn_id") == turn_id:
        return {}
    prompt = state.get("prompt")
    iteration = state.get("iteration")
    maximum = state.get("max_iterations")
    promise = state.get("completion_promise")
    if (not isinstance(prompt, str) or not prompt.strip()
            or type(iteration) is not int or iteration < 1
            or type(maximum) is not int or maximum < 0
            or promise is not None and not isinstance(promise, str)):
        path.unlink()
        return {"systemMessage": "Ralph state invalid; stopped this loop."}
    if promise and _normalized_promise(event.get("last_assistant_message")) == " ".join(promise.split()):
        path.unlink()
        return {}
    if maximum and iteration >= maximum:
        path.unlink()
        return {}
    next_iteration = iteration + 1
    state["iteration"] = next_iteration
    state["last_processed_turn_id"] = turn_id
    _save(path, state)
    header = f"[Ralph loop iteration {next_iteration}.]"
    if promise:
        header = (f"[Ralph loop iteration {next_iteration}. To complete: output "
                  f"<promise>{promise}</promise> ONLY when genuinely true.] ")
    return {"decision": "block", "reason": f"{header}\n\n{prompt}"}


def advisor_subagent_stop(event: dict, project: Path) -> dict:
    """Record only an expected advisor result; generic subagents cannot clear pending."""
    if not _bound_event(event, project, "SubagentStop"):
        return {}
    path = _state_path(project, "advisor")
    state = _load(path)
    if state is None or not _same_session(event, state):
        return {}
    agent_id = event.get("agent_id")
    if not isinstance(agent_id, str) or agent_id != state.get("expected_agent_id"):
        return {}
    if agent_id == state.get("last_recorded_agent_id"):
        return {}
    message = event.get("last_assistant_message")
    if not isinstance(message, str) or not re.search(r"^Verdict:\s*(proceed|proceed with changes|stop)\b", message, re.M):
        return {"systemMessage": "Advisor result lacked a verdict; pending work remains."}
    state["consults"] = int(state.get("consults", 0)) + 1
    state["pending"] = False
    state["last_recorded_agent_id"] = agent_id
    state["expected_agent_id"] = None
    state["last_verdict"] = message[:6000]
    _save(path, state)
    return {}


def advisor_stop(event: dict, project: Path) -> dict:
    """Issue at most one pre-completion consult nudge for a pending edit batch."""
    if not _bound_event(event, project, "Stop"):
        return {}
    path = _state_path(project, "advisor")
    state = _load(path)
    if state is None or not _same_session(event, state):
        return {}
    if not state.get("enabled") or not state.get("nudge") or not state.get("pending"):
        return {}
    turn_id = event.get("turn_id")
    if not isinstance(turn_id, str) or not turn_id:
        raise HookInputError("missing Codex turn_id")
    if state.get("last_nudged_turn_id") == turn_id:
        return {}
    message = event.get("last_assistant_message")
    if isinstance(message, str) and message.rstrip().endswith("?"):
        return {}
    state["pending"] = False
    state["last_nudged_turn_id"] = turn_id
    _save(path, state)
    return {
        "decision": "block",
        "reason": ("[Advisor] Files changed since the last consult. If this work is done, "
                   "run a bounded read-only advisor consult under the selected model/effort, "
                   "act on its verdict, and report it. If trivial or waiting on the user, "
                   "say so and stop."),
    }


HANDLERS = {
    "ralph-stop": ralph_stop,
    "advisor-subagent-stop": advisor_subagent_stop,
    "advisor-stop": advisor_stop,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handler", choices=sorted(HANDLERS))
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise HookInputError("hook input must be an object")
        result = HANDLERS[args.handler](event, args.project)
    except (HookInputError, OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"systemMessage": f"Cursor mirror hook skipped: {exc}"}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
