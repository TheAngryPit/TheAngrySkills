"""Bounded behavior proof for the held local Canvas fallbacks."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cursor_canvas_adapters import (  # noqa: E402
    AdapterError,
    MissingCapability,
    render_docs_canvas,
    render_pr_review_canvas,
)


class CursorCanvasAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_docs_produces_linked_markdown_and_html_without_canvas_claim(self) -> None:
        source = self.root / "docs" / "architecture.md"
        source.write_text(
            "# Architecture\n\n## Components\n\nThe API calls the worker.\n",
            encoding="utf-8",
        )

        result = render_docs_canvas(self.root, "docs/architecture.md")

        self.assertEqual(result["status"], "FALLBACK")
        self.assertEqual(result["canvas_parity"], "UNAVAILABLE")
        self.assertFalse(result["product_configuration"])
        markdown = Path(result["artifacts"]["markdown"])
        rendered = Path(result["artifacts"]["html"])
        self.assertTrue(markdown.is_file())
        self.assertTrue(rendered.is_file())
        self.assertIn("architecture.md", markdown.read_text(encoding="utf-8"))
        self.assertIn("id=\"architecture\"", rendered.read_text(encoding="utf-8"))
        self.assertIn("Canvas surface and SDK declarations are unavailable", rendered.read_text(encoding="utf-8"))

    def test_docs_rejects_implicit_invocation_and_symlink_escape(self) -> None:
        source = self.root / "docs" / "guide.md"
        source.write_text("# Guide\n", encoding="utf-8")
        blocked = render_docs_canvas(self.root, source, explicit=False)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertFalse((self.root / ".artifacts").exists())

        outside = Path(self.temp.name).parent / "canvas-outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        link = self.root / "docs" / "escape.md"
        try:
            link.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlink unavailable: {exc}")
        with self.assertRaises(AdapterError):
            render_docs_canvas(self.root, "docs/escape.md")
        outside.unlink()

        internal_link = self.root / "docs" / "internal-link.md"
        internal_link.symlink_to(source)
        with self.assertRaises(AdapterError):
            render_docs_canvas(self.root, internal_link)

    def test_pr_review_groups_fixture_diff_and_surfaces_attention(self) -> None:
        diff = self.root / "change.diff"
        diff.write_text(
            "diff --git a/src/auth.py b/src/auth.py\n"
            "--- a/src/auth.py\n+++ b/src/auth.py\n"
            "@@ -1,1 +1,2 @@\n-token = old\n+token = new\n+TODO: review auth boundary\n"
            "diff --git a/package-lock.json b/package-lock.json\n"
            "--- a/package-lock.json\n+++ b/package-lock.json\n"
            "@@ -1,1 +1,1 @@\n-old\n+new\n",
            encoding="utf-8",
        )

        result = render_pr_review_canvas(self.root, diff)

        self.assertEqual(result["status"], "FALLBACK")
        self.assertEqual(result["source"], "local-diff-fixture")
        self.assertEqual(result["canvas_parity"], "UNAVAILABLE")
        self.assertEqual(result["categories"], ("core logic", "boilerplate & mechanical"))
        markdown = Path(result["artifacts"]["markdown"]).read_text(encoding="utf-8")
        self.assertLess(markdown.index("Core Logic"), markdown.index("Boilerplate & Mechanical"))
        self.assertIn("Authentication or authorization changed", markdown)
        self.assertIn("TODO/FIXME marker changed", markdown)
        self.assertIn("PR metadata and `gh` access were not used", markdown)

    def test_pr_review_rejects_live_url_and_implicit_invocation(self) -> None:
        with self.assertRaises(MissingCapability):
            render_pr_review_canvas(self.root, "https://github.com/example/repo/pull/1")
        blocked = render_pr_review_canvas(self.root, "missing.diff", explicit=False)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertFalse((self.root / ".artifacts").exists())


if __name__ == "__main__":
    unittest.main()
