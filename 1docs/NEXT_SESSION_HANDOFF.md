# Next Coding Session Handoff — R2 &rarr; R3

**From session/release:** R2 — Evidence-Complete Library, Notebook, and Disaster Recovery  
**To proposed session/release:** R3 — Auditable Claims, Provenance, Tri-Ledger, Ontology, Graph, and Knowledge Publisher  
**Current State:** R0 PASS, R1 PASS (with G2 bare-metal execution safely BLOCKED under Option B), R2 PASS (Gates G3, G4, G5, G6 all verified with real sealed evidence)  
**Lab repository path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`)  
**Lab Git branch:** `main`  
**Read first:** `1docs/MSK_Research_Lab_OS_MASTER_SPEC_v3.0.md`, `1docs/MSK_Research_Lab_OS_ROADMAP_R0_R6.md`, `2data/evidence/R2_report.md`.

---

## 1. Completed Actual Features with Runnable Reproduction

1. **Immutable Document Store (G3):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest tests/unit/test_library_store.py`
   - Ingests 10 acceptance documents (4 PDF with scans, 3 EPUB, 3 DOCX) into `2data/originals/<sha256>/<filename>`.
2. **Exact Source Locators & Parsers (G3/G4):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest tests/unit/test_parsers.py`
   - PDF 1-based page locators, EPUB spine hrefs, DOCX heading paths & tables.
3. **FTS5 Search & Location Resolution (G4):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest tests/unit/test_library_search.py`
   - Full text search with snippet highlighting and disk byte hash verification.
4. **Research Notebook & Citations (G5):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest tests/unit/test_notes_citations.py`
   - Creates research note linked to &ge;2 documents + 1 Git commit; exports to JSON.
5. **Disaster Recovery Backup & Restore (G6):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest tests/unit/test_backup_restore.py`
   - Creates VACUUM INTO backup archive; restores to fresh directory; verifies 100% SHA-256 match and FTS5 search.
6. **Full Test Suite (41 Tests):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest -v`
   - Result: 41 passed, 0 failed in 10.96 seconds.

---

## 2. Next Authorized Bounded Task (R3)

**Goal:** Implement the Scholarly Tri-Ledger, Provenance Registry, Controlled Multilingual Ontology, Typed Graph, and Immutable Release Snapshot Publisher (Gates G7, G8, G9, G10).

**Work packages (R3-01 &rarr; R3-08):**
1. **R3-01:** Provenance registry (edition, translation, derivative lineage, source independence, exact locators).
2. **R3-02:** Tri-Ledger: `claims`, `evidence`, `contradictions`, review events, irreversible revision lineage.
3. **R3-03:** Fail-closed promotion: human content review gate, counter-evidence disclosure.
4. **R3-04:** Side-by-side original source/edition comparison (`MATCH`, `DIFFERENCE`, `UNCERTAIN`, `NOT_COMPARABLE`).
5. **R3-05:** Namespaced multilingual ontology, alias crosswalks (GB21 synthetic educational fixture).
6. **R3-06:** Typed SQLite graph with reviewed edge evidence and bounded one-hop neighborhood queries.
7. **R3-07:** Staged immutable SQLite knowledge snapshots, QA rights check, atomic pointer switch, rollback.
8. **R3-08:** Published-only read-only API and active snapshot awareness (`/api/v1/snapshots/current`).
