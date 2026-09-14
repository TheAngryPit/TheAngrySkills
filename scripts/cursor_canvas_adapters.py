"""Project-local fallbacks for the two held Cursor Canvas mirrors.

The pinned skills describe a Cursor Canvas SDK that is not available in the
current Codex host.  These adapters keep the workflows useful by producing a
small, linked Markdown/HTML review artifact under an explicitly supplied
project root.  They never read the user's Cursor home, invoke ``gh``, access a
network, install anything, or claim Canvas SDK parity.
"""

from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from urllib.parse import quote


MAX_DOCUMENTS = 32
MAX_DOCUMENT_BYTES = 256_000
MAX_DIFF_BYTES = 512_000
DEFAULT_DOCS_OUTPUT = ".artifacts/cursor-docs-canvas"
DEFAULT_REVIEW_OUTPUT = ".artifacts/cursor-pr-review-canvas"
CANVAS_GAP = (
    "Cursor Canvas surface and SDK declarations are unavailable; this is a "
    "linked local Markdown/HTML fallback, not Canvas runtime parity."
)


class AdapterError(ValueError):
    """Invalid bounded input or an unsafe project-local path."""


class MissingCapability(AdapterError):
    """A required external capability is unavailable."""


class PermissionDenied(AdapterError):
    """An action outside the adapter's read-and-local-artifact scope."""


@dataclass(frozen=True)
class _Document:
    path: Path
    relative: str
    text: str
    headings: tuple[str, ...]


@dataclass(frozen=True)
class _DiffFile:
    path: str
    status: str
    additions: int
    deletions: int
    patch: str
    category: str
    callouts: tuple[str, ...]


def _project_root(project_root: str | Path) -> Path:
    root_path = Path(project_root)
    if root_path.is_symlink():
        raise AdapterError("project root must not be a symlink")
    if not root_path.exists() or not root_path.is_dir():
        raise AdapterError("project root must be an existing directory")
    # Keep the caller's lexical spelling so links inside the selected root
    # remain observable.  Canonicalizing here would erase a symlink that
    # happens to resolve back inside the root.
    return Path(os.path.abspath(root_path))


def _reject_symlink_components(root: Path, relative: Path) -> None:
    """Reject links in every component below an explicit project root."""

    if root.is_symlink():
        raise AdapterError("project root must not be a symlink")
    current = root
    for component in relative.parts:
        if component in ("", "."):
            continue
        current /= component
        if current.is_symlink():
            raise AdapterError("project-local path must not contain symlinks")


def _inside_root(root: Path, candidate: Path, label: str) -> Path:
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise AdapterError(f"{label} must stay inside the project root") from exc
    _reject_symlink_components(root, relative)
    return candidate


def _resolve_input(root: Path, source: str | Path, label: str) -> Path:
    candidate = Path(source)
    if not candidate.is_absolute():
        candidate = root / candidate
    # Normalize ``..`` lexically before containment checks.  Resolve only
    # after checking links so a symlink escape remains observable and
    # rejectable rather than silently becoming an external source.
    candidate = Path(os.path.abspath(candidate))
    try:
        candidate.relative_to(root)
    except ValueError:
        # Temporary directories on macOS can be addressed through a stable
        # ``/var`` alias while ``Path.resolve`` returns ``/private/var``.
        # Normalize that alias, then apply the same containment check.  A
        # genuine outside path still fails the second check.
        candidate = candidate.resolve(strict=False)
    else:
        # Keep this check separate from alias normalization: a symlink inside
        # the project must be rejected even if it resolves back inside it.
        _reject_symlink_components(root, candidate.relative_to(root))
    _inside_root(root, candidate, label)
    if candidate.is_symlink():
        raise AdapterError(f"{label} must not be a symlink")
    if not candidate.exists():
        raise AdapterError(f"{label} does not exist")
    return candidate


def _safe_output(root: Path, output: str | Path) -> Path:
    candidate = Path(output)
    if candidate.is_absolute():
        target = candidate
    else:
        target = root / candidate
    target = Path(os.path.abspath(target))
    try:
        target.relative_to(root)
    except ValueError:
        target = target.resolve(strict=False)
    else:
        _reject_symlink_components(root, target.relative_to(root))
    _inside_root(root, target, "artifact output")
    if target.exists() and not target.is_dir():
        raise AdapterError("artifact output must be a directory")
    if target.is_symlink():
        raise AdapterError("artifact output must not be a symlink")
    return target


