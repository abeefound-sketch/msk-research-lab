# [R2] Milestone Validation Report

**Project:** MSK Research Lab OS v3.0  
**Release:** R2 — Evidence-Complete Library, Notebook, and Disaster Recovery  
**State:** PASS (All G3, G4, G5, G6 acceptance gates verified with real evidence and SHA-256 manifests)  
**Execution timestamp / timezone:** 2026-10-23T07:30:00+07:00 (UTC+7)  
**Lab repo path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`)  
**Target display resolution:** 1366x768 (Windows Browser)  
**Database:** SQLite 3.37.2 (WAL Mode = True, Foreign Keys = True, Migrations = v3)  

---

## 1. Scope and Actual Changed Files

### Planned work packages:
- **R2-01:** Content-addressed immutable original document store (`2data/originals/<sha256>/<filename>`), format sniffing (PDF, EPUB, DOCX), size limit defense, duplicate handling.
- **R2-02:** PDF extraction for native text and scanned pages; 1-based page indexing; normalized region locators.
- **R2-03:** Visual gap accounting; image and scanned page status tracking (`SCANNED_IMAGE_PAGE` vs `NATIVE_TEXT`).
- **R2-04:** EPUB chapter extraction via spine and safe HTML parsing; DOCX structural paragraph, heading, and table section extraction.
- **R2-05:** SQLite FTS5 search index across all formats with snippet highlighting and click-to-original resolution (`resolve_location`).
- **R2-06:** Research notes with linked citations (&ge;2 document references + 1 Git commit SHA); rights-filtered export to JSON/MD.
- **R2-07:** Authenticated research-note read API (`/api/v1/research/notes/{id}`); prepublication point knowledge endpoint (`/api/v1/knowledge/points/{code}`) returns 404 `UNREVIEWED_NOT_PUBLISHED` as required.
- **R2-08:** Consistent disaster recovery engine: VACUUM INTO backup of SQLite + originals to `.tar.gz`; restore to fresh directory; SHA-256 verification and FTS5 search functionality test.

### Files added / updated:
- `src/msk_research_lab/core/migrations.py`: Added Migration 0003 for `documents`, `document_locations`, `fts_document_locations`, `research_notes`, and `research_citations`.
- `src/msk_research_lab/library/store.py`: Ingestion, format sniffing, immutable byte storage.
- `src/msk_research_lab/library/parsers.py`: PDF, EPUB, and DOCX parsers with location extraction.
- `src/msk_research_lab/library/search.py`: FTS5 full-text search and citation location resolver.
- `src/msk_research_lab/research/notes.py`: Research notebook, citation linkage, JSON/MD export.
- `src/msk_research_lab/core/backup.py`: Disaster recovery backup and restore with manifest verification.
- `src/msk_research_lab/api/app.py`: Integrated R2 library and notes API endpoints.
- `tests/fixtures/synthetic_docs.py`: Deterministic generator for 10 acceptance fixtures (4 PDF, 3 EPUB, 3 DOCX).
- `tests/unit/`: `test_library_store.py`, `test_parsers.py`, `test_library_search.py`, `test_notes_citations.py`, `test_backup_restore.py`.
- `tests/integration/test_library_api.py`: Endpoint contract and auth tests.
- `2data/evidence/R2/run_r2_library_recovery_001/`: Sealed evidence bundle with SHA-256 manifest.

---

## 2. Ingested Acceptance Corpus (10 Documents)

| Document Filename | Format | SHA-256 (64 hex) | Pages/Sections | OCR / Content Status |
|---|---|---|---|---|
| `anatomy_guide_native.pdf` | PDF | `57530691500d0408d6c70b80ba9ec36465492d33458c358ff38848a60a7d5cb1` | 2 pages | Native PDF Text |
| `meridian_points_reference.pdf` | PDF | `ec56f3f3e2ec6e35cbaf3ff035e07a0166297ce1d5c22ee3a22be9b4f9f740eb` | 3 pages | Native PDF Text |
| `scanned_atlas_plates.pdf` | PDF | `8b0e77d01859942a7813a36db8a230514101e14934d4dd8899806497f1f0a200` | 1 page | Scanned Image Page |
| `scanned_historical_manuscript.pdf` | PDF | `88c2f1f01c2ec7175ce08272fefee58fbead94dfb5dbd094364407b1d9bf1d09` | 2 pages | Scanned Image Page |
| `clinical_study_vol1.epub` | EPUB | `8fef8eb025c862fc81ec451b6a7a7b82424cf3832c3f15d8f615594bb800eb75` | 1 chapter | Native HTML / Trapezius & GB21 |
| `clinical_study_vol2.epub` | EPUB | `414704e63084ee99c6fece940827435f29910d68f6ebc93a0b80a969f6e625be` | 1 chapter | Native HTML / Trapezius & GB21 |
| `clinical_study_vol3.epub` | EPUB | `299351e3c830eb847d25e0a6d0c4eb57a3e6f987dbe63737ec38c4c68832a5bf` | 1 chapter | Native HTML / Trapezius & GB21 |
| `research_monograph_part1.docx` | DOCX | `0dc25e36e651e7a6358ff21295b214ea02213df944b25f16fe775034c56ee937` | 3 blocks | Headings, Paragraphs & Table |
| `research_monograph_part2.docx` | DOCX | `184249a5b4f6e3c3b036577ba5bb6e1a7ba964c703112e75e11a2f0c74f56860` | 3 blocks | Headings, Paragraphs & Table |
| `research_monograph_part3.docx` | DOCX | `f287e0ce38d01b1cb91ee643a6ec040f757f4951fc239c0d486d302a50a1df27` | 3 blocks | Headings, Paragraphs & Table |

---

## 3. Gate-by-Gate Acceptance Results

| Gate ID | Requirement | Result | Evidence / Notes |
|---|---|---|---|
| **G3** | Ingest 10 originals (4 PDF with &ge;2 scans, 3 EPUB, 3 DOCX); exact hashes; page accounting | **PASS** | 10/10 documents ingested with immutable SHA-256 addresses; verified in `ingested_documents_manifest.json`. |
| **G4** | Exact source search opens correct original PDF page / EPUB spine-href / DOCX block | **PASS** | FTS5 queries for `Trapezius` and `scapula` return exact spine and paragraph locators; `resolve_location` verifies disk bytes before serving. |
| **G5** | Source-linked note with &ge;2 book refs + 1 Git SHA; authenticated read-only API; prepublication point returns 404 | **PASS** | Research note created with citations across EPUB, DOCX, and Git commit; bearer auth enforced; `/api/v1/knowledge/points/{code}` returns 404. |
| **G6** | Consistent backup of SQLite + originals; restore to fresh directory; hash verification & search test | **PASS** | Complete backup archive generated in `2data/exports/`; restored to fresh directory; 100% SHA-256 match; SQLite integrity OK; FTS5 search functional. |

---

## 4. Automated Test Battery

- **Test execution command:** `PYTHONPATH=src:. .venv/bin/pytest -v`
- **Result:** **41 passed, 0 failed** in 10.96 seconds.
- **Coverage:** R0 (G1, SEC), R1 (URL normalizer, rights matrix, cloner guard, surface registration v1 SR-01..10), R2 (G3, G4, G5, G6).

---

## 5. Tamper Detection & Manifest Sealing

- **Evidence bundle directory:** [`2data/evidence/R2/run_r2_library_recovery_001/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R2/run_r2_library_recovery_001)
- **Manifest Hash:** `6c6e9225c8b4d8e9af6ed9460d492ce407314b97678aac7ffafaac5311f36b7d`
- **Tamper verification:** `PASS` (`{"valid": true, "total_files": 4, "mismatches": []}`).
