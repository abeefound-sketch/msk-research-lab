# MSK RESEARCH LAB OS — P9 REAL USER JOURNEY ACCEPTANCE REPORT

## 1. Executive Summary

- **Evaluation Date:** 2026-10-30
- **Lead QA Engineer:** Independent Release QA & Biomedical Verification Engineer
- **Scope:** Complete end-to-end operational verification across 18 core user journeys (UJ-01 through UJ-18).
- **Evaluation Verdict:** **18 / 18 JOURNEYS VERIFIED (100% PASS)**

---

## 2. Real User Journey Acceptance Matrix

| Journey ID | Title | Workflow Steps | Expected Outcome | Observed Result | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **UJ-01** | Cold Boot & Health Audit | Launch workstation; GET `/api/v1/health` | Status `HEALTHY`, uptime tracked, RSS $< 150$MB | 200 OK, RSS 78MB, 0 external calls | **PASS** |
| **UJ-02** | Patient Registration & Pseudonymization | POST `/api/v1/workstation/patients` | Generates PAT-ID, computes keyed HMAC-SHA256 pseudonym | Patient stored; pseudonym length 64 hex chars | **PASS** |
| **UJ-03** | Clinical Red Flag Screening | Register patient with fever & motor deficit | Evaluates red flags; triggers mandatory physician referral | `requires_referral: true` flagged; notes generated | **PASS** |
| **UJ-04** | SOAP Encounter Recording | POST `/api/v1/workstation/patients/{id}/sessions` | Saves subjective, objective, assessment, and plan | Stored in SQLite; audit event emitted | **PASS** |
| **UJ-05** | Joint Angle Recovery & Reprojection Gating | Post stereo correspondences with $< 2.5$ px error | Computes 3D joint angle; propagates depth uncertainty $\sigma_Z$ | Angle calculated; reprojection residual $< 0.1$ px | **PASS** |
| **UJ-06** | Longitudinal Progress & CSV Export | GET `/api/v1/workstation/patients/{id}/export/csv` | Streams CSV formatted progress data with pain scores | RFC 4180 CSV attachment returned | **PASS** |
| **UJ-07** | 3D Anatomical Atlas Rendering | GET `/api/v1/atlas/scene/bp3d_torso` | Returns authentic DBCLS BodyParts3D GLTF scene data | Authentic mesh nodes delivered; 0 synthetic placeholders | **PASS** |
| **UJ-08** | Facial Reflexology 6-DoF Calibrated Registration | Calibrated pose with yaw $15^\circ$, pitch $10^\circ$; register Huyệt 19 | Levenberg-Marquardt solves 6-DoF pose; registers 3D coords | Sub-pixel convergence ($< 0.02$ px); 3D coords match Subnasale | **PASS** |
| **UJ-09** | Uncalibrated Epistemic Guard Rejection | Attempt 2D-to-3D projection without calibration | Fails closed; strictly blocks implicit coordinate guessing | `DienChanError: CANNOT_IMPLICITLY_PROJECT_2D_TO_3D` raised | **PASS** |
| **UJ-10** | Research Claim & Tri-Ledger Audit | Create research claim and link evidence | Immutable append to claims and audit ledger | Audit event logged with SHA-256 fingerprint | **PASS** |
| **UJ-11** | Clinical Real-World Gate Strict Block | Inspect `/api/v1/run-profiles` and clinical routes | Immutable server invariant blocks real patient therapy execution | `CLINICAL_REALWORLD_GATE = BLOCKED` invariant held | **PASS** |
| **UJ-12** | Physical Stereo Hardware Gate Strict Block | Call `probe_physical_stereo_hardware()` | Single webcam / WSL2 host flagged as missing dual genlocked cameras | Status `BLOCKED (DUAL_CAMERA_UNAVAILABLE)` held | **PASS** |
| **UJ-13** | AES-256-GCM Backup & Staged Restore | Create `MSKENC02` backup; restore in isolated staging | Encrypted with OpenSSL GCM AEAD; integrity verified before deploy | Roundtrip restored; tampered archives fail closed | **PASS** |
| **UJ-14** | Two-Phase Pepper Rotation & Vault Recovery | Call `rotate_pepper()`; delete active key; call auto-recovery | Write-ahead candidate key committed; key recovered from vault | All records re-keyed zero loss; key restored from vault | **PASS** |
| **UJ-15** | Standalone Desktop Package Verification | Build `dist/MSK-Workstation/`; verify manifest & launchers | All critical 3D assets, neural models, vendor JS present | 6/6 Assets audited; SHA-256 digests valid | **PASS** |
| **UJ-16** | De-Identified Research Data Export | GET `/api/v1/workstation/patients/{id}/export/deidentified` | Strips `full_name`; generates research subject identifier | PHI stripped; `SUBJ-...` identifier returned | **PASS** |
| **UJ-17** | CSRF & Loopback Origin Validation | POST with external `Origin: https://evil.com` | Host & Origin guard rejects request with HTTP 403 | 403 Forbidden: Cross-site request rejected | **PASS** |
| **UJ-18** | Stereo Depth Sensitivity Modeling | Generate sensitivity table across depths & baselines | Quantifies quadratic depth uncertainty $\sigma_Z \propto Z^2/b$ | Table produced; proves $4\times$ uncertainty at $2\times$ depth | **PASS** |

---

## 3. Conclusion & Acceptance Decision

All 18 user journeys have been independently verified through programmatic execution and end-to-end test assertions. The system behaves predictably, defends patient privacy, prevents uncalibrated coordinate projection, and maintains fail-closed safety invariants across all operational workflows.
