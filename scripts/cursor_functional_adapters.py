"""Small, local proof harnesses for promoted Cursor mirror boundaries.

These helpers do not activate Cursor, cloud, connector, or marketplace
surfaces. They exercise isolated playbook and verification fixtures while
keeping missing capabilities and failed proof states explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


class AdapterError(ValueError):
    """The bounded adapter input or proof state is invalid."""


class MissingCapability(AdapterError):
    """A required optional capability is not available."""


class PermissionDenied(AdapterError):
    """The requested operation exceeds the read-only adapter boundary."""


@dataclass(frozen=True)
class CapabilityResult:
    status: str
    missing: tuple[str, ...] = ()
    fallback: str = ""


PSTACK_PLAYBOOK_FILES = (
    "authoring-a-skill",
    "autonomous-run",
    "autopilot-full",
    "autopilot-stack",
    "babysit",
    "bug-fix",
    "eval",
    "feature",
    "hillclimb",
    "investigation",
    "multi-phase-plan",
    "opening-a-pr",
    "orchestrate",
    "pause-safely",
    "perf-issue",
    "prototype",
    "refactoring",
    "runtime-forensics",
    "session-pickup",
    "shipping",
    "trace-forensics",
    "visual-parity",
    "worktree-cleanup",
)


def read_pstack_playbook_fixture(
    playbook_root: str | Path,
    playbook: str,
    *,
    available_capabilities: Iterable[str] = ("local skill reader",),
    required_capabilities: Iterable[str] = (),
) -> dict[str, object]:
    """Read one exact playbook file structurally in a read-only fixture.

    The fixture records headings and ordered entries from the selected file.
    It does not apply contextual steps, run bundled commands, start a cloud
    task, or claim live playbook behavior.
    """

    if playbook not in PSTACK_PLAYBOOK_FILES:
        raise AdapterError(f"unknown pstack playbook: {playbook}")
    root = Path(playbook_root)
    path = root / f"{playbook}.md"
    if not path.is_file():
        return {
            "status": "FALLBACK",
            "playbook": playbook,
            "reason": "selected playbook file is missing; use sequential native steps",
            "external_writes": False,
        }
    if path.is_symlink():
        raise AdapterError("playbook fixture must not be a symlink")
    text = path.read_text()
    if not text.strip():
        return {
            "status": "ERROR",
            "playbook": playbook,
            "reason": "selected playbook fixture is empty",
            "external_writes": False,
        }
    capability_result = resolve_capabilities(
        required_capabilities,
        available_capabilities,
        "use sequential native steps",
    )
    if capability_result.status == "FALLBACK":
        return {
            "status": "FALLBACK",
            "playbook": playbook,
            "missing": capability_result.missing,
            "reason": capability_result.fallback,
            "external_writes": False,
        }
    entries = tuple(
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("#")
        or (len(line.strip()) > 2 and line.strip()[0].isdigit() and line.strip()[1:3] == ". ")
    )
    if not entries:
        return {
            "status": "ERROR",
            "playbook": playbook,
            "reason": "selected playbook fixture has no bounded sections",
            "external_writes": False,
        }
    return {
        "status": "READ",
        "playbook": playbook,
        "path": str(path),
        "entries": entries,
        "environment": "isolated-read-only-fixture",
        "external_writes": False,
    }


def _validate_fixture_component(value: str, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
    ):
        raise AdapterError(f"{label} must be a single non-empty path component")


def _reject_symlink_components(root: Path, relative: Path) -> None:
    if root.is_symlink():
        raise AdapterError("verification fixture project root must not be a symlink")
    current = root
    for component in relative.parts:
        current /= component
        if current.is_symlink():
            raise AdapterError("verification fixture path must not contain symlinks")


def run_verification_fixture(
    project_root: str | Path,
    app_name: str,
    features: Mapping[str, str],
    *,
    app_available: bool,
    observed_features: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Create and exercise a project-local verification fixture.

    The fixture writes only a temporary `.agents/skills/verify-<app>/` tree,
    reconciles its feature files, and compares supplied observations. The
    observations stand in for an app conduct pass; no real application is
    started and no product or external state is changed.
    """

    _validate_fixture_component(app_name, "app_name")
    if not features:
        raise AdapterError("verification fixture needs at least one feature")
    for name, body in features.items():
        _validate_fixture_component(name, "feature name")
        if not isinstance(body, str) or not body.strip():
            raise AdapterError("feature fixture content must be non-empty text")

    root_path = Path(project_root)
    if root_path.is_symlink():
        raise AdapterError("verification fixture project root must not be a symlink")
    root = root_path.resolve()
    target = root / ".agents" / "skills" / f"verify-{app_name}"
    _reject_symlink_components(root, target.relative_to(root))
    if target.exists() and not target.is_dir():
        raise AdapterError("verification target is not a directory")
    target.mkdir(parents=True, exist_ok=True)
    features_dir = target / "features"
    _reject_symlink_components(root, features_dir.relative_to(root))
    features_dir.mkdir(exist_ok=True)
    skill_path = target / "SKILL.md"
    if skill_path.is_symlink():
        raise AdapterError("verification fixture file must not be a symlink")
    skill_path.write_text(
        f"---\nname: verify-{app_name}\n---\n\n"
        "This is an isolated verification fixture.\n"
    )
    for name, body in features.items():
        feature_path = features_dir / f"{name}.md"
        if feature_path.is_symlink():
            raise AdapterError("verification fixture file must not be a symlink")
        feature_path.write_text(body)

    expected = tuple(sorted(features))
    actual = tuple(sorted(path.stem for path in features_dir.glob("*.md")))
    if actual != expected:
        return {
            "status": "ERROR",
            "target": str(target),
            "reason": "feature file reconciliation mismatch",
            "expected_features": expected,
            "actual_features": actual,
            "product_edits": False,
        }
    result: dict[str, object] = {
        "target": str(target),
        "created_skill": True,
        "reconciled_features": actual,
        "product_edits": False,
        "external_writes": False,
        "environment": "isolated-project-fixture",
    }
    if not app_available:
        result.update(
            {
                "status": "BLOCKED",
                "reason": "verification app is unavailable",
                "fixture_observations": (),
            }
        )
        return result
    if observed_features is None:
        result.update(
            {
                "status": "BLOCKED",
                "reason": "verification observations are missing",
                "fixture_observations": (),
            }
        )
        return result
    observed = tuple(sorted(observed_features))
    if dict(observed_features) != dict(features):
        result.update(
            {
                "status": "ERROR",
                "reason": "observed feature results do not match the reconciled map",
                "fixture_observations": observed,
            }
        )
        return result
    result.update(
        {
            "status": "FIXTURE_ONLY",
            "fixture_observations": observed,
        }
    )
    return result


