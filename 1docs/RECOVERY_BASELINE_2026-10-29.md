# MSK Research Lab OS v3.2 — Recovery Baseline & Safety Audit Report

**Date:** 2026-10-29  
**Branch:** `fix/workstation-real-functional-acceptance`  
**Base Commit:** `b4cafe0`  
**Operator/Engineer:** Principal Full-Stack Engineer, Biomedical Software Safety Engineer, QA Automation Engineer  
**System Status:** `RECOVERY_IN_PROGRESS`  
**Release Gate Verdict:** `PRODUCT_ACCEPTANCE_REVOKED_PENDING_RETEST`  
**Clinical Boundary:** `CLINICAL_REALWORLD_GATE = BLOCKED` (Personal Offline Educational & Synthetic Research Only)

---

## 1. Environment & Hardware Baseline

- **Host Hardware:** Intel(R) Core(TM) i7-5600U CPU @ 2.60GHz, 4 Cores, 8 GB RAM on host (WSL2 allocation: 3862 MB total, 3207 MB free).
- **GPU:** Intel HD Graphics 5500.
- **Operating System:** Linux 6.18.54.1-microsoft-standard-WSL2 (x86_64).
- **Python:** 3.10.12 in editable `.venv` (`msk-research-lab 0.1.0`).
- **Database:** SQLite 3.37.2 with WAL mode enabled, foreign keys ON, FTS5 full-text search active. Current schema version: `8`.
- **Idle Server Memory Footprint (Measured):** Application loaded RSS = **46.62 MB** (well within the <100 MB target).
- **Camera Access:** Physical webcam device `/dev/video*` is not mounted by default in WSL2. Fallback probe correctly identifies camera offline.
- **Disaster Recovery Backup:**
  - Backup ID: `backup_1793261456`
  - Archive: `2data/exports/backup_1793261456.tar.gz`
  - SHA-256: `08832b90a6d482b4f7174dd92c32abc716b81048d26aeeb7588f6d3b3053347c`
  - Files backed up: 399 files (database + originals).

---

## 2. Test Suite Baseline (163 Collected)

All 163 unit, integration, and security tests were executed:
- **Passed:** 163
- **Failed:** 0
- **Skipped:** 0
*(Note: `tests/security/test_sandbox_bubblewrap.py::test_sandbox_enforces_network_denial` was corrected so that executing inside bubblewrap invokes the system python binary under `/usr/bin/python3` rather than failing on the unmounted `/mnt` drive).*

---

## 3. Forensic Defect Verification (F-01 through F-12)

| Finding | Description | Verified Code Location | Status |
|---|---|---|---|
| **F-01** | `toggleAtlasLayer` triggers `alert()` instead of 3D scene toggling | `src/msk_research_lab/api/workstation_ui.py:1267` | Verified |
| **F-02** | Anatomy Workstation renders `THREE.CylinderGeometry` instead of authentic anatomy | `src/msk_research_lab/api/workstation_ui.py:1225` | Verified |
| **F-03** | Motion API labels fallback fixture as `WEBCAM_LIVE_FRAME` | `src/msk_research_lab/motion/camera_service.py:116` | Verified |
| **F-04** | Fallback fixtures saved to `motion_assessments` as real measurements | `src/msk_research_lab/motion/camera_service.py:143` | Verified |
| **F-05** | Missing landmarks default to `(0,0)` returning 0° and `OPTIMAL` status | `src/msk_research_lab/motion/kinematics.py:117` | Verified |
| **F-06** | `DEFAULT_PEPPER` hardcoded; pseudonym hash doesn't protect plaintext `full_name` | `src/msk_research_lab/workstation/patient_manager.py:11` | Verified |
| **F-07** | `record_therapy_session` not fail-closed when clinical red flags active | `src/msk_research_lab/workstation/therapy_manager.py:113` | Verified |
| **F-08** | SOAP generator inserts deductive clinical assumptions without user documentation | `src/msk_research_lab/workstation/therapy_manager.py:75` | Verified |
| **F-09** | Prior tests only check HTTP 200, lack full browser interaction verification | `tests/integration/test_workstation_api.py` | Verified |
| **F-10** | InnerHTML interpolation in patient table vulnerable to DOM injection | `src/msk_research_lab/api/workstation_ui.py:841` | Verified |
| **F-11** | Authentic 3D models (watercmy, spacejohnlf, jicio) exist locally but bypassed by workstation UI | `3refs/upstream/` and `src/msk_research_lab/api/app.py` | Verified |
| **F-12** | Start scripts have hardcoded absolute personal paths | `start-msk.bat` and `start-msk.sh` | Verified |

---

## 4. Immediate Remediation Action Plan (P0 through P5)

- **P0:** Server-authoritative Red Flag hard-stop in `therapy_manager.py` and API; fix `camera_service.py` and `kinematics.py` to prevent fake measurements and reject degenerate geometry; add regression test suite `test_safety_p0_gates.py`.
- **P1:** Portable launcher scripts (`start-msk.sh` and `start-msk.bat`); verified database migration and component health reporting.
- **P2:** Real UI workflows: Complete DOM escaping (F-10), add patient View/Edit modal, fix SOAP preview/confirmation workflow, audit every visible button into `UI_ACTION_MATRIX.md`.
- **P3:** Webcam & kinematics epistemics: fail-closed camera probe, explicit DEMO mode separation, GUM uncertainty transparency.
- **P4:** Integrate authentic 3D models (`/api/v1/atlas/scene/*` and GLTFLoader.js), real muscle and meridian layer toggle in UI, camera reset, empty states when assets missing.
- **P5:** Secret pepper management, privacy threat model, comprehensive browser E2E test suite (E2E-01 through E2E-12), release gate signoff.
