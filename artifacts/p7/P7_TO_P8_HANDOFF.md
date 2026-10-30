# MSK Research Lab OS — P7 to P8 Engineering Handoff

**Date:** 2026-10-30  
**Version:** v3.2 Personal Offline Workstation — P7 Operational Readiness  
**Git Branch:** `fix/workstation-real-functional-acceptance`  
**Base Commit:** `28240e6`  
**P7 Acceptance Verdict:** **`GO — PERSONAL OFFLINE / SYNTHETIC ONLY`**  
**Clinical Safety Boundary:** **`CLINICAL_REALWORLD_GATE = BLOCKED`** (Strictly Enforced Invariant)  

---

## 1. Executive Summary & Current Operational State

The P7 cycle has advanced MSK Research Lab OS from functional acceptance to **full operational readiness**. The workstation operates deterministically in both native Windows CMD and Linux/WSL environments without requiring internet access or external cloud services.

### Verified Capabilities
1. **Launch & Diagnostics:** Portable zero-config launchers (`start-msk.bat`, `start-msk.sh`) with dependency auto-detection and graceful cross-environment bridging.
2. **Interactive Controls:** All 49 UI controls verified on the running workstation with SQLite write and browser reload persistence (`49/49 VERIFIED`).
3. **Automated Testing:** 191/191 repository tests passing (100%), including 4 new dedicated operational readiness tests.
4. **Defect Remediation:** 8 total defects resolved (DEF-01 through DEF-04 in P6; DEF-05 through DEF-08 in P7).
5. **Metrological Integrity:** Four-way explicit provenance tagging (`LIVE_MEASURED`, `SYNTHETIC_TEST`, `NOT_MEASURABLE`, `INVALID_INPUT`). Low-visibility landmark propagation into ISO GUM uncertainty budgets. Explicit disclaimers separating 2D camera estimates from clinical 3D goniometry.
6. **3D Atlas Grounding:** Elimination of mock cylinder geometry fallbacks. Visibility toggles directly manipulate genuine Three.js scene graphs.
7. **Clinical Safety:** Permanent server-authoritative hard stop for red-flag patients (HTTP 400). Zero physical device actuation commands. Zero automatic clinical diagnosis.

---

## 2. P7 Deliverables Directory Manifest (`artifacts/p7/`)

All P7 verification artifacts and evidence are preserved under [`artifacts/p7/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7):

1. [`artifacts/p7/P7_BASELINE_AND_EVIDENCE_REVIEW.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/P7_BASELINE_AND_EVIDENCE_REVIEW.md) — Git audit, P6 evidence review, and 49-control evidence matrix.
2. [`artifacts/p7/P7_REAL_WORKFLOW_MATRIX.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/P7_REAL_WORKFLOW_MATRIX.md) — End-to-end verification of 12 real user workflows.
3. [`artifacts/p7/P7_DEFECT_REGISTER.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/P7_DEFECT_REGISTER.md) — Comprehensive log of defects DEF-01 through DEF-08 with root cause analysis.
4. [`artifacts/p7/P7_MOTION_METROLOGY_AUDIT.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/P7_MOTION_METROLOGY_AUDIT.md) — In-depth metrological audit of 2D kinematics, GUM budget, and MediaPipe Tasks.
5. [`artifacts/p7/P7_ATLAS_ASSET_AUDIT.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/P7_ATLAS_ASSET_AUDIT.md) — 3D asset inventory, SHA-256 digests, licenses, and Diện Chẩn 2D guards.
6. [`artifacts/p7/P7_SECURITY_PRIVACY_AUDIT.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/P7_SECURITY_PRIVACY_AUDIT.md) — Threat model, HMAC pseudonymization, CSV/XSS injection, and red flag enforcement.
7. [`artifacts/p7/P7_OFFLINE_INSTALLATION_REPORT.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/P7_OFFLINE_INSTALLATION_REPORT.md) — Launcher portability, SQLite WAL safety, backup/restore, and memory footprint.
8. [`artifacts/p7/P7_TEST_RESULTS.json`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/P7_TEST_RESULTS.json) — Consolidated test results (191 tests passed).
9. [`artifacts/p7/P7_INDEPENDENT_ACCEPTANCE_REPORT.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/P7_INDEPENDENT_ACCEPTANCE_REPORT.md) — Comprehensive final acceptance report.
10. [`artifacts/p7/p7_blackbox_runner.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/p7_blackbox_runner.py) — Live automated audit script for 49 controls.
11. [`artifacts/p7/p7_blackbox_results.json`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/p7_blackbox_results.json) — Structured execution results for all 49 controls.
12. [`artifacts/p7/p7_workstation_screenshot.png`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/p7_workstation_screenshot.png) — Headless Google Chrome 1366x768 live UI capture.
13. [`artifacts/p7/p7_chrome_rendered_dom.html`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/p7_chrome_rendered_dom.html) — Headless Google Chrome rendered DOM dump.
14. [`artifacts/p7/p7_pytest_full.txt`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p7/p7_pytest_full.txt) — Execution log of 191 repository tests.

---

## 3. Recommended P8 Scope & Roadmap

Based strictly on remaining gaps verified during P7, the following work items are recommended for **P8: Enterprise Hardening & Metrological Multi-View Calibration**:

1. **Multi-Camera Stereo Photogrammetry (P8-A):**
   - Extend the motion pipeline from single monocular 2D video to calibrated dual-camera stereo capture (e.g. frontal + sagittal) to eliminate out-of-plane yaw foreshortening confounders.
2. **Calibrated Bi-Planar Diện Chẩn 3D Registration (P8-B):**
   - Implement photogrammetric camera calibration using checkerboard/ChArUco targets to establish mathematically sound 2D-to-3D projection for Diện Chẩn facial points, satisfying the `ATLAS-06` epistemic guard.
3. **Database Key Versioning & HMAC Pepper Migration Tooling (P8-C):**
   - Add a `pepper_version` schema column and implement an atomic CLI command (`msk-admin rotate-pepper`) to re-encrypt and update `pseudonym_hash` records seamlessly.
4. **Native Desktop Packaging (P8-D):**
   - Bundle Python, Uvicorn, and Chromium/WebKit into a single self-contained executable (using PyInstaller + Neutralinojs/Tauri) for one-click installation on non-developer Windows machines.

---

## 4. Operational Invariant Reminders for P8 Engineers

1. **Offline-First:** Under no circumstances should runtime telemetry, remote crash reporting, or external web fonts/CDNs be introduced.
2. **Safety Hard-Stop:** `CLINICAL_REALWORLD_GATE = BLOCKED` must never be bypassed without formal institutional review board (IRB) and medical device software safety certification.
3. **Attribution & Provenance:** Never represent synthetic data as live recordings, and never substitute mock geometric primitives for missing anatomical assets.
