import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "mirror-sources.json"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
MIRROR_ROOT = ROOT / "skills" / "mirrors-emilkowalski"


def published_name(upstream_name: str) -> str:
    return upstream_name if upstream_name.startswith("emil-") else f"emil-{upstream_name}"


def mirror_note_value(note: str, label: str) -> str:
    return re.search(rf"^{re.escape(label)}:\s*(.+)$", note, re.MULTILINE).group(1).strip()


def test_emilkowalski_source_is_configured_like_curated_openclaw() -> None:
    manifest = json.loads(CONFIG.read_text())
    source = next(item for item in manifest["sources"] if item["id"] == "emilkowalski")

    assert source == {
        "id": "emilkowalski",
        "repository": "https://github.com/emilkowalski/skills.git",
        "branch": "main",
        "source_root": "skills",
        "destination_root": "skills/mirrors-emilkowalski",
        "prefix": "emil-",
        "rewrite_named_references": True,
    }
    assert "default" not in source


def test_emilkowalski_mirror_is_prefixed_once_and_has_provenance() -> None:
    directories = sorted(path.name for path in MIRROR_ROOT.iterdir() if path.is_dir())
    assert directories
    assert "emil-emil-design-eng" not in directories

    upstream_names = []
    for directory in directories:
        root = MIRROR_ROOT / directory
        skill_file = root / "SKILL.md"
        note_file = root / "MIRROR.md"
        assert skill_file.is_file()
        assert note_file.is_file()

        note = note_file.read_text()
        upstream_name = mirror_note_value(note, "Mirrored skill")
        upstream_names.append(upstream_name)
        assert directory == published_name(upstream_name)
        frontmatter_name = re.search(r"^name:\s*([^\n]+)$", skill_file.read_text(), re.MULTILINE).group(1).strip()
        assert frontmatter_name == directory
        assert mirror_note_value(note, "Source") == "https://github.com/emilkowalski/skills.git"
        assert re.fullmatch(r"[0-9a-f]{40}", mirror_note_value(note, "Commit"))

    assert len(upstream_names) == len(set(upstream_names))
    assert "emil-design-eng" in directories


def test_emilkowalski_named_sibling_references_are_prefixed() -> None:
    expected_references = {
        "review-animations": "emil-review-animations",
        "improve-animations": "emil-improve-animations",
        "find-animation-opportunities": "emil-find-animation-opportunities",
        "animate-expo": "emil-animate-expo",
        "pick-ui-library": "emil-pick-ui-library",
    }
    source = next(
        item for item in json.loads(CONFIG.read_text())["sources"] if item["id"] == "emilkowalski"
    )
    assert source["rewrite_named_references"] is True
    for path in MIRROR_ROOT.rglob("*"):
        if not path.is_file() or path.name == "MIRROR.md":
            continue
        text = path.read_text(errors="replace")
        for upstream_name, published in expected_references.items():
            if re.search(rf"(?<![A-Za-z0-9_-]){re.escape(upstream_name)}(?![A-Za-z0-9_-])", text):
                raise AssertionError(f"unprefixed named reference in {path}: {upstream_name}")


def test_emilkowalski_mirror_is_separate_from_owned_install_plugins() -> None:
    marketplace = json.loads(MARKETPLACE.read_text())
    mirror_plugin = next(item for item in marketplace["plugins"] if item["name"] == "mirrors-emilkowalski")
    assert mirror_plugin["skills"]
    assert all(path.startswith("./skills/mirrors-emilkowalski/") for path in mirror_plugin["skills"])
    assert not any(
        path.startswith("./skills/mirrors-emilkowalski/")
        for plugin in marketplace["plugins"]
        if plugin["name"] in {"the-angry-core", "the-angry-engineering", "the-angry-design", "founder-gtm"}
        for path in plugin["skills"]
    )


def test_existing_openclaw_mirror_note_keeps_legacy_wording() -> None:
    note = (ROOT / "skills" / "mirrors-openclaw" / "openclaw-agent-transcript" / "MIRROR.md").read_text()
    assert "The mirrored frontmatter name and references to sibling skill paths are adapted to the published names;" in note
    assert "frontmatter names and concrete references to renamed sibling paths and skill names" not in note
