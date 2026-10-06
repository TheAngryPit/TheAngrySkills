#!/usr/bin/env bash
set -eu
script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
exec python3 "$script_dir/cursor_worktree_audit.py" "$@"
