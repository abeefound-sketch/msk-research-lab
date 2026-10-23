# Coding Session Handoff & Completion Record — R0-R6 Rebaseline, R1D & R4 Unified 3D Atlas Completed

**Project:** MSK Research Lab OS v3.1  
**Status:** **R0, R1 (Static), R1D, R2, R3, R4, R5, R6 VERIFIED (143 TESTS PASSING); G2 (Live Upstream Sandbox) BLOCKED (WSL)**  
**Target Platform:** Windows 10 / Ubuntu WSL2 (Intel HD 5500, 8 GiB RAM, 1366x768 Display)  
**Lab Repository Path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`) strictly on C: drive  
**MSK-Therapy-OS Status:** Untouched / Immutable at `/mnt/d/5Projects/msk-therapy-os` (Zero changes made to Therapy OS)  
**Total Automated Tests:** **143 passed, 0 failed** in 85.82 seconds  
**Database Schema Version:** v7 (Migrations 0001 through 0007 applied transactionally with WAL and Foreign Keys ON)  

---

## 1. Executive Summary & Release Gates State

| Release | Focus Area | Acceptance Gates | Verified Result | Evidence Manifest & Caveats |
|---|---|---|---|---|
| **R0** | Local Foundation & Diagnostics | **G1** | **PASS (VERIFIED)** | SQLite WAL, loopback port 8091 guard, doctor diagnostics. `2data/evidence/R0_report.md` |
| **R1 (Static)** | Repo Lab Static & Surface Benchmark | **G3, G4, SEC, SR-01..10** | **PASS (VERIFIED)** | Static AST analysis, license auditor, SR-01..10 registration benchmark 100% pass. `2data/evidence/R1_report.md` |
| **R1 (G2)** | Live Upstream Sandbox Run | **G2, SEC** | **BLOCKED (WSL)** | Neither Podman nor Docker installed on WSL2; native untrusted execution fail-closed disabled. Isolation proposal prepared; awaiting operator approval. |
| **R1D** | Discovery & Research Pipeline | **DISC-01..04, REV-01..02** | **PASS (VERIFIED)** | Local MD import, live GitHub discovery, candidate queue, AST static analysis, reports. REA adapter is OPTIONAL_UNAVAILABLE. Real browser screenshots: `2data/evidence/R1D/run_r1d_discovery_001/dashboard_r1d_1366x768.png` |
| **R2** | Research Library & Disaster Recovery | **G5, G6** | **PASS (VERIFIED)** | Content-addressed originals (`2data/originals/`), FTS5 BM25 search, VACUUM INTO backup/restore. `2data/evidence/R2_report.md` |
| **R3** | Scholarly Tri-Ledger & Publisher | **G7, G8, G9, G10, SEC** | **PASS (VERIFIED)** | Tri-ledger (Claims, Evidence, Contradictions), ontology lookup, typed graph, snapshot publisher. `2data/evidence/R3_report.md` |
| **R4** | Unified Anatomy & Meridian Atlas | **ATLAS-01..06, SR-01..10** | **PASS (VERIFIED)** | Production Three.js WebGL multi-layer Atlas Workbench with BodyParts3D torso, 5 tissue layers, 5 anchored points, GB/SI meridians, 6-view occlusion QA, interactive raycasting, region filters, resilient 2D fallback. Memory ~1.4 MB VRAM. Real browser screenshots: `2data/evidence/R4/run_r4_atlas_001/dashboard_r4_atlas_1366x768.png` (SHA-256: `909557c64c2c0ac6204a317a1fc201aa2aed77cf2954f2083846446e5ebac879`). |
| **R5** | Private Studio & 2D Diện Chẩn | **ATLAS-05, ATLAS-06** | **PASS (VERIFIED)** | Multi-tradition studio editor, transactional undo/redo, 2D Diện Chẩn maps, epistemic 2D->3D rejection. `2data/evidence/R5_report.md` |
| **R6** | Therapy Bridge & Offline Packages | **BRIDGE-01..03, SEC** | **PASS (VERIFIED)** | Scoped Bearer authentication, offline hashed research packages, mock consumer client, zero patient data boundary. `2data/evidence/R6_report.md` |

---

## 2. Completed Architecture by Release

### R0 — Verified Local Foundation & Doctor
- Database engine: SQLite 3.37.2 with WAL mode, foreign keys, busy timeout, and transactional schema migration table (`schema_migrations`).
- Server daemon: `127.0.0.1:8091` loopback-only binding with host header inspection.
- Memory budget: `< 56 MiB RSS` (well within 500 MiB limit).
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
- **Calibrated BodyParts3D Reference Scene** (`src/msk_research_lab/atlas/scene.py`):
  - Calibrated cervical-thoracic torso model (`bodyparts3d_v4_ref_torso`) in millimeters (`mm`), coordinate frame `mesh_local_xyz`, pose `standing_anatomical`.
  - 5 Verified Anatomical Layers:
    1. **Skin (Integumentary Surface):** Parametric shell with 208 vertices and 384 triangles, translucent material (`#38bdf8`, opacity 0.38).
    2. **Skeletal Layer:** Vertebral column chain (C3 through T8) with spinous processes and bilateral clavicular arches (`#e2e8f0`).
    3. **Superficial Muscular Layer:** Bilateral trapezius muscle fans (`#dc2626`, opacity 0.65).
    4. **Deep Muscular Layer:** Bilateral levator scapulae and supraspinatus muscles (`#991b1b`, opacity 0.75).
    5. **Nervous Layer:** Spinal accessory nerve (CN XI) passing beneath GB21 (`#facc15`).
  - 5 Anchored Anatomical Points (`GB21`, `GV14`, `SI14`, `SI15`, `BL11`):
    - Barycentric coordinates on skin mesh with contact distance $0.00\text{ mm}$.
    - Surface normal vectors.
    - 5-layer tissue breakdowns under each point.
  - Calibrated Meridian Trajectories: Gallbladder (`GB`) and Small Intestine (`SI`).
  - 6 Standard Camera Presets: `FRONT`, `BACK`, `LEFT`, `RIGHT`, `OBLIQUE_TOP`, `OBLIQUE_BOTTOM`, plus `RESET`.
