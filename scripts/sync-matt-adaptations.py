#!/usr/bin/env python3
"""Rebuild approved Matt adaptations for review; no automatic upstream acceptance."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'scripts/matt-adaptations.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_ask():
    spec = importlib.util.spec_from_file_location('ask_base', ROOT / 'scripts/sync-ask-pit.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def file_map(root):
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise ValueError('Symlink requires review: ' + str(p))
        if p.is_file():
            result[str(p.relative_to(root))] = p.read_bytes()
    return result


def patch(work, name, reverse=False):
    args = ['git', 'apply'] + (['--reverse'] if reverse else [])
    subprocess.run(args + [str(work / name / 'ADAPTATIONS.patch')], cwd=work, check=True, capture_output=True)


def validate(destination):
    destination = Path(destination)
    record = json.loads((destination / 'UPSTREAM.json').read_text())
    actual = file_map(destination)
    if set(actual) != set(record['generated_sha256']) | {'UPSTREAM.json'}:
        raise ValueError('Adapted file inventory mismatch')
    for name, expected in record['generated_sha256'].items():
        if sha(actual[name]) != expected:
            raise ValueError('Adapted content changed: ' + name)
    # Reversibility proves that only the approved overlay and AskPit packaging
    # separate the shipped content from the recorded upstream source.
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp); target = work / record['name']
        shutil.copytree(destination, target)
        patch(work, record['name'], reverse=True)
        original = file_map(target)
        for meta in ('UPSTREAM.json', 'PROVENANCE.md', 'ADAPTATIONS.patch'):
            original.pop(meta)
        if record['name'] == 'ask-pit':
            original['SKILL.md'] = original['SKILL.md'].replace(b'name: ask-pit\n', b'name: ask-matt\n', 1).replace(b'/writing-for-astra', b'/writing-for-agents')
            key = 'agents/openai.yaml'
            if key in original:
                original[key] = original[key].replace(b'  display_name: "AskPit"', b'  display_name: "Ask Matt"')
        if {k:sha(v) for k,v in original.items()} != record['upstream_sha256']:
            raise ValueError('Unapproved difference from upstream')


def refresh(checkout, item, destination=None):
    checkout = Path(checkout)
    destination = Path(destination or ROOT / item['destination'])
    # Preserve operator-owned maintenance records, never copy them from upstream.
    patch_data = (destination / 'ADAPTATIONS.patch').read_bytes()
    provenance = (destination / 'PROVENANCE.md').read_bytes()
    original = file_map(checkout / item['source_path'])
    if 'SKILL.md' not in original:
        raise ValueError('Upstream skill missing')
    if any(n in original for n in ('UPSTREAM.json','PROVENANCE.md','ADAPTATIONS.patch')):
        raise ValueError('Upstream maintenance file collision')
    original['LICENSE'] = (checkout / 'LICENSE').read_bytes()
    commit = subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
    with tempfile.TemporaryDirectory(prefix='.matt-', dir=destination.parent) as temp:
        work = Path(temp); stage = work / item['name']
        stage.mkdir()
        if item['name'] == 'ask-pit':
            load_ask().refresh(checkout, stage)
        else:
            for name, data in original.items():
                p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        (stage/'ADAPTATIONS.patch').write_bytes(patch_data)
        (stage/'PROVENANCE.md').write_bytes(provenance)
        patch(work,item['name'])
        content=file_map(stage);content.pop('UPSTREAM.json',None)
        record=dict(name=item['name'],repository='https://github.com/mattpocock/skills.git',source_path=item['source_path'],commit=commit,
                    adaptation_patch='ADAPTATIONS.patch',upstream_sha256={k:sha(v) for k,v in original.items()},generated_sha256={k:sha(v) for k,v in content.items()})
        (stage/'UPSTREAM.json').write_text(json.dumps(record,indent=2)+'\n')
        validate(stage)
        backup=work/'previous'
        destination.rename(backup)
        try:
            stage.rename(destination)
        except BaseException:
            backup.rename(destination)
            raise
    print('validated adaptation: '+item['name'])


def main(single=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--upstream',type=Path)
    p.add_argument('--check',action='store_true')
    p.add_argument('--skill')
    args=p.parse_args()
    selected=single or args.skill
    items=[x for x in json.loads(CONFIG.read_text()) if not selected or x['name']==selected]
    if not items: p.error('Unknown adapted skill')
    if args.check:
        for item in items: validate(ROOT/item['destination'])
    elif args.upstream:
        for item in items: refresh(args.upstream,item)
    else:
        p.error('Use --upstream with a reviewed checkout, or --check; updates require review')


if __name__=='__main__':
    main()
