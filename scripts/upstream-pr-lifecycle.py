#!/usr/bin/env python3
"""Pure helpers for review-only upstream proposal PRs.

The GitHub workflow owns network operations.  This module owns the stable
markers and the fail-closed PR selection rule so shell quoting cannot weaken
deduplication.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MARKER_PREFIX = "upstream-update"
CODEX_HANDOFF_PREFIX = "codex-handoff"


def family_batch_marker(family: str, batch: str) -> str:
    return f"<!-- {MARKER_PREFIX}:family={family}:batch={batch} -->"


def codex_request_marker(family: str, batch: str, source_head: str) -> str:
    return f"<!-- {CODEX_HANDOFF_PREFIX}:family={family}:batch={batch}:head={source_head} -->"


def matching_prs(prs: list[dict[str, Any]], family: str, batch: str, base: str, head: str) -> list[dict[str, Any]]:
    """Return PRs with the exact family/batch marker and refs.

    A marker in a similarly named PR or a PR on another base/head is not a
    match.  Callers must abort if more than one exact match remains.
    """

    needle = family_batch_marker(family, batch)
    return [
        pr for pr in prs
        if needle in (pr.get("body") or "")
        and pr.get("baseRefName") == base
        and pr.get("headRefName") == head
    ]


def select_pr(prs: list[dict[str, Any]], family: str, batch: str, base: str, head: str) -> dict[str, Any]:
    needle = family_batch_marker(family, batch)
    marked = [pr for pr in prs if needle in (pr.get("body") or "")]
    if len(marked) > 1:
        numbers = [str(pr.get("number", "?")) for pr in marked]
        raise ValueError(f"multiple open PRs match {family}:{batch} ({', '.join(numbers)}); aborting")
    if not marked:
        return {"action": "create", "number": None}
    existing = marked[0]
    if existing.get("baseRefName") != base or existing.get("headRefName") != head:
        raise ValueError(
            f"open PR {existing.get('number', '?')} has marker {family}:{batch} "
            f"but unexpected refs {existing.get('baseRefName')}...{existing.get('headRefName')}; aborting"
        )
    return {"action": "update", "number": existing.get("number")}


def has_codex_request(comments: list[dict[str, Any]], family: str, batch: str, source_head: str) -> bool:
    needle = codex_request_marker(family, batch, source_head)
    return any(needle in (comment.get("body") or "") for comment in comments)


def validate_report(report: dict[str, Any]) -> None:
    required = {"family", "batch", "latest", "marker", "codex_request_marker"}
    missing = required - report.keys()
    if missing:
        raise ValueError(f"report missing keys: {', '.join(sorted(missing))}")
    expected = family_batch_marker(report["family"], report["batch"])
    if report["marker"] != expected:
        raise ValueError("report marker does not match family/batch")


def pr_body(report: dict[str, Any], report_markdown: str, codex_prompt: str) -> str:
    validate_report(report)
    if report.get("candidate_content_promoted"):
        raise ValueError("candidate content cannot be promoted by the proposal workflow")
    evidence = report_markdown.rstrip()
    # Detector reports carry the marker for standalone issue/archive use.  A
    # PR body owns one marker at its top so exact-marker deduplication remains
    # deterministic even when the evidence is copied verbatim.
    if evidence.startswith(report["marker"]):
        evidence = evidence[len(report["marker"]):].lstrip("\r\n")
    return (
        f"{report['marker']}\n"
        f"## Review-only upstream update: {report['family']} / {report['batch']}\n\n"
        "This PR carries detector evidence and the review handoff. It does not publish upstream content or accept a new baseline.\n\n"
        f"{evidence}\n\n"
        "## Codex handoff\n\n"
        f"{report['codex_request_marker']}\n"
        "Post the bounded non-review request below only after confirming this comment is visible:\n\n"
        f"```text\n{codex_prompt.rstrip()}\n```\n\n"
        "Record visible comment, Codex reaction/task, delivery commit, branch SHA/files, and passing checks. "
        "A human must approve any content or baseline change. No automatic merge or force-push.\n"
    )


def bounded_prompt(report: dict[str, Any]) -> str:
    validate_report(report)
    return (
        f"@codex update Review only the reported {report['family']} / {report['batch']} upstream delta "
        f"at {report['latest']}. Preserve the repository's pins, exclusions, provenance, patches, hashes, "
        "global installs and homes. Propose or implement only bounded adaptation changes supported by the "
        "PR evidence. Do not publish new skills, accept a baseline, install anything, merge, force-push, or "
        "broaden scope. Leave the branch reviewable and report changed files and checks."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    select = subparsers.add_parser("select")
    select.add_argument("--family", required=True)
    select.add_argument("--batch", required=True)
    select.add_argument("--base", required=True)
    select.add_argument("--head", required=True)
    select.add_argument("--prs-json", help="JSON array of open PRs; stdin when omitted")
    codex = subparsers.add_parser("request-present")
    codex.add_argument("--family", required=True)
    codex.add_argument("--batch", required=True)
    codex.add_argument("--source-head", required=True)
    codex.add_argument("--comments-json", help="JSON array of comments; stdin when omitted")
    render = subparsers.add_parser("render-pr")
    render.add_argument("--report-json", required=True)
    render.add_argument("--report-file", required=True)
    args = parser.parse_args()
    if args.command == "select":
        raw = args.prs_json if args.prs_json is not None else sys.stdin.read()
        try:
            result = select_pr(json.loads(raw or "[]"), args.family, args.batch, args.base, args.head)
        except (ValueError, json.JSONDecodeError) as error:
            print(str(error), file=sys.stderr)
            return 2
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.command == "render-pr":
        report = json.loads(args.report_json)
        print(pr_body(report, Path(args.report_file).read_text(), bounded_prompt(report)))
        return 0
    raw = args.comments_json if args.comments_json is not None else sys.stdin.read()
    print("true" if has_codex_request(json.loads(raw or "[]"), args.family, args.batch, args.source_head) else "false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
