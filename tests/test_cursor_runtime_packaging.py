import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('runtime_packaging',ROOT/'scripts/cursor_runtime_contracts.py')
runtime=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(runtime)


def contracts():
    entries=json.loads((ROOT/'sources/cursor-plugins/manifest.json').read_text())['skills']
    return runtime.load_contracts(ROOT/'sources/cursor-plugins/runtime-adapters/compatibility.json',entries)


def package(tmp_path,name='cursor-no-comments'):
    target=tmp_path/name;target.mkdir()
    text='---\nname: '+name+'\n---\n\n# Existing Codex\n\nRead [reference](guide.md#rules).\n'
    (target/'SKILL.md').write_text(text);(target/'guide.md').write_text('# Rules\n')
    return target,text


def test_no_runtime_declaration_preserves_bytes(tmp_path):
    target,text=package(tmp_path,'unlisted')
    assert hasattr(runtime,'render_runtime_package'), 'runtime package renderer is missing'
    runtime.render_runtime_package(target,{'published_name':'unlisted'},text,contracts())
    assert (target/'SKILL.md').read_text()==text
    assert not (target/'references/runtime').exists()


def test_retained_codex_resolves_original_targets(tmp_path):
    target,text=package(tmp_path)
    assert hasattr(runtime,'render_runtime_package'), 'runtime package renderer is missing'
    runtime.render_runtime_package(target,{'published_name':target.name},text,contracts())
    retained=target/'references/runtime/native-codex.md'
    assert (target/'references/runtime/original-codex.txt').read_text()==text
    assert retained.read_text().replace('../../guide.md','guide.md')==text
    assert (retained.parent/'../../guide.md').resolve()==(target/'guide.md').resolve()
    assert (target/'SKILL.md').read_text().endswith(text.split('---\n',2)[-1])
    assert 'original skill directory' in (target/'references/runtime/selection.md').read_text()
    assert 'native-codex.md' in (target/'references/runtime/selection.md').read_text()


def test_single_skill_package_is_self_contained(tmp_path):
    target,text=package(tmp_path)
    assert hasattr(runtime,'render_runtime_package'), 'runtime package renderer is missing'
    runtime.render_runtime_package(target,{'published_name':target.name},text,contracts())
    runtime.verify_runtime_packages(tmp_path,contracts())
    persona=target/'references/runtime/personas/comment-sicko.md'
    assert persona.is_file()
    assert 'Yes... Ha ha ha... Yes!' in persona.read_text()
    assert 'I never write application code' in persona.read_text()
    assert 'native registration' in persona.read_text()


def test_package_tampering_is_rejected(tmp_path):
    target,text=package(tmp_path)
    assert hasattr(runtime,'render_runtime_package'), 'runtime package renderer is missing'
    runtime.render_runtime_package(target,{'published_name':target.name},text,contracts())
    (target/'references/runtime/personas/comment-sicko.md').write_text('tampered')
    with pytest.raises(ValueError,match='runtime package drift'):
        runtime.verify_runtime_packages(tmp_path,contracts())


def test_unreviewed_profile_change_does_not_write_output(tmp_path,monkeypatch):
    target,text=package(tmp_path);data=contracts();data['profiles']['comment-sicko']['asset_sha256']='0'*64
    assert hasattr(runtime,'render_runtime_package'), 'runtime package renderer is missing'
    before={str(x.relative_to(target)):x.read_bytes() for x in target.rglob('*') if x.is_file()}
    with pytest.raises(ValueError,match='profile asset drift'):
        runtime.render_runtime_package(target,{'published_name':target.name},text,data)
    assert before=={str(x.relative_to(target)):x.read_bytes() for x in target.rglob('*') if x.is_file()}


def test_all_fourteen_profiles_have_portable_delivery():
    assert hasattr(runtime,'portable_profiles'), 'portable profile delivery is missing'
    profiles=runtime.portable_profiles(contracts())
    assert len(profiles)==14
    assert all('native registration' in p for p in profiles.values())
    assert 'parent owns' in profiles['poteto-agent'].lower()
    assert 'Do not spawn subagents' in profiles['advisor-subagent']


def test_changed_canonical_contract_is_detected(tmp_path,monkeypatch):
    target,text=package(tmp_path)
    runtime.render_runtime_package(target,{'published_name':target.name},text,contracts())
    read=runtime._read_owned
    def changed(root,path):
        value=read(root,path)
        return value+b'changed contract' if path.endswith('/t3.md') else value
    monkeypatch.setattr(runtime,'_read_owned',changed)
    with pytest.raises(ValueError,match='runtime package drift'):
        runtime.verify_runtime_packages(tmp_path,contracts())
