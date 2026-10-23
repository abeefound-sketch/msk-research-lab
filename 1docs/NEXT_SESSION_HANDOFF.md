# Next Coding Session Handoff — R1 &rarr; R2

**From session/release:** R1 — Repository Lab Static Inspection and Surface Registration Benchmark  
**To proposed session/release:** R2 — Evidence-Complete Library, Notebook, and Recovery  
**Current State:** R1 PASS (Static Inspection, URL Normalizer, Rights Matrix, Evidence Store, and SR-01..SR-10 PASS; G2 live execution truthfully marked `BLOCKED` under Option B)  
**Lab repository path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`)  
**Lab Git branch:** `main`  
**Read first:** `1docs/MSK_Research_Lab_OS_MASTER_SPEC_v3.0.md`, `1docs/MSK_Research_Lab_OS_ROADMAP_R0_R6.md`, `2data/evidence/R1_report.md`.

---

## 1. Completed Actual Features with Runnable Reproduction

1. **Static Repository Inspection & Rights Analysis:**
   - Command: `PYTHONPATH=src .venv/bin/pytest tests/unit/test_inspector.py tests/unit/test_cloner.py`
   - Validates URL normalization, shell injection defense, license scanning (detects AGPL-3.0 copyleft risk, asset license separation), and path traversal rejection.
2. **Surface Registration Benchmark (SR-01..SR-10):**
   - Command: `PYTHONPATH=src .venv/bin/pytest tests/unit/test_benchmark_sr.py`
   - Endpoint: `GET /api/v1/benchmarks/surface-registration`
   - 10/10 geometry tests PASS with zero topological penetration and verified 3-run determinism.
3. **Repository Lab Management API:**
   - Command: `PYTHONPATH=src .venv/bin/pytest tests/integration/test_repos_api.py`
   - Endpoints: `GET /api/v1/repos`, `POST /api/v1/repos/register`, `POST /api/v1/repos/{id}/inspect`, `POST /api/v1/repos/{id}/approve`, `POST /api/v1/repos/{id}/launch` (fails closed with 503 if container sandbox is missing).
4. **Evidence Store & Tamper Detection:**
   - Command: `PYTHONPATH=src .venv/bin/pytest tests/unit/test_evidence_bundle.py`
   - Verified immutable SHA-256 manifest sealing and automated tampering detection.
5. **Full Test Suite (29 Tests):**
   - Command: `PYTHONPATH=src .venv/bin/pytest -v`
   - Result: 29 passed, 0 failed in 4.65 seconds.

---

## 2. Next Authorized Bounded Task (R2)

**Goal:** Build source-first, image-aware private research document library that works before any AI service exists.

**Work packages (R2-01 &rarr; R2-08):**
1. **R2-01:** Immutable SHA-256 original documents store (`2data/originals/<sha256>`), metadata registry, zip safety.
2. **R2-02:** PDF extraction for native text and scanned pages; original page viewer; normalized region locators `[x1, y1, x2, y2]`.
3. **R2-03:** Opt-in local OCR worker, per-page status, image/table gap accounting.
4. **R2-04:** EPUB spine/href/chapter parser & safe HTML viewer; DOCX paragraph/heading/table parser with structural anchors.
5. **R2-05:** SQLite FTS5 search across all formats with snippet highlight and click-to-original navigation.
6. **R2-06:** Research notes & experiments linked to &ge;2 book citations + 1 Git SHA; export JSON/MD.
7. **R2-07:** Authenticated read-only research-note API (`/api/v1/research/notes/{id}`); `/api/v1/knowledge/points/{code}` must return 404 until R3.
8. **R2-08:** Consistent SQLite backup + originals + index; restore to fresh directory and verify SHA-256 integrity.
