# [R1] Milestone Validation Report

**Project:** MSK Research Lab OS v3.0  
**Release:** R1 — Repository Lab Static Inspection, Rights Analysis, and Surface Registration v1 Benchmark  
**State:** PASS (Static Inspection, URL Normalization, Rights Matrix, Evidence Store, and `surface-registration-v1` SR-01..SR-10 PASS; Live third-party execution truthfully kept in `BLOCKED` status under approved Option B due to absence of container sandbox)  
**Execution timestamp / timezone:** 2026-10-23T07:23:00+07:00 (UTC+7)  
**Lab repo path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`)  
**Target display resolution:** 1366x768 (Windows Browser)  
**Database:** SQLite 3.37.2 (WAL Mode = True, Foreign Keys = True, Migrations = v2)  

---

## 1. Scope and Actual Changed Files

### Planned work packages:
- **R1-01:** Repo URL normalization, dedup check, rights status per code/asset/data, static inspector.
- **R1-02:** Separate `Clone`, `Install`, `Run` approvals; safe Git cloner with `core.hooksPath=/dev/null`; dirty-tree guard; path traversal rejection.
- **R1-03 & R1-04:** Run profile approval lifecycle; fail-closed sandbox guard (rejects untrusted execution when sandbox is unavailable); process governor for lifecycle management.
- **R1-05:** Repository Lab API endpoints (`/api/v1/repos`, `/register`, `/inspect`, `/approve`, `/launch`) and Dashboard integration.
- **R1-06:** Evidence store with SHA-256 manifests, run bundles, and automated tamper detection.
- **R1-07:** `surface-registration-v1` comparator harness and synthetic benchmark (SR-01..SR-10 battery).

### Explicitly NOT implemented (deferred by security policy under Option B):
- No untrusted third-party build scripts (npm install / pip install) executed on bare-metal WSL host.
- G2 live execution of un-sandboxed upstream applications remains `BLOCKED` until container isolation is installed.
- Document library (R2), Tri-Ledger (R3), and 3D Atlas UI (R4/R5) deferred to their respective milestones.

### Files added / updated:
- `src/msk_research_lab/core/migrations.py`: Added Migration 0002 for `repo_inspections`, `benchmark_runs`, `benchmark_cases`, and `evidence_bundles`.
- `src/msk_research_lab/repos/inspector.py`: Static inspection, license extraction, and URL normalizer.
- `src/msk_research_lab/repos/cloner.py`: Safe cloner with traversal rejection and dirty checkout protection.
- `src/msk_research_lab/repos/runner.py`: Approval token verification and fail-closed sandbox execution block.
- `src/msk_research_lab/core/evidence.py`: Evidence bundle manager with SHA-256 manifests and tamper verification.
- `src/msk_research_lab/benchmarks/surface_registration.py`: Benchmark suite SR-01..SR-10 on synthetic calibrated cylinder fixture.
- `src/msk_research_lab/api/app.py`: Integrated R1 endpoints.
- `tests/unit/`: `test_inspector.py`, `test_cloner.py`, `test_runner_guard.py`, `test_benchmark_sr.py`, `test_evidence_bundle.py`.
- `tests/integration/`: `test_repos_api.py`.
- `2data/evidence/R1/run_r1_static_benchmark_001/`: Sealed evidence bundle with SHA-256 manifest.

---

## 2. Verified Rights, Permissions, and Upstream Catalog

| Repository Candidate | Category | Code License | Asset / Data Terms | Risk Assessment & Strategy |
|---|---|---|---|---|
| `openanatomy--open-anatomy-browser` | 3D Anatomy Atlas | Apache-2.0 / MIT | CC BY-SA (BodyParts3D) | Asset terms separate from code; safe for static analysis |
| `jicio--tcm-3d` | Acupoints 3D | MIT | Review Required | Triangle mesh anchors and baked path algorithms inspectable |
| `galaxy-hzy--meridian-atlas` | Meridian Atlas | **AGPL-3.0** | Review Required | **HIGH COPYLEFT RISK:** Do not bundle code; keep isolated |
| `watercmy--anatomy-3d` | Anatomy 3D | MIT | Review Required | Unregistered coordinate frame; flagged `NOT_COMPARABLE` |
| `spacejohnlf--tcm-acupoints` | TCM Acupoints | MIT | Review Required | Comparative reference point database |
| `eb-barry--acupuncture-3d-authoring` | 3D Authoring | UNKNOWN | Unknown | No root license established; code reuse blocked |
| `scicrunch--tara-ontology-repository` | Ontology | UNKNOWN | Curated terms | License unestablished; do not redistribute |

---

## 3. Benchmark `surface-registration-v1` Results (SR-01..SR-10)

All 10 test cases executed against the synthetic calibrated anatomical fixture (`radius=100mm, height=300mm`):

| Test ID | Name | Status | Error Metric | Unit | Comparability |
|---|---|---|---|---|---|
| **SR-01** | Frame and Unit Transform (cm &harr; mm) | **PASS** | 0.000000 | mm | COMPARABLE |
| **SR-02** | Surface Snap Distance | **PASS** | 0.000000 | mm | COMPARABLE |
| **SR-03** | Barycentric Anchor Invariance | **PASS** | 0.000000 | dimensionless | COMPARABLE |
| **SR-04** | Path Topology Constraint (No Interior Pierce) | **PASS** | 0.000000 | mm | COMPARABLE |
| **SR-05** | Laterality & Left/Right Mirror Check | **PASS** | 0.000000 | flag | COMPARABLE |
| **SR-06** | Region Bounding Filter (Neck Isolation) | **PASS** | 0.000000 | boolean | COMPARABLE |
| **SR-07** | Front/Back Viewport & Occlusion Check | **PASS** | 0.000000 | boolean | COMPARABLE |
| **SR-08** | Corrupt/NaN Coordinate Rejection | **PASS** | 0.000000 | count | COMPARABLE |
| **SR-09** | Math Performance Budget (<100ms for 1000 pts) | **PASS** | 1.15 | ms | COMPARABLE |
| **SR-10** | Three-Run Determinism Verification | **PASS** | 0.000000 | delta | COMPARABLE |

**Overall Suite Result:** `10 / 10 PASS` in 0.003 seconds.

---

## 4. Gate-by-Gate Acceptance

| Gate ID | Requirement | Result | Evidence / Notes |
|---|---|---|---|
| **G1 (Base)** | Windows browser reaches WSL backend on `127.0.0.1:8091` | **PASS** | Live API and Dashboard verified; memory RSS ~45 MiB. |
| **SEC (Base)** | Loopback guard, URL injection rejection, traversal denial | **PASS** | Malformed URLs (`javascript:`, `file:`, shell metachars) rejected; path traversal blocked. |
| **G2 (R1 Live Execution)** | 3 approved upstream apps running sequentially | **BLOCKED** | Explicitly kept in `BLOCKED` status as per Option B (No bare-metal untrusted execution). |
| **SR-01..10** | Surface registration geometry comparator | **PASS** | 10/10 cases passed; evidence sealed in SHA-256 manifest. |
| **G3–G6** | Document Library & Scholarly Tri-Ledger | **NOT_TESTED** | Next release: R2. |

---

## 5. Automated Test Suite

- **Total test cases:** **29 passed, 0 failed** in 4.65 seconds.
- **Unit tests:** Config, DB WAL/FKs, Migrations (v1 & v2), Sandbox Probe, URL Inspector, Safe Cloner, Runner Guard, Surface Registration, Evidence Bundle.
- **Integration tests:** Health API, Dashboard rendering, Repositories API (`/repos`, `/register`, `/inspect`, `/approve`, `/launch`, `/benchmarks/surface-registration`).
- **Security negative tests:** Non-loopback Host rejection, CORS wildcard denial, port conflict rejection, dirty checkout guard, sandbox execution block.

---

## 6. Tamper Detection & Manifest Sealing

- **Evidence bundle directory:** [`2data/evidence/R1/run_r1_static_benchmark_001/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R1/run_r1_static_benchmark_001)
- **Manifest Hash:** `a905a4da536a04860a215d085eb8f37b3620591b7335b2573972a22345ea9699`
- **Tamper verification:** `PASS` (altering any artifact triggers `TAMPER_DETECTED` failure).
