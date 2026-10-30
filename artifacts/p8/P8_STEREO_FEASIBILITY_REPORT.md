# MSK Research Lab OS — P8-D Stereo Camera Feasibility & Triangulation Report

**Evaluation Date:** 2026-10-30  
**Verification Role:** Computer Vision Engineer, Biomechanical Verification Specialist, and Independent Release QA  
**Module:** [`src/msk_research_lab/motion/stereo.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/stereo.py)  
**Mathematical Pipeline:** Direct Linear Transformation (DLT) Triangulation, Epipolar Geometry ($E, F$), and Reprojection Error Gating  
**Physical Hardware Gate:** **`BLOCKED (DUAL_CAMERA_UNAVAILABLE)`**  
**Mathematical Verification:** **`VERIFIED — PASS`**  

---

## 1. Executive Summary

Workstream **P8-D** investigates and implements stereo multi-view photogrammetry to overcome the fundamental physics limitation of monocular planar Range of Motion (ROM) measurement (out-of-plane yaw foreshortening).

Key accomplishments:
1. **Mathematical Epipolar Model:** Implemented `StereoCameraRig` supporting arbitrary calibrated camera baseline $b = \|t\|$, relative rotation matrix $R \in \mathrm{SO}(3)$, projection matrices $P_1 = K_1 [I \mid 0]$, $P_2 = K_2 [R \mid t]$, and essential matrix $E = [t]_\times R$.
2. **Direct Linear Transformation (DLT) Triangulation:** Implemented `triangulate_point_dlt()` solving the $4\times4$ linear homogeneous nullspace $A \mathbf{X} = 0$. Proven to reconstruct true metric 3D point positions with sub-millimeter accuracy ($< 0.5$ mm at 1.5 m depth).
3. **True 3D Euclidean Angle Recovery:** Implemented `triangulate_joint_angle_3d()`. Demonstrated that while monocular 2D angles degrade non-linearly under torso yaw ($\tan \alpha_{2D} = \tan \alpha_{3D} \cdot \cos \theta$), stereo 3D vector reconstruction ($\mathbf{u} = A_{3D} - B_{3D}, \mathbf{v} = C_{3D} - B_{3D}$) recovers the ground-truth $60.0^\circ$ joint angle with $< 0.2^\circ$ deviation regardless of out-of-plane rotation.
4. **Reprojection Error Gating:** Implemented `compute_reprojection_error()` ($e_{reproj} = \frac{1}{2}(\|p_1 - \hat{p}_1\| + \|p_2 - \hat{p}_2\|)$). Automatically fails closed and raises `StereoMetrologyError` if correspondence error exceeds $2.5$ pixels.
5. **Physical Hardware Gate Preservation:** Implemented `probe_physical_stereo_hardware()`. In compliance with biomedical safety standards, physical hardware availability is **NEVER** falsified: on WSL2 / single laptop webcam environments, the hardware gate strictly reports **`BLOCKED (DUAL_CAMERA_UNAVAILABLE)`**.

---

## 2. Multi-View Epipolar Triangulation Pipeline

```mermaid
flowchart LR
    LeftCam[Left Camera Frame (u1, v1)] --> DLT[DLT Triangulation (A * X = 0)]
    RightCam[Right Camera Frame (u2, v2)] --> DLT
    Rig[Calibrated Stereo Rig (K1, K2, R, t)] --> DLT

    DLT --> Point3D[Reconstructed 3D Points (X, Y, Z)]
    Point3D --> Reproj[Project Back via P1, P2]
    Reproj --> CheckError{Reprojection Error <= 2.5 px?}
    
    CheckError -->|No: Error > 2.5px| Reject[FAIL-CLOSED: Reject Triangulation (StereoMetrologyError)]
    CheckError -->|Yes: Error <= 2.5px| Vectors[Compute 3D Vectors u = A-B, v = C-B]
    Vectors --> Angle3D[True 3D Angle = arccos(u.v / |u||v|)]
    Angle3D --> Valid[VALID 3D ROM (Yaw-Immune)]
```

---

## 3. Verification Test Evidence

Automated test suite [`tests/unit/test_stereo_kinematics.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_stereo_kinematics.py):
- `test_stereo_camera_rig_geometry`: **PASSED** (verifies $P_1, P_2$, baseline, and essential matrix $E$)
- `test_dlt_triangulation_and_reprojection_accuracy`: **PASSED** (verifies 3D reconstruction error $< 0.5$ mm and reprojection error $< 0.05$ px)
- `test_3d_joint_angle_immunity_to_yaw`: **PASSED** (proves 3D angle recovery remains exactly $60.0^\circ$ under $30^\circ$ out-of-plane yaw)
- `test_reprojection_error_gating_rejects_corrupted_correspondence`: **PASSED** (rejects 15px corrupted landmark input)
- `test_physical_stereo_hardware_probe_blocked`: **PASSED** (verifies hardware gate correctly marks `BLOCKED (DUAL_CAMERA_UNAVAILABLE)`)

**Workstream Verdict:** **`MATHEMATICALLY PASS — HARDWARE BLOCKED`**
