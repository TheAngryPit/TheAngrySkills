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
import shlex
import sys
import tempfile
import time
from pathlib import Path


class HookInputError(ValueError):
    pass


def _state_path(project: Path, family: str) -> Path:
    for parent in (project / ".codex", project / ".codex" / "cursor-mirror-state",
                   project / ".codex" / "cursor-mirror-state" / family):
        if parent.is_symlink():
            raise HookInputError("hook state directory must not be a symlink")
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


def ralph_start(project: Path, session_id: str, prompt: str,
                maximum: int, promise: str | None) -> dict:
    """Arm a task-bound local loop; native project hook trust is still required."""
    if not project.is_dir() or not session_id or not prompt.strip() or maximum < 0:
        raise HookInputError("project, session, prompt, and nonnegative max are required")
    path = _state_path(project, "ralph")
    existing = _load(path)
    if existing is not None:
        raise HookInputError("Ralph loop already active; cancel it before starting another")
    _save(path, {
        "session_id": session_id,
        "prompt": prompt,
        "iteration": 1,
        "max_iterations": maximum,
        "completion_promise": promise,
    })
    return {"status": "ARMED_NOT_ACTIVE_UNTIL_HOOK_TRUSTED", "iteration": 1}


def ralph_cancel(project: Path, session_id: str) -> dict:
    """Cancel only the caller's loop state; never delete another task's state."""
    path = _state_path(project, "ralph")
    state = _load(path)
    if state is None:
        return {"status": "INACTIVE"}
    if not session_id or state.get("session_id") != session_id:
        return {"status": "OTHER_SESSION"}
    path.unlink()
    return {"status": "CANCELLED"}


def ralph_config(project: Path) -> dict:
    """Return an inactive project-hook fragment for review and exact-hash trust."""
    if not project.is_dir():
        raise HookInputError("project directory is missing")
    script = Path(__file__).resolve()
    command = (f"python3 {shlex.quote(str(script))} ralph-stop "
               f"--project {shlex.quote(str(project.resolve()))}")
    return {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": command}]}]}}


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
    if event.get("agent_type") != "advisor-subagent":
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


def advisor_post_tool_use(event: dict, project: Path) -> dict:
    """Mark a successful, known patch as pending for this task only.

    Bash and arbitrary MCP commands cannot be inferred to have edited a file
    from their names or output. They require a separate, proved change sensor.
    """
    if not _bound_event(event, project, "PostToolUse"):
        return {}
    if event.get("tool_name") != "apply_patch":
        return {}
    path = _state_path(project, "advisor")
    state = _load(path)
    if state is None or not _same_session(event, state) or not state.get("enabled"):
        return {}
    tool_use_id = event.get("tool_use_id")
    if not isinstance(tool_use_id, str) or not tool_use_id:
        raise HookInputError("missing Codex tool_use_id")
    if state.get("last_edit_tool_use_id") == tool_use_id:
        return {}
    response = event.get("tool_response")
    if isinstance(response, dict) and (
        response.get("isError") is True or response.get("exit_code") not in (None, 0)
    ):
        return {}
    state["pending"] = True
    state["last_edit_tool_use_id"] = tool_use_id
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


def continual_learning_stop(event: dict, project: Path) -> dict:
    """Evaluate pinned turn/time/mtime thresholds without reading transcripts."""
    if not _bound_event(event, project, "Stop"):
        return {}
    path = _state_path(project, "continual-learning")
    state = _load(path)
    if state is None or not _same_session(event, state) or not state.get("enabled"):
        return {}
    turn_id = event.get("turn_id")
    if not isinstance(turn_id, str) or not turn_id:
        raise HookInputError("missing Codex turn_id")
    if state.get("last_processed_turn_id") == turn_id or event.get("stop_hook_active") is True:
        return {}
    root_value = state.get("transcript_root")
    transcript_value = event.get("transcript_path")
    if not isinstance(root_value, str) or not Path(root_value).is_absolute():
        raise HookInputError("continual-learning needs an absolute transcript root")
    root = Path(root_value).resolve()
    transcript_mtime = None
    if isinstance(transcript_value, str) and transcript_value:
        transcript = Path(transcript_value)
        if (transcript.is_absolute() and not transcript.is_symlink()
                and transcript.resolve().is_relative_to(root) and transcript.is_file()):
            transcript_mtime = transcript.stat().st_mtime_ns // 1_000_000
    now = time.time_ns() // 1_000_000
    turns = state.get("turns_since_last_run", 0)
    last_run = state.get("last_run_at_ms", 0)
    last_mtime = state.get("last_transcript_mtime_ms")
    if (type(turns) is not int or turns < 0 or type(last_run) is not int or last_run < 0
            or last_mtime is not None and (type(last_mtime) is not int or last_mtime < 0)):
        raise HookInputError("invalid continual-learning counters")
    trial = state.get("trial", {})
    if not isinstance(trial, dict):
        raise HookInputError("invalid continual-learning trial settings")
    trial_started = state.get("trial_started_at_ms")
    if trial.get("enabled") and trial_started is None:
        trial_started = now
        state["trial_started_at_ms"] = now
    in_trial = (trial.get("enabled") is True and type(trial_started) is int
                and now - trial_started < 60_000 * 1440)
    minimum_turns = 3 if in_trial else 10
    minimum_minutes = 15 if in_trial else 120
    state["last_processed_turn_id"] = turn_id
    state["turns_since_last_run"] = turns + 1
    advanced = transcript_mtime is not None and (
        last_mtime is None or transcript_mtime > last_mtime
    )
    elapsed = last_run == 0 or now - last_run >= minimum_minutes * 60_000
    if state["turns_since_last_run"] >= minimum_turns and elapsed and advanced:
        state["last_run_at_ms"] = now
        state["turns_since_last_run"] = 0
        state["last_transcript_mtime_ms"] = transcript_mtime
        _save(path, state)
        return {
            "decision": "block",
            "reason": ("Run `cursor-continual-learning` with a bounded native memory-updater "
                       "only if that held skill and role are available in this project. "
                       "Consider only transcripts not indexed or with newer mtime, "
                       "exclude secrets and transient details, and edit AGENTS.md only "
                       "within the operator's authorized scope. Otherwise report the "
                       "exact capability gap and stop."),
        }
    _save(path, state)
    return {}


HOOK_HANDLERS = {
    "ralph-stop": ralph_stop,
    "advisor-post-tool-use": advisor_post_tool_use,
    "advisor-subagent-stop": advisor_subagent_stop,
    "advisor-stop": advisor_stop,
    "continual-learning-stop": continual_learning_stop,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handler", choices=sorted((*HOOK_HANDLERS, "ralph-start", "ralph-cancel", "render-ralph-config")))
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--session-id")
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--max-iterations", type=int, default=0)
    parser.add_argument("--completion-promise")
    args = parser.parse_args()
    try:
        if args.handler in HOOK_HANDLERS:
            event = json.load(sys.stdin)
            if not isinstance(event, dict):
                raise HookInputError("hook input must be an object")
            result = HOOK_HANDLERS[args.handler](event, args.project)
        elif args.handler == "ralph-start":
            if args.prompt_file is None or args.session_id is None:
                raise HookInputError("ralph-start requires --prompt-file and --session-id")
            result = ralph_start(args.project, args.session_id,
                                 args.prompt_file.read_text(), args.max_iterations,
                                 args.completion_promise)
        elif args.handler == "ralph-cancel":
            result = ralph_cancel(args.project, args.session_id or "")
        else:
            result = ralph_config(args.project)
    except (HookInputError, OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"systemMessage": f"Cursor mirror hook skipped: {exc}"}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
