#!/usr/bin/env python3
"""Probe Illustrator-oriented assets without opening Illustrator."""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=15)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"missing command: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout: {' '.join(cmd)}"


def illustrator_candidates() -> list[str]:
    if platform.system() != "Darwin":
        return []
    apps = Path("/Applications")
    if not apps.exists():
        return []
    return sorted(str(p) for p in apps.iterdir() if "illustrator" in p.name.lower())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("asset", help="Path to .ai, .pdf, .eps, .svg, or related Illustrator asset")
    args = ap.parse_args()

    asset = Path(args.asset).expanduser()
    result: dict[str, object] = {
        "asset": str(asset),
        "exists": asset.exists(),
        "suffix": asset.suffix.lower(),
        "platform": platform.system(),
        "illustrator_apps": illustrator_candidates(),
        "tools": {
            "file": bool(shutil.which("file")),
            "pdfinfo": bool(shutil.which("pdfinfo")),
            "pdftocairo": bool(shutil.which("pdftocairo")),
        },
    }

    if not asset.exists():
        result["recommended_lane"] = "missing-file"
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    code, out, err = run(["file", "-b", str(asset)])
    result["file"] = {"code": code, "stdout": out, "stderr": err}
    pdf_compatible = "PDF" in out or "PDF document" in out
    result["pdf_compatible"] = pdf_compatible

    if shutil.which("pdfinfo"):
        code, out, err = run(["pdfinfo", str(asset)])
        info = {"code": code, "stderr": err}
        if code == 0:
            for line in out.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    if key.strip() in {"Pages", "Creator", "Producer", "Page size", "PDF version"}:
                        info[key.strip()] = value.strip()
        result["pdfinfo"] = info

    if pdf_compatible and shutil.which("pdftocairo"):
        result["recommended_lane"] = "file-level-render-first"
    elif result["illustrator_apps"]:
        result["recommended_lane"] = "illustrator-scripting"
    else:
        result["recommended_lane"] = "install-open-illustrator-or-use-computer-use"

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
