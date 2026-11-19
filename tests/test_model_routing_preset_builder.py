import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/core/model-routing-preset-builder/SKILL.md"
PACKAGED_PRESETS = ROOT / "skills/core/model-routing-preset-builder/references/pstack-role-presets.json"
CANONICAL_PRESETS = ROOT / "skills/core/model-capability-router/references/pstack-role-presets.json"


class ModelRoutingPresetBuilderTests(unittest.TestCase):
    def test_packaged_codex_snapshot_matches_canonical_source(self):
        self.assertEqual(PACKAGED_PRESETS.read_bytes(), CANONICAL_PRESETS.read_bytes())
        parsed = json.loads(PACKAGED_PRESETS.read_text(encoding="utf-8"))
        self.assertEqual(parsed["default_preset"], "equilibrado")
        self.assertEqual(set(parsed["presets"]), {"economia", "equilibrado", "power"})

    def test_runtime_routes_are_separate_and_openclaw_uses_native_controls(self):
        text = SKILL.read_text(encoding="utf-8")
        for required in (
            "## Codex",
            "## OpenClaw",
            "Do not use the Codex preset JSON for OpenClaw",
            "/model list",
            "/models <provider>",
            "/model status",
            "-s` for a session-only selection",
        ):
            self.assertIn(required, text)

    def test_packaged_links_resolve_to_files_in_this_skill(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("[`references/pstack-role-presets.json`](references/pstack-role-presets.json)", text)
        self.assertTrue(PACKAGED_PRESETS.is_file())
        self.assertIn(
            "https://github.com/TheAngryPit/TheAngrySkills/blob/main/skills/core/model-capability-router/references/pstack-role-presets.json",
            text,
        )
        self.assertIn(
            "https://github.com/TheAngryPit/TheAngrySkills/blob/main/skills/core/model-capability-router/references/openclaw-subscriptions.md",
            text,
        )


if __name__ == "__main__":
    unittest.main()
