"""Behavioral proof for the bounded Cursor show-me-your-work writer."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "sources/cursor-plugins/manifest.json"
OVERLAY = REPO / "sources/cursor-plugins/overlays/cursor-show-me-your-work.json"


class ShowWorkFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="cursor-show-work-")
        cls.base = Path(cls.temp.name)
        cls.preview = cls.base / "preview"
        build = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/sync-cursor-plugin-skills.py"),
                "--preview-candidates",
                str(cls.preview),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if build.returncode:
            cls.temp.cleanup()
            raise RuntimeError(build.stderr)
        cls.helper = cls.preview / "cursor-show-me-your-work/scripts/log.sh"

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.task = self.base / self._testMethodName
        self.task.mkdir()

    def run_helper(self, logfile, *values, root=None, cwd=None, timeout=None):
        task_root = self.task if root is None else root
        return subprocess.run(
            [
                "bash",
                str(self.helper),
                "--root",
                str(task_root),
                str(logfile),
                *values,
            ],
            text=True,
            capture_output=True,
            check=False,
            cwd=cwd,
            timeout=timeout,
        )

    def test_normal_two_row_append_stays_under_root(self):
        logfile = self.task / "audit/decisions.tsv"
        for decision in ("first decision", "second decision"):
            result = self.run_helper(
                logfile,
                "phase",
                decision,
                "because",
                "artifact.txt",
                "VERIFIED",
            )
            self.assertEqual(result.returncode, 0, result.stderr)

        lines = logfile.read_text().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "ts\tphase\tdecision\twhy\tevidence\tresult")
        self.assertIn("\tfirst decision\tbecause\tartifact.txt\tVERIFIED", lines[1])
        self.assertIn("\tsecond decision\tbecause\tartifact.txt\tVERIFIED", lines[2])
        self.assertTrue(logfile.is_relative_to(self.task))

    def test_hostile_formula_and_newline_cells_are_sanitized(self):
        logfile = self.task / "decisions.tsv"
        result = self.run_helper(
            logfile,
            "phase\twith-tab",
            "=SUM(1,2)\nsecond line",
            "+why\rnext",
            "-evidence",
            "@result",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        line = logfile.read_text().splitlines()[1]
        self.assertEqual(
            line.split("\t")[1:],
            [
                "phase with-tab",
                "'=SUM(1,2) second line",
                "'+why next",
                "'-evidence",
                "'@result",
            ],
        )

    def test_secret_like_input_is_refused_before_log_mutation(self):
        logfile = self.task / "decisions.tsv"
        first = self.run_helper(
            logfile, "phase", "decision", "why", "artifact", "VERIFIED"
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        original = logfile.read_bytes()
        for candidate in (
            "Bearer synthetic-not-a-real-credential",
            "ghp_syntheticnotarealcredential123",
            '"api_key": "synthetic-not-a-real-credential"',
        ):
            rejected = self.run_helper(
                logfile, "phase", "decision", "why", candidate, "VERIFIED"
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("secret-like value refused", rejected.stderr)
            self.assertNotIn(candidate, rejected.stderr)
            self.assertEqual(logfile.read_bytes(), original)

    def test_existing_log_is_appended_without_a_second_header(self):
        logfile = self.task / "existing/decisions.tsv"
        logfile.parent.mkdir()
        logfile.write_text(
            "ts\tphase\tdecision\twhy\tevidence\tresult\n"
            "old\tphase\told\twhy\tevidence\tDONE\n"
        )
        result = self.run_helper(
            logfile,
            "phase",
            "new",
            "why",
            "evidence",
            "DONE",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = logfile.read_text().splitlines()
        self.assertEqual(lines[0], "ts\tphase\tdecision\twhy\tevidence\tresult")
        self.assertEqual(lines[1], "old\tphase\told\twhy\tevidence\tDONE")
        self.assertEqual(len(lines), 3)

    def test_parallel_writers_keep_one_header_and_complete_rows(self):
        logfile = self.task / "parallel/decisions.tsv"
        processes = [
            subprocess.Popen(
                [
                    "bash",
                    str(self.helper),
                    "--root",
                    str(self.task),
                    str(logfile),
                    "parallel",
                    f"decision-{index}",
                    "bounded writer",
                    "test:parallel",
                    "VERIFIED",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for index in range(24)
        ]
        for process in processes:
            _, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr)
        lines = logfile.read_text().splitlines()
        self.assertEqual(lines.count("ts\tphase\tdecision\twhy\tevidence\tresult"), 1)
        self.assertEqual(len(lines), 25)
        for line in lines[1:]:
            cells = line.split("\t")
            self.assertEqual(len(cells), 6)
            self.assertEqual(cells[1], "parallel")
            self.assertEqual(cells[3:], ["bounded writer", "test:parallel", "VERIFIED"])
        decisions = {line.split("\t")[2] for line in lines[1:]}
        self.assertEqual(decisions, {f"decision-{index}" for index in range(24)})

    def test_symlink_target_is_rejected_and_external_sentinel_survives(self):
        outside = self.base / "outside-target"
        outside.mkdir()
        sentinel = outside / "sentinel"
        sentinel.write_text("keep me")
        logfile = self.task / "decisions.tsv"
        logfile.symlink_to(sentinel)

        result = self.run_helper(logfile, "phase", "new", "why", "evidence", "DONE")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)
        self.assertEqual(sentinel.read_text(), "keep me")
        self.assertTrue(logfile.is_symlink())

    def test_fifo_target_is_rejected_without_blocking(self):
        logfile = self.task / "decisions.fifo"
        os.mkfifo(logfile, 0o600)

        result = self.run_helper(
            logfile,
            "phase",
            "new",
            "why",
            "evidence",
            "DONE",
            timeout=2,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("regular file", result.stderr)
        self.assertTrue(logfile.is_fifo())

    def test_hardlink_target_is_rejected_without_mutating_external_sentinel(self):
        outside = self.base / "outside-hardlink"
        outside.mkdir()
        sentinel = outside / "sentinel.tsv"
        sentinel.write_text("keep me")
        logfile = self.task / "hardlink.tsv"
        os.link(sentinel, logfile)

        result = self.run_helper(
            logfile,
            "phase",
            "new",
            "why",
            "evidence",
            "DONE",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hard-linked", result.stderr)
        self.assertEqual(sentinel.read_text(), "keep me")
        self.assertEqual(logfile.read_text(), "keep me")

    def test_symlink_parent_escape_is_rejected_and_external_sentinel_survives(self):
        outside = self.base / "outside-parent"
        outside.mkdir()
        sentinel = outside / "sentinel"
        sentinel.write_text("keep me")
        parent = self.task / "escape"
        parent.symlink_to(outside, target_is_directory=True)

        result = self.run_helper(
            parent / "decisions.tsv",
            "phase",
            "new",
            "why",
            "evidence",
            "DONE",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)
        self.assertEqual(sentinel.read_text(), "keep me")
        self.assertFalse((outside / "decisions.tsv").exists())

    def test_path_escape_and_invalid_or_missing_root_are_rejected(self):
        outside = self.base / "outside.tsv"
        escape = self.run_helper(
            self.task / "../outside.tsv",
            "phase",
            "new",
            "why",
            "evidence",
            "DONE",
        )
        self.assertNotEqual(escape.returncode, 0)
        self.assertFalse(outside.exists())

        missing_root = self.base / "missing-root"
        missing = self.run_helper(
            missing_root / "decisions.tsv",
            "phase",
            "new",
            "why",
            "evidence",
            "DONE",
            root=missing_root,
        )
        self.assertNotEqual(missing.returncode, 0)
        self.assertFalse(missing_root.exists())

        root_file = self.base / "root-file"
        root_file.write_text("not a directory")
        invalid = self.run_helper(
            root_file / "decisions.tsv",
            "phase",
            "new",
            "why",
            "evidence",
            "DONE",
            root=root_file,
        )
        self.assertNotEqual(invalid.returncode, 0)

    def test_root_is_required_and_old_interface_does_not_write(self):
        logfile = self.task / "decisions.tsv"
        missing_root_arg = subprocess.run(
            ["bash", str(self.helper), "--root"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(missing_root_arg.returncode, 0)

        old_interface = subprocess.run(
            [
                "bash",
                str(self.helper),
                str(logfile),
                "phase",
                "new",
                "why",
                "evidence",
                "DONE",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(old_interface.returncode, 0)
        self.assertFalse(logfile.exists())

    def test_absolute_logfile_outside_root_cannot_write_global_path(self):
        outside = self.base / "outside-global"
        outside.mkdir()
        global_log = outside / "decisions.tsv"
        result = self.run_helper(
            global_log,
            "phase",
            "new",
            "why",
            "evidence",
            "DONE",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(global_log.exists())

    def test_explicit_root_prevents_cwd_write(self):
        outside = self.base / "cwd"
        outside.mkdir()
        logfile = self.task / "nested/decisions.tsv"
        result = self.run_helper(
            "nested/decisions.tsv",
            "phase",
            "new",
            "why",
            "evidence",
            "DONE",
            cwd=outside,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(logfile.exists())
        self.assertFalse((outside / "nested").exists())

    def test_published_writer_matches_preview_and_source_pin(self):
        manifest = json.loads(MANIFEST.read_text())
        entry = next(item for item in manifest["skills"] if item["published_name"] == "cursor-show-me-your-work")
        overlay = json.loads(OVERLAY.read_text())
        self.assertTrue(entry["publish"])
        self.assertTrue(overlay["codex_contract"]["promotion_status"].startswith("promoted_"))
        self.assertEqual(overlay["source_sha256"], entry["files"]["SKILL.md"])
        published = REPO / "skills/mirrors-cursor/cursor-show-me-your-work"
        self.assertEqual(
            (published / "scripts/log.sh").read_bytes(), self.helper.read_bytes()
        )
        self.assertIn("scripts/log.sh --root <task-root>", (published / "SKILL.md").read_text())
        self.assertEqual(
            (published / "agents/openai.yaml").read_text(),
            "policy:\n  allow_implicit_invocation: false\n",
        )


if __name__ == "__main__":
    unittest.main()