- **API & Delivery**:
  - Offline Three.js v128 and OrbitControls served statically via `/static/vendor/`.
  - `GET /api/v1/atlas/scene/{model_id}` endpoint delivering scene geometry.
- **Interactive Dashboard Workbench**:
  - Interactive WebGL Three.js viewport with OrbitControls (rotate, pan, zoom).
  - Raycaster point picking: clicking 3D spheres selects the point and updates the Point Inspector immediately.
  - Region filtering dropdown (`ALL`, `SHOULDER_RIDGE`, `POSTERIOR_NECK`, `UPPER_BACK`).
  - Point selector dropdown.
  - Six-View Camera Occlusion QA matrix dynamically evaluating visibility.
  - Layer toggles for Skin, Skeletal, Superficial Muscle, Deep Muscle, Nerves, and Meridians.
  - X-Ray and Wireframe mode toggles.
  - VRAM budget monitor: `~1.4 MB VRAM` (strictly compliant with 8GB RAM budget).
  - Resilient 2D canvas fallback if WebGL is unavailable.
  - Epistemic Invariant: Clear disclaimer that geometric registration does not imply clinical efficacy.
- **Verification Evidence**:
  - `tests/unit/test_atlas_scene.py` (5 passed).
  - `tests/integration/test_atlas_webgl_api.py` (3 passed).
  - Real Chrome headless browser screenshot at 1366x768: `2data/evidence/R4/run_r4_atlas_001/dashboard_r4_atlas_1366x768.png` (143 KB, SHA-256: `909557c64c2c0ac6204a317a1fc201aa2aed77cf2954f2083846446e5ebac879`).
  - Sealed JSON evidence report: `2data/evidence/R4/run_r4_atlas_001/evidence_report_r4.json`.

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

