"""The adapted methods follow current upstream topology and native boundaries."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "sources/cursor-plugins"


def method(name):
    return (ROOT / "skills/mirrors-cursor" / name / "references/runtime/original-codex.txt").read_text()


def test_architect_sketches_locally_and_uses_arena_only_when_large_or_contested():
    text = method("cursor-architect")
    assert "trace every system" in text and "sketch two different shapes" in text
    assert "each piece of state has one owner" in text
    assert "large or contested" in text and "cursor-arena" in text
    for obsolete in ("Phase A", "Phase E", "runner-prompt", "rationale-template", "design-red-flags", "independent judge", "cursor-how"):
        assert obsolete not in text


def test_how_uses_one_read_only_explainer_and_preserves_its_output():
    text = method("cursor-how")
    assert "one authorized native read-only delegate" in text
    assert "explores and explains in one pass" in text
    assert "Light edits" in text and "Do not substantially rewrite" in text
    for obsolete in ("Assess complexity", "two to four", "references/explorer", "references/explainer", "## 3."):
        assert obsolete not in text


def test_why_is_record_first_without_investigator_or_synthesizer_topology():
    text = method("cursor-why")
    assert "record, not the code" in text
    assert "commits and PR discussions" in text
    assert "inferences as inferences" in text and "record does not answer" in text
    for obsolete in ("source-playbook", "synthesizer-prompt", "investigator-prompt", "Spawn", "Phase"):
        assert obsolete not in text


def test_reflect_mines_current_transcript_and_keeps_approval_and_source_boundaries():
    text = method("cursor-reflect")
    for phrase in ("this conversation", "six months", "Read that skill first", "Accepted", "Rejected", "Backlog", "wait for approval", "Never edit plugin caches", "canonical owning repository", "Do not install, open a PR or push"):
        assert phrase in text
    assert "Spawn three" not in text and "reviewer.md" not in text


def test_vendor_independence_and_disclosed_skip_are_the_current_judging_contract():
    arena = method("cursor-arena")
    audit = method("cursor-show-me-your-work")
    assert "different vendor than the parent" in arena
    assert "Fable and Opus count as the same vendor" in arena
    assert "skip the judge and say so" in arena
    assert "do not turn this disclosed skip into an extra acceptance gate" in arena
    assert "another vendor's model" in audit
    assert "Fable and Opus are the same vendor" in audit
    assert "report that review gap" in audit
    assert "different-family judge" not in arena


def test_obsolete_dependencies_are_absent_from_generated_packages_and_overlay_inputs():
    obsolete = ("runner-prompt.md", "rationale-template.md", "design-red-flags.md", "explorer-prompt.md", "explainer-prompt.md", "source-playbook.md", "synthesizer-prompt.md", "investigator-prompt.md", "judgment-reviewer.md", "tooling-reviewer.md", "divergent-reviewer.md", "check-plan.mjs", "playbooks/orchestrate.md")
    manifest = json.loads((BASE / "manifest.json").read_text())
    assert not any(path.startswith("scripts/cursor_pstack_") for path in manifest["native_support_files"])
    for name in ("cursor-architect", "cursor-how", "cursor-why", "cursor-reflect", "cursor-poteto-mode"):
        target = ROOT / "skills/mirrors-cursor" / name
        paths = [p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()]
        overlay = json.loads((BASE / "overlays" / (name + ".json")).read_text())
        for reference in obsolete:
            assert not any(path.endswith(reference) for path in paths), (name, reference)
            assert reference not in json.dumps(overlay), (name, reference)
    assert not [p for p in (ROOT / "scripts").glob("cursor_pstack_*") if p.suffix in {".md", ".mjs"}]


def test_sharpen_returns_a_prompt_that_requests_experiments_without_running_them():
    text = method("cursor-sharpen")
    assert "rewritten prompt ask the agent to prototype" in text
    assert "recommend an option based on what it observed" in text
    assert "do not execute the task" in text


def test_recall_and_benny_trace_directly_without_retired_why_or_how_routes():
    text = method("cursor-recall")
    assert "one investigator subagent per source" in text
    assert "source-playbook" not in text
    for name in ("cursor-setup-benny", "cursor-triage-issue-reports", "cursor-reproduce-and-fix-issues"):
        text = method(name)
        assert "cursor-how" not in text
        assert "cursor-why" in text


def test_canonical_preset_rows_match_current_setup_without_changing_policy_modes():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from cursor_functional_adapters import PSTACK_MODEL_ROLES
    data = json.loads((ROOT / "skills/core/model-capability-router/references/pstack-role-presets.json").read_text())
    assert [row["label"] for row in data["roles"]] == list(PSTACK_MODEL_ROLES)
    assert len(data["roles"]) == 9
    setup = method("cursor-setup-pstack")
    assert "explicitly selected role-aware preset" in setup
    assert "Do not combine a preset with an upstream global budget" in setup
    assert "preserving explicit overrides" in setup
