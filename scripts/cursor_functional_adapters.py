"""Small, local proof harnesses for promoted Cursor mirror boundaries.

These helpers do not activate Cursor, cloud, connector, or marketplace
surfaces. They exercise the promoted renderer boundary and guide rules while
keeping missing capabilities and failed proof states explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


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
