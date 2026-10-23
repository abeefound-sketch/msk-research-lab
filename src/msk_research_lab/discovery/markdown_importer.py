"""Local Markdown repository list importer with exact provenance tracking (DISC-01)."""

import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from pydantic import BaseModel, Field

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db
from msk_research_lab.repos.inspector import parse_canonical_github_url, MalformedUrlError

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MiB limit for 8 GiB RAM host
ALLOWED_EXTENSIONS = {".md", ".markdown"}

MD_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
PLAIN_GITHUB_URL_PATTERN = re.compile(r"(https?://github\.com/[a-zA-Z0-9_\-\./]+)")


class ImportSecurityError(Exception):
    """Raised when import violates file system or path security policies."""
    pass


class OccurrenceRecord(BaseModel):
    line_number: int
    raw_url: str
    canonical_url: str
    owner: str
    repo: str
    link_label: Optional[str] = None
    context_snippet: str


class MarkdownImportSummary(BaseModel):
    document_id: str
    file_path: str
    file_sha256: str
    line_count: int
    candidate_count: int
    occurrence_count: int
    new_candidates_registered: int
    skipped_invalid_urls: List[Dict[str, Any]] = Field(default_factory=list)


def get_default_allowlist_dir() -> Path:
    """Return default allowlisted directory for reference markdown lists."""
    cfg = get_config()
    ref_dir = cfg.storage.root_dir / "research" / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    return ref_dir.resolve()


def validate_import_path(file_path: Path, allowlist_dir: Optional[Path] = None) -> Path:
    """Verify that file path is safe, exists, and resides within allowlisted directory."""
    if allowlist_dir is None:
        allowlist_dir = get_default_allowlist_dir()
    else:
        allowlist_dir = allowlist_dir.resolve()

    resolved = file_path.resolve()

    # Path traversal and symlink escape check
    try:
        resolved.relative_to(allowlist_dir)
    except ValueError:
        raise ImportSecurityError(
            f"Import rejected: path {resolved} is outside allowlisted directory {allowlist_dir}"
        )

    if not resolved.exists():
        raise FileNotFoundError(f"Reference file does not exist: {resolved}")

    if not resolved.is_file():
        raise ImportSecurityError(f"Target is not a regular file: {resolved}")

    if resolved.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ImportSecurityError(
            f"Disallowed extension '{resolved.suffix}'. Only .md and .markdown allowed."
        )

    size = resolved.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        raise ImportSecurityError(
            f"File size ({size} bytes) exceeds safety limit of {MAX_FILE_SIZE_BYTES} bytes."
        )

    return resolved


def parse_markdown_occurrences(content: str) -> Tuple[List[OccurrenceRecord], List[Dict[str, Any]]]:
    """Parse links and URLs from markdown lines, skipping fenced code blocks."""
    lines = content.splitlines()
    in_code_block = False
    occurrences: List[OccurrenceRecord] = []
    skipped: List[Dict[str, Any]] = []

    for line_idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # Track fenced code blocks (``` or ~~~)
        if line.startswith("```") or line.startswith("~~~"):
            in_code_block = not in_code_block
            continue

        if in_code_block or not line:
            continue

        # 1. Parse markdown links [Label](URL)
        line_remaining = raw_line
        for match in MD_LINK_PATTERN.finditer(raw_line):
            label = match.group(1).strip()
            raw_url = match.group(2).strip()

            try:
                canonical, owner, repo = parse_canonical_github_url(raw_url)
                occurrences.append(OccurrenceRecord(
                    line_number=line_idx,
                    raw_url=raw_url,
                    canonical_url=canonical,
                    owner=owner,
                    repo=repo,
                    link_label=label,
                    context_snippet=line[:200]
                ))
            except MalformedUrlError as e:
                skipped.append({
                    "line_number": line_idx,
                    "raw_url": raw_url,
                    "reason": str(e)
                })

        # Blank out all markdown links from line_remaining so plain URL regex won't double-match
        line_remaining = MD_LINK_PATTERN.sub(" ", raw_line)

        # 2. Parse plain github URLs not captured in markdown links
        for match in PLAIN_GITHUB_URL_PATTERN.finditer(line_remaining):
            raw_url = match.group(1).strip()
            try:
                canonical, owner, repo = parse_canonical_github_url(raw_url)
                occurrences.append(OccurrenceRecord(
                    line_number=line_idx,
                    raw_url=raw_url,
                    canonical_url=canonical,
                    owner=owner,
                    repo=repo,
                    link_label=None,
                    context_snippet=line[:200]
                ))
            except MalformedUrlError as e:
                skipped.append({
                    "line_number": line_idx,
                    "raw_url": raw_url,
                    "reason": str(e)
                })

    return occurrences, skipped


