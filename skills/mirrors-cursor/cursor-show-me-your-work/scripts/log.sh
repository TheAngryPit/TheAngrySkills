#!/usr/bin/env bash
# Append a bounded, well-formed row to a show-me-your-work decision log.
# Usage: log.sh --root <task-root> <logfile> <phase> <decision> <why> <evidence> <result>
# The positional <task-root> <logfile> form is accepted for local preview compatibility.
set -euo pipefail

usage() {
	printf 'usage: log.sh --root <task-root> <logfile> <phase> <decision> <why> <evidence> <result>\n' >&2
	exit 2
}

if [ "$#" -ge 3 ] && [ "$1" = "--root" ]; then
	root="$2"
	logfile="$3"
	shift 3
elif [ "$#" -ge 2 ] && [ "$1" != "--root" ]; then
	root="$1"
	logfile="$2"
	shift 2
else
	usage
fi

if [ "$#" -ne 5 ] || [ -z "$root" ] || [ -z "$logfile" ]; then
	usage
fi

exec python3 - "$root" "$logfile" "$@" <<'PY'
import datetime
import errno
import fcntl
import os
import pathlib
import re
import stat
import sys

root_arg, logfile_arg = sys.argv[1:3]
values = sys.argv[3:]


def fail(message):
    print("log.sh: " + message, file=sys.stderr)
    raise SystemExit(1)


sensitive = re.compile(
    r"(?i)(?:\b(?:api[_-]?key|access[_-]?token|password|secret|authorization)[\\\"\']?\s*[:=]\s*[\\\"\']?\S+|\bBearer\s+\S+|\b(?:sk|ghp|gho|ghu|ghs|ghr|xai)[-_][A-Za-z0-9_-]{12,})"
)
if any(sensitive.search(value) for value in values):
    fail("secret-like value refused; redact before logging")


if (
    not hasattr(os, "O_NOFOLLOW")
    or not hasattr(os, "O_DIRECTORY")
    or not hasattr(os, "O_NONBLOCK")
):
    fail("host lacks required no-follow/nonblocking file support")

try:
    root_stat = os.lstat(root_arg)
except OSError as exc:
    fail("task/workspace root is missing or unreadable: " + str(exc))

if stat.S_ISLNK(root_stat.st_mode):
    fail("task/workspace root must not be a symlink")
if not stat.S_ISDIR(root_stat.st_mode):
    fail("task/workspace root must be an existing directory")

root_real = os.path.realpath(root_arg)
if not os.path.isabs(root_real):
    fail("task/workspace root did not resolve to an absolute directory")

raw_parts = pathlib.PurePath(logfile_arg).parts
if not logfile_arg or any(part == ".." for part in raw_parts):
    fail("logfile path escapes the task/workspace root")

root_abs = os.path.abspath(root_arg)
if os.path.isabs(logfile_arg):
    requested = os.path.normpath(logfile_arg)
    try:
        if os.path.commonpath((root_abs, requested)) == root_abs:
            relative = os.path.relpath(requested, root_abs)
        elif os.path.commonpath((root_real, requested)) == root_real:
            relative = os.path.relpath(requested, root_real)
        else:
            fail("logfile path escapes the task/workspace root")
    except ValueError:
        fail("logfile path is on a different filesystem root")
else:
    requested = os.path.normpath(os.path.join(root_real, logfile_arg))
    relative = os.path.relpath(requested, root_real)

relative_parts = pathlib.PurePath(relative).parts
if relative in (".", "") or not relative_parts or relative_parts[0] == "..":
    fail("logfile path escapes the task/workspace root")
if any(part in ("", ".") for part in relative_parts):
    fail("invalid logfile path")

no_follow_directory = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
no_follow_file = os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK
create_file = no_follow_file | os.O_CREAT | os.O_EXCL
header = b"ts\tphase\tdecision\twhy\tevidence\tresult\n"


def write_all(fd, data):
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        view = view[written:]


def clean(value):
    value = value.replace("\t", " ").replace("\n", " ").replace("\r", " ")
    if value[:1] in "=+-@":
        return "'" + value
    return value


row = (
    datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    + "\t"
    + "\t".join(clean(value) for value in values)
    + "\n"
).encode("utf-8")

root_fd = None
parent_fd = None
log_fd = None
try:
    root_fd = os.open(root_real, no_follow_directory)
    parent_fd = root_fd
    for component in relative_parts[:-1]:
        try:
            next_fd = os.open(component, no_follow_directory, dir_fd=parent_fd)
        except FileNotFoundError:
            try:
                os.mkdir(component, 0o700, dir_fd=parent_fd)
            except FileExistsError:
                pass
            next_fd = os.open(component, no_follow_directory, dir_fd=parent_fd)
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                try:
                    component_stat = os.stat(
                        component, dir_fd=parent_fd, follow_symlinks=False
                    )
                except OSError:
                    component_stat = None
                if component_stat is not None and stat.S_ISLNK(component_stat.st_mode):
                    fail("logfile path contains a symlink component")
            fail("logfile parent is not a directory: " + str(exc))
        if parent_fd != root_fd:
            os.close(parent_fd)
        parent_fd = next_fd

    filename = relative_parts[-1]
    try:
        target_stat = os.stat(filename, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        target_stat = None
    if target_stat is not None and stat.S_ISLNK(target_stat.st_mode):
        fail("logfile target must not be a symlink")
    if target_stat is not None and not stat.S_ISREG(target_stat.st_mode):
        fail("logfile target must be a regular file")
    if target_stat is not None and target_stat.st_nlink > 1:
        fail("logfile target must not be hard-linked")
    try:
        log_fd = os.open(filename, no_follow_file, dir_fd=parent_fd)
    except FileNotFoundError:
        try:
            log_fd = os.open(filename, create_file, 0o600, dir_fd=parent_fd)
        except FileExistsError:
            log_fd = os.open(filename, no_follow_file, dir_fd=parent_fd)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            fail("logfile target must not be a symlink")
        fail("cannot open logfile: " + str(exc))

    fcntl.flock(log_fd, fcntl.LOCK_EX)
    log_stat = os.fstat(log_fd)
    if not stat.S_ISREG(log_stat.st_mode):
        fail("logfile target must be a regular file")
    if log_stat.st_nlink > 1:
        fail("logfile target must not be hard-linked")
    if log_stat.st_size == 0:
        write_all(log_fd, header)
    write_all(log_fd, row)
finally:
    if log_fd is not None:
        os.close(log_fd)
    if parent_fd is not None and parent_fd != root_fd:
        os.close(parent_fd)
    if root_fd is not None:
        os.close(root_fd)
PY
