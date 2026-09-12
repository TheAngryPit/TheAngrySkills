import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ask_sync', ROOT / 'scripts/sync-ask-pit.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def source(tmp_path):
    checkout = tmp_path / 'source'
    root = checkout / sync.SOURCE_PATH
    (root / 'agents').mkdir(parents=True)
    (root / 'SKILL.md').write_text('---\nname: ask-matt\ndescription: Router\n---\nUse /writing-for-agents.\nOther steps stay.\n')
    (root / 'agents/openai.yaml').write_text('interface:\n  display_name: "Ask Matt"\npolicy:\n  allow_implicit_invocation: false\n')
    (root / 'support.md').write_text('Original support.\n')
    (checkout / 'LICENSE').write_text('Fixture license\n')
    subprocess.run(['git', 'init', '-q', str(checkout)], check=True)
    subprocess.run(['git', '-C', str(checkout), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(checkout), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
    return checkout, root


def test_refresh_preserves_only_approved_difference_and_tracks_support(tmp_path):
    checkout, root = source(tmp_path)
    dest = tmp_path / 'skills/core/ask-pit'
    writer = tmp_path / 'skills/engineering/writing-for-astra/SKILL.md'
    writer.parent.mkdir(parents=True)
    writer.write_text('Owned writer; preserve me.\n')
    sync.refresh(checkout, dest)
    assert (dest / 'SKILL.md').read_text() == (root / 'SKILL.md').read_text().replace('name: ask-matt', 'name: ask-pit').replace('/writing-for-agents', '/writing-for-astra')
    (root / 'support.md').unlink()
    (root / 'new-support.md').write_text('New upstream support\n')
    sync.refresh(checkout, dest)
    sync.validate(dest)
    assert not (dest / 'support.md').exists()
    assert (dest / 'new-support.md').read_text() == 'New upstream support\n'
    assert writer.read_text() == 'Owned writer; preserve me.\n'


def test_missing_route_preserves_previous_package(tmp_path):
    checkout, root = source(tmp_path)
    dest = tmp_path / 'ask-pit'
    sync.refresh(checkout, dest)
    before = {p.name: p.read_bytes() for p in dest.rglob('*') if p.is_file()}
    (root / 'SKILL.md').write_text('---\nname: ask-matt\ndescription: Router\n---\nNew architecture\n')
    with pytest.raises(ValueError, match='route missing'):
        sync.refresh(checkout, dest)
    assert {p.name: p.read_bytes() for p in dest.rglob('*') if p.is_file()} == before


def test_local_unapproved_edit_is_detected(tmp_path):
    checkout, _ = source(tmp_path)
    dest = tmp_path / 'ask-pit'
    sync.refresh(checkout, dest)
    (dest / 'support.md').write_text('Unexpected edit')
    with pytest.raises(ValueError, match='content changed'):
        sync.validate(dest)


def test_committed_package_matches_approved_transform():
    sync.validate()
    assert (ROOT / 'skills/engineering/writing-for-astra/SKILL.md').is_file()
