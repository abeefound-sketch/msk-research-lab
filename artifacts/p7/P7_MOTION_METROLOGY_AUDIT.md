# MSK Research Lab OS — P7 Motion Metrology & Kinematic Quality Audit

**Audit Role:** Biomedical Software Safety & Metrology Verification Engineer  
**Standard Audited:** ISO/IEC Guide 98-3 (GUM: Guide to the Expression of Uncertainty in Measurement)  
**Date:** 2026-10-30  
**Verification Target:** 2D Monocular Video Pose Estimation & Planar Joint Goniometry Pipeline  

---

## 1. Executive Summary & Epistemic Stance

A central requirement of the P7 Operational Readiness mission is guaranteeing that **monocular 2D computer-vision estimates are never represented as clinical-grade 3D goniometry**, and that uncalibrated optical inputs never produce false or ungrounded range-of-motion (ROM) figures.

This audit evaluates the end-to-end pipeline spanning camera hardware capture, Google MediaPipe Tasks pose estimation, coordinate normalization, out-of-plane confounder detection, ISO GUM uncertainty budgets, and database storage.

---

## 2. Pipeline Stage-by-Stage Verification

```
[Physical Camera] -> [Frame Ingestion & Cleanup] -> [MediaPipe Tasks Landmarker]
                                                                |
                                                                v
[Provenanced DB] <- [GUM Uncertainty & Confounders] <- [2D Planar Angle Engine]
```