def import_markdown_reference_list(
    file_path: Path,
    allowlist_dir: Optional[Path] = None,
    custom_db_path: Optional[Path] = None
) -> MarkdownImportSummary:
    """Import local Markdown file, extract GitHub repos, and record provenance in Tri-Ledger.

    Never clones, installs, or executes code.
    """
    safe_path = validate_import_path(file_path, allowlist_dir)

    raw_bytes = safe_path.read_bytes()
    file_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    content = raw_bytes.decode("utf-8", errors="replace")
    line_count = len(content.splitlines())

    doc_id = f"doc_{file_sha256[:16]}"
    occurrences, skipped = parse_markdown_occurrences(content)

    # Group occurrences by canonical repository
    candidates_map: Dict[str, Tuple[str, str, str]] = {}  # candidate_id -> (canonical_url, owner, repo)
    for occ in occurrences:
        cand_id = f"cand_{occ.owner.lower()}_{occ.repo.lower()}"
        if cand_id not in candidates_map:
            candidates_map[cand_id] = (occ.canonical_url, occ.owner, occ.repo)

    new_cands_count = 0

    with get_db(custom_db_path) as conn:
        # Clear older occurrences and reference_documents for this file upon re-import
        conn.execute(
            "DELETE FROM reference_occurrences WHERE document_id IN (SELECT id FROM reference_documents WHERE file_path = ?)",
            (str(safe_path),)
        )
        conn.execute("DELETE FROM reference_documents WHERE file_path = ?", (str(safe_path),))

        # Register reference_documents with current content hash
        conn.execute(
            """
            INSERT INTO reference_documents (id, file_path, file_sha256, line_count, candidate_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (doc_id, str(safe_path), file_sha256, line_count, len(candidates_map))
        )

        # Register candidate records deduplicated by canonical URL
        for cand_id, (canonical_url, owner, repo) in candidates_map.items():
            cur = conn.execute(
                "SELECT id FROM repository_candidates WHERE id = ? OR canonical_url = ?",
                (cand_id, canonical_url)
            )
            existing = cur.fetchone()
            if not existing:
                conn.execute(
                    """
                    INSERT INTO repository_candidates (
                        id, canonical_url, owner, repo, status, priority, discovery_source
                    ) VALUES (?, ?, ?, ?, 'DISCOVERED_UNVERIFIED', 'MEDIUM', 'MARKDOWN_IMPORT')
                    """,
                    (cand_id, canonical_url, owner, repo)
                )
                new_cands_count += 1

        # Register exact occurrences
        for occ in occurrences:
            cand_id = f"cand_{occ.owner.lower()}_{occ.repo.lower()}"
            conn.execute(
                """
                INSERT INTO reference_occurrences (
                    document_id, candidate_id, line_number, raw_url, link_label, context_snippet
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doc_id, cand_id, occ.line_number, occ.raw_url, occ.link_label, occ.context_snippet)
            )

        # Record audit event
        conn.execute(
            """
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                "MARKDOWN_LIST_IMPORTED",
                "OPERATOR",
                f'{{"doc_id": "{doc_id}", "candidates": {len(candidates_map)}, "occurrences": {len(occurrences)}, "new": {new_cands_count}}}'
            )
        )

    return MarkdownImportSummary(
        document_id=doc_id,
        file_path=str(safe_path),
        file_sha256=file_sha256,
        line_count=line_count,
        candidate_count=len(candidates_map),
        occurrence_count=len(occurrences),
        new_candidates_registered=new_cands_count,
        skipped_invalid_urls=skipped
    )
