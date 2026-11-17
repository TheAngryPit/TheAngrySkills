"""Current Pstack roles and relative budgets through the native dry-run boundary."""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from cursor_functional_adapters import (  # noqa: E402
    PSTACK_BUDGETS, PSTACK_MODEL_ROLES, run_pstack_model_mapping_fixture,
)

INVENTORY = {
    "gpt-6.2-sol": ("low", "medium", "high", "xhigh"),
    "claude-fable-5-2": ("low", "medium", "high"),
    "claude-opus-5-5": ("low", "medium", "high", "xhigh"),
}


def choices():
    return {
        "feature, refactoring": {"model": "gpt-6.2-sol", "effort": "xhigh"},
        "bug-fix": {"model": "gpt-6.2-sol", "effort": "xhigh"},
        "perf-issue": {"model": "gpt-6.2-sol", "effort": "xhigh"},
        "hillclimb": {"model": "gpt-6.2-sol", "effort": "xhigh"},
        "judgment and prose": "inherit-parent",
        "arena runners": ["claude-fable-5-2", "claude-opus-5-5"],
        "arena cross-judge pool": ["claude-opus-5-5", "gpt-6.2-sol"],
        "swarm workers": "gpt-6.2-sol",
        "interrogate reviewers": ["auto", "gpt-6.2-sol"],
    }


def test_current_role_mapping_is_dry_run_and_preserves_native_choices(tmp_path):
    sentinel = tmp_path / "config.toml"
    sentinel.write_text("explicit user binding\n")
    requested = choices()
    result = run_pstack_model_mapping_fixture(INVENTORY, requested)
    assert result["status"] == "DRY_RUN"
    assert not result["writes_performed"] and not result["configuration_changed"]
    assert set(result["mapping"]) == set(requested) == set(PSTACK_MODEL_ROLES)
    for role, row in result["mapping"].items():
        selections = requested[role] if isinstance(requested[role], list) else [requested[role]]
        expected = [value if isinstance(value, dict) else {"model": value} for value in selections]
        assert [value["selection"] for value in row["selections"]] == expected
    assert sentinel.read_text() == "explicit user binding\n"


@pytest.mark.parametrize("budget,code,panel", [
    ("large", "xhigh", "high"), ("medium", "high", "medium"), ("small", "medium", "low"),
])
def test_budgets_lower_each_roles_starting_effort(budget, code, panel):
    result = run_pstack_model_mapping_fixture(INVENTORY, choices(), budget=budget)
    assert result["status"] == "DRY_RUN"
    assert result["mapping"]["bug-fix"]["selections"][0]["selection"]["effort"] == code
    assert result["mapping"]["arena runners"]["selections"][0]["selection"]["effort"] == panel
    assert result["mapping"]["swarm workers"]["selections"][0]["selection"]["effort"] == panel
    assert result["mapping"]["judgment and prose"]["selections"][0]["selection"] == {"model": "inherit-parent"}
    assert result["mapping"]["interrogate reviewers"]["selections"][0]["selection"] == {"model": "auto"}
    assert set(PSTACK_BUDGETS) == {"large", "medium", "small"}


def test_retired_rows_and_unlimited_are_not_current_setup_options():
    requested = choices()
    requested["how explorer"] = "gpt-6.2-sol"
    assert run_pstack_model_mapping_fixture(INVENTORY, requested)["status"] == "ERROR"
    assert run_pstack_model_mapping_fixture(INVENTORY, choices(), budget="unlimited")["status"] == "ERROR"


def test_unavailable_native_model_or_effort_never_writes():
    requested = choices()
    requested["bug-fix"] = {"model": "unavailable", "effort": "high"}
    requested["perf-issue"] = {"model": "gpt-6.2-sol", "effort": "max"}
    result = run_pstack_model_mapping_fixture(INVENTORY, requested)
    assert result["status"] == "BLOCKED"
    assert any("unavailable model" in reason for reason in result["unavailable"])
    assert any("unavailable effort" in reason for reason in result["unavailable"])
    assert not result["writes_performed"]


def test_alias_effort_without_parent_identity_and_malformed_panels_are_errors():
    requested = choices()
    requested["judgment and prose"] = {"model": "auto", "effort": "high"}
    assert "without the parent model" in run_pstack_model_mapping_fixture(INVENTORY, requested)["reason"]
    requested = choices()
    requested["arena runners"] = "gpt-6.2-sol"
    assert "non-empty model panel" in run_pstack_model_mapping_fixture(INVENTORY, requested)["reason"]


def test_budget_with_no_supported_lower_effort_reports_choice_gap():
    inventory = {**INVENTORY, "claude-fable-5-2": ("high",)}
    result = run_pstack_model_mapping_fixture(inventory, choices(), budget="small")
    assert result["status"] == "BLOCKED"
    assert result["mapping"]["arena runners"]["selections"][0]["availability"] == "needs-choice"
    assert not result["configuration_changed"]


def test_budget_gap_names_the_role_target_not_the_shared_label():
    inventory = {model: ("xhigh",) for model in INVENTORY}
    result = run_pstack_model_mapping_fixture(inventory, choices(), budget="large")
    assert result["status"] == "BLOCKED"
    for role in ("arena runners", "swarm workers"):
        gaps = [reason for reason in result["unavailable"] if reason.startswith(role + "[")]
        assert gaps and all("at or below 'high'" in reason for reason in gaps)
    assert not any(reason.startswith("bug-fix[") for reason in result["unavailable"])
    assert not result["writes_performed"]
