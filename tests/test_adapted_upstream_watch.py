import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('watch', ROOT / 'scripts/check-adapted-skill-upstreams.py')
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


def test_detects_addition_removal_change():
    assert watch.changed_files({'old': 'a', 'changed': 'b', 'same': 'c'},
                               {'new': 'd', 'changed': 'e', 'same': 'c'}) == ['changed', 'new', 'old']


def test_watch_preserves_skills_and_baselines_and_ignores_other_paths(tmp_path):
    upstream = tmp_path / 'upstream'; upstream.mkdir()
    (upstream / 'LICENSE').write_text('MIT fixture')
    repo = tmp_path / 'ours'
    for package in watch.PACKAGES:
        source = 'skills/' + Path(package).name
        (upstream / source).mkdir(parents=True)
        (upstream / source / 'SKILL.md').write_text('original')
        dest = repo / package; dest.mkdir(parents=True)
        (dest / 'SKILL.md').write_text('our adaptation')
        (dest / 'UPSTREAM.json').write_text(json.dumps(dict(commit='reviewed', source_path=source,
                                                          upstream_sha256=watch.snapshot(upstream, source))))
    subprocess.run(['git', 'init', '-q', str(upstream)], check=True)
    subprocess.run(['git', '-C', str(upstream), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(upstream), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
    before = {str(p):p.read_bytes() for p in repo.rglob('*') if p.is_file()}
    (upstream / 'unrelated.md').write_text('not this package')
    assert watch.check(upstream, repo) == []
    (upstream / 'skills/ask-pit/SKILL.md').unlink()
    reports = watch.check(upstream, repo)
    assert len(reports) == 1 and reports[0]['changed'] == ['SKILL.md']
    assert before == {str(p):p.read_bytes() for p in repo.rglob('*') if p.is_file()}


def test_watch_reports_drift_for_empty_overlay_without_mutating_baseline(tmp_path):
    upstream = tmp_path / 'upstream'; upstream.mkdir()
    source = upstream / 'skills/domain-modeling'; source.mkdir(parents=True)
    (upstream / 'LICENSE').write_text('MIT fixture')
    (source / 'SKILL.md').write_text('original')
    repo = tmp_path / 'ours'; dest = repo / 'skills/mirrors-mattpocock/domain-modeling'
    dest.mkdir(parents=True)
    (dest / 'SKILL.md').write_text('original')
    (dest / 'ADAPTATIONS.patch').write_bytes(b'')
    (dest / 'UPSTREAM.json').write_text(json.dumps(dict(
        name='domain-modeling', commit='reviewed', source_path='skills/domain-modeling',
        overlay='empty', upstream_sha256=watch.snapshot(upstream, 'skills/domain-modeling'))))
    subprocess.run(['git', 'init', '-q', str(upstream)], check=True)
    subprocess.run(['git', '-C', str(upstream), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(upstream), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                    'commit', '-qm', 'fixture'], check=True)
    before = {str(p):p.read_bytes() for p in repo.rglob('*') if p.is_file()}
    (source / 'SKILL.md').write_text('changed upstream')
    original_packages = watch.PACKAGES
    watch.PACKAGES = (str(dest.relative_to(repo)),)
    try:
        reports = watch.check(upstream, repo)
    finally:
        watch.PACKAGES = original_packages
    assert len(reports) == 1
    assert reports[0]['skill'] == 'domain-modeling'
    assert reports[0]['changed'] == ['SKILL.md']
    assert before == {str(p):p.read_bytes() for p in repo.rglob('*') if p.is_file()}
