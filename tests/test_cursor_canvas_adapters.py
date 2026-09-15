"""Bounded behavior proof for the held local Canvas fallbacks."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cursor_canvas_adapters import (  # noqa: E402
    AdapterError,
    MissingCapability,
    extract_workflow_from_chats,
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
        (self.root / "docs" / "operations.md").write_text("# Operations\n", encoding="utf-8")
        source.write_text(
            "# Architecture\n\n## Components\n\nThe **API** calls the `worker`.\n\n"
            "Unsafe [script](javascript:alert(1)), [payload](data:text/html,owned), "
            "[tabbed](java\tscript:alert(1)), and [colon](foo:bar).\n"
            "See [operations](operations.md).\n"
            "Safe [guide](../README.md), [web](https://example.test), and [mail](mailto:docs@example.test).\n",
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
        markdown_text = markdown.read_text(encoding="utf-8")
        self.assertIn("architecture.md", markdown_text)
        for unsafe in ("javascript:", "data:text", "java\tscript:", "[colon](foo:bar)"):
            self.assertNotIn(unsafe, markdown_text)
        self.assertIn("[web](https://example.test)", markdown_text)
        rendered_text = rendered.read_text(encoding="utf-8")
        self.assertIn("id=\"doc-1-architecture\"", rendered_text)
        self.assertIn("<strong>API</strong>", rendered_text)
        self.assertIn("<code>worker</code>", rendered_text)
        self.assertNotIn("javascript:", rendered_text)
        self.assertNotIn("data:text", rendered_text)
        self.assertNotIn('href="java', rendered_text)
        self.assertNotIn('href="foo:bar"', rendered_text)
        self.assertIn('href="../../docs/operations.md"', rendered_text)
        self.assertIn('href="../../README.md"', rendered_text)
        self.assertIn('href="https://example.test"', rendered_text)
        self.assertIn('href="mailto:docs@example.test"', rendered_text)
        self.assertIn("Canvas surface and SDK declarations are unavailable", rendered_text)

    def test_docs_scopes_duplicate_document_and_section_anchors(self) -> None:
        (self.root / "docs" / "first.md").write_text(
            "# Guide\n\n## Setup\n\n## Setup\n", encoding="utf-8"
        )
        (self.root / "docs" / "second.md").write_text(
            "# Guide\n\n## Setup\n", encoding="utf-8"
        )

        result = render_docs_canvas(self.root, "docs")
        markdown = Path(result["artifacts"]["markdown"]).read_text(encoding="utf-8")
        rendered = Path(result["artifacts"]["html"]).read_text(encoding="utf-8")
        self.assertIn("[Setup](#doc-1-setup)", markdown)
        self.assertIn("[Setup](#doc-1-setup-2)", markdown)
        self.assertIn("[Setup](#doc-2-setup)", markdown)
        self.assertEqual(rendered.count('id="doc-1-setup"'), 1)
        self.assertEqual(rendered.count('id="doc-1-setup-2"'), 1)
        self.assertEqual(rendered.count('id="doc-2-setup"'), 1)
        self.assertNotIn('id="guide"', rendered)

        self.assertEqual(rendered.count('<h3 id="doc-1-setup"'), 1)
        self.assertEqual(rendered.count('<h3 id="doc-1-setup-2"'), 1)

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

    def test_docs_rejects_cross_reference_escape_before_writing(self) -> None:
        source = self.root / "docs" / "escape-link.md"
        source.write_text("# Escape\n\n[Outside](../../outside.md)\n", encoding="utf-8")
        with self.assertRaises(AdapterError):
            render_docs_canvas(self.root, source)
        self.assertFalse((self.root / ".artifacts").exists())

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
        self.assertIn("line 2 evidence", markdown)
        self.assertIn("Authentication or authorization changed", markdown)
        self.assertIn("TODO/FIXME marker was added or removed", markdown)
        self.assertIn("PR metadata and `gh` access were not used", markdown)
        self.assertIn("Mechanical change summarized", markdown)
        mechanical = markdown[markdown.index("## Boilerplate & Mechanical") :]
        self.assertNotIn("token = old", mechanical)

    def test_pr_review_rejects_live_url_and_implicit_invocation(self) -> None:
        with self.assertRaises(MissingCapability):
            render_pr_review_canvas(self.root, "https://github.com/example/repo/pull/1")
        blocked = render_pr_review_canvas(self.root, "missing.diff", explicit=False)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertFalse((self.root / ".artifacts").exists())

    def test_workflow_from_chats_extracts_redacted_parent_scoped_preferences(self) -> None:
        transcript = self.root / "export.jsonl"
        transcript.write_text(
            '{"thread_id":"parent-1","role":"user","timestamp":"2026-09-14T10:00:00Z",'
            '"text":"I prefer exact evidence and always cite the source file with token=secret-value."}\n'
            '{"thread_id":"child-1","parent_thread_id":"parent-1","role":"assistant",'
            '"timestamp":"2026-09-14T10:01:00Z","content":"Always cite the source file."}\n'
            '{"thread_id":"parent-1","role":"user","timestamp":"2026-09-14T11:00:00Z",'
            '"message":{"content":[{"text":"I prefer exact evidence and always cite the source file."}]}}\n'
            '{"thread_id":"other","role":"user","timestamp":"2026-09-14T10:00:00Z",'
            '"text":"I prefer to expose unrelated private material."}\n',
            encoding="utf-8",
        )

        result = extract_workflow_from_chats(
            self.root,
            transcript,
            parent_thread_id="parent-1",
            now=datetime(2026, 9, 14, 12, tzinfo=timezone.utc),
        )

        self.assertEqual(result["status"], "FIXTURE_ONLY")
        self.assertEqual(result["history_capability"], "SUPPLIED_EXPORT_ONLY")
        self.assertEqual(result["records"], 3)
        self.assertFalse(result["writes_performed"])
        proposal = Path(result["artifacts"]["proposal"])
        receipt = Path(result["artifacts"]["receipt"])
        proposal_text = proposal.read_text(encoding="utf-8")
        receipt_text = receipt.read_text(encoding="utf-8")
        self.assertIn("parent-1", proposal_text)
        self.assertIn("exact evidence", proposal_text)
        self.assertIn("strong", proposal_text)
        self.assertIn("<redacted>", proposal_text)
        self.assertNotIn("secret-value", proposal_text)
        self.assertNotIn("other", proposal_text)
        self.assertNotIn("secret-value", receipt_text)
        self.assertNotIn("/export.jsonl", proposal_text)
        self.assertIn("no automatic writeback", proposal_text)

    def test_workflow_from_chats_keeps_missing_history_and_bad_scope_write_free(self) -> None:
        missing = extract_workflow_from_chats(
            self.root,
            None,
            parent_thread_id="parent-1",
        )
        self.assertEqual(missing["status"], "PARTIAL")
        self.assertFalse(missing["writes_performed"])
        self.assertFalse((self.root / ".artifacts").exists())

        transcript = self.root / "empty-window.jsonl"
        transcript.write_text(
            '{"thread_id":"parent-1","role":"user","timestamp":"2020-01-01T00:00:00Z",'
            '"text":"I prefer exact evidence."}\n',
            encoding="utf-8",
        )
        no_records = extract_workflow_from_chats(
            self.root,
            transcript,
            parent_thread_id="parent-1",
            now=datetime(2026, 9, 14, tzinfo=timezone.utc),
        )
        self.assertEqual(no_records["status"], "PARTIAL")
        self.assertFalse((self.root / ".artifacts").exists())

        malformed = self.root / "malformed.jsonl"
        malformed.write_text("not-json\n", encoding="utf-8")
        with self.assertRaisesRegex(AdapterError, "valid JSON"):
            extract_workflow_from_chats(
                self.root,
                malformed,
                parent_thread_id="parent-1",
            )
        self.assertFalse((self.root / ".artifacts").exists())

    def test_workflow_from_chats_blocks_implicit_and_remote_history(self) -> None:
        blocked = extract_workflow_from_chats(
            self.root,
            "export.jsonl",
            parent_thread_id="parent-1",
            explicit=False,
        )
        self.assertEqual(blocked["status"], "BLOCKED")
        remote = extract_workflow_from_chats(
            self.root,
            "https://example.test/export.jsonl",
            parent_thread_id="parent-1",
        )
        self.assertEqual(remote["status"], "PARTIAL")
        self.assertFalse((self.root / ".artifacts").exists())


if __name__ == "__main__":
    unittest.main()
