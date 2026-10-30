# MSK Research Lab OS — P9-G0 Independent Baseline Revalidation

**Revalidation Date:** 2026-10-30  
**Audit Role:** Principal Software Architect, Applied Cryptography Security Engineer, Biomedical Safety Auditor, and Independent Release QA  
**Checkpoint Audited:** Commit [`844743d`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab) on branch `fix/workstation-real-functional-acceptance` (Code Base: [`4b8c95a`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab), Parent: [`4db570a`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab))  
**Verdict:** **`PASS — BASELINE CONFIRMED; CRITICAL GAPS IDENTIFIED FOR P9`**  
**Clinical Safety Invariant:** **`CLINICAL_REALWORLD_GATE = BLOCKED`** (Strictly Enforced Invariant)  
**Hardware Stereo Gate:** **`BLOCKED (DUAL_CAMERA_UNAVAILABLE)`**  

---

## 1. Git State, Working Tree & Lineage Verification

1. **Commit History:**
   - Commit `844743d`: Mirrored P8 handoffs and cumulative handoff to `2data/handoff md/`.
   - Commit `4b8c95a`: P8 native packaging, key lifecycle, metrological calibration, stereo kinematics, and calibrated facial registration.
   - Commit `4db570a`: P7 operational readiness baseline.
2. **Tracked Source Tree:** Clean working tree for all production code in `src/msk_research_lab/`, test suites in `tests/`, and distribution scripts in `packaging/`.
3. **P8 Deliverables Completeness Audit:** All 11 required P8 artifacts confirmed present in `artifacts/p8/` and mirrored in `2data/handoff md/`:
   - `P8_BASELINE_AUDIT.md`: Present (4,587 bytes)
   - `P8_DESKTOP_PACKAGING_REPORT.md`: Present (6,042 bytes)
   - `P8_KEY_MANAGEMENT_AUDIT.md`: Present (4,931 bytes)
   - `P8_METROLOGY_VALIDATION.md`: Present (4,200 bytes)
   - `P8_STEREO_FEASIBILITY_REPORT.md`: Present (4,136 bytes)
   - `P8_DIEN_CHAN_REGISTRATION_REPORT.md`: Present (4,579 bytes)
   - `P8_REAL_USER_ACCEPTANCE.md`: Present (12,776 bytes)
   - `P8_DEFECT_REGISTER.md`: Present (6,361 bytes)
   - `P8_TEST_RESULTS.json`: Present (2,903 bytes, 214 passed)
   - `P8_INDEPENDENT_ACCEPTANCE_REPORT.md`: Present (9,098 bytes)
   - `P8_TO_P9_HANDOFF.md`: Present (5,445 bytes)

---

## 2. Invariant & Safety Gate Verification

- **Clinical Real-World Gate:** Permanent server invariant in `src/msk_research_lab/api/workstation_routes.py` returning `BLOCKED` with reason `"Educational and synthetic workstation only. No automated diagnosis or clinical deployment."`
- **Stereo Hardware Gate:** `probe_physical_stereo_hardware()` returns `BLOCKED (DUAL_CAMERA_UNAVAILABLE)` on single-camera/WSL2 hosts.
- **Loopback Enforcement:** `security_host_guard` middleware strictly rejects non-loopback HTTP `Host` headers with HTTP 403 Forbidden.
- **Epistemic Reflexology Guard:** `attempt_project_2d_to_3d()` raises `DienChanError("CANNOT_IMPLICITLY_PROJECT_2D_TO_3D")` whenever calibration context is absent.

---

## 3. Critical Unverified Assumptions & Engineering Gaps Identified for P9

The P9 audit identifies the following specific vulnerabilities and engineering gaps that must be remediated in P9:

| Domain | Current Implementation in P8 | Identified Vulnerability / Defect | Remediation Objective | Target Workstream |
|---|---|---|---|---|
| **Cryptography** | Custom PBKDF2-HMAC-CTR/XOR stream cipher in `key_lifecycle.py` (`MSKENC01`). | Custom stream cipher risks; lack of standardized AEAD (AES-256-GCM / ChaCha20-Poly1305). | Migrate to standard OpenSSL EVP AES-256-GCM (`MSKENC02`) with dual-format backwards compatibility. | **P9-A** |
| **Fault Injection** | `rotate_pepper()` commits in single transaction, but file rotation happens after DB commit. | Power loss / crash between DB update and `.workstation_pepper` file replacement leaves mismatched active key. | Implement atomic two-phase write-ahead rollback journal for keys. | **P9-A** |
| **Restore Staging** | `restore_encrypted_backup()` extracts into target directory before SQLite integrity check. | Malformed or corrupted archives could overwrite or corrupt existing valid databases. | Implement isolated temporary staging directory; verify MAC, schema, and `PRAGMA integrity_check` before atomic swap. | **P9-A** |
| **Privacy / Local** | `patients` table stores `full_name` in plaintext alongside `pseudonym_hash`. | External export or database inspection leaks direct PII. | Implement strict de-identified research export view redacting `full_name`. | **P9-B** |
| **Local Security** | `security_host_guard` checks Host header, but lacks Origin/Referer CSRF check. | Malicious website opened in user's browser could forge cross-origin POST requests to loopback. | Add Origin / Referer validation for state-modifying requests (`POST`, `PUT`, `DELETE`). | **P9-B** |
| **Metrology / Stereo** | P8 report claimed 3D angle is immune to yaw foreshortening. | Mathematical vector angle coordinate invariance was conflated with real measurement accuracy; depth uncertainty $\sigma_Z \propto Z^2 / (f \cdot b)$ degrades under yaw and occlusion. | Separate mathematical coordinate invariance from empirical stereo measurement accuracy with formal depth uncertainty analysis. | **P9-C** |
| **Registration / PnP** | `estimate_rigid_pose_from_landmarks()` assumes $R = I$ and solves only translation $t$ ($2N \times 3$). | 3-DoF solver fails when head is tilted or rotated in yaw/pitch/roll ($> 3^\circ$ rotation causes residual failure). | Implement true 6-DoF Levenberg-Marquardt PnP pose estimator solving $(R, t) \in \mathrm{SE}(3)$. | **P9-D** |
| **Desktop Operations** | Launch scripts verified on dev tree. | Package extracted to fresh clean directory needs standalone execution and rollback verification. | Validate clean extracted package behavior, memory footprint, and rollback. | **P9-E** |

---

## 4. P9-G0 Baseline Gate Decision

**P9-G0 Baseline Status:** **`PASS — BASELINE ACCEPTED`**  
All P8 historical claims are confirmed reproducible. Proceed immediately to **P9-A (Cryptography & Backup Security Hardening)** as the highest-priority critical workstream.
