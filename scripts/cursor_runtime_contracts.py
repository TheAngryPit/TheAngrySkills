"""Validate runtime contracts without launching agents or changing operator policy."""
from __future__ import annotations

import copy
import json
from pathlib import Path, PurePosixPath

RUNTIMES = ('native-codex', 't3', 'hermes', 'openclaw-subagent', 'openclaw-codex', 'openclaw-acp')
EVIDENCE = {'retained', 'source-only', 'fixture', 'live', 'none'}
STATUSES = {'preserved', 'partial', 'unsupported', 'deferred', 'verified'}
T3_OPERATIONS = {'delegate': 'delegate_task', 'worktree': 'delegate_task',
                 'history': 't3_thread_read', 'link-pr': 'link_pull_request',
                 'watch-pr': 'watch_pull_request', 'schedule': 'schedule_task'}


def safe_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError('unsafe runtime path')
    p = PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or str(p) != value:
        raise ValueError('unsafe runtime path')
    return p


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate runtime contract key: ' + key)
        result[key] = value
    return result


def load_contracts(path: Path, entries: list[dict]) -> dict:
    data = json.loads(path.read_text(), object_pairs_hook=_object_pairs)
    if type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ValueError('unsupported runtime contract schema')
    expected = {e['published_name'] for e in entries if e['publish'] and not e.get('excluded_from_mirror')}
    known = {e['published_name'] for e in entries}
    if not isinstance(data.get('skills'), dict) or not expected <= set(data['skills']) <= known:
        raise ValueError('runtime skill coverage differs from published manifest')
    if not isinstance(data.get('profiles'), dict):
        raise ValueError('missing runtime profile coverage')
    coverage = json.loads((Path(__file__).resolve().parents[1] / 'sources/cursor-plugins/agent-coverage.json').read_text())['agents']
    expected_profiles = {value['native_name']: value for value in coverage.values()}
    if set(data['profiles']) != set(expected_profiles):
        raise ValueError('runtime profile coverage differs from native inventory')
    for name, profile in data['profiles'].items():
        original = expected_profiles[name]
        if profile.get('asset_path') != original['asset_path'] or profile.get('asset_sha256') != original['asset_sha256']:
            raise ValueError('runtime profile coverage differs from native provenance')
    for group in ('skills', 'profiles'):
        for name, item in data[group].items():
            safe_path(name)
            if not isinstance(item, dict):
                raise ValueError('invalid runtime item')
            if group == 'profiles':
                safe_path(item.get('asset_path'))
                if not isinstance(item.get('asset_sha256'), str) or len(item['asset_sha256']) != 64:
                    raise ValueError('profile asset digest missing')
            for runtime in RUNTIMES:
                record = item.get(runtime)
                if not isinstance(record, dict) or record.get('evidence') not in EVIDENCE:
                    raise ValueError('invalid runtime evidence: ' + name)
                if record.get('status') not in STATUSES or not record.get('reason'):
                    raise ValueError('runtime status/reason missing: ' + name)
                operations = record.get('operations')
                if not isinstance(operations, dict) or not operations:
                    raise ValueError('runtime operations missing: ' + name)
                for operation, status in operations.items():
                    if operation not in {'method', 'persona', *T3_OPERATIONS} or status not in STATUSES:
                        raise ValueError('invalid runtime operation: ' + name)
                if runtime not in RUNTIMES[:2] and record['status'] != 'deferred':
                    raise ValueError('future runtime must remain deferred')
                if record['evidence'] == 'live' and not record.get('receipt'):
                    raise ValueError('live runtime evidence requires a receipt')
    data['skills'] = {name: item for name, item in data['skills'].items() if name in expected}
    return data


