#!/usr/bin/env python3
"""Check external skill-audit tool versions without installing them."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, asdict


@dataclass
class ToolCheck:
    package: str
    version: str | None
    modified: str | None
    ok: bool
    error: str | None = None


def npm_view(package: str) -> ToolCheck:
    try:
        result = subprocess.run(
            ["npm", "view", package, "version", "time", "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        return ToolCheck(
            package=package,
            version=payload.get("version"),
            modified=(payload.get("time") or {}).get("modified"),
            ok=True,
        )
    except Exception as exc:  # noqa: BLE001 - report tool failure, do not hide it.
        return ToolCheck(package=package, version=None, modified=None, ok=False, error=str(exc))


def main() -> int:
    checks = [npm_view("@spboyer/sensei")]
    print(json.dumps({"checks": [asdict(check) for check in checks]}, indent=2))
    return 0 if all(check.ok for check in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
