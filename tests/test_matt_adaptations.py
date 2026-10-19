import importlib.util
import json
import os
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
    assert sum(item['overlay']=='patch' for item in ITEMS if item['name']!='ask-pit')==21
    assert sum(item['overlay']=='empty' for item in ITEMS)==11
    assert not names & {'ask-matt','writing-for-agents','claude-handoff','git-guardrails-claude-code',
                        'migrate-to-shoehorn','setup-pre-commit','setup-ts-deep-modules'}
    assert all(item['destination'].startswith('skills/mirrors-mattpocock/')
               for item in ITEMS if item['name']!='ask-pit')
    assert next(item for item in ITEMS if item['name']=='retro')['source_path']=='skills/engineering/retro'
    assert next(item for item in ITEMS if item['name']=='implement-spec')['source_path']=='skills/engineering/implement-spec'


def test_chief_of_staff_stays_explicit_only():
    item=next(i for i in ITEMS if i['name']=='chief-of-staff')
    package=ROOT/item['destination']
    assert item['overlay']=='patch'
    frontmatter=(package/'SKILL.md').read_text().split('---',2)[1]
    assert 'disable-model-invocation: true' in frontmatter


def test_new_pr_source_is_verbatim_and_provenance_uses_first_review():
    item=next(i for i in ITEMS if i['name']=='pr')
    package=ROOT/item['destination']
    record=json.loads((package/'UPSTREAM.json').read_text())
    provenance=(package/'PROVENANCE.md').read_text()
    assert item['source_path']=='skills/engineering/pr'
    assert item['overlay']=='empty'
    assert record['commit']=='49dd158d1076134a641b33efb035946536778336'
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
    assert '49dd158d1076134a641b33efb035946536778336' in provenance
    assert record['commit'] == '49dd158d1076134a641b33efb035946536778336'


def wizard_library(tmp_path):
    template = (ROOT / 'skills/mirrors-mattpocock/wizard/template.sh').read_text()
    library, marker, _ = template.partition('# STAGES: author this section.')
    assert marker, 'wizard template library marker is missing'
    path = tmp_path / 'wizard-library.sh'
    path.write_text(library)
    return path


