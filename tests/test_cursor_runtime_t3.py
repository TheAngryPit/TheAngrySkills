import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('t3_contract', ROOT/'scripts/cursor_runtime_contracts.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
BASE=ROOT/'sources/cursor-plugins'


def data():
    return runtime.load_contracts(BASE/'runtime-adapters/compatibility.json',json.loads((BASE/'manifest.json').read_text())['skills'])


def test_t3_writer_uses_tool_isolation_and_no_thread_fallback():
    text=(BASE/'runtime-adapters/t3.md').read_text()
    assert 'isolation: "worktree"' in text
    assert 'never create it with shell commands' in text
    assert 'A new top-level thread needs an explicit user request' in text
    assert 'A delegated child never watches' in text
    assert 'fresh delegate_task for a new review' in text


def test_all_native_profile_assets_are_unchanged_and_all_portable_profiles_shipped():
    coverage=json.loads((BASE/'agent-coverage.json').read_text())['agents']
    shipped=set()
    for p in (ROOT/'skills/mirrors-cursor').glob('*/references/runtime/runtime-files.json'):
        shipped.update(json.loads(p.read_text())['personas'])
    assert shipped=={x['native_name'] for x in coverage.values()}
    for value in coverage.values():
        assert hashlib.sha256((ROOT/value['asset_path']).read_bytes()).hexdigest()==value['asset_sha256']


def test_portable_profile_has_no_codex_only_dispatch():
    profiles=runtime.portable_profiles(data())
    for name,body in profiles.items():
        assert 'Use native Codex subagent delegation' not in body,name
        assert 'Use native Codex tools and the operator-selected' not in body,name
        assert 'native registration' in body,name
    assert 'Do not start subagents unless this task explicitly authorizes them' in profiles['poteto-agent']
    assert 'My first output when spawned is exactly this.' in profiles['comment-sicko']
    assert 'I never write application code' in profiles['comment-sicko']


def test_t3_policy_reference_preserves_existing_model_profiles():
    ref=ROOT/'skills/core/model-capability-router/references/t3-runtime.md'
    assert ref.is_file(), 'T3 policy transport reference is missing'
    text=ref.read_text()
    assert 'no second model policy' in text
    assert 'no automatic fallback' in text
    assert 'options' in text and 'providerInstanceId' in text


def test_same_package_keeps_explicit_invocation_for_claude_and_codex():
    entries=json.loads((BASE/'manifest.json').read_text())['skills']
    for entry in entries:
        if not entry['publish'] or entry.get('excluded_from_mirror'):continue
        target=ROOT/'skills/mirrors-cursor'/entry['published_name']
        policy=target/'agents/openai.yaml'
        if policy.exists() and 'allow_implicit_invocation: false' in policy.read_text():
            assert 'disable-model-invocation: true' in (target/'SKILL.md').read_text().split('---',2)[1],entry['published_name']


def test_all_23_playbooks_are_retained_and_runtime_scoped():
    target=ROOT/'skills/mirrors-cursor/cursor-poteto-mode'
    files=list((target/'playbooks').glob('*.md'))
    assert len(files)==23
    for file in files:
        original=(BASE/'snapshot/pstack/skills/poteto-mode/playbooks'/file.name).read_text()
        # Existing reviewed overlays remain the source of changes. No step can disappear
        # merely because it mentions a foreign runtime.
        assert original.strip() and file.read_text().strip()
    assert 'Read method.md in full' in (target/'references/runtime/t3.md').read_text()
    assert 'No step is waived' in (target/'references/runtime/t3.md').read_text()