def select_runtime(explicit: str | None, capabilities: dict) -> dict:
    host = capabilities.get('host')
    if host not in RUNTIMES or explicit is not None and explicit != host:
        return {'runtime': None, 'status': 'blocked', 'reason': 'unavailable or ambiguous host selection'}
    if host not in RUNTIMES[:2]:
        return {'runtime': host, 'status': 'deferred', 'reason': 'future adapter is not implemented'}
    tools = set(capabilities.get('tools', []))
    if host == 't3' and 'orchestrator_capabilities' not in tools:
        return {'runtime': None, 'status': 'blocked', 'reason': 'T3 host contract unavailable'}
    return {'runtime': host, 'status': 'selected', 'reason': 'explicit advertised host context'}


def resolve_operation(runtime: str, operation: str, capabilities: dict, denied: bool = False) -> dict:
    if denied:
        return {'route': None, 'status': 'blocked', 'reason': 'permission refusal is binding'}
    selection = select_runtime(runtime, capabilities)
    if selection['status'] != 'selected':
        return {'route': None, 'status': selection['status'], 'reason': selection['reason']}
    tools = set(capabilities.get('tools', []))
    route = T3_OPERATIONS.get(operation) if runtime == 't3' else {
        'delegate': 'collaboration.spawn_agent', 'history': 'native-authorized-history'
    }.get(operation)
    if route is None:
        return {'route': None, 'status': 'unsupported', 'reason': 'no runtime operation mapping'}
    if route not in tools:
        return {'route': None, 'status': 'blocked', 'reason': 'required tool unavailable: ' + route}
    return {'route': route, 'status': 'selected', 'reason': 'advertised operation; task authority still required'}


def t3_target(binding: dict, catalog: dict) -> dict:
    blocked = {'status': 'blocked', 'target': None, 'reason': 'selected target or option unavailable'}
    if not isinstance(binding, dict) or set(binding) - {'providerInstanceId', 'model', 'options'}:
        return blocked
    providers = [p for p in catalog.get('providers', []) if p.get('providerInstanceId') == binding.get('providerInstanceId')]
    if len(providers) != 1 or providers[0].get('canRunChildTask') is not True:
        return blocked
    models = [m for m in providers[0].get('models', []) if m.get('id') == binding.get('model')]
    if len(models) != 1:
        return blocked
    options = binding.get('options', {})
    if not isinstance(options, dict):
        return blocked
    allowed = {o['id']: o.get('values', []) for o in models[0].get('options', [])}
    for key, value in options.items():
        if not any(type(value) is type(v) and value == v for v in allowed.get(key, [])):
            return blocked
    return {'status': 'selected', 'target': copy.deepcopy(binding), 'reason': 'exact operator binding retained'}


def _read_owned(root: Path, relative: str) -> bytes:
    import hashlib
    p = root / safe_path(relative)
    if any(part.is_symlink() for part in [p, *p.parents] if part != root.parent):
        raise ValueError('runtime source symlink: ' + relative)
    if not p.resolve().is_relative_to(root.resolve()) or not p.is_file():
        raise ValueError('runtime source missing or escaping: ' + relative)
    return p.read_bytes()


def portable_profiles(contracts: dict) -> dict[str, str]:
    import hashlib
    import tomllib
    root = Path(__file__).resolve().parents[1]
    profiles = {}
    adaptations = contracts.get('profile_replacements', {})
    for name, profile in contracts['profiles'].items():
        raw = _read_owned(root, profile['asset_path'])
        if hashlib.sha256(raw).hexdigest() != profile['asset_sha256']:
            raise ValueError('profile asset drift: ' + name)
        parsed = tomllib.loads(raw.decode())
        if parsed.get('name') != name:
            raise ValueError('profile identity mismatch: ' + name)
        body = parsed['developer_instructions']
        for change in adaptations.get(name, []):
            if body.count(change['before']) != 1:
                raise ValueError('profile adaptation anchor drift: ' + name)
            body = body.replace(change['before'], change['after'], 1)
        profiles[name] = (
            '# Portable T3 persona: ' + name + '\n\n'
            'Delivery is an instruction persona, not native registration. The parent owns '
            'the task, scope, model and every authorized spawn. Read the parent-named skill and '
            'its runtime contract before acting. Preserve all role-specific restrictions below.\n\n'
            + body
        )
    return profiles


