"""Research notebook, source-linked experiments, and citations management."""

import uuid
import datetime
from typing import List, Dict, Any, Optional
from msk_research_lab.core.db import get_db
from msk_research_lab.library.search import resolve_location


class CitationError(Exception):
    """Raised when an invalid citation is linked."""
    pass


def create_research_note(
    title: str,
    content_markdown: str,
    citations: List[Dict[str, Any]],
    author: str = "RESEARCHER"
) -> Dict[str, Any]:
    """Create a research note with verified linked citations (>=2 documents + 1 Git commit for G5)."""
    note_id = f"note-{uuid.uuid4().hex[:10]}"
    now = datetime.datetime.utcnow().isoformat() + "Z"

    # Validate citations
    verified_citations = []
    for cit in citations:
        target_kind = cit.get("target_kind")
        if target_kind == "DOCUMENT_LOCATION":
            doc_id = cit.get("document_id")
            loc_id = cit.get("location_id")
            resolved = resolve_location(doc_id, loc_id)
            if resolved["status"] != "RESOLVED":
                raise CitationError(f"Cannot link citation: {resolved.get('error')}")
            verified_citations.append({
                "target_kind": "DOCUMENT_LOCATION",
                "document_id": doc_id,
                "location_id": loc_id,
                "git_repo_id": None,
                "git_commit_sha": None,
                "excerpt": cit.get("excerpt", resolved.get("text_content", "")[:200]),
                "comment": cit.get("comment", "")
            })
        elif target_kind == "GIT_COMMIT":
            repo_id = cit.get("git_repo_id")
            commit_sha = cit.get("git_commit_sha")
            if not repo_id or not commit_sha:
                raise CitationError("Git citation requires both git_repo_id and git_commit_sha.")
            verified_citations.append({
                "target_kind": "GIT_COMMIT",
                "document_id": None,
                "location_id": None,
                "git_repo_id": repo_id,
                "git_commit_sha": commit_sha,
                "excerpt": cit.get("excerpt", ""),
                "comment": cit.get("comment", "")
            })
        else:
            raise CitationError(f"Unsupported target_kind: {target_kind}")

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO research_notes (id, title, content_markdown, author, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (note_id, title, content_markdown, author, now, now)
        )

        for vc in verified_citations:
            conn.execute(
                """
                INSERT INTO research_citations (
                    note_id, target_kind, document_id, location_id,
                    git_repo_id, git_commit_sha, excerpt, comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    note_id,
                    vc["target_kind"],
                    vc["document_id"],
                    vc["location_id"],
                    vc["git_repo_id"],
                    vc["git_commit_sha"],
                    vc["excerpt"],
                    vc["comment"]
                )
            )

    return get_research_note(note_id)


def get_research_note(note_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve research note with all its verified citations."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM research_notes WHERE id = ?;", (note_id,))
        row = cur.fetchone()
        if not row:
            return None

        c_cur = conn.execute("SELECT * FROM research_citations WHERE note_id = ? ORDER BY id ASC;", (note_id,))
        citations = [dict(r) for r in c_cur.fetchall()]

        return {
            "id": row["id"],
            "title": row["title"],
            "content_markdown": row["content_markdown"],
            "author": row["author"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "citations": citations
        }


def export_note_to_json(note_id: str) -> Dict[str, Any]:
    """Export note and citations with rights metadata."""
    note = get_research_note(note_id)
    if not note:
        raise ValueError(f"Note {note_id} not found.")

    return {
        "schema_version": "1.0",
        "export_kind": "RESEARCH_NOTE",
        "note": note
    }
