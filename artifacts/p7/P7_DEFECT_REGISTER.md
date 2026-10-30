# MSK Research Lab OS — P7 Defect Register & Remediation Log

**Audit Scope:** Operational Readiness, Metrological Fidelity, 3D Geometry Integrity, Security & Packaging  
**Environment:** Dual-Host (Windows 11 DirectShow/MediaPipe + WSL2 Ubuntu 22.04 LTS Offline Workstation)  
**Verification Date:** 2026-10-30  
**Lead Engineer:** Principal Software Architect & Biomedical Software Safety Engineer  

---

## 1. Executive Summary

This register maintains the continuous record of all functional, metrological, and safety defects identified across P6 and P7. During the P7 operational readiness cycle, four new defects (**DEF-05**, **DEF-06**, **DEF-07**, **DEF-08**) were discovered through adversarial code inspection and black-box probing. All four defects have been diagnosed to root cause, accompanied by regression tests, and permanently remediated in the codebase.

---

## 2. Complete Defect Register

| Defect ID | Phase Found | Severity | Affected Module | Root Cause Analysis | Remediation & Verification | Status |
|---|---|---|---|---|---|---|
| **DEF-01** | P6 | **HIGH** | [`start-msk.bat`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/start-msk.bat) | Windows batch syntax bug: nested parenthesized `if defined` evaluated `PYTHON_EXE` to empty string. | Rewrote with label-based dispatch (`:found_python`, `:try_wsl`, `:launch_native`). Verified via `cmd.exe /c start-msk.bat --help` (exit code 0). | **CLOSED** |
| **DEF-02** | P6 | **HIGH** | [`camera_service.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/camera_service.py#L111-L180) | Live webcam pose estimator was disconnected and crashed with `AttributeError: module 'mediapipe' has no attribute 'solutions'` on MediaPipe 1.0+. | Implemented `_extract_live_pose()` using MediaPipe Tasks API (`PoseLandmarker`) with local model asset [`pose_landmarker_lite.task`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/models/pose_landmarker_lite.task) and legacy fallback. | **CLOSED** |
| **DEF-03** | P6 | **MEDIUM** | [`kinematics.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/kinematics.py#L14-L35) | Landmark dict format mismatch (`KeyError: 0` on `pt[0]`). | Added `_get_point_xy()` normalizer supporting both dictionary keys `{"x", "y"}` and sequence indices `(x, y)`. | **CLOSED** |
| **DEF-04** | P6 | **MEDIUM** | [`therapy_manager.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/therapy_manager.py#L55-L65) | String modality codes crashed `generate_soap_note()` with `AttributeError: 'str' object has no attribute 'get'`. | Updated formatter to inspect element type (`isinstance(mod, str)` vs `isinstance(mod, dict)`). Verified in SOAP preview. | **CLOSED** |
| **DEF-05** | P7 | **MEDIUM** | [`workstation_ui.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/workstation_ui.py#L1648-L1675) | **3D Atlas Mock Geometry Fallback:** When GLTFLoader failed or was unavailable, `renderCalibratedReferenceTorso()` rendered a `THREE.CylinderGeometry(0.5, 0.4, 1.4, 16)` and spine line, masquerading mock primitive geometry as anatomy. | Completely removed `renderCalibratedReferenceTorso()` and cylinder generation. Implemented `showAtlasAssetError()` to display explicit fail-closed safety banner (`3D ANATOMICAL ASSET ERROR`). Verified in [`test_p7_operational_readiness.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p7_operational_readiness.py). | **CLOSED** |
| **DEF-06** | P7 | **MEDIUM** | [`tutor.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/ai_tutor/tutor.py#L228-L266) | **FTS5 Search Query Error Fabrication:** SQLite FTS5 query syntax exceptions (e.g. `myofascial (trigger:`) returned a fabricated citation row `{"doc_id": "ERR", "title": "Search Query Note", ...}`, which rendered in the UI as real literature. | Sanitized query tokens using regex alphanumeric extraction (`\b[\w\-]+\b`) and prefix quotes (`"{term}"`). On database query exceptions, returns honest empty list `[]` instead of inventing citation entries. Verified in [`test_p7_operational_readiness.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p7_operational_readiness.py). | **CLOSED** |
| **DEF-07** | P7 | **HIGH** | [`camera_service.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/camera_service.py#L77-L345) & [`workstation_routes.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/workstation_routes.py#L249-L278) | **Metrology Pipeline Resource Leak, Missing Visibility Forwarding & Unclassified Provenance:**<br>1) `cap.release()` was omitted from `finally` blocks in `probe_hardware_camera()` and `execute_motion_assessment()`.<br>2) Extracted MediaPipe landmark visibility was discarded, defaulting tracking confidence to 1.0 (100%).<br>3) Missing landmarks caused unhandled `NOT NULL constraint failed: motion_assessments.measured_rom_deg`.<br>4) Explicit 4-way provenance categories (`LIVE_MEASURED`, `SYNTHETIC_TEST`, `NOT_MEASURABLE`, `INVALID_INPUT`) were not emitted. | 1) Wrapped camera handle in `try ... finally: cap.release()`.<br>2) Forwarded `visibility_scores` to `compute_joint_rom()`.<br>3) Added fail-closed `InsufficientLandmarksError` and `DegenerateGeometryError` guards when ROM is unmeasurable.<br>4) Implemented explicit `provenance_category` in service return dict and REST API HTTP 400/422 responses. Verified in [`test_p7_operational_readiness.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p7_operational_readiness.py). | **CLOSED** |
| **DEF-08** | P7 | **LOW** | [`start-msk.bat`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/start-msk.bat#L51-L58) | **Windows Launcher WSL Fallback Argument Drop:** Line 56 invoked `wsl -e bash -c "cd '%WORKDIR%' && bash start-msk.sh"` dropping CLI arguments `%*` (e.g. `--port`, `--help`) and using Windows path without `wslpath`. | Updated WSL fallback invocation: `wsl -e bash -c "cd \"$(wslpath '%WORKDIR%')\" && bash start-msk.sh %*"`. Verified argument passing and execution. | **CLOSED** |

---

## 3. Remediation Invariant Adherence

Every remediation satisfied the mandatory P7 rules:
1. **Zero Silent Fallback:** Missing cameras, landmarks, or 3D meshes fail closed with visible error notices rather than synthetic mock geometry or fabricated angles.
2. **Attribution Integrity:** Search queries only return stored documents in SQLite FTS5; errors return `[]`, never placeholder citation rows.
3. **Data Provenance:** Every angle measurement is strictly categorized as `LIVE_MEASURED`, `SYNTHETIC_TEST`, `NOT_MEASURABLE`, or `INVALID_INPUT`.
4. **Clinical Boundary:** `CLINICAL_REALWORLD_GATE = BLOCKED` remains permanently active.
