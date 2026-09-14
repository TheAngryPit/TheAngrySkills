import json
import hashlib
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-native-agent-profiles.py"
ASSETS = ROOT / "skills/core/model-capability-router/assets/agents"
PROFILE_NAMES = ("comment-sicko", "poteto-agent")


class NativeAgentProfileTests(unittest.TestCase):
    def test_manifest_and_overlays_point_to_the_same_native_profiles(self):
        manifest = json.loads(
            (ROOT / "sources/cursor-plugins/manifest.json").read_text()
        )
        skills = {item["published_name"]: item for item in manifest["skills"]}
        for skill_name, profile_name in (
            ("cursor-no-comments", "comment-sicko"),
            ("cursor-poteto-mode", "poteto-agent"),
        ):
            item = skills[skill_name]
            overlay = json.loads(
                (
                    ROOT / "sources/cursor-plugins/overlays" / f"{skill_name}.json"
                ).read_text()
            )
            manifest_profile = item["native_agent_profiles"][0]
            overlay_profile = overlay["native_agent_profiles"][0]
            expected_asset = f"skills/core/model-capability-router/assets/agents/{profile_name}.toml"
            expected_source = f"pstack/agents/{profile_name}.md"
            self.assertEqual(manifest_profile["name"], profile_name)
            self.assertEqual(overlay_profile["name"], profile_name)
            self.assertEqual(manifest_profile["asset_path"], expected_asset)
            self.assertEqual(overlay_profile["asset_path"], expected_asset)
            self.assertEqual(manifest_profile["pinned_source_path"], expected_source)
            self.assertEqual(overlay_profile["pinned_source_path"], expected_source)
            source = ROOT / "sources/cursor-plugins/snapshot" / expected_source
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(manifest_profile["pinned_source_sha256"], digest)
            self.assertTrue((ROOT / expected_asset).is_file())

    def test_assets_are_native_toml_and_source_grounded(self):
        anchors = {
            "comment-sicko": ("I hate comments.", "MUST KILL", "cursor-how", "cursor-why"),
            "poteto-agent": (
                "cursor-poteto-mode",
                "cursor-principle-",
                "native Codex subagent delegation",
                "reuse the existing poteto-agent",
            ),
        }
        for name in PROFILE_NAMES:
            asset = ASSETS / f"{name}.toml"
            parsed = tomllib.loads(asset.read_text())
            self.assertEqual(set(parsed), {"name", "description", "developer_instructions"})
            self.assertEqual(parsed["name"], name)
            for phrase in anchors[name]:
                self.assertIn(phrase, asset.read_text())
            self.assertNotIn("subagent_type:", asset.read_text())
            self.assertNotIn("generalPurpose", asset.read_text())
            self.assertFalse((ASSETS / f"{name}.md").exists())

    def test_checker_proves_distribution_and_explicit_install(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "agents"
            source_root = os.environ.get("PINNED_PSTACK_AGENT_ROOT")
            source_args = []
            if source_root and Path(source_root).is_dir():
                source_args = [
                    "--pinned-source-root",
                    source_root,
                    "--require-pinned-source",
                ]
            checked = subprocess.run(
                [sys.executable, str(SCRIPT), *source_args],
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(checked.stdout)["status"], "PASS")

            installed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--install",
                    "--installed-dir",
                    str(target),
                    *source_args,
                ],
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(installed.returncode, 0, installed.stderr)
            installed_report = json.loads(installed.stdout)
            self.assertTrue(all(item["installed_byte_match"] for item in installed_report["profiles"]))
            for name in PROFILE_NAMES:
                self.assertEqual((target / f"{name}.toml").read_bytes(), (ASSETS / f"{name}.toml").read_bytes())

            conflict = target / "comment-sicko.toml"
            conflict.write_text(conflict.read_text() + "\n")
            refused = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--install",
                    "--installed-dir",
                    str(target),
                ],
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("--replace", refused.stderr)

            with tempfile.TemporaryDirectory() as outside_temporary:
                outside = Path(outside_temporary) / "sentinel.toml"
                outside.write_text("preserve me")
                conflict.unlink()
                conflict.symlink_to(outside)
                symlink_refused = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "--install",
                        "--replace",
                        "--installed-dir",
                        str(target),
                        *source_args,
                    ],
                    cwd=str(ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(symlink_refused.returncode, 0)
                self.assertEqual(outside.read_text(), "preserve me")

            conflict.unlink()
            replaced = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--install",
                    "--replace",
                    "--installed-dir",
                    str(target),
                    *source_args,
                ],
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(replaced.returncode, 0, replaced.stderr)
            self.assertEqual(conflict.read_bytes(), (ASSETS / "comment-sicko.toml").read_bytes())


if __name__ == "__main__":
    unittest.main()
