"""Project-local fallbacks for the two held Cursor Canvas mirrors.

The pinned skills describe a Cursor Canvas SDK that is not available in the
current Codex host.  These adapters keep the workflows useful by producing a
small, linked Markdown/HTML review artifact under an explicitly supplied
project root.  They never read the user's Cursor home, invoke ``gh``, access a
network, install anything, or claim Canvas SDK parity.
"""

from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import quote, urlsplit


MAX_DOCUMENTS = 32
MAX_DOCUMENT_BYTES = 256_000
MAX_DIFF_BYTES = 512_000
MAX_TRANSCRIPT_BYTES = 512_000
MAX_TRANSCRIPT_RECORDS = 256
MAX_PREFERENCE_ATOMS = 64
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
    headings: tuple[tuple[int, str], ...]


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


_PREFERENCE_MARKER = re.compile(
    r"\b(?:i\s+(?:prefer|want|need)|always|never|please|do\s+not|don't|stop|keep|require|avoid|preserve|make\s+sure)\b",
    re.IGNORECASE,
)
_SECRET_VALUE = re.compile(
    r"(?i)\b(api[_ -]?key|access[_ -]?token|auth(?:orization)?|bearer|password|passwd|secret|token)\b\s*[:=]\s*[^\s,;]+"
)
_TOKEN_VALUE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,})\b")
_PRIVATE_PATH = re.compile(r"(?:(?:/Users|/private|/Volumes)/[^\s)`\]>,;]+|~/(?:[^\s)`\]>,;]+))")
_PRIVATE_CONTACT = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")


def _redact_preference_text(value: str) -> str:
    """Keep preference evidence useful without copying private transcript text."""

    redacted = _SECRET_VALUE.sub(lambda match: f"{match.group(1)}: <redacted>", value)
    redacted = _TOKEN_VALUE.sub("<redacted>", redacted)
    redacted = _PRIVATE_PATH.sub("<path>", redacted)
    redacted = _PRIVATE_CONTACT.sub("<private-contact>", redacted)
    redacted = re.sub(r"\s+", " ", redacted).strip()
    if any(ord(char) < 32 for char in redacted):
        raise AdapterError("transcript evidence contains control characters")
    return redacted


def _transcript_message(record: Mapping[str, Any]) -> str:
    """Extract text from common JSONL message shapes without accepting paths."""

    value: Any = record.get("text", record.get("content", record.get("message", "")))
    if isinstance(value, Mapping):
        value = value.get("text", value.get("content", ""))
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, Mapping) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        value = "\n".join(parts)
    if not isinstance(value, str):
        raise AdapterError("transcript record text must be text or content blocks")
    return value


