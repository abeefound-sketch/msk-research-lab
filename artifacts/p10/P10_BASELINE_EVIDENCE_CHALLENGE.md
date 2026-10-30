# MSK Research Lab OS — P10 Baseline Evidence Challenge

**Evaluation Date:** 2026-10-30  
**Evaluator:** Principal Software Architect, Applied Cryptography Security Auditor, Biomedical Metrology Verification Engineer, Desktop QA Engineer, and Independent Release Auditor  
**Workspace:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`)  
**Starting Checkpoint Audited:** Git Commit [`7e62b10`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab) on branch `fix/workstation-real-functional-acceptance`  
**Baseline Reproduction Verdict:** **VERIFIED (241 PASSED, 0 FAILED, 1 WARNING)**  
**Safety Invariant:** `CLINICAL_REALWORLD_GATE = BLOCKED`  
**Stereo Invariant:** `PHYSICAL_STEREO_HARDWARE_GATE = BLOCKED (DUAL_CAMERA_UNAVAILABLE)`  

---

## 1. Executive Summary

Milestone P10 independently evaluated the claims asserted at the conclusion of Milestone P9 (Commit [`7e62b10`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab)). P10 operated under an adversarial verification mandate: rather than accepting previous pass rates at face value, every subsystem was probed for edge-case vulnerabilities, mathematical simplifications, uncertified compliance assertions, and fault recovery failures.

### Key Audit Findings:
1. **Baseline Reproduction:**
   - The reported 241 passed tests from P9 were independently executed and reproduced with 100% precision (`241 passed, 1 warning in 265.07s`).
   - The single warning was identified: `StarletteDeprecationWarning: Using 'httpx' with 'starlette.testclient' is deprecated; install 'httpx2' instead.`
2. **Identification of 7 Latent Engineering & Compliance Defects (DEF-20 to DEF-26):**
   - **DEF-20 (HIGH):** Overbroad FIPS compliance claim when using default system `libcrypto` without CMVP validation.
   - **DEF-21 (HIGH):** Incomplete Safe Harbor de-identification: unscrubbed clinical free-text notes, unaggregated age > 89, specific occupations.
   - **DEF-22 (HIGH):** Non-enforcement of native Windows NTFS DACLs on cryptographic keys (`os.chmod 0600/0700` ineffective on Windows).
   - **DEF-23 (HIGH):** Non-atomic migration execution via `sqlite3.executescript()`, risking permanent schema corruption on multi-statement migration failures.
   - **DEF-24 (HIGH):** Reference landmark depth calculation error in 2D-to-3D ray projection under rotated camera frames ($Z_{cam} \neq t_z + ref\_3d[2]$).
   - **DEF-25 (MEDIUM):** Unconstrained rotation in 6-DoF Levenberg-Marquardt PnP when input landmarks are collinear.
   - **DEF-26 (MEDIUM):** IPv6 loopback `[::1]` parsing defect in `security_host_guard` due to colon splitting.

---

## 2. Independent Test Baseline Reproduction Matrix

| Metric | P9 Claim | P10 Independent Reproduction | Discrepancy / Evidence |
| :--- | :--- | :--- | :--- |
| **Git Branch** | `fix/workstation-real-functional-acceptance` | `fix/workstation-real-functional-acceptance` | Exact match |
| **Commit HEAD** | `7e62b10` | `7e62b10` | Verified via `git log -n 1` |
| **Test Count** | 241 Passed | 241 Passed | Exact reproduction |
| **Failed Tests** | 0 | 0 | 0 failures |
| **Warnings** | 1 Warning | 1 Warning | Starlette deprecation warning confirmed |
| **Clinical Gate** | `BLOCKED` | `BLOCKED` | Server invariant confirmed |
| **Stereo Gate** | `BLOCKED` | `BLOCKED (DUAL_CAMERA_UNAVAILABLE)` | Hardware probe confirmed |
| **2D->3D Guard** | Fail-Closed | Fail-Closed | `CANNOT_IMPLICITLY_PROJECT_2D_TO_3D` verified |

---

## 3. Workstation Packaging & Asset Lineage

The standalone Windows desktop package [`dist/MSK-Workstation/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/dist/MSK-Workstation) was inspected and re-verified:

| Asset Name | Expected SHA-256 | Actual SHA-256 | Status |
| :--- | :--- | :--- | :---: |
| `watercmy_anatomy_glb` | `318347f9...` | `318347f9...` | **VALID** |
| `spacejohnlf_body_glb` | `0886b6a0...` | `0886b6a0...` | **VALID** |
| `pose_landmarker_lite` | `59929e1d...` | `59929e1d...` | **VALID** |
| `vendor_three_js` | `9274bbce...` | `9274bbce...` | **VALID** |
| `vendor_gltf_loader` | `d073b438...` | `d073b438...` | **VALID** |
| `vendor_orbit_controls` | `02bb4ade...` | `02bb4ade...` | **VALID** |

All 6/6 critical assets match their expected cryptographic digests.