def _validate_limit(value: int, label: str, maximum: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise AdapterError(f"{label} must be a positive integer")
    if value > maximum:
        raise AdapterError(f"{label} exceeds the bounded maximum of {maximum}")


def _read_text(path: Path, maximum: int, label: str) -> str:
    if not path.is_file():
        raise AdapterError(f"{label} must be a regular file")
    if path.stat().st_size > maximum:
        raise AdapterError(f"{label} exceeds the bounded size limit")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise AdapterError(f"{label} must contain non-empty text")
    return text


def _heading_lines(text: str) -> tuple[str, ...]:
    return tuple(
        match.group(2).strip()
        for line in text.splitlines()
        if (match := re.match(r"^(#{1,6})\s+(.+?)\s*$", line))
    )


def _slug(value: str, fallback: str = "section") -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result or fallback


def _collect_documents(root: Path, source: str | Path, max_documents: int) -> tuple[_Document, ...]:
    _validate_limit(max_documents, "max_documents", MAX_DOCUMENTS)
    source_path = _resolve_input(root, source, "documentation input")
    candidates = [source_path] if source_path.is_file() else sorted(source_path.rglob("*.md"))
    if not candidates:
        raise AdapterError("documentation input contains no Markdown files")
    if len(candidates) > max_documents:
        raise AdapterError("documentation input exceeds max_documents")
    documents: list[_Document] = []
    for path in candidates:
        _inside_root(root, path, "documentation input")
        if path.is_symlink():
            raise AdapterError("documentation input must not contain symlinks")
        text = _read_text(path, MAX_DOCUMENT_BYTES, "documentation input")
        documents.append(
            _Document(
                path=path,
                relative=path.relative_to(root).as_posix(),
                text=text,
                headings=_heading_lines(text),
            )
        )
    return tuple(documents)


def _relative_link(from_dir: Path, target: Path) -> str:
    return quote(Path(os.path.relpath(target, from_dir)).as_posix(), safe="/._-~")


def _markdown_docs(documents: Sequence[_Document], artifact_dir: Path, root: Path) -> str:
    lines = [
        "# Documentation Canvas fallback",
        "",
        f"> {CANVAS_GAP}",
        "",
        "## Table of contents",
        "",
    ]
    for index, document in enumerate(documents, 1):
        anchor = _slug(document.headings[0] if document.headings else Path(document.relative).stem, f"document-{index}")
        lines.append(f"- [{document.relative}](#{anchor})")
    lines += ["", "## References", "", "This artifact links back to the bounded source files.", ""]
    for index, document in enumerate(documents, 1):
        title = document.headings[0] if document.headings else Path(document.relative).stem
        anchor = _slug(title, f"document-{index}")
        link = _relative_link(artifact_dir, root / document.relative)
        lines += [f"## {title} {{#{anchor}}}", "", f"Source: [{document.relative}]({link})", ""]
        if document.headings:
            lines.append("Sections: " + ", ".join(document.headings))
            lines.append("")
        lines.append(document.text.rstrip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _inline_markdown(value: str) -> str:
    escaped = html.escape(value, quote=True)
    return re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: f'<a href="{html.escape(match.group(2), quote=True)}">{match.group(1)}</a>',
        escaped,
    )


def _markdown_to_html(markdown: str, title: str) -> str:
    body: list[str] = []
    in_code = False
    in_list = False
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            body.append(f"<p>{_inline_markdown(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            body.append("</ul>")
            in_list = False

    for line in markdown.splitlines():
        if line.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                body.append("</code></pre>")
            else:
                body.append("<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            body.append(html.escape(line, quote=False) + "\n")
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)(?:\s+\{#([^}]+)\})?$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            anchor = heading.group(3) or _slug(heading.group(2))
            body.append(f'<h{level} id="{html.escape(anchor, quote=True)}">{_inline_markdown(heading.group(2))}</h{level}>')
        elif not line.strip():
            flush_paragraph()
            close_list()
        elif line.startswith("> "):
            flush_paragraph()
            close_list()
            body.append(f"<blockquote>{_inline_markdown(line[2:])}</blockquote>")
        elif line.startswith("- "):
            flush_paragraph()
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{_inline_markdown(line[2:])}</li>")
        else:
            close_list()
            paragraph.append(line.strip())
    flush_paragraph()
    close_list()
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>{html.escape(title)}</title>"
        "<style>body{font:16px system-ui;line-height:1.55;max-width:960px;margin:2rem auto;padding:0 1rem;color:#18212b}"
        "pre{background:#f3f5f7;padding:1rem;overflow:auto}a{color:#075985}blockquote{border-left:4px solid #94a3b8;padding-left:1rem;color:#475569}"
        ".meta{background:#fff7ed;border:1px solid #fdba74;padding:.8rem}</style></head><body>"
        + "".join(body)
        + "</body></html>\n"
    )


def _write_artifacts(output_dir: Path, markdown: str, title: str, root: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    _reject_symlink_components(root, output_dir.relative_to(root))
    if output_dir.is_symlink():
        raise AdapterError("artifact output must not be a symlink")
    markdown_path = output_dir / "index.md"
    html_path = output_dir / "index.html"
    for path in (markdown_path, html_path):
        _reject_symlink_components(root, path.relative_to(root))
        if path.exists() and not path.is_file():
            raise AdapterError("artifact target must be a regular file")
    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(_markdown_to_html(markdown, title), encoding="utf-8")
    return {"markdown": str(markdown_path), "html": str(html_path)}


def _blocked_result(reason: str) -> dict[str, object]:
    return {
        "status": "BLOCKED",
        "reason": reason,
        "canvas_parity": "UNAVAILABLE",
        "external_writes": False,
        "product_configuration": False,
    }


def render_docs_canvas(
    project_root: str | Path,
    source: str | Path,
    *,
    output: str | Path = DEFAULT_DOCS_OUTPUT,
    max_documents: int = MAX_DOCUMENTS,
    explicit: bool = True,
) -> dict[str, object]:
    """Render bounded Markdown sources to a linked local docs artifact."""

    if not explicit:
        return _blocked_result("this held workflow is explicit-only")
    root = _project_root(project_root)
    documents = _collect_documents(root, source, max_documents)
    output_dir = _safe_output(root, output)
    markdown = _markdown_docs(documents, output_dir, root)
    artifacts = _write_artifacts(output_dir, markdown, "Documentation Canvas fallback", root)
    return {
        "status": "FALLBACK",
        "source": "local-markdown",
        "documents": tuple(document.relative for document in documents),
        "artifacts": artifacts,
        "canvas_parity": "UNAVAILABLE",
        "parity_gap": CANVAS_GAP,
        "external_writes": False,
        "product_configuration": False,
        "policy": "explicit-only; conditional local fallback",
    }


def _diff_file_header(line: str) -> str | None:
    match = re.match(r"^diff --git a/(.+?) b/(.+?)$", line)
    if match:
        return match.group(2)
    match = re.match(r"^\+\+\+ b/(.+)$", line)
    return match.group(1) if match else None


def _category(path: str, patch: str) -> str:
    lower = path.lower()
    if any(token in lower for token in ("package-lock", "pnpm-lock", "yarn.lock", ".min.", "generated", "license", "readme")):
        return "boilerplate & mechanical"
    if any(token in lower for token in ("config", "route", "router", "workflow", "wiring", "manifest", ".yml", ".yaml", ".toml")):
        return "wiring & integration"
    return "core logic"


def _callouts(patch: str) -> tuple[str, ...]:
    lower = patch.lower()
    markers = {
        "security": "Security-sensitive change: inspect the trust boundary and error path.",
        "auth": "Authentication or authorization changed: verify denial behavior.",
        "migration": "Migration or schema change: check rollout and rollback assumptions.",
        "retry": "Retry or backoff logic changed: check duplicate effects and termination.",
        "concurr": "Concurrency-related change: inspect ordering and shared state.",
        "todo": "TODO/FIXME marker changed: confirm the follow-up is intentional.",
    }
    return tuple(message for marker, message in markers.items() if marker in lower)


def _parse_diff(text: str) -> tuple[_DiffFile, ...]:
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line.startswith("diff --git ")]
    if not starts:
        if any(line.startswith(("@@", "+", "-")) for line in lines):
            starts = [0]
        else:
            raise AdapterError("diff input has no reviewable hunks")
    files: list[_DiffFile] = []
    for offset, start in enumerate(starts):
        end = starts[offset + 1] if offset + 1 < len(starts) else len(lines)
        chunk = lines[start:end]
        path = next((_diff_file_header(line) for line in chunk if _diff_file_header(line)), None)
        if not path:
            path = "fixture.diff"
        additions = sum(1 for line in chunk if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in chunk if line.startswith("-") and not line.startswith("---"))
        status = "added" if additions and not deletions else "deleted" if deletions and not additions else "modified"
        patch = "\n".join(chunk).strip() + "\n"
        files.append(_DiffFile(path, status, additions, deletions, patch, _category(path, patch), _callouts(patch)))
    return tuple(files)


def _markdown_review(files: Sequence[_DiffFile]) -> str:
    additions = sum(item.additions for item in files)
    deletions = sum(item.deletions for item in files)
    lines = [
        "# PR review Canvas fallback",
        "",
        f"> {CANVAS_GAP}",
        "> Source is a bounded local diff fixture; PR metadata and `gh` access were not used.",
        "",
        f"**Stats:** {len(files)} files, +{additions}, -{deletions}",
        "",
        "## Table of contents",
        "",
    ]
    categories = ("core logic", "wiring & integration", "boilerplate & mechanical")
    for category in categories:
        selected = [item for item in files if item.category == category]
        if selected:
            lines.append(f"- [{category.title()}](#{_slug(category)})")
    for category in categories:
        selected = [item for item in files if item.category == category]
        if not selected:
            continue
        lines += ["", f"## {category.title()}", ""]
        for item in selected:
            lines += [f"### `{item.path}`", "", f"Status: {item.status}; +{item.additions}, -{item.deletions}", ""]
            for callout in item.callouts:
                lines += [f"> **Review attention:** {callout}", ""]
            lines += ["```diff", item.patch.rstrip(), "```", ""]
    return "\n".join(lines).rstrip() + "\n"


def render_pr_review_canvas(
    project_root: str | Path,
    diff_source: str | Path,
    *,
    output: str | Path = DEFAULT_REVIEW_OUTPUT,
    explicit: bool = True,
) -> dict[str, object]:
    """Render a bounded local unified diff into a linked review artifact.

    A GitHub URL is deliberately rejected: the pinned workflow's ``gh`` and
    live PR path are external capabilities that this fallback does not claim.
    """

    if not explicit:
        return _blocked_result("this held workflow is explicit-only")
    if isinstance(diff_source, str) and re.match(r"^https?://", diff_source):
        raise MissingCapability("live PR/gh input is unavailable; supply a project-local diff fixture")
    root = _project_root(project_root)
    diff_path = _resolve_input(root, diff_source, "diff input")
    text = _read_text(diff_path, MAX_DIFF_BYTES, "diff input")
    files = _parse_diff(text)
    output_dir = _safe_output(root, output)
    markdown = _markdown_review(files)
    artifacts = _write_artifacts(output_dir, markdown, "PR review Canvas fallback", root)
    return {
        "status": "FALLBACK",
        "source": "local-diff-fixture",
        "files": tuple(item.path for item in files),
        "categories": tuple(item.category for item in files),
        "artifacts": artifacts,
        "canvas_parity": "UNAVAILABLE",
        "parity_gap": CANVAS_GAP,
        "pr_metadata": "UNAVAILABLE",
        "external_writes": False,
        "product_configuration": False,
        "policy": "explicit-only; conditional local fallback",
    }


# Names that make the fallback easy to discover without coupling callers to
# the word "Canvas" as an implementation claim.
render_docs_artifact = render_docs_canvas
render_pr_review_artifact = render_pr_review_canvas


__all__ = [
    "AdapterError",
    "MissingCapability",
    "PermissionDenied",
    "render_docs_canvas",
    "render_docs_artifact",
    "render_pr_review_canvas",
    "render_pr_review_artifact",
]
