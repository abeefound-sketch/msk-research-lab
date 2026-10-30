# MSK RESEARCH LAB OS — P9 CUMULATIVE DEFECT REGISTER

## 1. Defect Tracking Overview

- **Audit Date:** 2026-10-30
- **Auditor Role:** Biomedical Software Safety Auditor & Principal QA Engineer
- **Status Summary:**
  - DEF-01 to DEF-12: RESOLVED (P6–P8 milestones)
  - DEF-13 to DEF-19: **RESOLVED (P9 milestone)**
  - Active Unresolved Defects: **0**
  - Safety Invariants: **STRICTLY ENFORCED**

---

## 2. Cumulative Defect Register (DEF-01 through DEF-19)

| Defect ID | Severity | Milestone | Module | Description | Root Cause | Remediated In | Status |
| :--- | :---: | :---: | :--- | :--- | :--- | :--- | :---: |
| **DEF-01** | CRITICAL | P6 | `motion/` | Synthetic webcam ROM measurements | Hardcoded mock data presented as real | `camera_service.py` | **RESOLVED** |
| **DEF-02** | HIGH | P6 | `core/` | SQLite migration initialization crashes | Migration table lock desync | `migrations.py` | **RESOLVED** |
| **DEF-03** | HIGH | P6 | `atlas/` | Geometric primitives masquerading as anatomy | Parametric spheres used instead of meshes | `scene.py` | **RESOLVED** |
| **DEF-04** | HIGH | P6 | `api/` | Incomplete control button handlers (49 controls) | Placeholder event listeners in UI | `dashboard.html` | **RESOLVED** |
| **DEF-05** | HIGH | P7 | `workstation/` | Patient search case-sensitivity & SQL injection risk | Raw query concatenation | `patient_manager.py` | **RESOLVED** |
| **DEF-06** | MEDIUM | P7 | `workstation/` | SOAP notes missing clinical red flag audit | Red flags not linked to session notes | `therapy_manager.py` | **RESOLVED** |
| **DEF-07** | MEDIUM | P7 | `workstation/` | CSV progress export lacked pain trend metrics | Pain scores omitted from CSV stream | `progress_tracker.py` | **RESOLVED** |
| **DEF-08** | MEDIUM | P7 | `motion/` | MediaPipe Landmarker Lite CPU execution jitter | Single-thread bottleneck | `camera_service.py` | **RESOLVED** |
| **DEF-09** | CRITICAL | P7 | `atlas/` | Missing BodyParts3D GLTF asset bundling | External URLs referenced in offline mode | `packaging/` | **RESOLVED** |
| **DEF-10** | HIGH | P7 | `security/` | Static unkeyed pseudonym hashing | Unsalted SHA-256 vulnerable to rainbow tables | `patient_manager.py` | **RESOLVED** |
| **DEF-11** | MEDIUM | P8 | `motion/` | Conflation of 3D invariance with empirical depth accuracy | Omission of optical $\sigma_Z \propto Z^2/b$ bounds | `stereo.py` | **RESOLVED** |
| **DEF-12** | HIGH | P8 | `security/` | Custom CTR keystream without standardized AEAD tag | Proprietary stream cipher construct | `key_lifecycle.py` | **RESOLVED** |
| **DEF-13** | HIGH | P9 | `security/` | Non-standard backup container format (`MSKENC01`) | Custom CTR mode lacks FIPS AEAD compliance | `openssl_gcm.py`, `key_lifecycle.py` | **RESOLVED** |
| **DEF-14** | CRITICAL | P9 | `security/` | Unstaged backup restoration risks corrupting database | Extraction directly to production DB directory | `key_lifecycle.py` | **RESOLVED** |
| **DEF-15** | HIGH | P9 | `security/` | Key rotation desynchronization risk on disk error | DB committed before active key file written | `key_lifecycle.py` | **RESOLVED** |
| **DEF-16** | HIGH | P9 | `workstation/` | Direct PII (`full_name`) exposed in research exports | Direct patient export included direct identifiers | `patient_manager.py`, `workstation_routes.py` | **RESOLVED** |
| **DEF-17** | HIGH | P9 | `api/` | Local loopback server vulnerable to cross-origin CSRF | Missing Origin/Referer header enforcement | `app.py` (`security_host_guard`) | **RESOLVED** |
| **DEF-18** | MEDIUM | P9 | `motion/` | Absence of depth uncertainty modeling in stereo metrology | Depth error scaling $\sigma_Z$ was unquantified | `stereo.py` | **RESOLVED** |
| **DEF-19** | HIGH | P9 | `studio/` | 3-DoF translation-only PnP model fails on rotated head poses | Assumed $R = I$, failing under yaw/pitch $> 3^\circ$ | `calibrated_registration.py` | **RESOLVED** |

---

## 3. Safety Invariants Status

- **`CLINICAL_REALWORLD_GATE`**: **BLOCKED (PERMANENT SERVER INVARIANT)**.
- **`CANNOT_IMPLICITLY_PROJECT_2D_TO_3D`**: **ENFORCED (FAIL-CLOSED)**.
- **`PHYSICAL_STEREO_HARDWARE_GATE`**: **BLOCKED (DUAL_CAMERA_UNAVAILABLE)**.
