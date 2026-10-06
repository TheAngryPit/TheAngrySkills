import importlib.util
import json
import os
import sys
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("raw_worktree,raw_file", [(False, False), (True, False), (False, True)])
def test_native_audit_preserves_space_paths_and_holds_unknown_usage_and_untracked_work(tmp_path, raw_worktree, raw_file):
    if (raw_worktree or raw_file) and (os.name != "posix" or sys.platform == "darwin"):
        pytest.skip("raw filename fixture requires a POSIX filesystem accepting non-UTF-8 bytes")
    repo = tmp_path / 'main repo'
    child = tmp_path / (os.fsdecode(b'child with spaces \xff') if raw_worktree else 'child with spaces')
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Fixture', '-c',
                    'user.email=fixture@example.invalid', 'commit', '--allow-empty', '-qm', 'initial'], check=True)
    subprocess.run(['git', '-C', str(repo), 'worktree', 'add', '-qb', 'fixture', str(child)], check=True)
    spec = importlib.util.spec_from_file_location('audit', ROOT / 'scripts/cursor_worktree_audit.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    clean = module.audit(repo)[0]
    assert clean['worktree'] == str(child)
    assert clean['session_usage'] == 'unknown'
    assert clean['merged_into_cached_origin_main'] == 'unknown'
    assert clean['bucket'] == 'verify-native-usage'
    filename = os.fsdecode(b'valuable untracked \xff.txt') if raw_file else 'valuable untracked.txt'
    (child / filename).write_text('keep this work')
    dirty = module.audit(repo)[0]
    assert dirty['dirty'] == 'has-work'
    assert dirty['bucket'] == 'hold-work'
    assert (child / filename).read_text() == 'keep this work'
    emitted = ROOT / 'skills/mirrors-cursor/cursor-poteto-mode/scripts/cursor_worktree_audit.py'
    cli = subprocess.run([sys.executable, str(emitted), str(repo)], capture_output=True, text=True, timeout=30)
    assert cli.returncode == 0, cli.stderr
    result = json.loads(cli.stdout)['worktrees'][0]
    assert os.fsencode(result['worktree']) == os.fsencode(child)
    assert result['bucket'] == 'hold-work'


def test_cli_missing_dependencies_fail_without_install_or_restart(tmp_path):
    bun = shutil.which('bun')
    if not bun:
        pytest.skip('existing Bun unavailable')
    source = ROOT / 'skills/mirrors-cursor/cursor-poteto-mode/scripts'
    for name in ('bootstrap.ts', 'package.json', 'bun.lock'):
        shutil.copy2(source / name, tmp_path / name)
    probe = tmp_path / 'probe.ts'
    probe.write_text('''import { ensureDependenciesInstalled } from "./bootstrap.ts";
let attempts = 0;
Bun.spawnSync = (() => { attempts++; throw new Error("UNAUTHORIZED_PROVISIONING"); }) as typeof Bun.spawnSync;
try { ensureDependenciesInstalled(); process.exitCode = 2; }
catch (error) { console.log(String(error)); }
console.log(`spawn_attempts=${attempts}`);
''')
    result = subprocess.run([bun, str(probe)], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'Missing pstack CLI dependencies' in result.stdout
    assert 'spawn_attempts=0' in result.stdout
    assert not (tmp_path / 'node_modules').exists()
    commander = tmp_path / "node_modules/commander/package.json"
    commander.parent.mkdir(parents=True)
    stamp = tmp_path / "node_modules/.poteto-mode-tools-install-key"
    stamp.write_text("old lockfile stamp")
    commander.write_text('{"version":"0.0.0"}')
    rejected = subprocess.run([bun, str(probe)], capture_output=True, text=True, timeout=15)
    assert rejected.returncode == 0
    assert "requires commander 14.0.0; installed 0.0.0" in rejected.stdout
    assert "spawn_attempts=0" in rejected.stdout
    commander.write_text('{"version":"14.0.0"}')
    probe.write_text(probe.read_text().replace("process.exitCode = 2;", 'console.log("dependencies_ready");'))
    recovered = subprocess.run([bun, str(probe)], capture_output=True, text=True, timeout=15)
    assert recovered.returncode == 0, recovered.stderr
    assert "dependencies_ready" in recovered.stdout
    assert "spawn_attempts=0" in recovered.stdout
    assert stamp.read_text() == "old lockfile stamp"


def test_git_process_output_decodes_raw_bytes_losslessly(tmp_path, monkeypatch):
    if os.name != "posix":
        pytest.skip("executable subprocess fixture uses POSIX shebang")
    executable = tmp_path / "git"
    executable.write_text(f"#!{sys.executable}\nimport os\nos.write(1, b'?? invalid\\xff\\r\\n\\0')\nos.write(2, b'warning \\xff')\n")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    spec = importlib.util.spec_from_file_location('audit_bytes', ROOT / 'scripts/cursor_worktree_audit.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = module.git(tmp_path, "status", "--porcelain", "-z")
    assert os.fsencode(output) == b"?? invalid\xff\r\n\0"
