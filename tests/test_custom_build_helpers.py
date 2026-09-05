"""Run the bundled JavaScript helper regressions in the existing pytest CI gate."""

from pathlib import Path
import subprocess


def test_custom_build_helpers():
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        ["node", "--test", "tests/test_custom_build_helpers.mjs"],
        cwd=root,
        check=True,
        timeout=60,
    )
