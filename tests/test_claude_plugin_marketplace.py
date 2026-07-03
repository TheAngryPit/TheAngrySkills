import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"


def test_marketplace_skill_paths_exist():
    manifest = json.loads(MARKETPLACE.read_text())
    seen = set()

    for plugin in manifest["plugins"]:
        assert plugin["name"]
        assert plugin["skills"]

        for skill_path in plugin["skills"]:
            assert skill_path.startswith("./")
            skill_dir = ROOT / skill_path[2:]
            assert (skill_dir / "SKILL.md").is_file(), skill_path
            seen.add(skill_path)

    discovered = {
        "./" + str(path.parent.relative_to(ROOT))
        for path in ROOT.glob("skills/**/SKILL.md")
    }
    assert discovered == seen