def select_verification_target(
    candidates: Iterable[str], *, requested: str | None = None
) -> dict[str, object]:
    """Select one project-local verification target without widening edit scope."""

    unique = tuple(dict.fromkeys(item for item in candidates if item))
    if requested:
        if requested not in unique:
            return {
                "status": "BLOCKED",
                "reason": "requested verification skill is not present",
            }
        return {"status": "READY", "target": requested}
    if not unique:
        return {"status": "BLOCKED", "reason": "no verification skill target exists"}
    if len(unique) > 1:
        return {"status": "NEEDS_INPUT", "candidates": unique}
    return {"status": "READY", "target": unique[0]}


def resolve_capabilities(
    required: Iterable[str], available: Iterable[str], fallback: str
) -> CapabilityResult:
    """Return a native path or an explicit fallback for missing capabilities."""

    required_set = {item for item in required if item}
    available_set = {item for item in available if item}
    missing = tuple(sorted(required_set - available_set))
    if missing:
        if not fallback.strip():
            raise MissingCapability("missing capabilities without a fallback")
        return CapabilityResult("FALLBACK", missing, fallback)
    return CapabilityResult("NATIVE")


def prove_rerunnable(first_output: str, second_output: str) -> dict[str, str]:
    """Prove that a lever returns the same output twice."""

    if not first_output or not second_output:
        raise AdapterError("lever output is empty")
    if first_output != second_output:
        raise AdapterError("lever output changed between identical runs")
    return {"status": "VERIFIED", "comparison": "identical"}


def bound_context(
    items: list[str], max_items: int, required_anchors: Iterable[str] = ()
) -> dict[str, object]:
    """Keep a context slice bounded while retaining named anchors when present."""

    if max_items < 1:
        raise AdapterError("max_items must be positive")
    anchors = [item for item in required_anchors if item in items]
    selected = list(dict.fromkeys(anchors + items))[:max_items]
    omitted = len(items) - len(selected)
    return {"status": "BOUNDED", "items": selected, "omitted": max(0, omitted)}


def choose_smallest(
    original: str, candidate: str, *, tests_pass: bool, deletion_safe: bool
) -> dict[str, str]:
    """Choose the smallest safe change, or preserve the original."""

    if not original or not candidate:
        raise AdapterError("change candidates must be non-empty")
    if not tests_pass or not deletion_safe:
        return {"status": "PRESERVED", "value": original}
    value = candidate if len(candidate) <= len(original) else original
    return {"status": "SMALLEST_SAFE", "value": value}


def verify_readback(expected: str, actual: str | None, *, runtime_available: bool) -> dict[str, str]:
    """Verify the value read from the real path, never a compile-only proxy."""

    if not runtime_available:
        return {"status": "NOT VERIFIED", "reason": "runtime unavailable"}
    if actual is None:
        raise AdapterError("real readback is missing")
    if expected != actual:
        return {"status": "NOT VERIFIED", "reason": "readback mismatch"}
    return {"status": "VERIFIED", "reason": "real readback matches"}


def review_prose(text: str, *, unslop_available: bool) -> dict[str, object]:
    """Run the bounded, instruction-only technical-writing checks."""

    if not text.strip():
        raise AdapterError("prose is empty")
    sentences = [part.strip() for part in text.split(".") if part.strip()]
    issues = []
    if any(word in text.lower().split() for word in ("simply", "utilize")):
        issues.append("replace filler or long synonym")
    if any(" should be " in f" {sentence.lower()} " for sentence in sentences):
        issues.append("use an active instruction")
    result = {"status": "PASS" if not issues else "ISSUES", "issues": issues}
    if not unslop_available:
        result["status"] = "PARTIAL" if result["status"] == "PASS" else result["status"]
        result["fallback"] = "built-in checks applied; optional unslop reference unavailable"
    return result


def review_canvas_request(
    *, gh_available: bool, local_diff: list[str] | None, action: str = "render"
) -> dict[str, object]:
    """Resolve a read-only PR review source without external writes."""

    if action not in {"render", "read"}:
        raise PermissionDenied("only read and render actions are allowed")
    if gh_available:
        source = "gh-read-only"
    elif local_diff:
        source = "local-fixture"
    else:
        raise MissingCapability("gh is unavailable and no local diff fixture exists")
    if local_diff is not None and not any(line.startswith(("+", "-", "@@")) for line in local_diff):
        raise AdapterError("diff fixture has no reviewable lines")
    return {"status": "READY", "source": source, "external_writes": False}
