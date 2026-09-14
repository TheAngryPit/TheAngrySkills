"""Focused contracts for the bounded native architect/arena adaptations."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OVERLAYS = ROOT / "sources/cursor-plugins/overlays"
MANIFEST = ROOT / "sources/cursor-plugins/manifest.json"


def _overlay(name: str) -> dict:
    return json.loads((OVERLAYS / f"{name}.json").read_text())


def _manifest_entry(name: str) -> dict:
    manifest = json.loads(MANIFEST.read_text())
    return next(item for item in manifest["skills"] if item["published_name"] == name)


def test_architect_native_roles_and_gates_are_explicit():
    overlay = _overlay("cursor-architect")
    contract = overlay["codex_contract"]
    assert "agent_type general-worker" in " ".join(contract["native_mapping"]["capabilities"])
    assert "agent_type planner" in " ".join(contract["native_mapping"]["capabilities"])
    assert "bounded_native_two_candidate_architect_pass_observed" in contract["native_mapping"]["availability"]
    assert "automatic trigger" in contract["native_mapping"]["availability"]
    assert contract["promotion_status"].startswith("held_until_")
    assert "invocation metadata" in overlay["proof"]
    assert contract["name_mapping"]["source_path"] == _manifest_entry("cursor-architect")["path"]


def test_arena_native_roles_and_partial_fallback_are_explicit():
    overlay = _overlay("cursor-arena")
    contract = overlay["codex_contract"]
    capabilities = " ".join(contract["native_mapping"]["capabilities"])
    assert "agent_type general-worker" in capabilities
    assert "agent_type reviewer" in capabilities
    assert "bounded_native_n2_candidates_cross_judge_graft_verify_observed" in contract["native_mapping"]["availability"]
    assert "Work cloud" in contract["native_mapping"]["availability"]
    assert "partial" in contract["native_mapping"]["fallback"]
    assert contract["promotion_status"].startswith("held_until_")
    assert "candidate artifacts" in overlay["proof"]
    assert contract["name_mapping"]["source_path"] == _manifest_entry("cursor-arena")["path"]
