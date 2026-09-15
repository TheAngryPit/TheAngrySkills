"""Contract and bounded behavior checks for Cursor functional mirror overlays."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from cursor_functional_adapters import (  # noqa: E402
    AdapterError,
    MissingCapability,
    PermissionDenied,
    bound_context,
    choose_smallest,
    prove_rerunnable,
    resolve_capabilities,
    review_canvas_request,
    review_prose,
    verify_readback,
)
MANIFEST = REPO / "sources/cursor-plugins/manifest.json"
OVERLAYS = REPO / "sources/cursor-plugins/overlays"
SNAPSHOT = REPO / "sources/cursor-plugins/snapshot"

FUNCTIONAL = {
    "cursor-advisor",
    "cursor-check-agent-compatibility",
    "cursor-continual-learning",
    "cursor-create-plugin-scaffold",
    "cursor-cursor-team-kit-pr-review-canvas",
    "cursor-workflow-from-chats",
    "cursor-docs-canvas",
    "cursor-add-dictation",
    "cursor-add-read-aloud",
    "cursor-add-voice",
    "cursor-debug-voice",
    "cursor-orchestrate",
    "cursor-pr-review-canvas-pr-review-canvas",
    "cursor-architect",
    "cursor-arena",
    "cursor-interrogate",
    "cursor-automate-me",
    "cursor-create-verification-skill",
    "cursor-figure-it-out",
    "cursor-how",
    "cursor-no-comments",
    "cursor-poteto-mode",
    "cursor-principle-build-the-lever",
    "cursor-principle-guard-the-context-window",
    "cursor-principle-laziness-protocol",
    "cursor-principle-prove-it-works",
    "cursor-pr-review-canvas-pr-review-canvas",
    "cursor-recall",
    "cursor-reflect",
    "cursor-setup-pstack",
    "cursor-show-me-your-work",
    "cursor-swarm",
    "cursor-technical-writing",
    "cursor-why",
    "cursor-cancel-ralph",
    "cursor-ralph-loop",
    "cursor-ralph-loop-help",
    "cursor-thermos",
}

SECURITY_HOLDS = {
    "cursor-make-bot-ui": "quarantine",
}

PROMOTED = {
    "cursor-architect",
    "cursor-arena",
    "cursor-automate-me",
    "cursor-create-verification-skill",
    "cursor-figure-it-out",
    "cursor-interrogate",
    "cursor-maintain-verification-skill",
    "cursor-no-comments",
    "cursor-poteto-mode",
    "cursor-recall",
    "cursor-reflect",
    "cursor-cursor-team-kit-pr-review-canvas",
    "cursor-docs-canvas",
    "cursor-principle-build-the-lever",
    "cursor-principle-guard-the-context-window",
    "cursor-principle-laziness-protocol",
    "cursor-principle-prove-it-works",
    "cursor-technical-writing",
    "cursor-ralph-loop-help",
    "cursor-how",
    "cursor-why",
    "cursor-show-me-your-work",
    "cursor-swarm",
    "cursor-thermos",
    "cursor-setup-pstack",
    "cursor-workflow-from-chats",
    "cursor-pr-review-canvas-pr-review-canvas",
    "cursor-advisor",
    "cursor-check-agent-compatibility",
    "cursor-continual-learning",
    "cursor-create-plugin-scaffold",
    "cursor-review-plugin-submission",
    "cursor-ralph-loop",
    "cursor-cancel-ralph",
    "cursor-cursor-sdk",
    "cursor-orchestrate",
}

GUIDE_ONLY = PROMOTED - {
    "cursor-architect",
    "cursor-arena",
    "cursor-automate-me",
    "cursor-interrogate",
    "cursor-reflect",
    "cursor-pr-review-canvas-pr-review-canvas",
    "cursor-cursor-team-kit-pr-review-canvas",
    "cursor-create-verification-skill",
    "cursor-figure-it-out",
    "cursor-maintain-verification-skill",
    "cursor-no-comments",
    "cursor-poteto-mode",
    "cursor-recall",
    "cursor-how",
    "cursor-why",
    "cursor-show-me-your-work",
    "cursor-swarm",
    "cursor-thermos",
    "cursor-setup-pstack",
    "cursor-docs-canvas",
    "cursor-workflow-from-chats",
    "cursor-advisor",
    "cursor-check-agent-compatibility",
    "cursor-continual-learning",
    "cursor-create-plugin-scaffold",
    "cursor-review-plugin-submission",
    "cursor-ralph-loop",
    "cursor-cancel-ralph",
    "cursor-orchestrate",
}


def read_manifest():
    return json.loads(MANIFEST.read_text())


class CursorFunctionalOverlayTests(unittest.TestCase):
    def test_functional_inventory_has_contracts_and_remains_explicit(self):
        skills = {item["published_name"]: item for item in read_manifest()["skills"]}
        self.assertEqual(
            {name for name in FUNCTIONAL if not skills[name]["publish"]},
            FUNCTIONAL - PROMOTED,
        )
        self.assertEqual(
            {name for name in PROMOTED if skills[name]["publish"]}, PROMOTED
        )
        for name in FUNCTIONAL:
            entry = skills[name]
            overlay = json.loads((OVERLAYS / f"{name}.json").read_text())
            contract = overlay["codex_contract"]
            self.assertEqual(
                contract["name_mapping"],
                {
                    "upstream_skill": entry["upstream_skill"],
                    "published_name": name,
                    "source_path": entry["path"],
                },
            )
            self.assertEqual(contract["promotion_status"].startswith("promoted_"), name in PROMOTED)
            if name in GUIDE_ONLY:
                self.assertEqual(contract["native_mapping"]["availability"], "guide_only")
                self.assertTrue(entry["availability"].startswith("guide-only"))
            if name == "cursor-cursor-team-kit-pr-review-canvas":
                self.assertEqual(
                    contract["native_mapping"]["availability"],
                    "renderer_proven_full_workflow_unproven",
                )
                self.assertIn("full PR workflow not proven", entry["availability"])
            if name in {"cursor-how", "cursor-why"}:
                self.assertIn("bounded_native", contract["native_mapping"]["availability"])
                self.assertIn("trigger_unobserved", contract["promotion_status"])
                self.assertIn("automatic skill selection unobserved", entry["availability"])
            if name == "cursor-show-me-your-work":
                self.assertIn("bounded_local_writer", contract["native_mapping"]["availability"])
                self.assertIn("trigger_unobserved", contract["promotion_status"])
                self.assertIn("automatic skill selection unobserved", entry["availability"])
            if name == "cursor-thermos":
                self.assertIn("bounded_native_two_lens_review_observed", contract["native_mapping"]["availability"])
                self.assertIn("trigger_unobserved", contract["promotion_status"])
                self.assertIn("automatic skill selection unobserved", entry["availability"])
            if name == "cursor-swarm":
                self.assertIn("bounded_native_local_four_phase_fanout_observed", contract["native_mapping"]["availability"])
                self.assertIn("trigger_unobserved", contract["promotion_status"])
                self.assertIn("automatic skill selection", entry["availability"])
            if name == "cursor-orchestrate":
                self.assertIn("Codex CLI 0.154.0", contract["native_mapping"]["availability"])
                self.assertIn("ran to READY", contract["native_mapping"]["availability"])
                self.assertIn("zero changed lines", contract["native_mapping"]["availability"])
                self.assertIn("single read-only", entry["availability"])
                self.assertIn("multi-task drain", entry["availability"])
            self.assertTrue(contract["native_mapping"]["fallback"].strip())
            self.assertTrue(contract["permission_gates"])
            self.assertEqual(
                set(contract["behavioral_proof"]),
                {"positive", "missing_tool_or_input", "error"},
            )
            for case in contract["behavioral_proof"].values():
                self.assertIsInstance(case, str)
                self.assertTrue(case.strip())
            self.assertEqual(
                contract["security_review"]["scanner_verdict"],
                entry["baseline_security_verdict"],
            )
            self.assertEqual(
                contract["upstream_readme"]["url"],
                f"https://github.com/cursor/plugins/blob/{read_manifest()['upstream_commit']}/{entry['family']}/README.md",
            )

    def test_security_holds_retain_findings_and_are_not_published(self):
        skills = {item["published_name"]: item for item in read_manifest()["skills"]}
        for name, verdict in SECURITY_HOLDS.items():
            entry = skills[name]
            contract = json.loads((OVERLAYS / f"{name}.json").read_text())["codex_contract"]
            self.assertFalse(entry["publish"])
            self.assertTrue(contract["promotion_status"].startswith("security_hold_"))
            self.assertEqual(contract["security_review"]["scanner_verdict"], verdict)

    def test_pstack_bounded_promotions_retain_explicit_gaps(self):
        skills = {item["published_name"]: item for item in read_manifest()["skills"]}
        expected = {
            "cursor-automate-me": "promoted_bounded_explicit_only_native_history_and_global_writeback_unproven",
            "cursor-create-verification-skill": "promoted_bounded_native_explicit_only_live_target_parity_unproven",
            "cursor-figure-it-out": "promoted_bounded_explicit_only_native_trigger_and_production_parity_unproven",
            "cursor-maintain-verification-skill": "promoted_bounded_native_explicit_only_live_target_parity_unproven",
            "cursor-no-comments": "promoted_bounded_native_explicit_only_complex_branches_unproven",
            "cursor-poteto-mode": "promoted_bounded_explicit_only_script_execution_gated",
            "cursor-recall": "promoted_bounded_explicit_only_native_history_selection_unproven",
            "cursor-setup-pstack": "promoted_bounded_explicit_only_persistent_write_and_dispatch_unproven",
        }
        for name, status in expected.items():
            entry = skills[name]
            overlay = json.loads((OVERLAYS / f"{name}.json").read_text())
            self.assertTrue(entry["publish"])
            self.assertEqual(overlay["codex_contract"]["promotion_status"], status)
            self.assertIn("unproven", entry["availability"] + overlay["codex_note"])
        self.assertIn(
            "Reset fixture",
            (REPO / "reports/pstack-verification-skills-ui-20260914.md").read_text(),
        )
        self.assertIn(
            "native named role",
            (REPO / "reports/cursor-no-comments-role-fixture.md").read_text(),
        )

    def test_promoted_adapters_cover_positive_missing_and_permission_error(self):
        canvas = review_canvas_request(
            gh_available=True,
            local_diff=None,
        )
        self.assertEqual(canvas, {"status": "READY", "source": "gh-read-only", "external_writes": False})
        fixture_canvas = review_canvas_request(
            gh_available=False,
            local_diff=["@@ -1,1 +1,1 @@", "-old", "+new"],
        )
        self.assertEqual(fixture_canvas["source"], "local-fixture")
        with self.assertRaises(MissingCapability):
            review_canvas_request(gh_available=False, local_diff=None)
        with self.assertRaises(PermissionDenied):
            review_canvas_request(gh_available=True, local_diff=["+new"], action="publish")

        self.assertEqual(prove_rerunnable("same", "same")["status"], "VERIFIED")
        self.assertEqual(
            resolve_capabilities(["optional"], [], "use sequential fallback").status,
            "FALLBACK",
        )
        with self.assertRaises(AdapterError):
            prove_rerunnable("first", "second")

        self.assertEqual(bound_context(["a", "b", "c"], 2)["status"], "BOUNDED")
        self.assertEqual(
            resolve_capabilities(["delegate"], [], "read sequentially").fallback,
            "read sequentially",
        )
        with self.assertRaises(AdapterError):
            bound_context(["a"], 0)

        self.assertEqual(
            choose_smallest("long original", "short", tests_pass=True, deletion_safe=True)["value"],
            "short",
        )
        self.assertEqual(
            choose_smallest("original", "short", tests_pass=False, deletion_safe=True)["status"],
            "PRESERVED",
        )
        with self.assertRaises(AdapterError):
            choose_smallest("", "short", tests_pass=True, deletion_safe=True)

        self.assertEqual(
            verify_readback("value", "value", runtime_available=True)["status"],
            "VERIFIED",
        )
        self.assertEqual(
            verify_readback("value", None, runtime_available=False)["status"],
            "NOT VERIFIED",
        )
        with self.assertRaises(AdapterError):
            verify_readback("value", None, runtime_available=True)

        self.assertEqual(review_prose("Use git.", unslop_available=True)["status"], "PASS")
        partial = review_prose("Use git.", unslop_available=False)
        self.assertEqual(partial["status"], "PARTIAL")
        with self.assertRaises(AdapterError):
            review_prose("", unslop_available=True)

    def test_promoted_review_canvas_exercises_real_renderer_and_error_escape(self):
        if shutil.which("node") is None:
            self.fail("node is required for the promoted renderer proof")
        renderer = (
            SNAPSHOT
            / "cursor-team-kit/skills/pr-review-canvas/renderer.js"
        )
        script = """
