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
    "cursor-automate-me",
    "cursor-create-verification-skill",
    "cursor-figure-it-out",
    "cursor-how",
    "cursor-interrogate",
    "cursor-no-comments",
    "cursor-poteto-mode",
    "cursor-principle-build-the-lever",
    "cursor-principle-guard-the-context-window",
    "cursor-principle-laziness-protocol",
    "cursor-principle-prove-it-works",
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
    "cursor-cursor-sdk": "blocked_malicious",
    "cursor-make-bot-ui": "quarantine",
    "cursor-review-plugin-submission": "needs_human_review",
}

PROMOTED = {
    "cursor-cursor-team-kit-pr-review-canvas",
    "cursor-principle-build-the-lever",
    "cursor-principle-guard-the-context-window",
    "cursor-principle-laziness-protocol",
    "cursor-principle-prove-it-works",
    "cursor-technical-writing",
}

GUIDE_ONLY = PROMOTED - {"cursor-cursor-team-kit-pr-review-canvas"}


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


if __name__ == "__main__":
    unittest.main()
