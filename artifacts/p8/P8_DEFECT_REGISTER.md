# MSK Research Lab OS — P8 Defect Register

**Date:** 2026-10-30  
**Status:** **`ALL DEFECTS RESOLVED (DEF-01 through DEF-12)`**  
**Role:** Biomedical Software Safety Engineer, Systems Architect, and Independent Release QA  

---

## 1. Cumulative Defect Register (P6 → P8)

| Defect ID | Severity | Discovery Phase | Description | Root Cause | Remediated In | Verification Status |
|---|---|---|---|---|---|---|
| **DEF-01** | HIGH | P6 Black-box | `start-msk.bat` crashed during execution | Batch syntax error in label jumping and conditional execution | `start-msk.bat` | **RESOLVED** |
| **DEF-02** | HIGH | P6 Vision | MediaPipe 1.0+ Tasks API integration failed | Transition from deprecated Solutions API to Pose Landmarker Lite task model | `camera_service.py` | **RESOLVED** |
| **DEF-03** | MEDIUM | P6 Kinematics | Landmark coordinate indexing mismatch | Tuple vs dict landmark representations in MediaPipe | `kinematics.py` | **RESOLVED** |
| **DEF-04** | MEDIUM | P6 Therapy | Modality string vs dict mismatch in SOAP generation | String formatting assumed plain strings instead of modality dictionaries | `therapy_manager.py` | **RESOLVED** |
| **DEF-05** | MEDIUM | P7 Operational | 3D Atlas fallback substitution substituted mock cylinder | UI rendered fake geometry on model loading error | `workstation_ui.py` | **RESOLVED** |
| **DEF-06** | MEDIUM | P7 Operational | FTS5 search query syntax crash and fake citations | Unsanitized query tokens and dummy fallback citation rows | `app.py`, `fts_store.py` | **RESOLVED** |
| **DEF-07** | HIGH | P7 Metrology | Webcam resource leak on error & unverified provenance | Missing `try ... finally: cap.release()` and missing 4-way data provenance | `camera_service.py` | **RESOLVED** |
| **DEF-08** | LOW | P7 Launcher | `start-msk.bat` failed to forward CLI arguments to WSL | Argument forwarding (`%*`) missing in WSL invocation path | `start-msk.bat` | **RESOLVED** |
| **DEF-09** | MEDIUM | P8 Packaging | Insecure Database Storage Path in Desktop Mode | Hardcoded `2data/db/` caused permission failures when installed to protected desktop locations | `config.py`, `db.py` | **RESOLVED** |
| **DEF-10** | HIGH | P8 Security | Unversioned HMAC Pepper with Rotation Data Loss | Rotating secret pepper invalidated historical patient pseudonym hashes with no audit trail | `migrations.py`, `key_lifecycle.py` | **RESOLVED** |
| **DEF-11** | MEDIUM | P8 Performance | Pure Python CTR Byte-by-Byte Keystream Execution Bottleneck | Iterating byte-by-byte in Python across 10MB tar archives took 35+ seconds | `key_lifecycle.py` | **RESOLVED** |
| **DEF-12** | HIGH | P8 Calibration | Non-Coplanar PnP Depth Ambiguity in Facial Landmark Registration | 2D scale heuristic failed to account for 3D facial depth variation between Sellion and Tragion | `calibrated_registration.py` | **RESOLVED** |

---

## 2. Detailed Technical Remediation for P8 Defects

### DEF-09: Insecure Database Storage Path in Desktop Mode
- **Impact:** Non-administrative desktop users installing to `C:\Program Files\MSKResearchLab\` suffered permission crashes on database writes.
- **Fix:** Implemented `get_desktop_user_data_dir()` and `MSK_STORAGE_MODE=desktop` in [`src/msk_research_lab/core/config.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/core/config.py). Persists SQLite database to `%LOCALAPPDATA%\MSKResearchLab\db\lab.sqlite3` with fallback to portable repository storage.
- **Test:** Verified in [`tests/integration/test_p8_desktop_packaging.py::test_storage_mode_desktop`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p8_desktop_packaging.py).

### DEF-10: Unversioned HMAC Pepper with Rotation Data Loss
- **Impact:** Rotating secret pepper permanently orphaned patient pseudonym hashes, preventing patient lookups.
- **Fix:** Added database Migration 10 in [`src/msk_research_lab/core/migrations.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/core/migrations.py) adding `pepper_version` to `patients`, creating `pepper_key_store` and `pepper_rotation_log`. Implemented atomic re-keying in [`src/msk_research_lab/security/key_lifecycle.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/key_lifecycle.py).
- **Test:** Verified in [`tests/integration/test_p8_security_key_lifecycle.py::test_rotate_pepper_zero_record_loss`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p8_security_key_lifecycle.py).

### DEF-11: Pure Python CTR Keystream Performance Bottleneck
- **Impact:** Generating keystream byte-by-byte in Python for large archives took $>35$ seconds, hanging background backups.
- **Fix:** Vectorized keystream generation using 64-bit integer XOR (`int.from_bytes` / `to_bytes`), dropping 10MB processing time to $<0.25$ seconds. Added `include_originals` parameter defaulting to database-only disaster snapshots.
- **Test:** Verified in [`tests/integration/test_p8_security_key_lifecycle.py::test_encrypted_backup_and_restore`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p8_security_key_lifecycle.py).

### DEF-12: Non-Coplanar PnP Depth Ambiguity in Facial Landmark Registration
- **Impact:** PnP pose estimation residual exceeded tolerance ($14.9$ px vs $3.0$ px limit) due to depth difference between Tragion ($Z=-38$ mm) and Subnasale ($Z=+20$ mm).
- **Fix:** Replaced 2D scale approximation with exact linear least-squares normal equations ($2N \times 3$) solving rigid translation $(t_x, t_y, t_z)$ across all 3D features simultaneously.
- **Test:** Verified in [`tests/unit/test_calibrated_registration.py::test_estimate_rigid_pose_residual_gating`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_calibrated_registration.py).

---

## 3. Defect Prevention Invariants

1. **Safety Gate Permanence:** `CLINICAL_REALWORLD_GATE = BLOCKED` remains locked on server.
2. **Epistemic Invariant:** `CANNOT_IMPLICITLY_PROJECT_2D_TO_3D` strictly enforced in both Diện Chẩn and 3D Atlas modules.
3. **Hardware Gate Honesty:** `probe_physical_stereo_hardware()` strictly reports `BLOCKED (DUAL_CAMERA_UNAVAILABLE)` on single-camera or virtualized hosts.
4. **Cryptographic Integrity:** Backups authenticated via HMAC tag before decryption; wrong passwords fail closed immediately.
