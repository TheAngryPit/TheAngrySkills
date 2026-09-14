"""Read-only fixture for separating native profile proof from live execution."""

from __future__ import annotations

import hashlib
import re
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path


PROFILE_NAMES = ("comment-sicko", "poteto-agent")
SELECTOR_FIELDS = ("agent_type", "agent_profile", "profile", "subagent_type")
SKILL_REFERENCE_PATTERN = re.compile(r"`(cursor-[a-z0-9*-]+)`")


def _error(reason: str, details: Iterable[str] = ()) -> dict[str, object]:
    detail_lines = tuple(details)
    return {
        "status": "ERROR",
        "fixture_only": True,
        "writes_performed": False,
        "session_created": False,
        "configuration_changed": False,
        "reason": reason,
        "details": detail_lines,
        "report": "PROFILE-FIXTURE ERROR: "
        + reason
        + ("\n" + "\n".join(detail_lines) if detail_lines else ""),
    }


def _read_profile(profile_root: Path, name: str) -> dict[str, object]:
    path = profile_root / f"{name}.toml"
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing or symlinked profile: {path}")
    parsed = tomllib.loads(path.read_text())
    if set(parsed) != {"name", "description", "developer_instructions"}:
        raise ValueError(f"{name}: unexpected TOML keys: {sorted(parsed)}")
    if parsed["name"] != name:
        raise ValueError(f"{name}: TOML name does not match requested profile")
    if not all(
        isinstance(parsed[key], str) and parsed[key].strip() for key in parsed
    ):
        raise ValueError(f"{name}: profile fields must be non-empty strings")
    instructions = parsed["developer_instructions"]
    return {
        "name": name,
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "instruction_sha256": hashlib.sha256(instructions.encode()).hexdigest(),
        "skill_references": tuple(
            sorted(set(SKILL_REFERENCE_PATTERN.findall(instructions)))
        ),
        "static_toml_load": "PASS",
        "session_instruction_load": "NOT_OBSERVED",
    }


def run_native_agent_profile_fixture(
    profile_root: str | Path,
    observed_surface: Mapping[str, Iterable[str]],
    *,
    synthetic_input: str = "NATIVE_PROFILE_SYNTHETIC_INPUT_V1",
) -> dict[str, object]:
    """Produce a local proof record without selecting or running an agent.

    ``observed_surface`` must be captured from the actual native interface by
    the caller.  The fixture only checks whether a named-agent selector is
    present; it does not invent or call one.
    """

    if not isinstance(observed_surface, Mapping):
        return _error("observed native surface must be a tool-to-fields mapping")
    if not isinstance(synthetic_input, str) or not synthetic_input.strip():
        return _error("synthetic input must be a non-empty string")

    try:
        surface: dict[str, tuple[str, ...]] = {}
        for tool, fields in observed_surface.items():
            if not isinstance(tool, str) or not tool.strip():
                raise ValueError("native surface tool names must be non-empty strings")
            if isinstance(fields, (str, bytes)):
                raise ValueError(f"native surface fields for {tool!r} must be iterable")
            normalized = tuple(fields)
            if any(
                not isinstance(field, str) or not field.strip()
                for field in normalized
            ):
                raise ValueError(f"native surface fields for {tool!r} must be strings")
            surface[tool] = normalized
        profiles = tuple(
            _read_profile(Path(profile_root), name) for name in PROFILE_NAMES
        )
    except (OSError, TypeError, ValueError, tomllib.TOMLDecodeError) as error:
        return _error(str(error))

    exposed_selectors = tuple(
        field
        for field in SELECTOR_FIELDS
        if any(field in fields for fields in surface.values())
    )
    if exposed_selectors:
        discovery_status = "EXPOSED_NOT_RUN"
        selection = {
            "status": "NOT_ATTEMPTED",
            "reason": "selector exists in the supplied surface, but this fixture never invokes it",
        }
    else:
        discovery_status = "NOT_EXPOSED"
        selection = {
            "status": "NOT_ATTEMPTED",
            "reason": "no named-agent selector is present in the supplied native surface",
        }

    returns = tuple(
        {
            "profile_name": profile["name"],
            "synthetic_input": synthetic_input,
            "instruction_sha256": profile["instruction_sha256"],
            "observed_by": "local fixture",
        }
        for profile in profiles
    )
    lines = [
        "PROFILE-FIXTURE static proof only (no native selection or session)",
        f"1 discovery: {discovery_status}; selectors={exposed_selectors or 'none'}",
        f"2 nominal selection: {selection['status']}",
        "3 instructions: "
        + ", ".join(
            f"{profile['name']}={profile['static_toml_load']}"
            for profile in profiles
        ),
        f"4 synthetic execution: FIXTURE_ONLY; input={synthetic_input}",
        f"5 return: {len(returns)} local fixture result(s) observed",
        "6 limits: skills_invoked=none; host=local fixture; session_created=false",
    ]
    return {
        "status": "STATIC_PROOF_ONLY",
        "fixture_only": True,
        "writes_performed": False,
        "session_created": False,
        "configuration_changed": False,
        "discovery": {
            "status": discovery_status,
            "selector_fields_checked": SELECTOR_FIELDS,
            "exposed_selectors": exposed_selectors,
            "observed_surface": surface,
        },
        "nominal_selection": selection,
        "instructions": profiles,
        "execution": {
            "status": "FIXTURE_ONLY",
            "input": synthetic_input,
            "returns": returns,
        },
        "limits": {
            "skills_invoked": (),
            "host": "local fixture",
            "session_created": False,
            "live_agent_type": "NOT_PROVEN",
            "live_return": "NOT_PROVEN",
        },
        "report": "\n".join(lines),
    }
