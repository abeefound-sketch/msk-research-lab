# Coding Session Handoff & Completion Record — Bubblewrap Sandbox Verified & R4 Anatomical Honesty Reassessment

**Project:** MSK Research Lab OS v3.1  
**Status:** **R0, R1 (Static), R1D, R2, R3, R4 (Procedural Demo), R5, R6 VERIFIED (153 TESTS PASSING); G2 (Bubblewrap Rootless Sandbox Verified, Execution Fail-Closed Awaiting Per-Repo Approval)**  
**Target Platform:** Windows 10 / Ubuntu WSL2 (Intel HD 5500, 8 GiB RAM, 1366x768 Display)  
**Lab Repository Path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`) strictly on C: drive  
**MSK-Therapy-OS Status:** Untouched / Immutable at `/mnt/d/5Projects/msk-therapy-os` (Zero changes made to Therapy OS)  
**Total Automated Tests:** **153 passed, 0 failed** in 106.25 seconds  
**Database Schema Version:** v7 (Migrations 0001 through 0007 applied transactionally with WAL and Foreign Keys ON)  

---

## 1. Executive Summary & Release Gates State

| Release | Focus Area | Acceptance Gates | Verified Result | Evidence Manifest & Caveats |
|---|---|---|---|---|
| **R0** | Local Foundation & Diagnostics | **G1** | **PASS (VERIFIED)** | SQLite WAL, loopback port 8091 guard, doctor diagnostics. `2data/evidence/R0_report.md` |
| **R1 (Static)** | Repo Lab Static & Surface Benchmark | **G3, G4, SEC, SR-01..10** | **PASS (VERIFIED)** | Static AST analysis, license auditor, SR-01..10 registration benchmark 100% pass. `2data/evidence/R1_report.md` |
| **R1 (G2)** | Live Upstream Sandbox Run | **G2, SEC** | **BLOCKED (APPROVAL REQ)** | Bubblewrap rootless container sandbox installed and isolated on WSL2. Filesystem, network, PID, and memory isolation verified (8/8 security tests pass). Native execution strictly fail-closed; awaiting separate per-repo operator execution approval. |
| **R1D** | Discovery & Research Pipeline | **DISC-01..04, REV-01..02** | **PASS (VERIFIED)** | Local MD import, live GitHub discovery, candidate queue, AST static analysis, reports. REA adapter is OPTIONAL_UNAVAILABLE. Real browser screenshots: `2data/evidence/R1D/run_r1d_discovery_001/dashboard_r1d_1366x768.png` |
| **R2** | Research Library & Disaster Recovery | **G5, G6** | **PASS (VERIFIED)** | Content-addressed originals (`2data/originals/`), FTS5 BM25 search, VACUUM INTO backup/restore. `2data/evidence/R2_report.md` |
| **R3** | Scholarly Tri-Ledger & Publisher | **G7, G8, G9, G10, SEC** | **PASS (VERIFIED)** | Tri-ledger (Claims, Evidence, Contradictions), ontology lookup, typed graph, snapshot publisher. `2data/evidence/R3_report.md` |
| **R4** | Unified Anatomy & Meridian Atlas | **ATLAS-01..06, SR-01..10** | **PROTOTYPE (PROCEDURAL)** | Production Three.js WebGL multi-layer Atlas Workbench with calibrated torso, 5 tissue layers, 5 anchored points, GB/SI meridians, 6-view occlusion QA, interactive raycasting, region filters, resilient 2D fallback. Epistemic reassessment: procedural benchmark demonstration only; does NOT constitute clinical BodyParts3D asset. Real DBCLS OBJ parser with FMA ontology provenance implemented. Memory ~1.4 MB VRAM. Real browser screenshots: `2data/evidence/R4/run_r4_atlas_001/dashboard_r4_atlas_1366x768.png` |
| **R5** | Private Studio & 2D Diện Chẩn | **ATLAS-05, ATLAS-06** | **PASS (VERIFIED)** | Multi-tradition studio editor, transactional undo/redo, 2D Diện Chẩn maps, epistemic 2D->3D rejection. `2data/evidence/R5_report.md` |
| **R6** | Therapy Bridge & Offline Packages | **BRIDGE-01..03, SEC** | **PASS (VERIFIED)** | Scoped Bearer authentication, offline hashed research packages, mock consumer client, zero patient data boundary. `2data/evidence/R6_report.md` |

---

## 2. Completed Architecture by Release

### R0 — Verified Local Foundation & Doctor
- Database engine: SQLite 3.37.2 with WAL mode, foreign keys, busy timeout, and transactional schema migration table (`schema_migrations`).
- Server daemon: `127.0.0.1:8091` loopback-only binding with host header inspection.
- Memory budget: `< 56 MiB RSS` (well within 500 MiB limit).
- Automated doctor diagnostics script: `scripts/doctor.py`.
- Path resolution: `_find_repo_root()` and `AppConfig.data_dir` anchored to repository root `pyproject.toml`.

### R1 & R1D — Static Repo Lab & Discovery Research Pipeline
- Untrusted repo catalog loaded into SQLite without auto-cloning.
- URL normalizer and license auditor (MIT, AGPL-3.0, asset licenses, lookalike hostname rejection).
- Safe cloner with `--config core.hooksPath=/dev/null` and fail-closed sandbox guard.
- Surface registration benchmark harness: SR-01..SR-10 all 100% PASS.
- **DISC-01**: Local Markdown repo list import (`research/references/*.md`) with exact line/SHA provenance, deduplication by canonical URL, registering exclusively as `DISCOVERED_UNVERIFIED`.
- **DISC-02**: Live GitHub repository search with query caching (24h TTL in `github_discovery_queries`), rate-limit (403/429) backoff, and transparent non-medical heuristic scoring.
- **DISC-03**: Persistent research queue and 16-state lifecycle state machine (`update_candidate_state`, `queue_candidate_for_research`, `approve_and_clone_candidate`). Distinct clone approval vs run approval. Untrusted execution fails closed as `BLOCKED (EXECUTION_APPROVAL_REQUIRED)`.
- **DISC-04**: Side-by-side candidate comparison matrix. Source-cited Markdown & JSON research reports generated in `research/reports/<repo-id>/v<rev>/` with SHA-256 manifests. Ingested into Tri-Ledger `evidence` table as `UNREVIEWED_SOURCE_FINDING`.
- **REV-01**: Read-only static source AST investigation mapping entrypoints, dependencies (npm, PyPI), 3D formats (`.glb`, `.obj`), UI frameworks (Three.js), and high-risk install hooks (`postinstall`, `os.system`). Zero external code executed.
- **REV-02**: Optional REA reverse-engineering adapter cleanly reporting `OPTIONAL_UNAVAILABLE` on WSL2 host without crashing or auto-installing.
- Interactive Dashboard UI with Import, Search, Inspect, Report, and Decide actions. Verified via real Chrome headless browser E2E test at 1366x768.

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

### R4 — Unified Anatomy & Meridian Atlas (ATLAS-01..06)
- **Epistemic Invariant & Honest Labeling**:
  - Procedural torso demonstration model is NOT a verified clinical BodyParts3D asset.
  - Model metadata explicitly set to `asset_kind: PROCEDURAL_BENCHMARK_DEMONSTRATION` and `clinical_validation_status: NOT_CLINICALLY_VALIDATED; PROCEDURAL_BENCHMARK_ONLY`.
  - Added authentic DBCLS BodyParts3D Wavefront `.obj` parser (`import_bodyparts3d_obj`) with FMA ontology provenance mapping.
- **Calibrated Reference Scene** (`src/msk_research_lab/atlas/scene.py`):
  - Calibrated cervical-thoracic torso model in millimeters (`mm`), coordinate frame `mesh_local_xyz`, pose `standing_anatomical`.
  - 5 Anatomical Layers: Skin, Skeletal, Superficial Muscular, Deep Muscular, Nervous.
  - 5 Anchored Anatomical Points (`GB21`, `GV14`, `SI14`, `SI15`, `BL11`) with barycentric contact distance $0.00\text{ mm}$ and surface normal vectors.
  - Calibrated Meridian Trajectories: Gallbladder (`GB`) and Small Intestine (`SI`).
  - 6 Standard Camera Presets: `FRONT`, `BACK`, `LEFT`, `RIGHT`, `OBLIQUE_TOP`, `OBLIQUE_BOTTOM`, plus `RESET`.
- **API & Delivery**:
  - Offline Three.js v128 and OrbitControls served statically via `/static/vendor/`.
  - `GET /api/v1/atlas/scene/{model_id}` endpoint delivering scene geometry.
- **Interactive Dashboard Workbench**:
  - Interactive WebGL Three.js viewport with OrbitControls (rotate, pan, zoom).
  - Raycaster point picking: clicking 3D spheres selects the point and updates the Point Inspector immediately.
  - Region filtering dropdown (`ALL`, `SHOULDER_RIDGE`, `POSTERIOR_NECK`, `UPPER_BACK`).
  - Six-View Camera Occlusion QA matrix dynamically evaluating visibility.
  - Layer toggles, X-Ray and Wireframe mode toggles.
  - VRAM budget monitor: `~1.4 MB VRAM` (strictly compliant with 8GB RAM budget).
  - Resilient 2D canvas fallback if WebGL is unavailable.

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

## 3. Priority 2: G2 Bubblewrap Sandbox Implementation & Security Verification

### Bubblewrap Rootless Architecture
In accordance with Directive 8 (Option A), `bubblewrap` (v0.6.1) was retrieved from the official Ubuntu APT repository and deployed to `~/.local/bin/bwrap` and the virtual environment without storing, requesting, or exposing sudo credentials.

1. **Restricted Filesystem Mounts:**
   - Read-only binds: `/bin`, `/lib`, `/lib64`, `/usr`, and the active virtual environment.
   - Read-only bind of target repository to `/app`.
   - Complete exclusion of Windows drives (`/mnt`, `/mnt/c`, `/mnt/d`, and `/mnt/d/5Projects/msk-therapy-os`).
   - Complete exclusion of private credentials and SSH keys (`/home/tuan/.ssh`, `.env`, tokens).
   - Volatile, isolated in-memory scratch storage (`--tmpfs /tmp`).
2. **Strict Network Denial:**
   - `--unshare-net` completely detaches the network namespace.
   - Loopback and external sockets are blocked (`ConnectionRefusedError` / `OSError`).
3. **Process Namespace & Lifecycle Isolation:**
   - `--unshare-pid` and private `--proc /proc` prevent inspecting host processes or daemons.
   - `--die-with-parent` guarantees child processes terminate if the runner process exits.
4. **Independent Memory Enforcement:**
   - Because Bubblewrap relies on user namespaces rather than cgroups, memory limits are enforced via POSIX `resource.setrlimit(resource.RLIMIT_AS, (500MB, 500MB))` in the preexec child hook.
   - Allocations exceeding 500 MB immediately trigger `MemoryError`, protecting system RAM.
5. **Execution Fail-Closed Gate & Approval Requirement:**
   - Security gate G2 remains strictly **BLOCKED (APPROVAL REQ)**.
   - ProcessGovernor and the API endpoint `/api/v1/repos/{repo_id}/launch` fail closed unless an explicit human operator approval token is provided (`ApprovalRequiredError` / HTTP 503 `EXECUTION_APPROVAL_REQUIRED`).

### Automated Security Test Suite (8/8 Passed)
All security invariants verified in `tests/security/test_sandbox_bubblewrap.py`:
- `test_bwrap_probe_reports_verified`: Probe reports `SANDBOX_VERIFIED_BUBBLEWRAP`.
- `test_sandbox_blocks_windows_and_therapy_os_mounts`: Confirms `/mnt`, `/mnt/c`, and `/mnt/d/5Projects/msk-therapy-os` are completely blocked.
- `test_sandbox_blocks_ssh_keys_and_private_home`: Confirms `/home/tuan/.ssh` and user files are invisible.
- `test_sandbox_enforces_network_denial`: Confirms socket connections to loopback (`127.0.0.1:8091`) or external IPs (`8.8.8.8`) fail immediately.
- `test_sandbox_private_tmp_storage_isolated`: Confirms `/tmp` writes are volatile and isolated from host.
- `test_sandbox_process_namespace_isolation`: Confirms isolated PID namespace cannot see host daemon processes.
- `test_memory_resource_limits_enforced`: Confirms allocations exceeding limits raise `MemoryError`.
- `test_execution_blocked_without_operator_approval`: Confirms unapproved execution raises `ApprovalRequiredError`.

---

## 4. Verification Evidence & Artifact Manifest

| Artifact | Path | SHA-256 Hash |
|---|---|---|
| **G2 Sandbox Screenshot (1366x768)** | `2data/evidence/R1_G2/run_g2_bubblewrap_001/dashboard_bubblewrap_sandbox_1366x768.png` | `03be7923f6af68098b4ffb6121d4c5e6b49cde9ba70c6080c18af8c6a6a30b01` |
| **G2 Evidence Report** | `2data/evidence/R1_G2/run_g2_bubblewrap_001/evidence_report_g2.json` | Sealed JSON manifest |
| **R4 Dashboard Screenshot (1366x768)** | `2data/evidence/R4/run_r4_atlas_001/dashboard_r4_atlas_1366x768.png` | `909557c64c2c0ac6204a317a1fc201aa2aed77cf2954f2083846446e5ebac879` |
| **R4 Evidence Report** | `2data/evidence/R4/run_r4_atlas_001/evidence_report_r4.json` | Sealed JSON manifest |
| **R1D Dashboard Screenshot** | `2data/evidence/R1D/run_r1d_discovery_001/dashboard_r1d_updated_1366x768.png` | Verified in commit `2966adf` |
| **Bubblewrap Security Suite** | `tests/security/test_sandbox_bubblewrap.py` | 8/8 passed |

---

## 5. How to Run and Verify the System

### Full Regression Test Suite (153 Tests)
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
/home/tuan/.venvs/msk-lab/bin/pytest tests
```
*Result: 153 passed, 0 failed in 106.25s.*

### Run Bubblewrap Security Verification
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
/home/tuan/.venvs/msk-lab/bin/pytest tests/security/test_sandbox_bubblewrap.py -v
```

### Start MSK Research Lab OS Daemon
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
/home/tuan/.venvs/msk-lab/bin/python3 -m msk_research_lab serve --port 8091
```
Then visit `http://127.0.0.1:8091/` or `http://127.0.0.1:8091/dashboard` in a Windows web browser.

### Run System Diagnostics Doctor
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
/home/tuan/.venvs/msk-lab/bin/python3 scripts/doctor.py
```
