# MSK RESEARCH LAB OS — P10 TO P11 HANDOFF SPECIFICATION

## 1. Executive Checkpoint & Provenance

- **Handoff Date:** 2026-10-30
- **From Milestone:** P10 (Independent Release Challenge, Windows Operational Proof & Scientific Integrity)
- **To Milestone:** P11 (Physical Multi-Sensor Genlock Hardware Integration & Multi-User Workstation Deployments)
- **Git Branch:** `fix/workstation-real-functional-acceptance`
- **Release Verdict:** **GO — PERSONAL OFFLINE WORKSTATION / SYNTHETIC & RESEARCH ONLY**
- **Safety Invariant:** `CLINICAL_REALWORLD_GATE = BLOCKED`
- **Hardware Invariant:** `PHYSICAL_STEREO_HARDWARE_GATE = BLOCKED (DUAL_CAMERA_UNAVAILABLE)`

---

## 2. Completed P10 Engineering Baseline

All six workstreams of Milestone P10 have been independently verified, remediated, and integrated:

1. **Workstream P10-G0: Independent Baseline Reproduction & Evidence Chain**
   - Independently verified the 241 passing tests from P9 in 265s.
   - Identified and audited the Starlette testclient deprecation warning.
   - Documented in [`artifacts/p10/P10_BASELINE_EVIDENCE_CHALLENGE.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_BASELINE_EVIDENCE_CHALLENGE.md).
2. **Workstream P10-A: Cryptography, Privacy & Local Attack Surface**
   - **DEF-20:** Corrected FIPS claims via `probe_fips_status()` in [`src/msk_research_lab/security/openssl_gcm.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/openssl_gcm.py); accurately reporting NIST SP 800-38D standard alignment with non-FIPS default provider.
   - **DEF-21:** Implemented clinical free-text pattern scrubber (`scrub_phi_from_text()`) in [`src/msk_research_lab/workstation/patient_manager.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/patient_manager.py); aggregated age $> 89$ to `"90+"`; labeled export `NOT_CERTIFIED_FOR_PHI`.
   - **DEF-22:** Implemented native Windows NTFS DACLs using `icacls.exe` in [`src/msk_research_lab/security/permissions.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/permissions.py).
   - **DEF-26:** Upgraded loopback parsing in [`src/msk_research_lab/api/app.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/app.py) to support IPv6 `[::1]` and reject state-changing `Origin: null` CSRF attempts.
   - Verified via `tests/integration/test_p10_adversarial_security.py` (7/7 pass).
3. **Workstream P10-B: Crash-Consistent Data Durability & Fault Injection**
   - **DEF-23:** Replaced `conn.executescript()` in [`src/msk_research_lab/core/migrations.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/core/migrations.py) with statement splitting and transactional savepoint blocks, ensuring clean atomic rollback on multi-statement migration failure.
   - Added automatic unlinking of candidate key file (`.workstation_pepper.new`) on transaction error in [`src/msk_research_lab/security/key_lifecycle.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/key_lifecycle.py).
   - Verified via `tests/integration/test_p10_disaster_fault_injection.py` (4/4 pass).
4. **Workstream P10-C: Metrology & Scientific Geometry Challenge**
   - **DEF-24:** Corrected reference landmark depth in 2D-to-3D ray projection to use true rotated camera-space depth $Z_{cam} = (\mathbf{R}\mathbf{X}_{ref} + \mathbf{t})_z$ in [`src/msk_research_lab/studio/calibrated_registration.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/studio/calibrated_registration.py).
   - **DEF-25:** Added 3D spatial variance / collinearity detection in `estimate_rigid_pose_from_landmarks()`, failing closed if landmarks lack 2D/3D variance.
   - Added `evaluate_focal_length_depth_sensitivity()` in [`src/msk_research_lab/motion/stereo.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/stereo.py).
   - Verified via `tests/unit/test_p10_metrology_degeneracy.py` (4/4 pass).
5. **Workstream P10-D: Clean Windows Release and Usability Proof**
   - Rebuilt [`dist/MSK-Workstation/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/dist/MSK-Workstation) with 6/6 verified assets, SHA-256 manifests, and Windows launchers.
   - Verified all 49 interactive controls in [`artifacts/p10/P10_UI_ACTION_MATRIX.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_UI_ACTION_MATRIX.md).
6. **Workstream P10-E: Anti-Self-Certification & Supply Chain Assurance**
   - Executed negative fault injection tests and compiled third-party SBOM/licensing inventory in [`artifacts/p10/P10_INDEPENDENT_TEST_VALIDITY_AND_RELEASE_PROVENANCE.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_INDEPENDENT_TEST_VALIDITY_AND_RELEASE_PROVENANCE.md).

