#!/usr/bin/env python3
"""Prove complete raw Cursor source preservation without executing upstream files."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'sources/cursor-plugins'


def verify(upstream=None):
    ledger = json.loads((BASE / 'full-tree.json').read_text())
    tree = BASE / 'upstream-tree'
    actual = {p.relative_to(tree).as_posix(): p for p in tree.rglob('*') if p.is_file() or p.is_symlink()}
    if set(actual) != set(ledger['files']):
        raise ValueError('full upstream inventory drift')
    for name, record in ledger['files'].items():
        path = actual[name]
        if path.is_symlink():
            raise ValueError(f'unsupported upstream symlink: {name}')
        data = path.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if hashlib.sha256(data).hexdigest() != record['sha256'] or blob != record['git_blob']:
            raise ValueError(f'full upstream content drift: {name}')
        if record['mode'] not in ('100644', '100755'):
            raise ValueError(f'unsupported upstream mode: {name}')
    if upstream:
        head = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
        if head != ledger['commit']:
            raise ValueError('upstream commit differs from full-tree pin')
        observed = {}
        for line in subprocess.check_output(['git', '-C', str(upstream), 'ls-tree', '-r', 'HEAD'], text=True).splitlines():
            meta, name = line.split('\t')
            mode, kind, blob = meta.split()
            observed[name] = (mode, blob)
            if kind != 'blob':
                raise ValueError(f'unsupported upstream entry: {name}')
        expected = {name: (record['mode'], record['git_blob']) for name, record in ledger['files'].items()}
        if observed != expected:
            raise ValueError('upstream Git tree inventory differs from preserved tree')
    return {'files': len(actual), 'skills': sum(n.endswith('/SKILL.md') for n in actual),
            'agents': sum('/agents/' in n and n.endswith('.md') for n in actual),
            'commit': ledger['commit'], 'runtime_activation': 'not performed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--upstream', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.upstream), indent=2))
