"""Exercise the bundled pstack decision-log helper in an isolated directory."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent


class ShowWorkFixture(unittest.TestCase):
    def test_append_sanitizes_cells_and_keeps_evidence(self):
        with tempfile.TemporaryDirectory(prefix="cursor-show-work-") as temp:
            root = Path(temp)
            preview = root / "preview"
            build = subprocess.run(
                [sys.executable, str(REPO / "scripts/sync-cursor-plugin-skills.py"),
                 "--preview-candidates", str(preview)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            helper = preview / "cursor-show-me-your-work/scripts/log.sh"
            logfile = root / "scratch/decisions.tsv"
            for decision in ("=SUM(1,2)", "fixed\nsecond line"):
                run = subprocess.run(
                    ["bash", str(helper), str(logfile), "phase", decision,
                     "reason", "artifact.txt", "VERIFIED"],
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(run.returncode, 0, run.stderr)
            lines = logfile.read_text().splitlines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(lines[0], "ts\tphase\tdecision\twhy\tevidence\tresult")
            self.assertIn("\t'=SUM(1,2)\t", lines[1])
            self.assertIn("\tfixed second line\t", lines[2])
            self.assertIn("\tartifact.txt\tVERIFIED", lines[2])


if __name__ == "__main__":
    unittest.main()