def assert_node_dotenv_value(node, env_file, env):
    parser_check = subprocess.run(
        [node, '-e', "require('node:util').parseEnv('')"], capture_output=True, text=True
    )
    if parser_check.returncode:
        pytest.skip('Node util.parseEnv is unavailable')
    parser = r'''const fs = require('node:fs');
const { parseEnv } = require('node:util');
const parsed = parseEnv(fs.readFileSync(process.argv[1], 'utf8'));
if (parsed.VALUE !== process.env.EXPECTED_VALUE || parsed.KEEP !== 'keep') {
  console.error(JSON.stringify({ parsed, expected: process.env.EXPECTED_VALUE }));
  process.exit(1);
}'''
    result = subprocess.run([node, '-e', parser, str(env_file)], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('reader', ['ask', 'ask_secret'])
@pytest.mark.parametrize('value', [
    "O'Brien",
    '$HOME ${TOKEN} $$',
    r'C:\temp\path\file',
    r'literal backslash-n: \n and backslash-r: \r',
    'first line\nsecond line\n',
    'a "double-quoted" value',
    'O\'Brien says "hello"',
    "O'Brien uses `command`",
], ids=['apostrophe', 'dollar', 'backslash', 'literal-escapes', 'multiline', 'double-quote', 'mixed-quotes', 'double-fallback'])
def test_wizard_env_round_trips_through_node_dotenv(tmp_path, value, reader):
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node is required for dotenv parser proof')
    library = wizard_library(tmp_path)
    env_file = tmp_path / '.env'
    env = os.environ.copy()
    env.update(WIZARD_LIBRARY=str(library), ENV_FILE=str(env_file), EXPECTED_VALUE=value, READER=reader)
    shell = r'''source "$WIZARD_LIBRARY"
write_env KEEP keep >/dev/null
write_env VALUE "$EXPECTED_VALUE" >/dev/null
unset VALUE
if [[ "$READER" == "ask" ]]; then
  ask VALUE "round-trip test" <<< ""
else
  ask_secret VALUE "round-trip test" <<< ""
fi
[[ "$VALUE" == "$EXPECTED_VALUE" ]]
write_env VALUE "$EXPECTED_VALUE" >/dev/null'''
    subprocess.run(['bash', '-c', shell], env=env, check=True, capture_output=True, text=True)
    assert env_file.read_text().count('VALUE=') == 1
    assert_node_dotenv_value(node, env_file, env)


def test_wizard_reuses_legacy_shell_quoted_apostrophe_and_rewrites_it(tmp_path):
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node is required for dotenv parser proof')
    library = wizard_library(tmp_path)
    env_file = tmp_path / '.env'
    env_file.write_text("VALUE='O'\\''Brien'\nKEEP=keep\n")
    env = os.environ.copy()
    env.update(WIZARD_LIBRARY=str(library), ENV_FILE=str(env_file), EXPECTED_VALUE="O'Brien")
    shell = r'''source "$WIZARD_LIBRARY"
unset VALUE
ask_secret VALUE "legacy value" <<< ""
[[ "$VALUE" == "$EXPECTED_VALUE" ]]
write_env VALUE "$VALUE" >/dev/null'''
    subprocess.run(['bash', '-c', shell], env=env, check=True, capture_output=True, text=True)
    assert_node_dotenv_value(node, env_file, env)


def test_wizard_rejects_value_without_a_dotenv_quote_delimiter(tmp_path):
    library = wizard_library(tmp_path)
    env_file = tmp_path / '.env'
    env_file.write_text('KEEP=keep\n')
    env = os.environ.copy()
    env.update(WIZARD_LIBRARY=str(library), ENV_FILE=str(env_file), EXPECTED_VALUE="single' double\" backtick`")
    shell = r'''source "$WIZARD_LIBRARY"
if write_env VALUE "$EXPECTED_VALUE" >/dev/null 2>&1; then exit 2; fi'''
    subprocess.run(['bash', '-c', shell], env=env, check=True, capture_output=True, text=True)
    assert env_file.read_text() == 'KEEP=keep\n'


def test_batch_refresh_retains_legacy_and_reaches_later_packages(tmp_path, monkeypatch, capsys):
    item, checkout, src, dest = fixture_source(tmp_path)
    workspace = tmp_path / 'workspace'
    legacy = dict(item, name='retired', destination='retired-package',
                  source_path='missing-upstream-source', refresh_policy='pinned_legacy')
    active = dict(item, destination='active-package')
    workspace.mkdir()
    shutil.copytree(dest, workspace / legacy['destination'])
    shutil.copytree(dest, workspace / active['destination'])
    before = matt.file_map(workspace / legacy['destination'])
    config = workspace / 'manifest.json'
    config.write_text(json.dumps([legacy, active]))
    monkeypatch.setattr(matt, 'ROOT', workspace)
    monkeypatch.setattr(matt, 'CONFIG', config)
    monkeypatch.setattr('sys.argv', ['sync', '--upstream', str(checkout)])
    matt.main()
    assert matt.file_map(workspace / legacy['destination']) == before
    record = json.loads((workspace / active['destination'] / 'UPSTREAM.json').read_text())
    assert record['commit'] == subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    assert 'retained pinned legacy: retired' in capsys.readouterr().out
    monkeypatch.setattr('sys.argv', ['sync', '--upstream', str(checkout), '--skill', 'retired'])
    with pytest.raises(SystemExit) as error:
        matt.main()
    assert error.value.code == 2
    assert matt.file_map(workspace / legacy['destination']) == before


def test_two_refreshes_preserve_history_and_one_current_revision(tmp_path):
    item, checkout, src, dest = fixture_source(tmp_path)
    matt.refresh(checkout, item, dest)
    first = json.loads((dest / 'UPSTREAM.json').read_text())['commit']
    (src / 'new-support.md').write_text('second revision')
    subprocess.run(['git', '-C', str(checkout), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(checkout), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'second'], check=True)
    matt.refresh(checkout, item, dest)
    second = json.loads((dest / 'UPSTREAM.json').read_text())['commit']
    provenance = (dest / 'PROVENANCE.md').read_text()
    assert f'Historical upstream review: `{first}`' in provenance
    assert f'Current upstream review: `{second}`' in provenance
    assert provenance.count('Current upstream review:') == 1
    assert 'Original integration source revision: 3cca18b368ae95cdbdebbff572ccafa662551015.' in provenance
    before = matt.file_map(dest)
    matt.refresh(checkout, item, dest)
    assert matt.file_map(dest) == before