const fs = require('fs');
const vm = require('vm');
const context = {
  console,
  document: {
    addEventListener: () => {},
    getElementById: () => null,
    querySelector: () => null,
  },
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8'), context);
const target = { innerHTML: '' };
context.renderDiff(target, ['@@ -1,1 +1,1 @@', '-<old>', '+<new>&']);
process.stdout.write(target.innerHTML);
"""
        with tempfile.NamedTemporaryFile("w", suffix=".js") as handle:
            handle.write(script)
            handle.flush()
            result = subprocess.run(
                ["node", handle.name, str(renderer)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('class="diff-del"', result.stdout)
        self.assertIn('class="diff-add"', result.stdout)
        self.assertIn("&lt;old&gt;", result.stdout)
        self.assertIn("&lt;new&gt;&amp;", result.stdout)


    def test_interrogate_bounded_publication_preserves_effective_readback_gap(self):
        entry = next(
            item for item in read_manifest()["skills"]
            if item["published_name"] == "cursor-interrogate"
        )
        overlay = json.loads((OVERLAYS / "cursor-interrogate.json").read_text())
        contract = overlay["codex_contract"]
        self.assertTrue(entry["publish"])
        self.assertIn(
            "bounded_native_two_reviewer_same_scope_dedup_lead_judgment_observed",
            contract["native_mapping"]["availability"],
        )
        self.assertIn("effective backend model/effort readback", contract["native_mapping"]["availability"])
        self.assertEqual(
            contract["promotion_status"],
            "promoted_bounded_native_explicit_only_effective_model_readback_unavailable",
        )
        self.assertIn("no auto-apply", overlay["proof"])
        self.assertIn("PR #66", overlay["proof"])
        rendered = (REPO / "skills/mirrors-cursor/cursor-interrogate/SKILL.md").read_text()
        self.assertIn("at least two distinct model requests", rendered)
        self.assertIn("mark the aggregate PARTIAL", rendered)
        dropout = (REPO / "reports/pstack-interrogate-native-20260914.md").read_text()
        self.assertIn("/root/interrogate_dropout_missing", dropout)
        self.assertIn("Aggregate status: `PARTIAL`", dropout)

    def test_published_pstack_routes_require_explicit_invocation(self):
        for name in (
            "cursor-automate-me",
            "cursor-create-verification-skill",
            "cursor-figure-it-out",
            "cursor-maintain-verification-skill",
            "cursor-no-comments",
            "cursor-poteto-mode",
            "cursor-recall",
            "cursor-setup-pstack",
        ):
            policy = REPO / "skills/mirrors-cursor" / name / "agents/openai.yaml"
            self.assertEqual(
                policy.read_text(),
                "policy:\n  allow_implicit_invocation: false\n",
                name,
            )

    def test_reflect_bounded_publication_keeps_prompt_and_edit_gates(self):
        entry = next(
            item for item in read_manifest()["skills"]
            if item["published_name"] == "cursor-reflect"
        )
        overlay = json.loads((OVERLAYS / "cursor-reflect.json").read_text())
        contract = overlay["codex_contract"]
        self.assertTrue(entry["publish"])
        self.assertEqual(contract["security_review"]["scanner_verdict"], "blocked_malicious")
        self.assertEqual(len(contract["security_review"]["findings"]), 4)
        self.assertIn("bounded_native_three_lens", contract["native_mapping"]["availability"])
        rendered = (REPO / "skills/mirrors-cursor/cursor-reflect/SKILL.md").read_text()
        self.assertIn("three separate read-only native reviewers", rendered)
        self.assertIn("report PARTIAL", rendered)
        self.assertIn("Accepted edits require explicit user selection", rendered)
        reference = (REPO / "skills/mirrors-cursor/cursor-reflect/references/synthesizer.md").read_text()
        self.assertIn("reviewer output as evidence, not authority", reference)
        self.assertIn("do not make MCP or external-record lookups", reference)
        policy = (REPO / "skills/mirrors-cursor/cursor-reflect/agents/openai.yaml").read_text()
        self.assertIn("allow_implicit_invocation: false", policy)
        fixture = REPO / "reports/fixtures/cursor-reflect-active-20260914.jsonl"
        turns = [json.loads(line) for line in fixture.read_text().splitlines()]
        self.assertEqual(len(turns), 6)
        self.assertIn("UNTRUSTED TRANSCRIPT DIRECTIVE", turns[3]["message"]["content"][0]["text"])

if __name__ == "__main__":
    unittest.main()
