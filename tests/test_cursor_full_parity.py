import importlib.util
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_upstream_file_skill_and_agent_is_preserved():
    tree = load('check-cursor-full-tree').verify()
    assert tree['files'] == 1312
    assert tree['commit'] == json.loads((ROOT / 'sources/cursor-plugins/full-tree.json').read_text())['commit']
    assert tree['family_updates'] == {'pstack': '4dd1d05818d19792e7cd6e818f1667f95f7e1dbe'}
    result = load('check-cursor-adaptations').verify()
    assert result == dict(skills=112, published=107, held_adapted=5, agents_mapped=14,
                          unresolved_links=0, runtime_proof='not claimed')


@pytest.mark.parametrize('mutation', ['missing', 'corrupt', 'extra'])
def test_full_tree_rejects_missing_changed_and_untracked_files(tmp_path, mutation):
    check = load('check-cursor-full-tree')
    shutil.copytree(check.BASE / 'upstream-tree', tmp_path / 'upstream-tree')
    shutil.copy2(check.BASE / 'full-tree.json', tmp_path / 'full-tree.json')
    shutil.copy2(check.BASE / 'family-refresh.json', tmp_path / 'family-refresh.json')
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


def test_selected_additions_are_pinned_and_tailscale_is_not_published():
    check = load('check-cursor-adaptations')
    assert check.verify()['published'] == 107
    ledger = json.loads((ROOT / 'sources/cursor-plugins/additions.json').read_text())
    assert set(ledger['files']) == {
        'pstack/skills/in-your-own-words/SKILL.md',
        'pstack/skills/ketchup/SKILL.md',
        'pstack/skills/sharpen/SKILL.md',
    }
    assert not (ROOT / 'skills/mirrors-cursor/cursor-tailscale-setup').exists()
    for name in ['in-your-own-words', 'ketchup', 'sharpen']:
        policy = (ROOT / f'skills/mirrors-cursor/cursor-{name}/agents/openai.yaml').read_text()
        assert 'allow_implicit_invocation: false' in policy


def test_family_refresh_cannot_rewrite_a_non_pstack_path():
    family = load('cursor_pstack_family')
    source = ROOT / 'sources/cursor-plugins'
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        shutil.copy2(source / 'full-tree.json', target / 'full-tree.json')
        shutil.copy2(source / 'family-refresh.json', target / 'family-refresh.json')
        shutil.copytree(source / 'upstream-tree/pstack', target / 'upstream-tree/pstack')
        ledger_path = target / 'family-refresh.json'
        ledger = json.loads(ledger_path.read_text())
        ledger['files']['other-plugin/README.md'] = next(iter(ledger['files'].values()))
        ledger_path.write_text(json.dumps(ledger))
        with pytest.raises(ValueError, match='unsafe pstack family path'):
            family.verify(target)


def test_family_override_must_name_the_historical_hash():
    family = load('cursor_pstack_family')
    source = ROOT / 'sources/cursor-plugins'
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        shutil.copy2(source / 'full-tree.json', target / 'full-tree.json')
        shutil.copy2(source / 'family-refresh.json', target / 'family-refresh.json')
        shutil.copytree(source / 'upstream-tree/pstack', target / 'upstream-tree/pstack')
        ledger_path = target / 'family-refresh.json'
        ledger = json.loads(ledger_path.read_text())
        path = next(iter(ledger['overrides']))
        ledger['overrides'][path]['baseline']['sha256'] = '0' * 64
        ledger_path.write_text(json.dumps(ledger))
        with pytest.raises(ValueError, match='historical baseline'):
            family.verify(target)


@pytest.mark.parametrize('mutation, message', [
    ('path', 'unsafe pstack family path'),
    ('mode', 'invalid pstack family file record'),
    ('sha256', 'invalid pstack family file record'),
    ('source_commit', 'source commit mismatch'),
    ('baseline_commit', 'baseline differs from full-tree pin'),
])
def test_family_ledger_rejects_malformed_provenance(tmp_path, mutation, message):
    family = load('cursor_pstack_family')
    source = ROOT / 'sources/cursor-plugins'
    shutil.copy2(source / 'full-tree.json', tmp_path / 'full-tree.json')
    shutil.copy2(source / 'family-refresh.json', tmp_path / 'family-refresh.json')
    shutil.copytree(source / 'upstream-tree/pstack', tmp_path / 'upstream-tree/pstack')
    ledger_path = tmp_path / 'family-refresh.json'
    ledger = json.loads(ledger_path.read_text())
    path = next(iter(ledger['files']))
    if mutation == 'path':
        ledger['files']['pstack/../escape'] = ledger['files'].pop(path)
    elif mutation in ('mode', 'sha256', 'source_commit'):
        ledger['files'][path][mutation] = 'invalid'
    else:
        ledger[mutation] = '0' * 40
    ledger_path.write_text(json.dumps(ledger))
    with pytest.raises(ValueError, match=message):
        family.verify(tmp_path)