def _transcript_timestamp(record: Mapping[str, Any]) -> datetime:
    value = record.get("timestamp", record.get("created_at"))
    if not isinstance(value, str) or not value.strip():
        raise AdapterError("transcript records need an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdapterError("transcript timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise AdapterError("transcript timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _load_scoped_transcript(
    root: Path,
    source: str | Path,
    parent_thread_id: str,
    *,
    window_days: int,
    now: datetime,
) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    if not isinstance(parent_thread_id, str) or not parent_thread_id.strip():
        raise AdapterError("parent_thread_id must be a non-empty identifier")
    _validate_limit(window_days, "window_days", 30)
    source_path = _resolve_input(root, source, "transcript input")
    text = _read_text(source_path, MAX_TRANSCRIPT_BYTES, "transcript input")
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if len(records) >= MAX_TRANSCRIPT_RECORDS:
            raise AdapterError("transcript input exceeds the bounded record limit")
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AdapterError(f"transcript record {line_number} is not valid JSON") from exc
        if not isinstance(record, dict):
            raise AdapterError(f"transcript record {line_number} must be an object")
        thread_id = record.get("thread_id")
        child_parent = record.get("parent_thread_id")
        if thread_id == parent_thread_id:
            scope = "parent"
        elif child_parent == parent_thread_id and thread_id and thread_id != parent_thread_id:
            scope = "subagent"
        else:
            continue
        timestamp = _transcript_timestamp(record)
        if not (now - timedelta(days=window_days) <= timestamp <= now):
            continue
        message = _transcript_message(record)
        if not message.strip():
            continue
        records.append({
            "scope": scope,
            "role": record.get("role", "unknown"),
            "timestamp": timestamp,
            "message": message,
        })
    if not records:
        return (), ()
    dates = tuple(sorted({item["timestamp"].date().isoformat() for item in records}))
    return tuple(records), dates


def _preference_atoms(records: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    evidence: dict[str, dict[str, Any]] = {}
    for record in records:
        scope = str(record["scope"])
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", str(record["message"])):
            if not _PREFERENCE_MARKER.search(sentence):
                continue
            atom = _redact_preference_text(sentence)
            if not atom:
                continue
            if len(atom) > 180:
                atom = atom[:177].rstrip() + "..."
            key = re.sub(r"\s+(?:with\s+)?(?:api[_ -]?key|access[_ -]?token|authorization|bearer|password|passwd|secret|token):\s*<redacted>", "", atom.casefold())
            key = re.sub(r"\s+", " ", key).strip().rstrip(".!?")
            entry = evidence.setdefault(key, {"text": atom, "parent": 0, "subagent": 0})
            entry[scope] += 1
    atoms: list[dict[str, Any]] = []
    for entry in evidence.values():
        parent_count = int(entry["parent"])
        subagent_count = int(entry["subagent"])
        total = parent_count + subagent_count
        if parent_count >= 2:
            confidence = "strong"
        elif parent_count and subagent_count:
            confidence = "medium"
        else:
            confidence = "weak"
        atoms.append({
            "text": entry["text"],
            "confidence": confidence,
            "parent_evidence": parent_count,
            "subagent_evidence": subagent_count,
            "evidence_count": total,
        })
    atoms.sort(key=lambda item: (-item["evidence_count"], item["text"].casefold()))
    if len(atoms) > MAX_PREFERENCE_ATOMS:
        raise AdapterError("transcript input produces too many preference atoms")
    return tuple(atoms)


def _heading_lines(text: str) -> tuple[tuple[int, str], ...]:
    return tuple(
        (len(match.group(1)), match.group(2).strip())
        for line in text.splitlines()
        if (match := re.match(r"^(#{1,6})\s+(.+?)\s*$", line))
    )


def _slug(value: str, fallback: str = "section") -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result or fallback


def _unique_slug(value: str, used: set[str], fallback: str = "section") -> str:
    base = _slug(value, fallback)
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


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


def _safe_href(raw: str) -> str | None:
    candidate = html.unescape(raw).strip()
    parsed = urlsplit(candidate)
    if parsed.scheme.lower() not in {"", "http", "https", "mailto"}:
        return None
    if any(ord(char) < 0x20 or ord(char) == 0x7F or char == "\\" for char in candidate):
        return None
    if not parsed.scheme and (parsed.netloc or candidate.startswith("//")):
        return None
    if not parsed.scheme and ":" in candidate.split("/", 1)[0]:
        return None
    return candidate


def _document_sections(document: _Document, index: int) -> tuple[tuple[int, str, str], ...]:
    """Return stable, document-scoped heading anchors for a generated page."""

    used: set[str] = set()
    title = document.headings[0][1] if document.headings else Path(document.relative).stem
    sections: list[tuple[int, str, str]] = [(2, title, f"doc-{index}-{_unique_slug(title, used)}")]
    for source_level, heading in document.headings[1:]:
        sections.append((min(source_level + 1, 6), heading, f"doc-{index}-{_unique_slug(heading, used)}"))
    return tuple(sections)


def _rebase_document_links(
    line: str, document: _Document, artifact_dir: Path, root: Path, sections: Sequence[tuple[int, str, str]]
) -> str:
    """Rebase relative source links to the generated artifact directory."""

    fragment_map = {_slug(heading): anchor for _, heading, anchor in sections}

    def rebase(match: re.Match[str]) -> str:
        raw = html.unescape(match.group(2)).strip()
        if _safe_href(raw) is None:
            return match.group(1)
        parsed = urlsplit(raw)
        if parsed.scheme or parsed.netloc or raw.startswith("//"):
            return match.group(0)
        if not parsed.path:
            fragment = parsed.fragment
            anchor = fragment_map.get(_slug(fragment), fragment)
            return f"[{match.group(1)}](#{anchor})"
        candidate = Path(os.path.abspath(document.path.parent / parsed.path))
        _inside_root(root, candidate, "documentation cross-reference")
        if candidate.is_symlink():
            raise AdapterError("documentation cross-reference must not be a symlink")
        if candidate.exists() and not candidate.is_file():
            raise AdapterError("documentation cross-reference must target a regular file")
        target = _relative_link(artifact_dir, candidate)
        if parsed.query:
            target += "?" + parsed.query
        if parsed.fragment:
            target += "#" + parsed.fragment
        return f"[{match.group(1)}]({target})"

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", rebase, line)


def _rewrite_document_headings(
    document: _Document, index: int, artifact_dir: Path, root: Path
) -> str:
    """Nest source headings below the generated document heading with unique IDs."""

    sections = _document_sections(document, index)
    title = sections[0][1]
    section_index = 1
    output: list[str] = []
    for line in document.text.rstrip().splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not match:
            output.append(line)
            continue
        heading = match.group(2).strip()
        if section_index == 1 and heading == title:
            continue
        if section_index >= len(sections):
            # A malformed or unusual source heading still receives a stable
            # anchor rather than colliding with another document.
            used = {item[2].removeprefix(f"doc-{index}-") for item in sections}
            anchor = f"doc-{index}-{_unique_slug(heading, used)}"
            level = min(len(match.group(1)) + 1, 6)
        else:
            level, expected, anchor = sections[section_index]
            if expected != heading:
                used = {item[2].removeprefix(f"doc-{index}-") for item in sections}
                anchor = f"doc-{index}-{_unique_slug(heading, used)}"
                level = min(len(match.group(1)) + 1, 6)
            section_index += 1
        output.append(f"{'#' * level} {heading} {{#{anchor}}}")
    return "\n".join(_rebase_document_links(line, document, artifact_dir, root, sections) for line in output)


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
        sections = _document_sections(document, index)
        lines.append(f"- [{sections[0][1]}](#{sections[0][2]})")
        for _, heading, anchor in sections[1:]:
            lines.append(f"  - [{heading}](#{anchor})")
    lines += ["", "## References", "", "This artifact links back to the bounded source files.", ""]
    for index, document in enumerate(documents, 1):
        sections = _document_sections(document, index)
        title, anchor = sections[0][1], sections[0][2]
        link = _relative_link(artifact_dir, root / document.relative)
        lines += [f"## {title} {{#{anchor}}}", "", f"Source: [{document.relative}]({link})", ""]
        if document.headings:
            lines.append("Sections: " + ", ".join(f"[{heading}](#{section_anchor})" for _, heading, section_anchor in sections[1:]))
            lines.append("")
        lines.append(_rewrite_document_headings(document, index, artifact_dir, root))
        lines.append("")
    markdown = "\n".join(lines).rstrip() + "\n"
    return re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: match.group(0) if _safe_href(match.group(2)) is not None else match.group(1),
        markdown,
    )


def _inline_markdown(value: str) -> str:
    escaped = html.escape(value, quote=True)
    replacements: dict[str, str] = {}

    def hold(value: str) -> str:
        token = f"\x00{len(replacements)}\x00"
        replacements[token] = value
        return token

    # Code spans are protected before emphasis/link markup is expanded.
    escaped = re.sub(
        r"`([^`]+)`",
        lambda match: hold(f"<code>{match.group(1)}</code>"),
        escaped,
    )

    def link(match: re.Match[str]) -> str:
        href = _safe_href(match.group(2))
        label = match.group(1)
        if href is None:
            return label
        return hold(f'<a href="{html.escape(href, quote=True)}">{label}</a>')

    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*|__([^_]+)__", lambda match: f"<strong>{match.group(1) or match.group(2)}</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)", lambda match: f"<em>{match.group(1) or match.group(2)}</em>", escaped)
    for token, replacement in replacements.items():
        escaped = escaped.replace(token, replacement)
    return escaped


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
        elif re.match(r"^\s*-\s+", line):
            flush_paragraph()
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{_inline_markdown(re.sub(r'^\s*-\s+', '', line))}</li>")
        else:
            close_list()
            paragraph.append(line.strip())
    flush_paragraph()
    close_list()
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>{html.escape(title)}</title>"
        "<style>body{font:16px system-ui;line-height:1.55;max-width:72ch;margin:2rem auto;padding:0 1rem;color:#18212b}"
        "h1,h2,h3,h4,h5,h6{line-height:1.2;margin:1.7em 0 .55em}h1{font-size:2.1rem;letter-spacing:-.025em}"
        "h2{font-size:1.45rem}h3{font-size:1.15rem}code{background:#eef2f7;padding:.08em .28em;border-radius:3px}"
        "pre{background:#f3f5f7;padding:1rem;overflow:auto;tab-size:2}a{color:#075985;text-underline-offset:3px}"
        "blockquote{border-left:1px solid #94a3b8;padding-left:1rem;color:#475569}.meta{background:#fff7ed;border:1px solid #fdba74;padding:.8rem}"
        "@media(max-width:640px){body{font-size:15px;margin:1rem auto;padding:0 .75rem}h1{font-size:1.7rem}h2{font-size:1.3rem}h3{font-size:1.05rem;overflow-wrap:anywhere}"
        "pre{font-size:.78rem;line-height:1.45;padding:.7rem;white-space:pre-wrap;overflow-wrap:anywhere}ul{padding-left:1.25rem}blockquote{margin-left:.35rem}}"
        "</style></head><body><main>"
        + "".join(body)
        + "</main></body></html>\n"
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


