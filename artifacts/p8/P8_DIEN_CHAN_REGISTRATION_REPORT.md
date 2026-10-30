# MSK Research Lab OS — P8-E Calibrated 2D/3D Facial Registration Report

**Evaluation Date:** 2026-10-30  
**Verification Role:** Computer Vision Engineer, Biomechanical Safety Engineer, and Independent Release QA  
**Module:** [`src/msk_research_lab/studio/calibrated_registration.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/studio/calibrated_registration.py)  
**Research Focus:** Diện Chẩn 2D Facial Atlas Optical Calibration and 3D Anthropometric Mesh Mapping  
**Status:** **`VERIFIED — PASS`**  
**Safety Invariant:** `CANNOT_IMPLICITLY_PROJECT_2D_TO_3D` (Server-Authoritative Epistemic Guard)  

---

## 1. Executive Summary

Workstream **P8-E** addresses the critical epistemic boundary in facial reflexology (Diện Chẩn): monocular 2D clinical diagrams and photographic annotations cannot be projected into 3D space without mathematically defensible, calibrated photogrammetric transformation chains.

Key deliveries:
1. **Preservation of the Epistemic Invariant:**
   - Any attempt to map uncalibrated 2D pixels $(u, v)$ to a 3D anatomical mesh (`watercmy_bp3d_z_anatomy`) without an active, validated calibration context is strictly blocked by `attempt_project_2d_to_3d()`, raising `DienChanError("CANNOT_IMPLICITLY_PROJECT_2D_TO_3D")`.
2. **Canonical 3D Anthropometric Facial Landmarks:**
   - Defined `CANONICAL_FACIAL_3D_LANDMARKS` with bilateral symmetry in millimeter Euclidean space:
     - Subnasale (`SUBNASALE`, $(0.0, 0.0, 20.0)$ mm, site of Huyệt 19)
     - Pronasale (`PRONASALE`, $(0.0, 18.0, 36.0)$ mm)
     - Sellion (`SELLION`, $(0.0, 48.0, 18.0)$ mm)
     - Tragion Notch (`TRAGION_LEFT`, $(-76.0, 10.0, -38.0)$ mm and `TRAGION_RIGHT`, $(76.0, 10.0, -38.0)$ mm, site of Huyệt 0)
     - Mandibular Angle (`GONION_LEFT` / `GONION_RIGHT`, site of Huyệt 275)
     - Chin midpoint (`GNATHION`, $(0.0, -68.0, 12.0)$ mm)
3. **PnP Rigid Pose Estimation & Residual Gating:**
   - Implemented `estimate_rigid_pose_from_landmarks()` solving rigid pose $(R, t)$ via normal equations over non-coplanar feature correspondences.
   - Computes reprojection residuals for every calibration landmark. Fails closed with `CalibratedRegistrationError` if maximum residual exceeds $3.0$ pixels.
4. **Calibrated Ray-Casting & Uncertainty Sphere:**
   - Implemented `register_2d_reflexology_point_to_3d()`. Computes ray direction in camera frame, solves metric intersection with reference facial topography, transforms to head coordinate frame ($X_{obj} = R^T(P_{cam} - t)$), and reports uncertainty radius in millimeters ($r_{uncertainty} = 1.96 \cdot \frac{e_{res}}{f_x} \cdot Z_{depth}$).

---

## 2. Optical Registration Transformation Chain

```mermaid
flowchart TD
    Photo[2D Clinical Diagram / Photograph (u, v)] --> CalibCheck{Calibration Context Active?}
    
    CalibCheck -->|None / Uncalibrated| EpistemicGuard[FAIL-CLOSED: CANNOT_IMPLICITLY_PROJECT_2D_TO_3D (DienChanError)]
    
    CalibCheck -->|Calibrated Context Present| PnP[Estimate Rigid Head Pose (R, t) via PnP]
    PnP --> ResidualCheck{Max Reprojection Residual <= 3.0 px?}
    
    ResidualCheck -->|No: Residual > 3.0px| RejectPnP[FAIL-CLOSED: CALIBRATION_RESIDUAL_EXCEEDS_TOLERANCE]
    ResidualCheck -->|Yes: Residual <= 3.0px| RayCast[Cast Normalized Ray: r = K^-1 * [u, v, 1]^T]
    
    RayCast --> Intersect[Surface Intersection with Reference Topography]
    Intersect --> Transform[Rigid Transform: X_obj = R^T * (P_cam - t)]
    Transform --> Uncertainty[Compute ISO GUM Uncertainty Radius (r_mm)]
    Uncertainty --> Output[CALIBRATED_RESEARCH_REGISTRATION (X, Y, Z, r_mm)]
```

---

## 3. Verification Test Evidence

Automated test suite [`tests/unit/test_calibrated_registration.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_calibrated_registration.py):
- `test_canonical_facial_landmarks_topology`: **PASSED** (verifies presence and bilateral metric symmetry of facial landmarks)
- `test_project_canonical_landmark_validity`: **PASSED** (validates pinhole projection into sensor viewport)
- `test_estimate_rigid_pose_residual_gating`: **PASSED** (accepts valid correspondences with residual $< 2.0$ px; rejects 25px corrupted landmarks)
- `test_epistemic_guard_strictly_enforced_without_calibration`: **PASSED** (verifies `CANNOT_IMPLICITLY_PROJECT_2D_TO_3D` strictly enforced)
- `test_calibrated_reflexology_point_registration_success`: **PASSED** (verifies Subnasale / Huyệt 19 registration within $\pm 1.5$ mm of ground truth with computed uncertainty radius)

**Workstream Verdict:** **`PASS`**
