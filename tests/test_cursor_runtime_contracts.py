import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'scripts/cursor_runtime_contracts.py'


def module():
    assert PATH.is_file(), 'runtime contract implementation is missing'
    spec = importlib.util.spec_from_file_location('runtime_contracts', PATH)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def capabilities(host='t3', tools=None):
    return {'host': host, 'provider': 'codex', 'tools': tools or ['delegate_task', 'orchestrator_capabilities']}


@pytest.mark.parametrize('host,expected', [('native-codex','native-codex'), ('t3','t3'), (None,None)])
def test_runtime_uses_host_not_model(host, expected):
    result = module().select_runtime(None, capabilities(host))
    assert result['runtime'] == expected
    assert result['status'] == ('selected' if expected else 'blocked')


def test_explicit_selection_cannot_bypass_host():
    assert module().select_runtime('native-codex', capabilities())['status'] == 'blocked'


def test_permission_denial_never_falls_through():
    result = module().resolve_operation('t3', 'delegate', capabilities(), denied=True)
    assert result['status'] == 'blocked'
    assert result['route'] is None


def test_missing_tool_is_blocked_not_native_fallback():
    result = module().resolve_operation('t3', 'delegate', capabilities(tools=['orchestrator_capabilities']))
    assert result['status'] == 'blocked' and result['route'] is None


@pytest.mark.parametrize('runtime', ['hermes','openclaw-subagent','openclaw-codex','openclaw-acp'])
def test_future_runtime_is_explicitly_deferred(runtime):
    assert module().select_runtime(runtime, capabilities(runtime))['status'] == 'deferred'
    assert module().resolve_operation(runtime, 'delegate', capabilities(runtime))['status'] == 'deferred'


def catalog():
    return {'providers': [{'providerInstanceId':'test-provider','canRunChildTask':True,
        'models':[{'id':'test-model','options':[{'id':'effort','values':['low','medium']}]}]}]}


def binding():
    return {'providerInstanceId':'test-provider','model':'test-model','options':{'effort':'medium'}}


def test_exact_selected_target_preserved():
    chosen = binding()
    assert module().t3_target(chosen, catalog())['target'] == chosen
    assert chosen == binding()


@pytest.mark.parametrize('change', ['provider','model','option','disabled','boolean'])
def test_unavailable_target_never_substitutes(change):
    b = binding(); c = catalog()
    if change == 'provider':b['providerInstanceId']='absent'
    if change == 'model':b['model']='absent'
    if change == 'option':b['options']['effort']='max'
    if change == 'disabled':c['providers'][0]['canRunChildTask']=False
    if change == 'boolean':b['options']['effort']=True
    result = module().t3_target(b,c)
    assert result['status']=='blocked' and result['target'] is None


def test_full_published_coverage_and_profiles_are_inventoried():
    m = json.loads((ROOT/'sources/cursor-plugins/manifest.json').read_text())
    data = module().load_contracts(ROOT/'sources/cursor-plugins/runtime-adapters/compatibility.json',m['skills'])
    assert set(data['skills']) == {x['published_name'] for x in m['skills'] if x['publish'] and not x.get('excluded_from_mirror')}
    assert len(data['profiles']) == 14
    assert {'comment-sicko','poteto-agent'} <= set(data['profiles'])
    assert all(x['t3']['evidence'] != 'live' for x in data['profiles'].values())


@pytest.mark.parametrize('mutation', ['missing','unknown','evidence','path','duplicate'])
def test_ledger_rejects_incomplete_or_unsafe_coverage(tmp_path, mutation):
    m = json.loads((ROOT/'sources/cursor-plugins/manifest.json').read_text())
    original = ROOT/'sources/cursor-plugins/runtime-adapters/compatibility.json'
    assert original.is_file(), 'reviewed runtime ledger is missing'
    d = json.loads(original.read_text());name=next(iter(d['skills']))
    if mutation=='missing':d['skills'].pop(name)
    if mutation=='unknown':d['skills']['unknown']=d['skills'][name]
    if mutation=='evidence':d['skills'][name]['t3']['evidence']='certified-by-install'
    if mutation=='path':d['profiles']['comment-sicko']['asset_path']='../../private.toml'
    if mutation=='duplicate':d['schema_version']=True
    p=tmp_path/'contracts.json';p.write_text(json.dumps(d))
    with pytest.raises(ValueError):module().load_contracts(p,m['skills'])


def test_ledger_cannot_omit_a_native_profile(tmp_path):
    m=json.loads((ROOT/'sources/cursor-plugins/manifest.json').read_text())
    d=json.loads((ROOT/'sources/cursor-plugins/runtime-adapters/compatibility.json').read_text())
    d['profiles'].pop('comment-sicko')
    p=tmp_path/'contracts.json';p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='profile coverage'):
        module().load_contracts(p,m['skills'])


def test_ledger_source_identity_is_reviewed(tmp_path):
    entries=json.loads((ROOT/'sources/cursor-plugins/manifest.json').read_text())['skills']
    d=json.loads((ROOT/'sources/cursor-plugins/runtime-adapters/compatibility.json').read_text())
    d['skills']['cursor-no-comments']['source_path']='different/skill.md'
    p=tmp_path/'contracts.json';p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='source identity'):
        module().load_contracts(p,entries)


@pytest.mark.parametrize('binding_value,catalog_value', [({}, {'providers':[{'canRunChildTask':True,'models':[{}]}]}),
    ({'providerInstanceId':'','model':''},{'providers':[{'providerInstanceId':'','canRunChildTask':True,'models':[{'id':''}]}]}),
    ({'providerInstanceId':None,'model':None},{'providers':[{'providerInstanceId':None,'canRunChildTask':True,'models':[{'id':None}]}]})])
def test_malformed_identifiers_never_select_inheritance(binding_value,catalog_value):
    result=module().t3_target(binding_value,catalog_value)
    assert result['status']=='blocked' and result['target'] is None


@pytest.mark.parametrize('options', [[], [{'id':'effort','value':'medium'}]])
def test_supported_t3_option_array_is_preserved(options):
    b=binding();b['options']=options
    assert module().t3_target(b,catalog())['target']==b