def _changed_lines(patch: str) -> tuple[tuple[int | None, str], ...]:
    """Return added/deleted lines with their hunk-local source line numbers."""

    old_line: int | None = None
    new_line: int | None = None
    changed: list[tuple[int | None, str]] = []
    for line in patch.splitlines():
        hunk = re.match(r"^@@ -(?P<old>\d+)(?:,\d+)? \+(?P<new>\d+)(?:,\d+)? @@", line)
        if hunk:
            old_line = int(hunk.group("old"))
            new_line = int(hunk.group("new"))
        elif line.startswith(("+++", "---")):
            continue
        elif line.startswith("+"):
            changed.append((new_line, line[1:]))
            if new_line is not None:
                new_line += 1
        elif line.startswith("-"):
            changed.append((old_line, line[1:]))
            if old_line is not None:
                old_line += 1
        elif old_line is not None and new_line is not None:
            old_line += 1
            new_line += 1
    return tuple(changed)


def _callouts(patch: str) -> tuple[str, ...]:
    changed = _changed_lines(patch)
    markers = {
        "security": "Security-sensitive change: inspect the trust boundary and error path.",
        "auth": "Authentication or authorization changed: verify denial behavior.",
        "migration": "Migration or schema change: check rollout and rollback assumptions.",
        "retry": "Retry or backoff logic changed: check duplicate effects and termination.",
        "concurr": "Concurrency-related change: inspect ordering and shared state.",
        "todo": "TODO/FIXME marker was added or removed: confirm the follow-up is intentional.",
    }
    callouts: list[str] = []
    for marker, message in markers.items():
        evidence = next(
            ((line_number, line) for line_number, line in changed if marker in line.lower()),
            None,
        )
        # TODO/FIXME is only an attention item when the marker itself changed;
        # a mention in surrounding context is not evidence of a new task.
        if marker == "todo":
            evidence = next(
                ((line_number, line) for line_number, line in changed if re.search(r"\b(?:TODO|FIXME)\b", line, re.I)),
                None,
            )
        if evidence is None:
            continue
        line_number, line = evidence
        line = re.sub(r"\s+", " ", line).strip().replace("`", "'")
        if len(line) > 120:
            line = line[:117] + "..."
        location = f"line {line_number}" if line_number is not None else "changed line"
        callouts.append(f"{location} evidence `{line}` — {message}")
    return tuple(callouts)


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
            if category == "boilerplate & mechanical":
                lines.append("Mechanical change summarized; inspect the source file for the generated or formatting details.")
            else:
                lines += ["```diff", item.patch.rstrip(), "```"]
            lines.append("")
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