### 2.1 Hardware Capture & Resource Lifecycle
- **Implementation:** [`src/msk_research_lab/motion/camera_service.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/camera_service.py#L77-L109)
- **Verified Environment:** Windows 11 Native Host (`C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv`, OpenCV DirectShow backend, 640x480 @ 30 FPS).
- **WSL2 Boundary Behavior:** WSL2 kernel lacks hardware `/dev/video0` attachment. [`probe_hardware_camera()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/camera_service.py#L77) truthfully returns `status: "CAMERA_OFFLINE_FAIL_CLOSED"`, `available: false`, `backend: "NO_DEVICE"`.
- **Resource Cleanup (Remediated DEF-07):** Both [`probe_hardware_camera()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/camera_service.py#L77) and [`execute_motion_assessment()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/camera_service.py#L202) wrap OpenCV `VideoCapture` instances in `try ... finally: cap.release()`, guaranteeing that DirectShow or V4L2 handles are immediately released even if a frame read raises an I/O exception.

### 2.2 Google MediaPipe Tasks Model Loading & Multi-Subject Handling
- **Model Ingestion:** Loads local standalone model asset [`2data/models/pose_landmarker_lite.task`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/models/pose_landmarker_lite.task) (5,777,746 bytes, SHA-256: `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a`).
- **Offline Integrity:** Model is bundled locally; zero external network requests or CDN dependencies are made at runtime.
- **Ambiguous Multi-Subject Guard (DEF-07):** In [`_extract_live_pose()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/camera_service.py#L112), if `len(res.pose_landmarks) > 1`, the system raises [`InsufficientLandmarksError`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/camera_service.py#L67):
  ```python
  if len(res.pose_landmarks) > 1:
      raise InsufficientLandmarksError("AMBIGUOUS_POSE: Multiple subjects detected in camera frame. Assessment requires isolated single subject.")
  ```
- **Empty / Obstructed Frames:** When no human skeleton is detected, the pipeline raises `InsufficientLandmarksError("NO_POSE: Human subject was not detected in camera frame.")`.

### 2.3 Landmark Visibility Forwarding & Coordinate Normalization
- **Implementation:** [`src/msk_research_lab/motion/kinematics.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/kinematics.py#L14-L49)
- **Coordinate Flexibility:** [`_get_point_xy()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/kinematics.py#L14) handles both MediaPipe Tasks dictionary outputs (`{"x": float, "y": float, "visibility": float}`) and tuple fixtures (`(x, y)`).
- **Visibility Propagation (DEF-07):** Previous implementation dropped `raw[i].visibility`, defaulting confidence to 1.0. The pipeline now extracts `vis_scores = {k: v.get("visibility", 1.0) for k, v in landmarks.items()}` and forwards them directly to [`compute_joint_rom()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/kinematics.py#L125). If the average visibility falls below 0.60, `quality_status` transitions from `OPTIMAL` to `DEGRADED`.

---

## 3. Strict 4-Way Provenance Categorization

To guarantee unambiguous clinical audit trails, every measurement response and database record is explicitly categorized into one of four mutually exclusive states:

| Category | Trigger Conditions | `is_synthetic` | HTTP Code | Database Persistence |
|---|---|---|---|---|
| **`LIVE_MEASURED`** | Physical webcam online, single subject detected, valid 2D landmarks, non-degenerate vectors. | `0` (False) | 200 OK | Saved to `motion_assessments` (`data_source = 'HARDWARE_CAMERA'`). |
| **`SYNTHETIC_TEST`** | Standard posture fixture (e.g. `ELBOW_FLEXION_90`, `TADASANA_NEUTRAL`) or custom client test payload in DEMO mode. | `1` (True) | 200 OK | Saved to `motion_assessments` (`data_source = 'FIXTURE_*'` or `'SYNTHETIC_CLIENT_PAYLOAD'`). |
| **`NOT_MEASURABLE`** | Camera offline in LIVE mode, empty frame (`NO_POSE`), missing anatomical landmarks (`INSUFFICIENT_DATA`), degenerate joint vectors (`DEGENERATE_GEOMETRY`). | N/A | 400 Bad Request / 422 Unprocessable | **Blocked from DB insertion** (avoids polluting longitudinal patient tables). |
| **`INVALID_INPUT`** | Missing `patient_id`, malformed JSON, invalid data types, non-numeric coordinates. | N/A | 400 Bad Request | **Blocked from DB insertion**. |

---

## 4. GUM Uncertainty Budget & Metrological Critique

### 4.1 Current Mathematical Model in [`kinematics.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/kinematics.py#L93-L114)
The system calculates combined standard uncertainty $u_c$ following ISO/IEC Guide 98-3:
$$u_c = \sqrt{u_{\text{resolution}}^2 + u_{\text{operator}}^2 + u_{\text{yaw}}^2}$$
where:
- $u_{\text{resolution}} = 0.5^\circ$ (sensor pixel quantization at standard distance)
- $u_{\text{operator}} = 0.8^\circ$ (landmark localization jitter across frames)
- $u_{\text{yaw}} = 0.4^\circ$ if torso is planar, or $1.5^\circ$ if $\text{apparent\_span\_ratio} < 0.85$ (out-of-plane rotation $> 15^\circ$).

Expanded uncertainty at nominal 95% confidence:
$$U_{95} = k \cdot u_c \quad (k = 1.96)$$
Nominal expanded uncertainty: $U_{95} \approx \pm 2.01^\circ$ (optimal) to $\pm 3.48^\circ$ (yaw confounded).

### 4.2 Adversarial Metrological Critique of Assumptions
1. **Gaussian Normality Assumption ($k=1.96$):**
   - *Limitation:* The GUM calculation assumes asymptotic normality ($\nu_{\text{eff}} = \infty$) via the Welch-Satterthwaite relation. However, deep neural network landmark regressors (MediaPipe heatmaps) exhibit non-Gaussian tail behavior, discrete coordinate jumps, and non-stationary jitter.
   - *Metrological Verdict:* $U_{95} = \pm 2.01^\circ$ is a **theoretical lower bound**, valid only under ideal laboratory conditions with high contrast and zero subject motion blur.
2. **2D Monocular Perspective Distortion (Out-of-Plane Foreshortening):**
   - When a limb rotates away from the camera optical axis by angle $\theta$ (yaw), the apparent planar angle $\alpha_{2D}$ is related to the true 3D angle $\alpha_{3D}$ by a non-linear trigonometric projection:
     $$\tan(\alpha_{2D}) = \tan(\alpha_{3D}) \cdot \cos(\theta)$$
   - This effect is asymmetrical and cannot be modeled by symmetric additive Gaussian noise.
3. **Mandatory Software Boundary:**
   - The application enforces this limitation in every calculation output:
     > `"clinical_disclaimer": "2D planar camera estimate only. NOT validated for surgical or orthopedic diagnostic decisions."`
   - Monocular 2D measurements must never be claimed or documented as replacing 3D optical motion capture (Vicon/Qualisys) or calibrated clinical manual goniometry.

---

## 5. Automated Verification Evidence

The metrology fixes and provenance categories are continuously verified by [`tests/integration/test_p7_operational_readiness.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p7_operational_readiness.py):
- `test_def_07_motion_provenance_categories_and_visibility`: **PASS**
- `test_def_07_api_provenance_on_errors`: **PASS**
- `test_e2e_06_e2e_07_camera_provenance_and_demo_mode`: **PASS**
- `test_e2e_08_kinematics_completeness_and_degenerate_guard`: **PASS**
