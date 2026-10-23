"""Document parsers for PDF, EPUB, and DOCX formats with exact location indexing."""

import zipfile
import json
from pathlib import Path
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import pypdf
import docx
from msk_research_lab.core.db import get_db


def parse_and_index_document(doc_id: str, file_path: Path, file_type: str) -> List[Dict[str, Any]]:
    """Parse document into exact locators and update database + FTS5 index."""
    locations = []

    if file_type == "PDF":
        locations = _parse_pdf(doc_id, file_path)
    elif file_type == "EPUB":
        locations = _parse_epub(doc_id, file_path)
    elif file_type == "DOCX":
        locations = _parse_docx(doc_id, file_path)

    # Persist locations and index into FTS5
    with get_db() as conn:
        # Clear existing locations if re-indexing
        conn.execute("DELETE FROM document_locations WHERE document_id = ?;", (doc_id,))
        conn.execute("DELETE FROM fts_document_locations WHERE document_id = ?;", (doc_id,))

        for loc in locations:
            conn.execute(
                """
                INSERT INTO document_locations (
                    id, document_id, location_type, page_number, spine_href,
                    block_index, heading_path, normalized_region, text_content,
                    has_images, ocr_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    loc["id"],
                    doc_id,
                    loc["location_type"],
                    loc.get("page_number"),
                    loc.get("spine_href"),
                    loc.get("block_index"),
                    json.dumps(loc.get("heading_path", [])),
                    json.dumps(loc.get("normalized_region", [])),
                    loc.get("text_content", ""),
                    loc.get("has_images", 0),
                    loc.get("ocr_status", "NATIVE_TEXT")
                )
            )

            # Insert into FTS5 virtual table
            heading_str = " > ".join(loc.get("heading_path", []))
            conn.execute(
                """
                INSERT INTO fts_document_locations (document_id, location_id, heading, body)
                VALUES (?, ?, ?, ?);
                """,
                (doc_id, loc["id"], heading_str, loc.get("text_content", ""))
            )

        # Update page / section count on document record
        conn.execute(
            "UPDATE documents SET page_or_section_count = ? WHERE id = ?;",
            (len(locations), doc_id)
        )

    return locations


def _parse_pdf(doc_id: str, file_path: Path) -> List[Dict[str, Any]]:
    """Extract every PDF page with 1-based page numbers and image/scan flags."""
    reader = pypdf.PdfReader(str(file_path))
    results = []

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1  # Strictly 1-based page index
        text = page.extract_text() or ""
        has_images = 1 if len(page.images) > 0 else 0
        ocr_status = "NATIVE_TEXT"

        if not text.strip() and has_images:
            ocr_status = "SCANNED_IMAGE_PAGE"
        elif not text.strip():
            ocr_status = "EMPTY_OR_UNPARSED"

        loc_id = f"loc:{doc_id}:p{page_num}"
        results.append({
            "id": loc_id,
            "location_type": "PDF_PAGE",
            "page_number": page_num,
            "heading_path": [f"Page {page_num}"],
            "text_content": text.strip(),
            "has_images": has_images,
            "ocr_status": ocr_status,
            "normalized_region": [0.0, 0.0, 1.0, 1.0]
        })

    return results


def _parse_epub(doc_id: str, file_path: Path) -> List[Dict[str, Any]]:
    """Extract EPUB chapters based on spine and XHTML structure."""
    results = []
    with zipfile.ZipFile(file_path, "r") as zf:
        # Locate all html/xhtml content documents
        content_files = [f for f in zf.namelist() if f.lower().endswith((".xhtml", ".html", ".htm"))]
        content_files.sort()

        for idx, filename in enumerate(content_files):
            try:
                raw_html = zf.read(filename).decode("utf-8", errors="ignore")
                soup = BeautifulSoup(raw_html, "html.parser")
                # Clean scripts and styles
                for s in soup(["script", "style"]):
                    s.decompose()

                title_tag = soup.find(["h1", "h2", "title"])
                chapter_title = title_tag.get_text().strip() if title_tag else f"Section {idx + 1}"
                text = soup.get_text(separator="\n").strip()
                has_images = 1 if soup.find("img") else 0

                loc_id = f"loc:{doc_id}:s{idx + 1}"
                results.append({
                    "id": loc_id,
                    "location_type": "EPUB_CHAPTER",
                    "block_index": idx + 1,
                    "spine_href": filename,
                    "heading_path": [chapter_title],
                    "text_content": text,
                    "has_images": has_images,
                    "ocr_status": "NATIVE_HTML"
                })
            except Exception:
                pass

    return results


def _parse_docx(doc_id: str, file_path: Path) -> List[Dict[str, Any]]:
    """Extract DOCX paragraphs, headings, and table sections with structural hierarchy."""
    doc = docx.Document(str(file_path))
    results = []
    current_headings = []
    block_idx = 0

    for p in doc.paragraphs:
        block_idx += 1
        text = p.text.strip()
        if not text:
            continue

        if p.style.name.startswith("Heading"):
            current_headings = [text]

        loc_id = f"loc:{doc_id}:b{block_idx}"
        results.append({
            "id": loc_id,
            "location_type": "DOCX_PARAGRAPH",
            "block_index": block_idx,
            "heading_path": list(current_headings),
            "text_content": text,
            "has_images": 0,
            "ocr_status": "NATIVE_TEXT"
        })

    # Also extract tables
    for table in doc.tables:
        block_idx += 1
        table_rows = []
        for row in table.rows:
            table_rows.append(" | ".join([cell.text.strip() for cell in row.cells]))
        table_text = "\n".join(table_rows)

        loc_id = f"loc:{doc_id}:t{block_idx}"
        results.append({
            "id": loc_id,
            "location_type": "DOCX_TABLE",
            "block_index": block_idx,
            "heading_path": list(current_headings) + ["Table"],
            "text_content": table_text,
            "has_images": 0,
            "ocr_status": "NATIVE_TEXT"
        })

    return results
