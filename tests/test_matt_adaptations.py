import importlib.util
import json
from datetime import date
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('matt',ROOT/'scripts/sync-matt-adaptations.py')
matt=importlib.util.module_from_spec(spec);spec.loader.exec_module(matt)
ITEMS=json.loads((ROOT/'scripts/matt-adaptations.json').read_text())

def test_manifest_contains_the_approved_surface_only():
    names={item['name'] for item in ITEMS}
    assert len(ITEMS)==33
    assert len(names-{ 'ask-pit' })==32
    assert sum(item['overlay']=='patch' for item in ITEMS if item['name']!='ask-pit')==19
    assert sum(item['overlay']=='empty' for item in ITEMS)==13
    assert not names & {'ask-matt','writing-for-agents','claude-handoff','git-guardrails-claude-code',
                        'migrate-to-shoehorn','setup-pre-commit','setup-ts-deep-modules'}
    assert all(item['destination'].startswith('skills/mirrors-mattpocock/')
               for item in ITEMS if item['name']!='ask-pit')
    assert next(item for item in ITEMS if item['name']=='retro')['source_path']=='skills/engineering/retro'
    assert next(item for item in ITEMS if item['name']=='implement-spec')['source_path']=='skills/engineering/implement-spec'


def test_new_pr_source_is_verbatim_and_provenance_uses_first_review():
    item=next(i for i in ITEMS if i['name']=='pr')
    package=ROOT/item['destination']
    record=json.loads((package/'UPSTREAM.json').read_text())
    provenance=(package/'PROVENANCE.md').read_text()
    assert item['source_path']=='skills/engineering/pr'
    assert item['overlay']=='empty'
    assert record['commit']=='4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d'
    assert record['overlay']=='empty'
    assert (package/'ADAPTATIONS.patch').read_bytes()==b''
    assert 'Original integration source revision: 24fe0ef7737efae15c87225755e9f6f5965e4888.' in provenance
    assert 'first source inclusion on 2026-10-05' in provenance
    assert 'OpenAI Astra guidance' not in provenance
    assert 'author: Dex Horthy' in (package/'SKILL.md').read_text()
    assert 'organisation: Humanlayer' in (package/'SKILL.md').read_text()


@pytest.mark.parametrize('item',ITEMS,ids=lambda i:i['name'])
def test_all_approved_overlays_reverse_to_upstream(item):
    matt.validate(ROOT/item['destination'])


def test_empty_overlay_is_explicit_and_reversible(tmp_path):
    item=next(i for i in ITEMS if i['name']=='domain-modeling')
    package=ROOT/item['destination']
    assert item['overlay']=='empty'
    assert (package/'ADAPTATIONS.patch').read_bytes()==b''
    work=tmp_path/'reverse'; work.mkdir()
    target=work/item['name']; shutil.copytree(package,target)
    before=matt.file_map(target)
    matt.patch(work,item['name'],reverse=True)
    assert matt.file_map(target)==before


def fixture_source(tmp_path):
    item=next(i for i in ITEMS if i['name']=='code-review')
    work=tmp_path/'reverse';work.mkdir()
    target=work/item['name'];shutil.copytree(ROOT/item['destination'],target)
    matt.patch(work,item['name'],reverse=True)
    checkout=tmp_path/'upstream';src=checkout/item['source_path'];src.parent.mkdir(parents=True)
    shutil.copytree(target,src)
    for name in ('ADAPTATIONS.patch','PROVENANCE.md','UPSTREAM.json'):(src/name).unlink()
    (src/'LICENSE').rename(checkout/'LICENSE')
    subprocess.run(['git','init','-q',str(checkout)],check=True)
    subprocess.run(['git','-C',str(checkout),'add','.'],check=True)
    subprocess.run(['git','-C',str(checkout),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],check=True)
    dest=tmp_path/'adapted';shutil.copytree(ROOT/item['destination'],dest)
    return item,checkout,src,dest


def test_conflicting_upstream_preserves_existing_skill(tmp_path):
    item,checkout,src,dest=fixture_source(tmp_path)
    before=matt.file_map(dest)
    (src/'SKILL.md').write_text('Entirely changed upstream contract\n')
    with pytest.raises(subprocess.CalledProcessError):matt.refresh(checkout,item,dest)
    assert matt.file_map(dest)==before


def test_support_additions_and_removals_preserve_overlay(tmp_path):
    item,checkout,src,dest=fixture_source(tmp_path)
    (src/'new-support.md').write_text('New upstream support')
    (src/'agents/openai.yaml').unlink()
    matt.refresh(checkout,item,dest)
    matt.validate(dest)
    assert (dest/'new-support.md').is_file()
    assert not (dest/'agents/openai.yaml').exists()
    assert 'git diff --cached' in (dest/'SKILL.md').read_text()
    reviewed=json.loads((dest/'UPSTREAM.json').read_text())['commit']
    provenance=(dest/'PROVENANCE.md').read_text()
    assert 'Original integration source revision: 3cca18b368ae95cdbdebbff572ccafa662551015.' in provenance
    assert f'Current upstream review: `{reviewed}` on {date.today().isoformat()}.' in provenance


def test_patch_applies_inside_repository_staging_directory(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir()
    subprocess.run(['git','init','-q',str(repo)],check=True)
    work=repo/'nested'/'stage'; package=work/'example'; package.mkdir(parents=True)
    (package/'SKILL.md').write_text('Before\n')
    (package/'ADAPTATIONS.patch').write_text(
        'diff --git a/example/SKILL.md b/example/SKILL.md\n'
        'index 1234567..abcdef0 100644\n'
        '--- a/example/SKILL.md\n+++ b/example/SKILL.md\n'
        '@@ -1 +1 @@\n-Before\n+After\n')
    matt.patch(work,'example')
    assert (package/'SKILL.md').read_text()=='After\n'
    matt.patch(work,'example',reverse=True)
    assert (package/'SKILL.md').read_text()=='Before\n'


def test_astra_original_integration_is_distinct_from_current_review():
    package = ROOT / 'skills/engineering/writing-for-astra'
    provenance = (package / 'PROVENANCE.md').read_text()
    record = json.loads((package / 'UPSTREAM.json').read_text())
    assert 'Original integration revision: 3cca18b368ae95cdbdebbff572ccafa662551015' in provenance
    assert '4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d' in provenance
    assert record['commit'] == '4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d'