def _validate_thread_identifier(value: str, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value) is None:
        raise AdapterError(f"{label} must be a bounded identifier without path separators")
    return value


def _workflow_markdown(
    parent_thread_id: str,
    records: Sequence[Mapping[str, Any]],
    dates: Sequence[str],
    atoms: Sequence[Mapping[str, Any]],
    window_days: int,
) -> str:
    parent_count = sum(1 for record in records if record["scope"] == "parent")
    subagent_count = sum(1 for record in records if record["scope"] == "subagent")
    lines = [
        "# Workflow from chats proposal",
        "",
        "> This is a redacted, project-local proposal from an explicitly supplied transcript export.",
        "> It does not write a skill, rule, memory, or global setting and does not claim native history access.",
        "",
        "## Evidence scope",
        "",
        f"- Parent record: `{parent_thread_id}`",
        f"- Window: last `{window_days}` days; observed dates: `{', '.join(dates)}`",
        f"- Records: `{parent_count}` parent, `{subagent_count}` subagent evidence",
        "- Subagent text contributes evidence only; citations identify the parent record.",
        "- Transcript paths, credentials, contacts, and raw chat excerpts are omitted or redacted.",
        "",
        "## Preference profile",
        "",
    ]
    if not atoms:
        lines.append("No preference atom met the extraction markers in the selected window.")
    else:
        for atom in atoms:
            text = str(atom["text"]).replace("`", "'").replace("[", "(").replace("]", ")")
            lines.append(
                f"- **{atom['confidence']}** {text} "
                f"(parent evidence: {atom['parent_evidence']}; subagent evidence: {atom['subagent_evidence']})"
            )
    lines += [
        "",
        "## Proposed artifact",
        "",
        "Draft one project-local skill, rule, or workflow document only after the operator reviews the profile.",
        "The proposal is traceable to the parent record above; no automatic writeback is performed.",
        "",
        "## Current gaps",
        "",
        "- Native scoped task-history acquisition is unavailable in this session; the export was supplied explicitly.",
        "- Automatic skill selection, durable artifact approval, and global writeback remain unproven.",
        "",
    ]
    return "\n".join(lines)