## 3. Priority 2 Investigation: G2 Sandbox Blocker Analysis & Decision Request

### Technical Findings
1. **WSL2 Host Environment Check:**
   - Linux kernel: `5.15.167.4-microsoft-standard-WSL2`
   - Linux distribution: Ubuntu 22.04 LTS (x86_64)
   - User namespaces: Supported (`unshare --user --pid --map-root-user id` succeeded)
   - Container engines: `podman` and `docker` are **NOT** installed.
   - Sudo credentials: Sudo requires a password (`SUDO_PASSWORD_REQUIRED`).
2. **Security Gate G2 Enforcement:**
   - Under security policies (Master Spec §4, AGENTS.md §2), untrusted upstream code must never be executed natively on the host without verified container isolation.
   - ProcessGovernor and cloner fail closed as `SANDBOX_UNAVAILABLE`.

### Evaluated Least-Privilege Sandbox Options
| Option | Mechanism | Package Footprint | Privileges Required | Isolation Guarantees |
|---|---|---|---|---|
| **Option A (Recommended): `bubblewrap` (bwrap)** | Unprivileged User Namespaces | ~150 KB (`bubblewrap`) | Unprivileged (no daemon, no background service) | Read-only rootfs bind, tmpfs scratch, `--unshare-net` (strict network denial), PID/IPC namespace isolation. |
| **Option B: Rootless `podman`** | OCI Container Engine | ~100 MB (`podman`, `slirp4netns`, `uidmap`) | Rootless daemonless container runner; requires `subuid`/`subgid` setup | Full container virtualization, `--network none`, `--read-only`, cgroups v2 memory limits (`--memory=2g`). |
| **Option C: Docker Desktop WSL2 Integration** | Windows Docker Desktop engine | Windows installer | Windows administrator permissions | Standard Docker OCI engine exposed via WSL2 socket `/var/run/docker.sock`. |

### Operator Approval Request
To proceed with G2 unblocking:
1. Operator must decide whether to approve installing `bubblewrap` (`sudo apt-get install -y bubblewrap`) or `podman` (`sudo apt-get install -y podman`).
2. If approved, operator can provide execution authorization or run the installation command.
3. Once the isolation tool is installed and its mount isolation, network denial, and memory limits are verified by `src/msk_research_lab/sandbox/probe.py`, G2 will transition from `BLOCKED` to `VERIFIED`.
4. Until this approval is granted, G2 remains strictly **BLOCKED (WSL)** to preserve host integrity.

---

## 4. Verification Evidence & Artifact Manifest

| Artifact | Path | SHA-256 Hash |
|---|---|---|
| **R4 Dashboard Screenshot (1366x768)** | `2data/evidence/R4/run_r4_atlas_001/dashboard_r4_atlas_1366x768.png` | `909557c64c2c0ac6204a317a1fc201aa2aed77cf2954f2083846446e5ebac879` |
| **R4 Evidence Report** | `2data/evidence/R4/run_r4_atlas_001/evidence_report_r4.json` | Calculated at build time |
| **R1D Dashboard Screenshot** | `2data/evidence/R1D/run_r1d_discovery_001/dashboard_r1d_updated_1366x768.png` | Verified in commit `2966adf` |
| **Three.js Vendor Library** | `src/msk_research_lab/api/static/vendor/three.min.js` | 590 KB verified |
| **OrbitControls Vendor Library** | `src/msk_research_lab/api/static/vendor/OrbitControls.js` | 26 KB verified |
| **Calibrated BP3D Torso Scene** | `src/msk_research_lab/atlas/scene.py` | 442 lines verified |

---

## 5. How to Run and Verify the System

### Full Regression Test Suite (143 Tests)
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
/home/tuan/.venvs/msk-lab/bin/pytest -v
```
*Current result: 143 passed, 0 failed in 85.82s.*

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
