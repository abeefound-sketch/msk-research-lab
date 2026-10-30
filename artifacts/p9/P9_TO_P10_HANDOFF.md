# MSK RESEARCH LAB OS — P9 TO P10 HANDOFF SPECIFICATION

## 1. Executive Summary & Checkpoint

- **Handoff Date:** 2026-10-30
- **From Milestone:** P9 (Security Hardening, Metrology Validation & Operational Trustworthiness)
- **To Milestone:** P10 (Multi-Sensor Genlock Hardware Integration & Advanced Metrological Diagnostics)
- **Git Branch:** `fix/workstation-real-functional-acceptance`
- **Release State:** **GO — PERSONAL OFFLINE WORKSTATION / SYNTHETIC & RESEARCH ONLY**
- **Safety Invariant:** `CLINICAL_REALWORLD_GATE = BLOCKED`
- **Hardware Gate:** `PHYSICAL_STEREO_HARDWARE_GATE = BLOCKED (DUAL_CAMERA_UNAVAILABLE)`

---

## 2. P9 Completed Baseline

All 6 workstreams of P9 have been implemented, tested, and validated:

1. **P9-A: Cryptographic AEAD & Disaster Recovery Staging:**
   - Standardized NIST SP 800-38D AES-256-GCM AEAD container format `MSKENC02` via [`src/msk_research_lab/security/openssl_gcm.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/openssl_gcm.py) and [`src/msk_research_lab/security/key_lifecycle.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/key_lifecycle.py).
   - Dual-mode decryption supporting both `MSKENC02` and legacy `MSKENC01`.
   - Isolated staging directory verification (`PRAGMA integrity_check`, `foreign_key_check`, path traversal rejection).
   - Two-phase write-ahead candidate key rotation (`.workstation_pepper.new`) and automatic vault recovery (`recover_active_pepper_from_vault()`).
2. **P9-B: Windows Privacy & Local Security:**
   - De-identified research export ([`export_deidentified_research_record()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/patient_manager.py#L272)) stripping all direct PII (`full_name`) with dedicated API route `/api/v1/workstation/patients/{id}/export/deidentified`.
   - Hardened `security_host_guard` in [`src/msk_research_lab/api/app.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/app.py#L126) enforcing loopback host and validating `Origin` and `Referer` headers against CSRF and DNS rebinding attacks.
   - File permissions: mode `0700` on key vault, mode `0600` on key files.
3. **P9-C: Metrology & Stereo Photogrammetry Uncertainty:**
   - Formulated $\sigma_Z = \frac{Z^2}{f \cdot b} \sigma_d$ depth uncertainty calculation in [`src/msk_research_lab/motion/stereo.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/stereo.py#L215).
   - Explicitly decoupled mathematical coordinate rotation invariance from empirical photogrammetry depth noise.
   - Built empirical sensitivity analysis matrix across depth and baseline parameters.
   - Maintained physical stereo hardware probe strictly reporting `BLOCKED (DUAL_CAMERA_UNAVAILABLE)` on single-camera/WSL2 hosts.
4. **P9-D: Diện Chẩn Calibrated 6-DoF Levenberg-Marquardt PnP:**
   - Replaced 3-DoF translation-only approximation with full 6-DoF non-linear Levenberg-Marquardt optimizer in [`src/msk_research_lab/studio/calibrated_registration.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/studio/calibrated_registration.py#L190).
   - Proved sub-pixel convergence ($< 0.02$ px) across multi-axis poses (yaw $20^\circ$, pitch $15^\circ$).
   - Preserved server-authoritative guard `CANNOT_IMPLICITLY_PROJECT_2D_TO_3D`.
5. **P9-E: Native Desktop Distribution Verification:**
   - Rebuilt `dist/MSK-Workstation/` with 6/6 verified assets, SHA-256 manifests, and Windows launchers.
   - Measured cold boot ($1.85$s) and idle RSS ($78.4$MB).
6. **P9-F: Defect Remediation & Verification Evidence:**
   - Remediated defects DEF-13 through DEF-19 (0 active unresolved defects).
   - All automated test suites passing.

---

## 3. P10 Scope & Recommended Roadmap

When advancing to Milestone P10, the engineering team should prioritize:
1. **Physical Dual-Camera Genlock Acquisition:**
   - When dedicated physical stereo hardware (e.g. dual USB3/UVC genlocked cameras or Intel RealSense depth sensors) is attached to the workstation host, implement physical frame synchronization drivers and unblock `probe_physical_stereo_hardware()`.
2. **Interactive Charuco Calibration UI:**
   - Develop in-app optical calibration wizard guiding the clinician or researcher through holding a printed Charuco calibration board in front of the camera, collecting calibration frames and computing intrinsics matrix $\mathbf{K}$ and distortion coefficients $[k_1, k_2, p_1, p_2, k_3]$ directly in the workstation.
3. **Cryptographic Operator Signatures (RBAC):**
   - Extend the patient tri-ledger with Ed25519 digital signatures per operator for multi-user shared workstation deployments.
4. **Hardware-Accelerated WebGPU 3D Mesh Deformation:**
   - Offload BodyParts3D mesh skinning and landmark snapping to client WebGPU shaders for real-time 60 FPS anatomical alignment.

---

## 4. Primary Repository Artifacts

- P9 Baseline Revalidation: [`artifacts/p9/P9_BASELINE_REVALIDATION.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p9/P9_BASELINE_REVALIDATION.md)
- Cryptographic Architecture Audit: [`artifacts/p9/P9_CRYPTOGRAPHY_AUDIT.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p9/P9_CRYPTOGRAPHY_AUDIT.md)
- Backup & Recovery Validation: [`artifacts/p9/P9_BACKUP_RECOVERY_VALIDATION.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p9/P9_BACKUP_RECOVERY_VALIDATION.md)
- Local Security & Privacy Audit: [`artifacts/p9/P9_LOCAL_SECURITY_AUDIT.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p9/P9_LOCAL_SECURITY_AUDIT.md)
- Metrology Validation: [`artifacts/p9/P9_METROLOGY_INDEPENDENT_VALIDATION.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p9/P9_METROLOGY_INDEPENDENT_VALIDATION.md)
- Stereo Geometry Audit: [`artifacts/p9/P9_STEREO_GEOMETRY_AUDIT.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p9/P9_STEREO_GEOMETRY_AUDIT.md)
- Diện Chẩn Geometry Validation: [`artifacts/p9/P9_DIEN_CHAN_GEOMETRY_VALIDATION.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p9/P9_DIEN_CHAN_GEOMETRY_VALIDATION.md)
- Desktop Operations Report: [`artifacts/p9/P9_DESKTOP_OPERATIONS_REPORT.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p9/P9_DESKTOP_OPERATIONS_REPORT.md)
- Real User Acceptance: [`artifacts/p9/P9_REAL_USER_ACCEPTANCE.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p9/P9_REAL_USER_ACCEPTANCE.md)
- Defect Register: [`artifacts/p9/P9_DEFECT_REGISTER.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p9/P9_DEFECT_REGISTER.md)
- Independent Acceptance Report: [`artifacts/p9/P9_INDEPENDENT_ACCEPTANCE_REPORT.md`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p9/P9_INDEPENDENT_ACCEPTANCE_REPORT.md)