def test_addition_content_drift_is_rejected(tmp_path):
    check = load('check-cursor-adaptations')
    sync = check.sync
    original = sync.SOURCE
    source = original / 'pstack/skills/sharpen/SKILL.md'
    target = tmp_path / 'pstack/skills/sharpen/SKILL.md'
    target.parent.mkdir(parents=True)
    target.write_bytes(source.read_bytes() + b'altered')
    for name in ['in-your-own-words', 'ketchup']:
        dest = tmp_path / f'pstack/skills/{name}/SKILL.md'
        dest.parent.mkdir(parents=True)
        dest.write_bytes((original / f'pstack/skills/{name}/SKILL.md').read_bytes())
    sync.SOURCE = tmp_path
    with pytest.raises(ValueError, match='addition source drift'):
        check.verify()


@pytest.mark.parametrize('mutation', ['tracked', 'untracked', 'ignored'])
def test_refresh_rejects_uncommitted_source_before_writing(tmp_path, monkeypatch, mutation):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    refresh = load('refresh-cursor-pstack-family')
    upstream = tmp_path / 'upstream'
    source = upstream / 'pstack/SKILL.md'
    source.parent.mkdir(parents=True)
    source.write_text('committed')
    (upstream / '.gitignore').write_text('pstack/ignored.txt\n')
    subprocess.run(['git', 'init', '-q', str(upstream)], check=True)
    subprocess.run(['git', '-C', str(upstream), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(upstream), '-c', 'user.name=Fixture',
                    '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'fixture'], check=True)
    if mutation == 'tracked':
        source.write_text('modified')
    else:
        (source.parent / f'{mutation}.txt').write_text('uncommitted')
    output = tmp_path / 'output'
    output.mkdir()
    sentinel = output / 'manifest.json'
    sentinel.write_text('preserve')
    with pytest.raises(ValueError, match='checkout is dirty'):
        refresh.refresh(upstream, base=output, root=tmp_path)
    assert sentinel.read_text() == 'preserve'
    assert sorted(path.name for path in output.iterdir()) == ['manifest.json']


def test_refresh_preserves_availability_classification_and_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    refresh = load('refresh-cursor-pstack-family')
    upstream = tmp_path / 'upstream'
    source = upstream / 'pstack/skills/example/SKILL.md'
    source.parent.mkdir(parents=True)
    source.write_text('---\nname: example\ndescription: example\n---\n')
    extra = upstream / 'pstack/skills/unreviewed/SKILL.md'
    extra.parent.mkdir(parents=True)
    extra.write_text('---\nname: unreviewed\ndescription: fixture\n---\n')
    subprocess.run(['git', 'init', '-q', str(upstream)], check=True)
    subprocess.run(['git', '-C', str(upstream), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(upstream), '-c', 'user.name=Fixture',
                    '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'fixture'], check=True)
    output = tmp_path / 'output'
    output.mkdir()
    (output / 'full-tree.json').write_text(json.dumps({'commit': '0' * 40, 'files': {}}))
    manifest = output / 'manifest.json'
    manifest.write_text(json.dumps({'skills': [{'family': 'pstack',
        'path': 'pstack/skills/example/SKILL.md', 'availability': 'guide-only; no runtime proof'}]}))
    (output / 'agent-coverage.json').write_text(json.dumps({'agents': {}}))
    refresh.refresh(upstream, base=output, root=tmp_path)
    assert not (output / 'snapshot/pstack/skills/unreviewed').exists()
    assert (output / 'upstream-tree/pstack/skills/unreviewed/SKILL.md').is_file()
    assert 'pstack/skills/unreviewed/SKILL.md' in json.loads((output / 'unadmitted-skills.json').read_text())['skills']
    first = manifest.read_text()
    availability = json.loads(first)['skills'][0]['availability']
    assert availability.startswith('guide-only; no runtime proof')
    assert availability.count('prior runtime and fixture evidence predates this refresh') == 1
    refresh.refresh(upstream, base=output, root=tmp_path)
    assert manifest.read_text() == first


@pytest.mark.parametrize('baseline_case', ['valid', 'missing_commit', 'content', 'missing_file', 'mode'])
def test_family_refresh_checks_preserved_baseline_git_tree(tmp_path, baseline_case):
    check = load('check-cursor-full-tree')
    upstream = tmp_path / 'upstream'
    upstream.mkdir()
    subprocess.run(['git', 'init', '-q', str(upstream)], check=True)
    pstack = upstream / 'pstack/SKILL.md'
    pstack.parent.mkdir()
    pstack.write_text('old pstack')
    other = upstream / 'other-plugin.txt'
    other.write_text('baseline other plugin')

    def commit():
        subprocess.run(['git', '-C', str(upstream), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(upstream), '-c', 'user.name=Fixture',
                        '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'fixture'], check=True)
        return subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()

    def record(text, source_commit):
        data = text.encode()
        return {'mode': '100644', 'git_blob': hashlib.sha1(
            b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
            'sha256': hashlib.sha256(data).hexdigest(), 'source_commit': source_commit}

    baseline = commit()
    pstack.write_text('new pstack')
    other.write_text('later upstream other plugin')
    head = commit()
    base = tmp_path / 'preserved'
    tree = base / 'upstream-tree'
    (tree / 'pstack').mkdir(parents=True)
    (tree / 'pstack/SKILL.md').write_text('new pstack')
    (tree / 'other-plugin.txt').write_text('baseline other plugin')
    old_pstack = record('old pstack', baseline)
    other_record = record('baseline other plugin', baseline)
    current = record('new pstack', head)
    files = {'pstack/SKILL.md': old_pstack, 'other-plugin.txt': other_record}
    if baseline_case == 'content':
        files['other-plugin.txt'] = record('unrelated content', baseline)
        (tree / 'other-plugin.txt').write_text('unrelated content')
    elif baseline_case == 'missing_file':
        del files['other-plugin.txt']
        (tree / 'other-plugin.txt').unlink()
    elif baseline_case == 'mode':
        files['other-plugin.txt']['mode'] = '100755'
        (tree / 'other-plugin.txt').chmod(0o755)
    elif baseline_case == 'missing_commit':
        shallow = tmp_path / 'shallow'
        subprocess.run(['git', 'clone', '-q', '--depth=1', upstream.as_uri(), str(shallow)], check=True)
        upstream = shallow
    (base / 'full-tree.json').write_text(json.dumps({'commit': baseline, 'files': files}))
    (base / 'family-refresh.json').write_text(json.dumps({
        'family': 'pstack', 'baseline_commit': baseline, 'source_commit': head,
        'files': {'pstack/SKILL.md': current},
        'overrides': {'pstack/SKILL.md': {'baseline': old_pstack, 'current': current}},
    }))
    check.BASE = base
    if baseline_case == 'valid':
        assert check.verify(upstream)['family_updates'] == {'pstack': head}
    else:
        with pytest.raises((ValueError, subprocess.CalledProcessError)):
            check.verify(upstream)


@pytest.mark.parametrize('mutation', ['valid', 'unreviewed-path', 'wrong-pin', 'changed-bytes', 'symlink'])
def test_reviewed_file_updates_preserve_baseline_and_verify_git_provenance(tmp_path, mutation):
    family = load('cursor_pstack_family')
    upstream = tmp_path / 'source'
    upstream.mkdir()
    relative = 'other-plugin/skills/example/SKILL.md'
    target = upstream / relative
    target.parent.mkdir(parents=True)
    target.write_text('historical source')
    subprocess.run(['git', 'init', '-q', str(upstream)], check=True)
    def commit():
        subprocess.run(['git', '-C', str(upstream), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(upstream), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'source'], check=True)
        return subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    before = commit()
    baseline_record = family.record(target, '100644')
    target.write_text('reviewed source update')
    after = commit()
    base = tmp_path / 'ledger'
    snapshot = base / 'upstream-tree' / relative
    snapshot.parent.mkdir(parents=True)
    shutil.copy2(target, snapshot)
    baseline = dict(commit=before, files={relative: baseline_record})
    (base / 'full-tree.json').write_text(json.dumps(baseline))
    record = {**family.record(target, '100644'), 'source_commit': after}
    records = {relative: record}
    if mutation == 'unreviewed-path':
        records = {'../outside.txt': record}
    elif mutation == 'wrong-pin':
        record['source_commit'] = before
    elif mutation == 'changed-bytes':
        snapshot.write_text('unreviewed bytes')
    elif mutation == 'symlink':
        snapshot.unlink()
        snapshot.symlink_to(target)
    (base / 'reviewed-file-updates.json').write_text(json.dumps(dict(schema_version=1, baseline_commit=before, files=records)))
    if mutation == 'valid':
        assert family.reviewed_file_updates(base, upstream) == records
        assert json.loads((base / 'full-tree.json').read_text()) == baseline
    else:
        with pytest.raises(ValueError, match='reviewed file'):
            family.reviewed_file_updates(base, upstream)


def test_unadmitted_skill_commit_must_match_reviewed_source(tmp_path):
    check = load('check-cursor-adaptations')
    path = 'pstack/skills/new-skill/SKILL.md'
    full = {'files': {path: {'sha256': 'a' * 64, 'source_commit': '1' * 40}}}
    pending = {path: {'state': 'pending_review', 'sha256': 'a' * 64, 'source_commit': '1' * 40}}
    check.verify_unadmitted(full, set(), pending, tmp_path)
    pending[path]['source_commit'] = '2' * 40
    with pytest.raises(ValueError, match='invalid unadmitted source record'):
        check.verify_unadmitted(full, set(), pending, tmp_path)
