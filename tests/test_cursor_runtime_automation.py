import hashlib
import importlib.util
import json
import subprocess
import shutil
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
PRESERVED_FOLDERS = ('.github/workflows', 'sources/cursor-plugins/snapshot', 'sources/cursor-plugins/upstream-tree')
PRESERVED_FILES = (
    'scripts/detect-upstream-updates.py', 'scripts/upstream-pr-lifecycle.py',
    'sources/cursor-plugins/manifest.json', 'sources/cursor-plugins/full-tree.json',
    'sources/cursor-plugins/family-refresh.json', 'sources/cursor-plugins/agent-coverage.json',
)


def preservation_snapshot(root):
    paths = set(PRESERVED_FILES)
    for folder in PRESERVED_FOLDERS:
        files = {path.relative_to(root).as_posix() for path in (root / folder).rglob('*') if path.is_file()}
        assert files, folder
        paths.update(files)
    coverage = json.loads((root / 'sources/cursor-plugins/agent-coverage.json').read_text())['agents']
    paths.update(profile['asset_path'] for profile in coverage.values())
    return {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in sorted(paths)}


@pytest.fixture(scope='module')
def regenerated_tree():
    spec = importlib.util.spec_from_file_location('runtime_mirror_fixture', ROOT / 'tests/test_cursor_plugin_mirror.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    mirror = module.CursorMirrorTests()
    mirror.setUp()
    try:
        for relative in ('.github/workflows', 'scripts/detect-upstream-updates.py', 'scripts/upstream-pr-lifecycle.py'):
            source, target = ROOT / relative, mirror.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
        assert not (mirror.root / '.git').exists()
        before = preservation_snapshot(mirror.root)
        result = mirror.run_build()
        assert result.returncode == 0, result.stderr
        yield before, preservation_snapshot(mirror.root)
    finally:
        mirror.doCleanups()


def test_runtime_generation_preserves_upstream_ownership(regenerated_tree):
    before, after = regenerated_tree
    assert after == before


def test_runtime_input_drift_requires_review():
    # The existing deterministic checker must actually cover the new artifacts.
    spec=importlib.util.spec_from_file_location('check_runtime',ROOT/'scripts/check-cursor-adaptations.py')
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    assert hasattr(checker,'verify_runtime_contracts'),'admission check does not yet validate runtime inputs'
    result=checker.verify_runtime_contracts()
    assert result=={'skills':107,'profiles':14,'live_workflows_claimed':False}


def test_no_profile_native_bytes_are_replaced(regenerated_tree):
    before, after = regenerated_tree
    coverage = json.loads((ROOT / 'sources/cursor-plugins/agent-coverage.json').read_text())['agents']
    for profile in coverage.values():
        path = profile['asset_path']
        assert before[path] == after[path] == profile['asset_sha256'], path


def test_compatibility_document_separates_proof_and_future_runtime():
    file=ROOT/'docs/cursor-runtime-compatibility.md'
    assert file.exists(),'compatibility and rollback documentation missing'
    text=file.read_text()
    assert 'Hermes' in text and 'ACP' in text
    assert 'not a live workflow certificate' in text
    assert 'Rollback' in text


def test_baseline_checks_do_not_need_git_objects(monkeypatch, regenerated_tree):
    def unavailable(*args, **kwargs):
        raise subprocess.CalledProcessError(128, args[0], stderr=b'baseline commit is not in a shallow checkout')

    monkeypatch.setattr(subprocess, 'check_output', unavailable)
    test_runtime_generation_preserves_upstream_ownership(regenerated_tree)
    test_no_profile_native_bytes_are_replaced(regenerated_tree)
