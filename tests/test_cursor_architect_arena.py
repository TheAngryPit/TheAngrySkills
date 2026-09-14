"""Focused contracts for the bounded native architect/arena adaptations."""

import json
import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest


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
    assert "bounded_native_two_candidate_architect_pass_and_disposable_runtime_contract_observed" in contract["native_mapping"]["availability"]
    assert "generated cursor-how/cursor-why mirror read/role-flow observed" in contract["native_mapping"]["availability"]
    assert "automatic trigger" in contract["native_mapping"]["availability"]
    assert contract["promotion_status"].startswith("held_until_")
    assert "invocation metadata" in overlay["proof"]
    assert "collaboration.spawn_agent" in overlay["codex_note"]
    assert "multi_agent_v1__spawn_agent" not in overlay["codex_note"]
    assert contract["name_mapping"]["source_path"] == _manifest_entry("cursor-architect")["path"]


def test_arena_native_roles_and_partial_fallback_are_explicit():
    overlay = _overlay("cursor-arena")
    contract = overlay["codex_contract"]
    capabilities = " ".join(contract["native_mapping"]["capabilities"])
    assert "agent_type general-worker" in capabilities
    assert "agent_type reviewer" in capabilities
    assert "bounded_native_n2_candidates_cross_judge_graft_verify_and_runtime_contract_observed" in contract["native_mapping"]["availability"]
    assert "Work cloud" in contract["native_mapping"]["availability"]
    assert "partial" in contract["native_mapping"]["fallback"]
    assert contract["promotion_status"].startswith("promoted_")
    assert "candidate artifacts" in overlay["proof"]
    assert "collaboration.spawn_agent" in overlay["codex_note"]
    assert "multi_agent_v1__spawn_agent" not in overlay["codex_note"]
    assert contract["name_mapping"]["source_path"] == _manifest_entry("cursor-arena")["path"]


@dataclass(frozen=True)
class _RuntimeNote:
    title: str
    body: str


class _DisposableNotesApp:
    """Black-box disposable app for the final export contract."""

    def __init__(self, root: Path):
        self.source = root / "notes.json"
        self.notes: list[_RuntimeNote] = []

    def create(self, title: str, body: str) -> None:
        self.notes.append(_RuntimeNote(title.strip(), body.strip()))
        self._persist_source()

    def search(self, query: str) -> list[_RuntimeNote]:
        needle = query.strip().lower()
        return [
            note
            for note in self.notes
            if not needle
            or needle in note.title.lower()
            or needle in note.body.lower()
        ]

    def reset(self) -> None:
        self.notes.clear()
        self._persist_source()

    def export_matching(self, query: str, destination: Path) -> tuple[str, str]:
        target = (destination / "notes.json").resolve()
        if target == self.source.resolve():
            raise RuntimeError("source/destination conflict")
        destination.mkdir(parents=True, exist_ok=True)
        notes = self.search(query)
        payload = {"version": 1, "query": query.strip().lower(), "notes": [note.__dict__ for note in notes]}
        revision = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        document = {"revision": revision, "payload": payload}
        target = destination / "notes.json"
        if target.exists():
            try:
                current = json.loads(target.read_text())
            except json.JSONDecodeError as exc:
                raise RuntimeError("malformed target") from exc
            if current == document:
                return "unchanged", revision
            status = "replaced"
        else:
            status = "created"
        target.write_text(json.dumps(document, sort_keys=True))
        return status, revision

    def _persist_source(self) -> None:
        self.source.write_text(json.dumps([note.__dict__ for note in self.notes], sort_keys=True))


def test_disposable_runtime_observes_create_retry_replace_and_conflict():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        app = _DisposableNotesApp(root)
        destination = root / "exports"
        app.create("One", "alpha")
        app.create("Two", "beta")

        first, revision = app.export_matching("", destination)
        retry, retry_revision = app.export_matching("", destination)
        assert (first, retry) == ("created", "unchanged")
        assert revision == retry_revision
        assert json.loads((destination / "notes.json").read_text())["payload"]["notes"][-1]["title"] == "Two"

        app.create("Three", "gamma")
        replaced, _ = app.export_matching("", destination)
        assert replaced == "replaced"
        assert len(json.loads((destination / "notes.json").read_text())["payload"]["notes"]) == 3

        (destination / "notes.json").write_text("not-json")
        with pytest.raises(RuntimeError, match="malformed target"):
            app.export_matching("", destination)
        with pytest.raises(RuntimeError, match="source/destination conflict"):
            app.export_matching("", root)
