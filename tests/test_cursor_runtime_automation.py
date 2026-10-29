import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
BASE='ecd94d59f67ad39c33f53a88b04a4c9d092cde4b'


def tracked_bytes(revision,path):
    return subprocess.check_output(['git','show',f'{revision}:{path}'],cwd=ROOT)


def test_runtime_generation_preserves_upstream_ownership():
    for folder in ['.github/workflows','sources/cursor-plugins/snapshot','sources/cursor-plugins/upstream-tree']:
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,folder],cwd=ROOT,text=True).splitlines()
        assert paths
        for path in paths:assert (ROOT/path).read_bytes()==tracked_bytes(BASE,path),path
    for file in ['scripts/detect-upstream-updates.py','scripts/upstream-pr-lifecycle.py',
                 'sources/cursor-plugins/manifest.json','sources/cursor-plugins/full-tree.json',
                 'sources/cursor-plugins/family-refresh.json','sources/cursor-plugins/agent-coverage.json']:
        assert (ROOT/file).read_bytes()==tracked_bytes(BASE,file),file


def test_runtime_input_drift_requires_review():
    # The existing deterministic checker must actually cover the new artifacts.
    spec=importlib.util.spec_from_file_location('check_runtime',ROOT/'scripts/check-cursor-adaptations.py')
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    assert hasattr(checker,'verify_runtime_contracts'),'admission check does not yet validate runtime inputs'
    result=checker.verify_runtime_contracts()
    assert result=={'skills':107,'profiles':14,'live_workflows_claimed':False}


def test_no_profile_native_bytes_are_replaced():
    coverage=json.loads((ROOT/'sources/cursor-plugins/agent-coverage.json').read_text())['agents']
    for profile in coverage.values():
        assert (ROOT/profile['asset_path']).read_bytes()==tracked_bytes(BASE,profile['asset_path'])


def test_compatibility_document_separates_proof_and_future_runtime():
    file=ROOT/'docs/cursor-runtime-compatibility.md'
    assert file.exists(),'compatibility and rollback documentation missing'
    text=file.read_text()
    assert 'Hermes' in text and 'ACP' in text
    assert 'not a live workflow certificate' in text
    assert 'Rollback' in text
