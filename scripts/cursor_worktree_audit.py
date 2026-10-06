#!/usr/bin/env python3
"""Read-only Git inventory; native session/attachment checks remain required."""
import argparse
import json
import os
import subprocess
from pathlib import Path


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                            text=True, timeout=30)
    return result.stdout.strip() if result.returncode == 0 else None


def audit(repo):
    raw = git(repo, 'worktree', 'list', '--porcelain', '-z')
    if raw is None:
        raise ValueError('cannot list repository worktrees')
    records = []
    current = {}
    for field in raw.split('\0'):
        if not field:
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = field.partition(' ')
        current[key] = value
    if current:
        records.append(current)
    result = []
    for entry in records[1:]:
        path = Path(entry['worktree'])
        status = git(path, 'status', '--porcelain', '-z')
        head = git(path, 'rev-parse', 'HEAD')
        branch = git(path, 'symbolic-ref', '--quiet', '--short', 'HEAD')
        merged = subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor',
                                 head or '', 'origin/main'], capture_output=True, timeout=30)
        merge_state = {0: 'yes', 1: 'no'}.get(merged.returncode, 'unknown')
        remote_head = git(path, 'rev-parse', '--verify', f'refs/remotes/origin/{branch}') if branch else None
        size = 0
        size_complete = True
        def onerror(error):
            nonlocal size_complete
            size_complete = False
        for root, dirs, files in os.walk(path, followlinks=False, onerror=onerror):
            for name in files:
                try:
                    size += (Path(root) / name).lstat().st_size
                except OSError:
                    size_complete = False
        result.append(dict(worktree=str(path), head=head, branch=branch,
                           size_bytes=size, size_complete=size_complete,
                           merged_into_cached_origin_main=merge_state,
                           remote='detached' if not branch else ('pushed' if remote_head == head else 'differs-or-missing'),
                           dirty='unknown' if status is None else ('has-work' if status else 'clean'),
                           session_usage='unknown', pr_state='not-queried',
                           bucket='hold-work' if status else 'verify-native-usage'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', nargs='?', default='.')
    args = parser.parse_args()
    print(json.dumps({'worktrees': audit(Path(args.repo)),
                      'limits': 'Cached refs only. No fetch, PR query, transcript scan or deletion. Check native attachments and sessions before any removal.'}, indent=2))


if __name__ == '__main__':
    main()
