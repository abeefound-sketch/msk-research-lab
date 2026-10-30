# MSK Research Lab OS — P10 Defect Register

**Milestone:** P10  
**Defect Series:** DEF-20 through DEF-26  
**Status:** ALL 7 REMEDIATED & VERIFIED (0 OPEN DEFECTS)  

---

## Remediated Defect Summaries

| Defect ID | Severity | Category | Affected Component | Root Cause | Remediation | Verification Test |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **DEF-20** | **HIGH** | Compliance / Crypto | `security/openssl_gcm.py` | Overbroad "FIPS-compliant" claim despite system `libcrypto` default provider being non-FIPS. | Implemented `probe_fips_status()`; corrected claims to "NIST SP 800-38D standard-aligned AES-256-GCM AEAD". | `test_openssl_fips_status_probe_reporting` |
| **DEF-21** | **HIGH** | Privacy / Security | `workstation/patient_manager.py` | Exported raw clinical free-text containing provider names, phones, emails, and dates; exact age > 89; claimed Safe Harbor. | Built `scrub_phi_from_text()`; aggregated age > 89 to `"90+"`; labeled output `NOT_CERTIFIED_FOR_PHI`. | `test_phi_free_text_scrubber`, `test_hipaa_safe_harbor_age_aggregation` |
| **DEF-22** | **HIGH** | OS Security | `security/permissions.py`, `key_lifecycle.py` | POSIX `os.chmod 0600/0700` ineffective on Windows NTFS, leaving key material with inherited user read permissions. | Implemented `secure_file_permissions()` and `secure_directory_permissions()` utilizing native Windows `icacls.exe`. | `test_windows_and_posix_permissions_helpers` |
| **DEF-23** | **HIGH** | Durability | `core/migrations.py` | `conn.executescript()` issued implicit commit before execution; multi-statement failures left partial tables committed. | Implemented statement splitting and wrapped each migration in transactional savepoint blocks with atomic rollback. | `test_atomic_migration_rollback_on_failure` |
| **DEF-24** | **HIGH** | Metrology | `studio/calibrated_registration.py` | Ray back-projection assumed $R=I$ ($z_{target} = t_z + ref\_3d[2]$), causing depth errors under yaw/pitch. | Computed true rotated reference depth in camera frame $Z_{cam} = (\mathbf{R}\mathbf{X}_{ref} + \mathbf{t})_z$. | `test_rotated_camera_frame_depth_ray_projection` |
| **DEF-25** | **MEDIUM** | Geometry | `studio/calibrated_registration.py` | 6-DoF LM PnP optimizer had unconstrained rotation when input landmarks were collinear. | Added pairwise 3D cross-product spatial variance evaluation; fails closed if landmarks lack 2D/3D variance. | `test_collinear_landmark_degeneracy_rejection` |
| **DEF-26** | **MEDIUM** | Network Security | `api/app.py` | `host_header.split(":")[0]` caused IPv6 `[::1]:8000` to be misparsed as `"["`, falsely rejecting loopback requests. | Parsed host via `urllib.parse.urlsplit`; added `::1` to loopback hosts; rejected `Origin: null` on state-changing calls. | `test_security_host_guard_ipv6_loopback`, `test_security_host_guard_csrf_null_origin_rejection` |

---

## Cumulative Defect Status

- **DEF-01 through DEF-12:** Remediated in P6–P8.
- **DEF-13 through DEF-19:** Remediated in P9.
- **DEF-20 through DEF-26:** Remediated in P10.
- **Total Historical Defects Identified & Resolved:** 26
- **Active Unresolved Defects:** **0**
