#!/usr/bin/env python3
"""Rebuild approved Matt adaptations for review; no automatic upstream acceptance."""
import argparse
from datetime import date
import hashlib
import importlib.util
import json
import re
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'scripts/matt-adaptations.json'
REPOSITORY = 'https://github.com/mattpocock/skills.git'
ASTRA_GUIDANCE = 'https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra'


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
    patch_file = work / name / 'ADAPTATIONS.patch'
    if not patch_file.read_bytes().strip():
        return
    args = ['git', 'apply'] + (['--reverse'] if reverse else [])
    env = os.environ.copy()
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
        env.pop(key, None)
    env['GIT_CEILING_DIRECTORIES'] = str(work.parent.resolve())
    subprocess.run(args + [str(patch_file)], cwd=work, env=env, check=True, capture_output=True)


def prefix_patch(data, name):
    """Prefix only patch path headers so git apply runs from the work parent."""
    prefix = name.encode() + b'/'
    result = []
    for line in data.splitlines(keepends=True):
        if line.startswith(b'--- a/') and not line.startswith(b'--- a/' + prefix):
            line = b'--- a/' + prefix + line[len(b'--- a/'):]
        elif line.startswith(b'+++ b/') and not line.startswith(b'+++ b/' + prefix):
            line = b'+++ b/' + prefix + line[len(b'+++ b/'):]
        elif line.startswith(b'diff --git a/'):
            marker = b'diff --git a/'
            rest = line[len(marker):]
            left, separator, right = rest.partition(b' b/')
            if separator and not left.startswith(prefix) and not right.startswith(prefix):
                line = marker + prefix + left + separator + prefix + right
        result.append(line)
    return b''.join(result)


def render_provenance(item, patch_data):
    overlay = item.get('overlay') or ('empty' if not patch_data.strip() else 'patch')
    reviewed_revision = item.get('reviewed_source_revision', '3cca18b368ae95cdbdebbff572ccafa662551015')
    approval_notice = item.get(
        'provenance_approval_notice',
        'Operator approved the final Matt Pocock integration on 2026-09-12. MIT attribution is retained in LICENSE.',
    )
    provenance_basis = item.get('provenance_basis', ASTRA_GUIDANCE)
    if overlay == 'empty':
        change = ('No content adaptation is approved for this package. The upstream '
                  'files are preserved verbatim behind an explicit empty overlay.')
    else:
        change = item.get('provenance_summary', 'The approved adaptation is recorded in ADAPTATIONS.patch.')
    overlay_note = ('The empty file is intentional for a maintained copy.'
                    if overlay == 'empty' else
                    'The patch file contains only the approved overlay.')
    lines = [
        f"# {item['name']}: approved adaptation",
        '',
        f'Source: [{REPOSITORY}]({REPOSITORY}).',
        f'Reviewed source revision: {reviewed_revision}.',
        approval_notice,
        '',
        '## What changed and why',
        '',
        change,
        '',
        f'The exact approved difference is [ADAPTATIONS.patch](ADAPTATIONS.patch). {overlay_note}',
    ]
    if provenance_basis:
        lines.append(f'Basis: [OpenAI Astra guidance]({provenance_basis}).')
    lines.extend([
        'No additional behavior was invented during integration.',
        '',
        '## Upstream review',
        '',
        'The daily Review adapted skill upstreams workflow alerts through a GitHub issue',
        'when source files, supporting files or license change. It does not overwrite this',
        'skill or accept a new baseline. UPSTREAM.json records reviewed hashes and commit.',
        'During an approved review, scripts/sync-matt-adaptations.py builds in a temporary',
        'directory, reapplies this overlay and validates it. A patch conflict preserves the',
        'published version. Review every new upstream change before merging.',
    ])
    return ('\n'.join(lines) + '\n').encode()


def record_current_source_review(provenance, previous_commit, current_commit):
    """Keep the original integration record distinct from a refreshed source pin."""
    text = provenance.decode('utf-8')
    if previous_commit == current_commit:
        return provenance
    text = text.replace('Reviewed source revision:', 'Original integration source revision:', 1)
    text = re.sub(r'(?m)^Current upstream review: `([0-9a-f]{40})`',
                  lambda match: match.group(0) if match.group(1) == current_commit
                  else f'Historical upstream review: `{match.group(1)}`', text)
    marker = f'Current upstream review: `{current_commit}`'
    if marker not in text:
        line = (f'{marker} on {date.today().isoformat()}. Per-file source hashes are '
                'recorded in UPSTREAM.json.')
        heading = '## Upstream review\n'
        if heading not in text:
            raise ValueError('Provenance is missing the upstream review section')
        text = text.replace(heading, line + '\n\n' + heading, 1)
    return text.encode('utf-8')


