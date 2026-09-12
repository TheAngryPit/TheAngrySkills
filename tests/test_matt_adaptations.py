import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('matt',ROOT/'scripts/sync-matt-adaptations.py')
matt=importlib.util.module_from_spec(spec);spec.loader.exec_module(matt)
ITEMS=json.loads((ROOT/'scripts/matt-adaptations.json').read_text())

@pytest.mark.parametrize('item',ITEMS,ids=lambda i:i['name'])
def test_all_approved_overlays_reverse_to_upstream(item):
    matt.validate(ROOT/item['destination'])


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