def extract_workflow_from_chats(
    project_root: str | Path,
    transcript_source: str | Path | None,
    *,
    parent_thread_id: str,
    output: str | Path = ".artifacts/cursor-workflow-from-chats",
    window_days: int = 7,
    now: datetime | None = None,
    explicit: bool = True,
) -> dict[str, object]:
    """Extract redacted preference atoms from one explicitly scoped JSONL export.

    The native Codex history reader is not assumed. A supplied local export is
    accepted only inside the selected project root; the result is a proposal
    artifact and never a durable skill or global preference write.
    """

    if not explicit:
        return _blocked_result("this held workflow is explicit-only")
    parent_thread_id = _validate_thread_identifier(parent_thread_id, "parent_thread_id")
    if transcript_source is None:
        return {
            "status": "PARTIAL",
            "reason": "native scoped task-history reader is unavailable; supply one exact local export",
            "history_capability": "UNAVAILABLE",
            "writes_performed": False,
            "external_writes": False,
        }
    if isinstance(transcript_source, str) and re.match(r"^https?://", transcript_source):
        return {
            "status": "PARTIAL",
            "reason": "remote transcript acquisition is unavailable; supply a project-local export",
            "history_capability": "UNAVAILABLE",
            "writes_performed": False,
            "external_writes": False,
        }
    root = _project_root(project_root)
    records, dates = _load_scoped_transcript(
        root,
        transcript_source,
        parent_thread_id,
        window_days=window_days,
        now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc),
    )
    if not records:
        return {
            "status": "PARTIAL",
            "reason": "no matching parent or child records in the bounded window",
            "history_capability": "SUPPLIED_EXPORT_ONLY",
            "writes_performed": False,
            "external_writes": False,
        }
    atoms = _preference_atoms(records)
    output_dir = _safe_output(root, output)
    output_dir.mkdir(parents=True, exist_ok=True)
    _reject_symlink_components(root, output_dir.relative_to(root))
    proposal_path = output_dir / "proposal.md"
    receipt_path = output_dir / "receipt.json"
    for path in (proposal_path, receipt_path):
        _reject_symlink_components(root, path.relative_to(root))
        if path.exists() and not path.is_file():
            raise AdapterError("workflow proposal target must be a regular file")
    proposal_path.write_text(
        _workflow_markdown(parent_thread_id, records, dates, atoms, window_days),
        encoding="utf-8",
    )
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "parent_thread_id": parent_thread_id,
                "window_days": window_days,
                "observed_dates": list(dates),
                "parent_records": sum(1 for record in records if record["scope"] == "parent"),
                "subagent_records": sum(1 for record in records if record["scope"] == "subagent"),
                "atoms": list(atoms),
                "history_capability": "SUPPLIED_EXPORT_ONLY",
                "artifact_writes_performed": True,
                "durable_writeback_performed": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "status": "ADAPTED_PROPOSAL",
        "history_capability": "SUPPLIED_EXPORT_ONLY",
        "parent_thread_id": parent_thread_id,
        "records": len(records),
        "preference_atoms": len(atoms),
        "artifacts": {"proposal": str(proposal_path), "receipt": str(receipt_path)},
        "artifact_writes_performed": True,
        "durable_writeback_performed": False,
        "external_writes": False,
        "policy": "explicit-only; redacted proposal; no durable writeback",
    }


# Names that make the fallback easy to discover without coupling callers to
# the word "Canvas" as an implementation claim.
render_docs_artifact = render_docs_canvas
render_pr_review_artifact = render_pr_review_canvas
workflow_from_chats = extract_workflow_from_chats


__all__ = [
    "AdapterError",
    "MissingCapability",
    "PermissionDenied",
    "render_docs_canvas",
    "render_docs_artifact",
    "render_pr_review_canvas",
    "render_pr_review_artifact",
    "extract_workflow_from_chats",
    "workflow_from_chats",
]