---

## 3. Recommended P11 Backlog & Technical Priorities

For Milestone P11, incoming engineering teams should advance:
1. **Physical Dual-Camera Genlock Synchronization:**
   - Implement native UVC/USB3 hardware frame capture with hardware genlock synchronization when dual physical cameras or depth sensors (e.g. Intel RealSense) are physically connected to the host.
2. **Interactive Optical Calibration Wizard (Charuco Board):**
   - Provide an in-app visual calibration tool to capture multiple orientations of a printed Charuco board to calibrate camera intrinsics $\mathbf{K}$ and lens distortion parameters $[k_1, k_2, p_1, p_2, k_3]$.
3. **Multi-User Cryptographic Role-Based Access Control (RBAC):**
   - Introduce Ed25519 operator signatures for multi-clinician / multi-researcher workstation deployments.
4. **Client-Side WebGPU Mesh Acceleration:**
   - Offload BodyParts3D mesh skinning and landmark snapping to client WebGPU shaders for real-time 60 FPS anatomical alignment.

---

## 4. Primary Repository Artifacts Directory

- Baseline Evidence Challenge: [`artifacts/p10/P10_BASELINE_EVIDENCE_CHALLENGE.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_BASELINE_EVIDENCE_CHALLENGE.md)
- Cryptography & Privacy Security Report: [`artifacts/p10/P10_CRYPTO_PRIVACY_SECURITY_REPORT.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_CRYPTO_PRIVACY_SECURITY_REPORT.md)
- Data Durability & Disaster Recovery: [`artifacts/p10/P10_DATA_DURABILITY_AND_DISASTER_RECOVERY.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_DATA_DURABILITY_AND_DISASTER_RECOVERY.md)
- Metrology & Geometry Challenge: [`artifacts/p10/P10_METROLOGY_GEOMETRY_INDEPENDENT_CHALLENGE.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_METROLOGY_GEOMETRY_INDEPENDENT_CHALLENGE.md)
- Clean Windows Release Acceptance: [`artifacts/p10/P10_CLEAN_WINDOWS_RELEASE_ACCEPTANCE.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_CLEAN_WINDOWS_RELEASE_ACCEPTANCE.md)
- Test Validity & Release Provenance: [`artifacts/p10/P10_INDEPENDENT_TEST_VALIDITY_AND_RELEASE_PROVENANCE.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_INDEPENDENT_TEST_VALIDITY_AND_RELEASE_PROVENANCE.md)
- Defect Register (DEF-20 to DEF-26): [`artifacts/p10/P10_DEFECT_REGISTER.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_DEFECT_REGISTER.md)
- UI Action Matrix (49 controls): [`artifacts/p10/P10_UI_ACTION_MATRIX.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_UI_ACTION_MATRIX.md)
- Independent Release Decision: [`artifacts/p10/P10_INDEPENDENT_RELEASE_DECISION.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_INDEPENDENT_RELEASE_DECISION.md)
- Handoff Specification: [`artifacts/p10/P10_TO_P11_HANDOFF.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p10/P10_TO_P11_HANDOFF.md)