def _relocate_links(text: str) -> str:
    import re
    def replace(match):
        value = match.group(1)
        path, sep, fragment = value.partition('#')
        if not path or ':' in path or path.startswith('/'):
            return match.group(0)
        return '](' + '../../' + path + sep + fragment + ')'
    return re.sub(r'\]\(([^)]+)\)', replace, text)


def render_runtime_package(target: Path, entry: dict, rendered_codex: str, contracts: dict) -> None:
    import hashlib
    name = entry['published_name']
    if name not in contracts['skills']:
        return
    root = Path(__file__).resolve().parents[1]
    base = 'sources/cursor-plugins/runtime-adapters/'
    payloads = {'selection.md': _read_owned(root, base + 'selection.md'),
                't3.md': _read_owned(root, base + 't3.md'),
                'native-codex.md': _relocate_links(rendered_codex).encode(),
                'original-codex.txt': rendered_codex.encode(), 'method.md': _relocate_links(rendered_codex).encode()}
    profiles = portable_profiles(contracts)
    selected = contracts['skills'][name].get('profiles', [])
    for role in selected:
        safe_path(role)
        if role not in profiles:
            raise ValueError('unknown portable persona: ' + role)
        payloads['personas/' + role + '.md'] = profiles[role].encode()
    record = {'schema_version': 1, 'skill': name, 'native_base': '../..',
              'personas': {role: 'personas/' + role + '.md' for role in selected},
              'files': {key: hashlib.sha256(value).hexdigest() for key, value in payloads.items()}}
    payloads['package.json'] = (json.dumps(record, indent=2, sort_keys=True) + '\n').encode()
    folder = target / 'references/runtime'
    if folder.exists() or folder.is_symlink():
        raise ValueError('runtime package output collision: ' + name)
    # All source/profile checks finish before any output mutation.
    for relative, content in payloads.items():
        path = folder / safe_path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    import re
    marker = re.match(r'^---\r?\n[\s\S]*?\r?\n---\r?\n', rendered_codex)
    if not marker:
        raise ValueError('runtime package missing skill frontmatter')
    dispatch = (
        '\n## Runtime selection\n\n'
        'Before runtime-dependent work, read [execution selection](references/runtime/selection.md). '
        'In a verified T3 host follow [the T3 contract](references/runtime/t3.md) and its method reference; '
        'the inline section below is the native Codex branch, not literal T3 dispatch. '
        'Outside T3, native Codex follows that inline branch unchanged. '
        'If the host is ambiguous or a required capability is unavailable, report the gap; '
        'a permission refusal never authorizes switching branches.\n\n'
        '## Native Codex branch\n'
    )
    (target / 'SKILL.md').write_text(rendered_codex[:marker.end()] + dispatch + rendered_codex[marker.end():])


def verify_runtime_packages(root: Path, contracts: dict) -> None:
    import hashlib
    for name in contracts['skills']:
        folder = root / name / 'references/runtime'
        if not (root / name).exists():
            continue
        record_path = folder / 'package.json'
        if not record_path.is_file() or record_path.is_symlink():
            raise ValueError('runtime package drift: missing metadata ' + name)
        record = json.loads(record_path.read_text(), object_pairs_hook=_object_pairs)
        if record.get('skill') != name or record.get('schema_version') != 1:
            raise ValueError('runtime package drift: identity ' + name)
        expected = record.get('files', {})
        actual = {}
        for p in folder.rglob('*'):
            if p.is_symlink():
                raise ValueError('runtime package drift: symlink ' + name)
            if p.is_file() and p != record_path:
                actual[p.relative_to(folder).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('runtime package drift: files ' + name)
