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
    if not isinstance(data.get('skills'), dict) or set(data['skills']) != expected:
        raise ValueError('runtime skill coverage differs from published manifest')
    if not isinstance(data.get('profiles'), dict):
        raise ValueError('missing runtime profile coverage')
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
