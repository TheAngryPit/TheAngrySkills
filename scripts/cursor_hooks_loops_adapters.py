#!/usr/bin/env python3
"""Disposable, project-local fixtures for the held hook and loop overlays.

The upstream advisor, continual-learning, and Ralph skills are driven by
Cursor hooks.  This module exercises the already bounded native adapter with
synthetic events in a temporary project.  It never registers a hook, starts a
process, reads a real transcript, or writes outside the supplied project.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from cursor_native_hook_adapters import (
    advisor_enable,
    advisor_expect,
    advisor_post_tool_use,
    advisor_stop,
    advisor_subagent_stop,
    continual_learning_stop,
    ralph_cancel,
    ralph_start,
    ralph_stop,
)


class FixtureError(ValueError):
    """Raised when a fixture would escape its disposable project boundary."""


def _event(project: Path, session_id: str, event_name: str, **fields: Any) -> dict[str, Any]:
    return {
        "hook_event_name": event_name,
        "cwd": str(project.resolve()),
        "session_id": session_id,
        **fields,
    }


class HooksLoopsFixture:
    """Small in-process harness for positive and degraded contract cases."""

    def __init__(self, project: Path, session_id: str = "fixture-session") -> None:
        project = project.resolve()
        if not project.is_dir():
            raise FixtureError("fixture project must already exist")
        if not session_id or any(char.isspace() for char in session_id):
            raise FixtureError("fixture session must be a single non-empty token")
        self.project = project
        self.session_id = session_id

    def enable_advisor(self, model: str = "gpt-5.6-luna") -> dict[str, Any]:
        return advisor_enable(self.project, self.session_id, model)

    def mark_advisor_edit(self, tool_use_id: str = "fixture-edit") -> dict[str, Any]:
        return advisor_post_tool_use(
            _event(
                self.project,
                self.session_id,
                "PostToolUse",
                tool_name="apply_patch",
                tool_use_id=tool_use_id,
                tool_response={"exit_code": 0},
            ),
            self.project,
        )

    def expect_advisor(self, agent_id: str = "fixture-advisor") -> dict[str, Any]:
        return advisor_expect(self.project, self.session_id, agent_id)

    def complete_advisor(
        self,
        agent_id: str = "fixture-advisor",
        verdict: str = "proceed",
    ) -> dict[str, Any]:
        return advisor_subagent_stop(
            _event(
                self.project,
                self.session_id,
                "SubagentStop",
                agent_id=agent_id,
                agent_type="advisor-subagent",
                last_assistant_message=f"Verdict: {verdict}\nFixture result.",
            ),
            self.project,
        )

    def advisor_nudge(self, turn_id: str = "fixture-turn") -> dict[str, Any]:
        return advisor_stop(
            _event(
                self.project,
                self.session_id,
                "Stop",
                turn_id=turn_id,
                last_assistant_message="Finished the bounded fixture.",
            ),
            self.project,
        )

    def arm_ralph(
        self,
        prompt: str = "Improve the fixture.",
        max_iterations: int = 2,
        completion_promise: str | None = "DONE",
    ) -> dict[str, Any]:
        return ralph_start(
            self.project,
            self.session_id,
            prompt,
            max_iterations,
            completion_promise,
        )

    def ralph_iteration(
        self,
        turn_id: str = "fixture-turn-1",
        message: str = "Still working.",
    ) -> dict[str, Any]:
        return ralph_stop(
            _event(
                self.project,
                self.session_id,
                "Stop",
                turn_id=turn_id,
                last_assistant_message=message,
            ),
            self.project,
        )

    def cancel_ralph(self) -> dict[str, Any]:
        return ralph_cancel(self.project, self.session_id)

    def arm_continual_learning(
        self,
        transcript_root: Path,
        *,
        turns_since_last_run: int = 0,
        last_run_at_ms: int = 0,
        last_transcript_mtime_ms: int | None = None,
    ) -> Path:
        """Arm only fixture state; no transcript is read by the adapter."""

        transcript_root = transcript_root.resolve()
        if not transcript_root.is_dir():
            raise FixtureError("transcript root must already exist")
        if turns_since_last_run < 0 or last_run_at_ms < 0:
            raise FixtureError("fixture counters must be non-negative")
        state_path = (
            self.project
            / ".codex"
            / "cursor-mirror-state"
            / "continual-learning"
            / "state.json"
        )
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(
                {
                    "enabled": True,
                    "session_id": self.session_id,
                    "turns_since_last_run": turns_since_last_run,
                    "last_run_at_ms": last_run_at_ms,
                    "last_transcript_mtime_ms": last_transcript_mtime_ms,
                    "transcript_root": str(transcript_root),
                    "trial": {},
                },
                sort_keys=True,
            )
            + "\n"
        )
        return state_path

    def continual_learning_stop(
        self,
        transcript: Path | None,
        turn_id: str = "fixture-turn-1",
    ) -> dict[str, Any]:
        return continual_learning_stop(
            _event(
                self.project,
                self.session_id,
                "Stop",
                turn_id=turn_id,
                transcript_path=str(transcript.resolve()) if transcript else None,
                stop_hook_active=False,
            ),
            self.project,
        )


def disposable_project() -> tempfile.TemporaryDirectory[str]:
    """Return a caller-owned temporary project context for tests."""

    return tempfile.TemporaryDirectory(prefix="cursor-hooks-loops-")

