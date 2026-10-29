#!/usr/bin/env python3
"""Check source adapter coverage, held renderings, agent hashes and cross-pack links."""
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'sources/cursor-plugins'
spec = importlib.util.spec_from_file_location('cursor_sync', ROOT / 'scripts/sync-cursor-plugin-skills.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)
family_spec = importlib.util.spec_from_file_location('cursor_pstack_family', ROOT / 'scripts/cursor_pstack_family.py')
family = importlib.util.module_from_spec(family_spec)
family_spec.loader.exec_module(family)


def verify_runtime_contracts():
    spec = importlib.util.spec_from_file_location('cursor_runtime_contracts', ROOT / 'scripts/cursor_runtime_contracts.py')
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    manifest = json.loads((BASE / 'manifest.json').read_text())
    contracts = runtime.load_contracts(BASE / 'runtime-adapters/compatibility.json', manifest['skills'])
    runtime.verify_runtime_packages(sync.DEST, contracts)
    live = any(item['t3']['evidence'] == 'live' for group in ('skills', 'profiles') for item in contracts[group].values())
    return {'skills': len(contracts['skills']), 'profiles': len(contracts['profiles']), 'live_workflows_claimed': live}


def verify(write_held=False):
    manifest = json.loads((BASE / 'manifest.json').read_text())
    full = json.loads((BASE / 'full-tree.json').read_text())
    if (BASE / family.LEDGER_NAME).exists():
        family.verify(BASE)
    additions_path = BASE / 'additions.json'
    if additions_path.exists():
        additions = json.loads(additions_path.read_text())
        for path, record in additions['files'].items():
            if path in full['files']:
                raise ValueError('addition collides with preserved baseline: ' + path)
            source = sync.SOURCE / path
            data = source.read_bytes()
            blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if hashlib.sha256(data).hexdigest() != record['sha256'] or blob != record['git_blob']:
                raise ValueError('addition source drift: ' + path)
            entry = next((e for e in manifest['skills'] if e['path'] == path), None)
            if entry is None or entry.get('source_commit') != record['source_commit']:
                raise ValueError('addition pin drift: ' + path)
            full['files'][path] = record
    if (BASE / family.LEDGER_NAME).exists():
        full['files'] = family.merged_inventory(BASE)
    entries = manifest['skills']
    if {e['path'] for e in entries} != {p for p in full['files'] if p.endswith('/SKILL.md')}:
        raise ValueError('skill adapter coverage is incomplete')
    for entry in entries:
        for relative, digest in entry['files'].items():
            source = (Path(entry['path']).parent / relative).as_posix()
            if full['files'].get(source, {}).get('sha256') != digest:
                raise ValueError(f'adapter snapshot is not current: {source}')
    held = BASE / 'adapted-held'
    with tempfile.TemporaryDirectory() as temporary:
        stage = Path(temporary)
        mapping = {(sync.SOURCE / e['path']).resolve(): e for e in entries}
        for entry in entries:
            if entry.get('excluded_from_mirror'):
                sync.render_skill(entry, stage, manifest['upstream_commit'], mapping)
        if write_held:
            held.mkdir(exist_ok=True)
            for source in stage.rglob('*'):
                if source.is_file():
                    target = held / source.relative_to(stage)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
        if sync.compare_trees(stage, held):
            raise ValueError('held source adapters differ; regenerate explicitly with --write-held')
    coverage = json.loads((BASE / 'agent-coverage.json').read_text())['agents']
    upstream_agents = {p for p in full['files'] if '/agents/' in p and p.endswith('.md')}
    if set(coverage) != upstream_agents:
        raise ValueError('agent mapping coverage is incomplete')
    for source, record in coverage.items():
        asset = ROOT / record['asset_path']
        if hashlib.sha256(asset.read_bytes()).hexdigest() != record['asset_sha256']:
            raise ValueError(f'agent asset drift: {source}')
        if full['files'][source]['sha256'] != record['source_sha256']:
            raise ValueError(f'agent source drift: {source}')
        if tomllib.loads(asset.read_text())['name'] != record['native_name']:
            raise ValueError(f'agent native name drift: {source}')
    names = {e['published_name'] for e in entries}
    missing = []
    for entry in entries:
        directory = (held if entry.get('excluded_from_mirror') else sync.DEST) / entry['published_name']
        for source in directory.rglob('*.md'):
            if source.name == 'MIRROR.md':
                continue
            text = source.read_text()
            for name in re.findall(r'(?<![\w-])cursor-[a-z][a-z0-9]*(?:-[a-z0-9]+)+', text):
                if name not in names and name != 'cursor-team-kit':
                    missing.append(f'{entry["published_name"]}: unknown native skill {name}')
            for target in re.findall(r'\]\(([^)]+)\)', text):
                path = target.split('#', 1)[0]
                if not path or ':' in path or path.startswith('/'):
                    continue
                resolved = (source.parent / path).resolve()
                if resolved.exists():
                    continue
                # Held adapters are not installed beside the published catalog.
                peer = re.match(r'\.\./(cursor-[\w-]+)/(.*)', path)
                if peer and peer.group(1) in names:
                    for root in (sync.DEST, held):
                        if (root / peer.group(1) / peer.group(2)).exists():
                            break
                    else:
                        missing.append(f'{entry["published_name"]}: {target}')
                    continue
                missing.append(f'{entry["published_name"]}: {target}')
    if missing:
        raise ValueError('unresolved cross-pack links: ' + '; '.join(missing))
    if (BASE / 'runtime-adapters/compatibility.json').exists():
        verify_runtime_contracts()
    return {'skills': len(entries), 'published': sum(e['publish'] for e in entries),
            'held_adapted': sum(bool(e.get('excluded_from_mirror')) for e in entries),
            'agents_mapped': len(coverage), 'unresolved_links': 0,
            'runtime_proof': 'not claimed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-held', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify(args.write_held), indent=2))