def bootstrap_assets(item, proposal_root):
    """Load one approved proposal only while first creating a new package."""
    proposal = item.get('proposal_patch')
    if proposal:
        if proposal_root is None:
            raise ValueError('Missing --proposals-root for new approved package: ' + item['name'])
        patch_data = prefix_patch((Path(proposal_root) / proposal).read_bytes(), item['name'])
    elif item.get('overlay') == 'empty':
        patch_data = b''
    else:
        raise ValueError('New package has no approved overlay source: ' + item['name'])
    return patch_data, render_provenance(item, patch_data)


def validate(destination):
    destination = Path(destination)
    record = json.loads((destination / 'UPSTREAM.json').read_text())
    patch_data = (destination / 'ADAPTATIONS.patch').read_bytes()
    overlay = record.get('overlay')
    if overlay == 'empty' and patch_data.strip():
        raise ValueError('Empty overlay contains patch content')
    if overlay == 'patch' and not patch_data.strip():
        raise ValueError('Non-empty overlay is missing patch content')
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


def refresh(checkout, item, destination=None, proposal_root=None):
    checkout = Path(checkout)
    destination = Path(destination or ROOT / item['destination'])
    # Preserve operator-owned maintenance records, never copy them from upstream.
    if destination.exists():
        patch_data = (destination / 'ADAPTATIONS.patch').read_bytes()
        provenance = (destination / 'PROVENANCE.md').read_bytes()
    else:
        patch_data, provenance = bootstrap_assets(item, proposal_root)
    expected_overlay = item.get('overlay') or ('empty' if not patch_data.strip() else 'patch')
    if expected_overlay == 'empty' and patch_data.strip():
        raise ValueError('Approved empty overlay contains patch content: ' + item['name'])
    if expected_overlay == 'patch' and not patch_data.strip():
        raise ValueError('Approved non-empty overlay has no patch content: ' + item['name'])
    original = file_map(checkout / item['source_path'])
    if 'SKILL.md' not in original:
        raise ValueError('Upstream skill missing')
    if any(n in original for n in ('UPSTREAM.json','PROVENANCE.md','ADAPTATIONS.patch')):
        raise ValueError('Upstream maintenance file collision')
    original['LICENSE'] = (checkout / 'LICENSE').read_bytes()
    commit = subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
    if destination.exists():
        previous = json.loads((destination / 'UPSTREAM.json').read_text())
        provenance = record_current_source_review(provenance, previous.get('commit'), commit)
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
        record=dict(name=item['name'], repository=REPOSITORY, source_path=item['source_path'], commit=commit,
                    adaptation_patch='ADAPTATIONS.patch', overlay=expected_overlay,
                    upstream_sha256={k:sha(v) for k,v in original.items()}, generated_sha256={k:sha(v) for k,v in content.items()})
        (stage/'UPSTREAM.json').write_text(json.dumps(record,indent=2)+'\n')
        validate(stage)
        backup=work/'previous'
        had_destination = destination.exists()
        if had_destination:
            destination.rename(backup)
        try:
            stage.rename(destination)
        except BaseException:
            if had_destination and backup.exists():
                backup.rename(destination)
            raise
    print('validated adaptation: '+item['name'])


def main(single=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--upstream',type=Path)
    p.add_argument('--check',action='store_true')
    p.add_argument('--skill')
    p.add_argument('--proposals-root', type=Path,
                   help='Read approved proposal patches only when creating new packages')
    args=p.parse_args()
    selected=single or args.skill
    items=[x for x in json.loads(CONFIG.read_text()) if not selected or x['name']==selected]
    if not items: p.error('Unknown adapted skill')
    if args.check:
        for item in items: validate(ROOT/item['destination'])
    elif args.upstream:
        for item in items:
            if item.get('refresh_policy') == 'pinned_legacy':
                if selected:
                    p.error(f"{item['name']} is pinned legacy; use --check to validate its retained package")
                validate(ROOT / item['destination'])
                print('retained pinned legacy: ' + item['name'])
                continue
            refresh(args.upstream, item, proposal_root=args.proposals_root)
    else:
        p.error('Use --upstream with a reviewed checkout, or --check; updates require review')


if __name__=='__main__':
    main()
