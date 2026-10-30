# P11 DEFECT REGISTER (DEF-27 TO DEF-32)
**MSK Research Lab OS — Milestone P11 Remediation Log**

- **Audit Date:** 2026-10-30
- **Auditor:** Biomedical Software Safety & Verification Engineers
- **Status:** ALL DEF-27 THROUGH DEF-32 REMEDIATED & VERIFIED

---

### DEF-27: Non-Atomic Database File Overwrite During Backup Restoration
- **Severity:** HIGH
- **Discovered In:** `src/msk_research_lab/security/key_lifecycle.py`
- **Root Cause:** Direct `shutil.copy2` over destination database files in `restore_encrypted_backup()`. An interrupted restoration could leave `lab.sqlite3` truncated or corrupted.
- **Remediation:** Staged copy to randomly named temporary file (`.{name}.tmp.{token}`) followed by atomic `os.replace` within target restore directory.
- **Verification:** [`test_def27_atomic_restore_preserves_integrity`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p11_security_durability.py#L37) in `test_p11_security_durability.py`.

---

### DEF-28: Brown-Conrady Lens Distortion Uncompensated in Ray-Surface Projection
- **Severity:** HIGH
- **Discovered In:** `src/msk_research_lab/studio/calibrated_registration.py`
- **Root Cause:** 2D pixel coordinates were mapped directly to normalized camera coordinates $(u - c_x)/f_x$ without inverting lens distortion. Peripheral reflexology points suffered $> 3$ mm radial positional distortion.
- **Remediation:** Integrated fixed-point `undistort_normalized_point()` in back-projection and `distort_normalized_point()` in forward projection in `calibrated_registration.py`.
- **Verification:** [`test_distortion_compensation_roundtrip_oracle`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_p11_metrology_oracle.py#L48) and [`test_calibrated_registration_with_distortion_compensation`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_p11_metrology_oracle.py#L112).

---

### DEF-29: Incomplete Textual Dates, Postal Codes, and MRN PHI Scrubbing
- **Severity:** HIGH
- **Discovered In:** `src/msk_research_lab/workstation/patient_manager.py`
- **Root Cause:** Free-text scrubber only matched numeric dates (`MM/DD/YYYY`). Spelled-out dates (e.g. `October 14, 2024`), MRNs (`MRN: 98765432`), IPv4 addresses, and postal codes were unscrubbed, and exports lacked explicit regex limitation disclosures.
- **Remediation:** Expanded regex patterns in `scrub_phi_from_text()` and added `regex_based_scrubbing_only: True` and `not_anonymized_guaranteed: True` to export records.
- **Verification:** [`test_def29_enhanced_phi_scrubbing_textual_dates_mrn_ip_zip`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p11_security_durability.py#L58) and [`test_def29_safe_harbor_export_metadata_flags`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p11_security_durability.py#L88).

---

### DEF-30: Missing Standardized Provenance Classification
- **Severity:** MEDIUM
- **Discovered In:** `src/msk_research_lab/scientific/provenance.py`
- **Root Cause:** No unified four-state enumeration (`LIVE_MEASURED`, `SYNTHETIC_TEST`, `NOT_MEASURABLE`, `INVALID_INPUT`) across kinematic and reflexology modules.
- **Remediation:** Created `src/msk_research_lab/scientific/provenance.py` defining `MeasurementProvenanceType` and `build_measurement_provenance()` helper, tagging all kinematic assessments and 3D registrations.
- **Verification:** [`test_def30_uniform_measurement_provenance_types`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p11_security_durability.py#L107).

---

### DEF-31: Windows Security Descriptor Failure When `USERNAME` is Unset
- **Severity:** MEDIUM
- **Discovered In:** `src/msk_research_lab/security/permissions.py`
- **Root Cause:** `secure_file_permissions()` and `secure_directory_permissions()` relied solely on `os.environ.get("USERNAME")`. In headless or service environments without this variable, `icacls` was skipped entirely.
- **Remediation:** Implemented multi-tier fallback `get_current_windows_identity()` resolving environment variables, `getpass.getuser()`, `ctypes.windll.advapi32.GetUserNameW`, and default `*S-1-3-4` SID.
- **Verification:** [`test_def31_windows_identity_resolution_fallback`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p11_security_durability.py#L131).

---

### DEF-32: 6-DoF Levenberg-Marquardt Ill-Conditioning and Coplanarity Non-Disclosure
- **Severity:** MEDIUM
- **Discovered In:** `src/msk_research_lab/studio/calibrated_registration.py`
- **Root Cause:** Near-coplanar landmark sets could suffer from depth ambiguity (Necker reversal) without computing spatial condition numbers or planarity metrics.
- **Remediation:** Added `compute_landmark_spatial_conditioning()` to compute 3D landmark spatial covariance eigenvalues $\lambda_1, \lambda_2, \lambda_3$, condition number $\kappa$, and planarity ratio $\rho$, exposing them on `OpticalCalibrationContext`.
- **Verification:** [`test_spatial_conditioning_eigenvalues_and_coplanarity`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_p11_metrology_oracle.py#L31).
