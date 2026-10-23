# Coding Session Handoff & Completion Record — R0-R6 Rebaseline & R1D Completed

**Project:** MSK Research Lab OS v3.1  
**Status:** **REBASELINED & R1D COMPLETED (135 TESTS PASSING)**  
**Target Platform:** Windows 10 / Ubuntu WSL2 (Intel HD 5500, 8 GiB RAM, 1366x768 Display)  
**Lab Repository Path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`) strictly on C: drive  
**MSK-Therapy-OS Status:** Untouched / Immutable at `/mnt/d/5Projects/msk-therapy-os` (Zero changes made to Therapy OS)  
**Total Automated Tests:** **135 passed, 0 failed** in 77.21 seconds  
**Database Schema Version:** v7 (Migrations 0001 through 0007 applied transactionally with WAL and Foreign Keys ON)  

---

## 1. Executive Summary & Release Gates State (Rebaselined)

| Release | Focus Area | Acceptance Gates | Verified Result | Evidence Manifest & Caveats |
|---|---|---|---|---|
| **R0** | Local Foundation & Diagnostics | **G1** | **PASS** | `2data/evidence/R0_report.md` |
| **R1** | Repo Lab Static & Surface Benchmark | **G2, G3, G4, SEC, SR-01..10** | **PARTIAL** | Static analysis/SR harness PASS. **G2 Live Upstream Run BLOCKED**: Neither Podman nor Docker detected in WSL environment; native untrusted execution fail-closed disabled. |
| **R1D** | Discovery & Research Pipeline | **DISC-01..04, REV-01..02** | **PASS** | Local MD import, live GitHub discovery, candidate queue, AST static analysis, reports. REA adapter is OPTIONAL_UNAVAILABLE. `2data/evidence/R1D_report.md` |
| **R2** | Research Library & Disaster Recovery | **G5, G6** | **PASS** | `2data/evidence/R2_report.md` |
| **R3** | Scholarly Tri-Ledger & Publisher | **G7, G8, G9, G10, SEC** | **PASS** | `2data/evidence/R3_report.md` |
| **R4** | Unified Anatomy & Meridian Atlas | **ATLAS-01..04, SR-01..10** | **PARTIAL** | Python registry, barycentric anchors, occlusion QA PASS. Hardware WebGL BodyParts3D rendering partial/pending hardware harness. |
| **R5** | Private Studio & 2D Diện Chẩn | **ATLAS-05, ATLAS-06** | **PASS** | `2data/evidence/R5_report.md` |
| **R6** | Therapy Bridge & Offline Packages | **BRIDGE-01..03, SEC** | **PASS** | `2data/evidence/R6_report.md` |

---

## 2. Completed Architecture by Release

### R0 — Verified Local Foundation & Doctor
- Database engine: SQLite 3.37.2 with WAL mode, foreign keys, busy timeout, and transactional schema migration table (`schema_migrations`).
- Server daemon: `127.0.0.1:8091` loopback-only binding with host header inspection.
- Memory budget: `< 46 MiB RSS` (well within 500 MiB limit).
- Automated doctor diagnostics script: `scripts/doctor.py`.

### R1 & R1D — Static Repo Lab & Discovery Research Pipeline
- Untrusted repo catalog loaded into SQLite without auto-cloning.
- URL normalizer and license auditor (MIT, AGPL-3.0, asset licenses, lookalike hostname rejection).
- Safe cloner with `--config core.hooksPath=/dev/null` and fail-closed sandbox guard.
- Surface registration benchmark harness: SR-01..SR-10 all 100% PASS.
- **DISC-01**: Local Markdown repo list import (`research/references/*.md`) with exact line/SHA provenance, deduplication by canonical URL, registering exclusively as `DISCOVERED_UNVERIFIED`.
- **DISC-02**: Live GitHub repository search with query caching (24h TTL in `github_discovery_queries`), rate-limit (403/429) backoff, and transparent non-medical heuristic scoring.
- **DISC-03**: Persistent research queue and 16-state lifecycle state machine (`update_candidate_state`, `queue_candidate_for_research`, `approve_and_clone_candidate`). Distinct clone approval vs run approval. Untrusted execution fails closed as `BLOCKED (SANDBOX_UNAVAILABLE)`.
- **DISC-04**: Side-by-side candidate comparison matrix. Source-cited Markdown & JSON research reports generated in `research/reports/<repo-id>/v<rev>/` with SHA-256 manifests. Ingested into Tri-Ledger `evidence` table as `UNREVIEWED_SOURCE_FINDING`.
- **REV-01**: Read-only static source AST investigation mapping entrypoints, dependencies (npm, PyPI), 3D formats (`.glb`, `.obj`), UI frameworks (Three.js), and high-risk install hooks (`postinstall`, `os.system`). Zero external code executed.
- **REV-02**: Optional REA reverse-engineering adapter cleanly reporting `OPTIONAL_UNAVAILABLE` on WSL2 host without crashing or auto-installing.


### R2 — Content-Addressed Library, Search & Disaster Recovery
- Content-addressed originals store (`2data/originals/<sha256>/`).
- Multi-format parsers (PDF, EPUB, DOCX, TXT) extracting text and locators.
- SQLite FTS5 full-text search indexing with BM25 snippet ranking.
- Scholarly research notebook requiring $\ge 2$ book extracts and $\ge 1$ Git SHA citation.
- Hot backup via `VACUUM INTO` and clean restore verification drill.

### R3 — Auditable Claims, Tri-Ledger, Controlled Ontology, Typed Graph & Snapshot Publisher
- Sources provenance registry tracking editions, translations, and independence groups.
- Tri-ledger for Claims, Evidence, and open Contradictions with fail-closed promotion gates.
- Side-by-side comparator with epistemic geometry guard (`NOT_COMPARABLE` when unaligned).
- Controlled multilingual ontology (`config/ontology_seed.json`) with deterministic lookups (`GB21` &rarr; `Jianjing` / `Kiên tỉnh`).
- Typed SQLite graph with mandatory edge provenance and bounded 1-hop queries.
- Immutable snapshot publisher with automated QA validation, atomic pointer switch via `os.replace`, and rollback.

### R4 — Unified Anatomy & Meridian Atlas
- ADR-004 evaluating rights-cleared anatomical viewer and BodyParts3D reference torso.
- Calibrated 3D model registry with units (`mm`), frames (`mesh_local_xyz`), poses, and landmarks.
- Barycentric surface registration on skin meshes with `INVALIDATED_TOPOLOGY_CHANGED` guard.
- Meridian path baker flagging interior body penetration (>25 mm) with `DISCONTINUOUS_PENETRATION_GAP` to prevent imaginary lines through internal organs.
- Multi-camera 6-view occlusion QA (Front, Back, Left, Right, Oblique Top, Oblique Bottom).
- Two-source comparative adapter prohibiting fake millimeter subtraction on unregistered frames.
- Synchronized point and tissue inspector linking 3D anchors, ontology, claims, and tissue layers.
- Production WebGL Atlas Workbench integrated into Dashboard at 1366x768.

### R5 — Private Atlas Studio & 2D Diện Chẩn Reflexology
- Private atlas project management with per-tradition namespace isolation (TCM, Diện Chẩn, Thai Sen, Trigger Point, Custom).
- Studio editor with barycentric sum validation ($u+v+w=1.0$), coordinate move/delete, and transactional undo/redo lineage.
- 2D Diện Chẩn facial maps with pinned image SHA-256 and pixel coordinates `(x_px, y_px)`.
- Epistemic guard: Rejection of implicit 2D &rarr; 3D conversion (`CANNOT_IMPLICITLY_PROJECT_2D_TO_3D`).
- Fixed vs Reactive distinction: Session-specific observations cannot be promoted to global standards (`REACTIVE_OBSERVATION_CANNOT_BECOME_GLOBAL_FIXED`).
- Versioned JSON Schema transfer conforming to `schemas/atlas_point.schema.json` (v3.0.0), roundtrip import/export, and diff engine.

### R6 — Therapy Delivery Bridge & Offline Packages
- Scoped read-only Bearer authentication for external consumers against active release snapshot.
- Offline hashed research packages conforming to `schemas/research_package.schema.json` with per-member SHA-256 validation.
- Standalone Mock Consumer client (`TherapyResearchClient`) proving multi-channel survivability on Windows/WSL:
  - Online channel: Bearer queries against `/api/v1/knowledge/points/{code}`.
  - Offline channel: Transparent fallback to verified local package when Lab OS is offline.
  - Tamper detection: Fails closed on altered files (`TamperedPackageError`) or path traversal (`PackageSecurityError`).
- Field-level security & privacy boundary (BRIDGE-03): Raw PDFs/EPUBs excluded, process runner APIs locked, and zero patient data accepted or stored in Lab OS.

---

## 3. How to Run and Verify the System

### Full Regression Test Suite (104 Tests)
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
PYTHONPATH=src:. .venv/bin/python3 -m pytest -v
```

### Start MSK Research Lab OS Daemon
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
PYTHONPATH=src:. .venv/bin/python3 -m msk_research_lab
```
Then visit `http://127.0.0.1:8091/` or `http://127.0.0.1:8091/dashboard` in a Windows web browser.

### Run System Diagnostics Doctor
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
PYTHONPATH=src:. .venv/bin/python3 scripts/doctor.py
```
