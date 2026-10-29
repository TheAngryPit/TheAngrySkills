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
    by_name = {e['published_name']: e for e in entries}
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
            if group == 'skills':
                if item.get('source_path') != by_name[name]['path']:
                    raise ValueError('runtime skill source identity differs: ' + name)
                digest = item.get('reviewed_workflow_sha256')
                if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                    raise ValueError('reviewed workflow digest missing: ' + name)
                roles = item.get('profiles', [])
                if not isinstance(roles, list) or len(roles) != len(set(roles)) or not set(roles) <= set(data['profiles']):
                    raise ValueError('invalid reviewed persona coverage: ' + name)
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
    if any(not isinstance(binding.get(key), str) or not binding[key].strip() for key in ('providerInstanceId', 'model')):
        return blocked
    providers = [p for p in catalog.get('providers', []) if p.get('providerInstanceId') == binding['providerInstanceId']]
    if len(providers) != 1 or providers[0].get('canRunChildTask') is not True:
        return blocked
    models = [m for m in providers[0].get('models', []) if m.get('id') == binding.get('model')]
    if len(models) != 1:
        return blocked
    options = binding.get('options', {})
    if isinstance(options, list):
        if any(not isinstance(o, dict) or set(o) != {'id', 'value'} or not isinstance(o['id'], str) for o in options):
            return blocked
        if len({o['id'] for o in options}) != len(options):
            return blocked
        option_pairs = [(o['id'], o['value']) for o in options]
    elif isinstance(options, dict):
        option_pairs = list(options.items())
    else:
        return blocked
    allowed = {o['id']: o.get('values', []) for o in models[0].get('options', [])}
    for key, value in option_pairs:
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
    relocated = re.sub(r'\]\(([^)]+)\)', replace, text)
    relocated = relocated.replace('relative to this file', 'relative to the original skill root')
    relocated = relocated.replace('from this file', 'from the original skill root')
    marker = re.match(r'^---\r?\n[\s\S]*?\r?\n---\r?\n', relocated)
    offset = marker.end() if marker else 0
    context = (
        '\n## Reference path base\n\n'
        'Shell commands, bare/backticked paths and prose use the original skill root '
        '(two directories above this reference). References to the original file mean that root, '
        'including sibling skills and playbooks. Markdown link destinations are file-relative '
        'and have already been relocated; do not apply the command base to those links.\n\n'
    )
    return relocated[:offset] + context + relocated[offset:]


def render_runtime_package(target: Path, entry: dict, rendered_codex: str, contracts: dict) -> None:
    import hashlib
    name = entry['published_name']
    if name not in contracts['skills']:
        return
    if workflow_digest(target, rendered_codex) != contracts['skills'][name]['reviewed_workflow_sha256']:
        raise ValueError('workflow coverage drift requires review: ' + name)
    required = referenced_personas(target, rendered_codex, contracts['profiles'])
    if not required <= set(contracts['skills'][name].get('profiles', [])):
        raise ValueError('missing reviewed persona: ' + name)
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
    payloads['runtime-files.json'] = (json.dumps(record, indent=2, sort_keys=True) + '\n').encode()
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
    frontmatter = rendered_codex[:marker.end()]
    policy = target / 'agents/openai.yaml'
    if policy.is_file() and 'allow_implicit_invocation: false' in policy.read_text():
        frontmatter = frontmatter[:-4] + 'disable-model-invocation: true\n---\n'
    (target / 'SKILL.md').write_text(frontmatter + dispatch + rendered_codex[marker.end():])


def verify_runtime_packages(root: Path, contracts: dict) -> None:
    import hashlib
    source_root = Path(__file__).resolve().parents[1]
    profiles = portable_profiles(contracts)
    for name, skill in contracts['skills'].items():
        folder = root / name / 'references/runtime'
        if not (root / name).exists():
            continue
        original = folder / 'original-codex.txt'
        if not original.is_file() or original.is_symlink() or workflow_digest(root / name, original.read_text()) != skill['reviewed_workflow_sha256']:
            raise ValueError('runtime package drift: reviewed workflow ' + name)
        if not referenced_personas(root / name, original.read_text(), contracts['profiles']) <= set(skill.get('profiles', [])):
            raise ValueError('runtime package drift: missing reviewed persona ' + name)
        record_path = folder / 'runtime-files.json'
        if not record_path.is_file() or record_path.is_symlink():
            raise ValueError('runtime package drift: missing metadata ' + name)
        record = json.loads(record_path.read_text(), object_pairs_hook=_object_pairs)
        if record.get('skill') != name or record.get('schema_version') != 1:
            raise ValueError('runtime package drift: identity ' + name)
        expected = record.get('files', {})
        personas = {role: 'personas/' + role + '.md' for role in skill.get('profiles', [])}
        required = {'selection.md', 't3.md', 'native-codex.md', 'original-codex.txt', 'method.md', *personas.values()}
        if set(expected) != required or record.get('personas') != personas:
            raise ValueError('runtime package drift: contract coverage ' + name)
        for file in ('selection.md', 't3.md'):
            canonical = _read_owned(source_root, 'sources/cursor-plugins/runtime-adapters/' + file)
            if expected[file] != hashlib.sha256(canonical).hexdigest():
                raise ValueError('runtime package drift: canonical input ' + name)
        for role, relative in personas.items():
            if expected[relative] != hashlib.sha256(profiles[role].encode()).hexdigest():
                raise ValueError('runtime package drift: persona ' + name)
        actual = {}
        for p in folder.rglob('*'):
            if p.is_symlink():
                raise ValueError('runtime package drift: symlink ' + name)
            if p.is_file() and p != record_path:
                actual[p.relative_to(folder).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('runtime package drift: files ' + name)


def _workflow_files(target: Path, rendered_codex: str) -> dict[str, bytes]:
    result = {'SKILL.md': rendered_codex.encode()}
    for path in target.rglob('*'):
        relative = path.relative_to(target).as_posix()
        if relative == 'SKILL.md' or path.name in {'MIRROR.md', 'LICENSE.upstream'} or relative.startswith('references/runtime/'):
            continue
        if path.is_symlink():
            raise ValueError('workflow coverage drift: symlink')
        if path.is_file():
            result[relative] = path.read_bytes()
    return result


def workflow_digest(target: Path, rendered_codex: str) -> str:
    import hashlib
    files = {name: hashlib.sha256(body).hexdigest() for name, body in _workflow_files(target, rendered_codex).items()}
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def referenced_personas(target: Path, rendered_codex: str, profiles: dict) -> set[str]:
    import re
    text = '\n'.join(value.decode(errors='replace') for name, value in _workflow_files(target, rendered_codex).items() if name.endswith('.md'))
    return {name for name in profiles if re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', text)}
