"""Distribution contracts for the selected OpenClaw core adaptation pack."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "skills" / "engineering" / "openclaw-core"
MANIFEST = json.loads((PACK / "manifest.json").read_text())


def test_documentation_dependency_retains_its_own_mit_notice():
    notice = PACK / "openclaw-refactor-docs/references/technical-documentation/LICENSE"
    archive = ROOT / "sources/openclaw-core/.agents/skills/technical-documentation/LICENSE"
    raw = notice.read_bytes()
    assert raw == archive.read_bytes()
    assert b"Copyright (c) 2026 Vincent Koc" in raw
    assert b"The above copyright notice and this permission notice shall be included" in raw
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == "a7cb85a0d651801a2d601d0b31cbbc8b417dff76"


def test_selective_heap_install_declares_the_complete_required_closure():
    entries = {entry["name"]: entry for entry in MANIFEST["skills"]}

    def closure(name, seen=()):
        assert name not in seen, "required companion cycle"
        result = set()
        for companion in entries[name]["required_companions"]:
            assert companion in entries, "required companion is not distributed"
            result.add(companion)
            result.update(closure(companion, (*seen, name)))
        return result

    assert closure("openclaw-test-heap-leaks") == {"openclaw-test-performance", "openclaw-testing"}
    for name in ("openclaw-debugging", "openclaw-test-performance", "openclaw-release-plugin-testing"):
        assert closure(name) == {"openclaw-testing"}
    for name, entry in entries.items():
        text = (ROOT / entry["path"] / "SKILL.md").read_text()
        assert all("`$" + companion + "`" in text for companion in closure(name))
    readme = (PACK / "README.md").read_text()
    assert "-s openclaw-test-heap-leaks openclaw-test-performance openclaw-testing" in readme
    assert "does not resolve" in readme


def test_all_installed_markdown_relative_links_resolve():
    for entry in MANIFEST["skills"]:
        directory = ROOT / entry["path"]
        for document in directory.rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
                if target.startswith(("http:", "https:", "mailto:", "#")):
                    continue
                path = (document.parent / target.split("#", 1)[0]).resolve()
                assert path.is_file(), (document.relative_to(ROOT), target)
                assert path.is_relative_to(directory.resolve()), "selective install cannot rely on an unpackaged relative sibling"


def test_nested_docker_link_is_pinned_and_mapped_from_its_own_resource():
    directory = PACK / "openclaw-testing"
    resource = "references/upstream/references/package-and-docker.md"
    url = "https://github.com/openclaw/openclaw/blob/" + MANIFEST["source_commit"] + "/.agents/skills/openclaw-docker-e2e-authoring/SKILL.md"
    assert url in (directory / resource).read_text()
    mapping = json.loads((directory / "references/upstream-link-map.json").read_text())
    assert any(link["source_file"] == resource and link["original"] == "../../openclaw-docker-e2e-authoring/SKILL.md" and link["pinned_url"] == url for link in mapping["links"])


def test_resource_hashes_and_native_entrypoints_match_the_declared_pack():
    assert len(MANIFEST["skills"]) == 12
    assert len(list(PACK.rglob("SKILL.md"))) == 12
    assert len({entry["name"] for entry in MANIFEST["skills"]}) == 12
    for entry in MANIFEST["skills"]:
        directory = ROOT / entry["path"]
        record = json.loads((directory / "UPSTREAM.json").read_text())
        for resource, expected in record["resources"].items():
            assert hashlib.sha256((directory / resource).read_bytes()).hexdigest() == expected, resource
