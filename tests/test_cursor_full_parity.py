import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_upstream_file_skill_and_agent_is_preserved():
    assert load('check-cursor-full-tree').verify()['files'] == 890
    result = load('check-cursor-adaptations').verify()
    assert result == dict(skills=104, published=96, held_adapted=8, agents_mapped=14,
                          unresolved_links=0, runtime_proof='not claimed')


@pytest.mark.parametrize('mutation', ['missing', 'corrupt', 'extra'])
def test_full_tree_rejects_missing_changed_and_untracked_files(tmp_path, mutation):
    check = load('check-cursor-full-tree')
    shutil.copytree(check.BASE / 'upstream-tree', tmp_path / 'upstream-tree')
    shutil.copy2(check.BASE / 'full-tree.json', tmp_path / 'full-tree.json')
    check.BASE = tmp_path
    target = tmp_path / 'upstream-tree/pstack/automations/benny/FOR_AGENTS.md'
    if mutation == 'missing':
        target.unlink()
    elif mutation == 'corrupt':
        target.write_text('changed')
    else:
        (tmp_path / 'upstream-tree/unreviewed.txt').write_text('new')
    with pytest.raises(ValueError, match='drift'):
        check.verify()


def test_full_tree_compares_real_git_inventory(tmp_path):
    check = load('check-cursor-full-tree')
    upstream = tmp_path / 'upstream'
    upstream.mkdir()
    subprocess.run(['git', 'init', '-q', str(upstream)], check=True)
    (upstream / 'one.txt').write_text('one')
    subprocess.run(['git', '-C', str(upstream), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(upstream), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'fixture'], check=True)
    with pytest.raises(ValueError, match='commit differs'):
        check.verify(upstream)


def test_detector_notices_new_non_pstack_plugin_and_dormant_pack_change(tmp_path):
    detector = load('detect-upstream-updates')
    source = ROOT / 'sources/cursor-plugins'
    upstream = tmp_path / 'upstream'
    shutil.copytree(source / 'upstream-tree', upstream)
    subprocess.run(['git', 'init', '-q', str(upstream)], check=True)
    subprocess.run(['git', '-C', str(upstream), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(upstream), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'fixture'], check=True)
    new = upstream / 'new-plugin/skills/new/SKILL.md'
    new.parent.mkdir(parents=True)
    new.write_text('new skill')
    (upstream / 'pstack/automations/benny/FOR_AGENTS.md').write_text('changed Benny')
    subprocess.run(['git', '-C', str(upstream), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(upstream), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'change'], check=True)
    report = detector.detect_cursor(upstream)
    assert 'new-plugin/skills/new' in report['new_skills']
    assert 'pstack/automations/benny/FOR_AGENTS.md' in report['changed_support_files']
    assert report['batch'] == 'pstack'
