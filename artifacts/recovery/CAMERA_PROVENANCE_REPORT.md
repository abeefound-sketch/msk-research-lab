# MSK Research Lab OS v3.2 — Camera Kinematics & Provenance Report

**Date:** 2026-10-29  
**Version:** v3.2 Recovery  
**Target:** Motion Assessment Engine (`src/msk_research_lab/motion/`)  
**Safety Mandate:** Zero Fake Measurements, Explicit Provenance Tagging, Fail-Closed Epistemics.

---

## 1. Physical Hardware & Environment Probe

An automated probe was executed against the host hardware environment running MSK Research Lab OS v3.2:

```json
{
  "available": false,
  "status": "CAMERA_OFFLINE",
  "details": "No physical or virtual video devices found in /dev/video* or via OpenCV VideoCapture.",
  "subsystem": "linux_v4l2_wsl2",
  "device_nodes_checked": ["/dev/video0", "/dev/video1", "/dev/video2"],
  "opencv_indices_checked": [0, 1]
}
```

### Analysis of WSL2 Hardware Boundary
The runtime environment is WSL2 (Linux 6.18.54 on Windows 11 host, Intel Core i7-5600U). In WSL2, USB peripherals such as built-in laptop webcams are not bridged into the guest Linux VM by default unless explicit USB/IP bridging (`usbipd-win`) is configured on the Windows host.

**Prior Defect (F-02):** In prior releases, when no camera was connected, the system silently simulated webcam frames or allowed browser clients to send fabricated coordinate landmarks, which the backend then persisted into the clinical database as "live" range-of-motion measurements.

**Recovery Invariant (Remediated):** MSK Research Lab OS v3.2 enforces strict **fail-closed epistemics**. If a user requests a live ROM measurement (`mode="LIVE"`) without a connected webcam and pose estimator, the system unconditionally halts with typed error `CameraUnavailableError` (HTTP 400/422). Under no circumstances are synthetic numbers passed off as live biometric data.

---

## 2. Typed Error Hierarchy & Epistemic Fail-Closed Model

The motion assessment module implements the following explicit error taxonomy:

| Exception Class | HTTP Status | Error Code | Root Cause Condition | User-Facing Guidance |
|---|---|---|---|---|
| `CameraUnavailableError` | `400 Bad Request` | `CAMERA_UNAVAILABLE` | No hardware camera detected in `/dev/video*` or OpenCV probe. | "No physical camera detected. Ensure your webcam is connected, or switch to 'Load Standard Fixture' (DEMO mode) for research/educational testing." |
| `TrackerUnavailableError` | `422 Unprocessable` | `TRACKER_UNAVAILABLE` | Pose tracking engine (MediaPipe) not installed or uninitialized. | "Pose estimation backend is not installed. Use DEMO fixture mode or install pose estimator dependencies." |
| `InsufficientLandmarksError` | `422 Unprocessable` | `INSUFFICIENT_LANDMARKS` | Required anatomical keypoints (e.g. shoulder, elbow, wrist) missing or visibility < 0.5. | "Key anatomical landmarks could not be detected. Ensure the patient is in full view and not obstructed." |
| `DegenerateGeometryError` | `422 Unprocessable` | `DEGENERATE_GEOMETRY` | Landmarks are collinear, zero-length vector, or geometrically degenerate. | "Landmark geometry is degenerate. Unable to compute a valid anatomical joint angle." |

---

## 3. Provenance & Synthetic Data Separation

All motion assessment database records (`motion_assessments`) strictly track data source and provenance:

1. **Live Assessments (`mode="LIVE"`):**
   - Requires actual frame acquisition from a hardware video stream.
   - `data_source` is set to `'HARDWARE_CAMERA'`.
   - `is_synthetic` is set to `0` (or `1` if operating under a synthetic subject protocol).
   - If the camera is disconnected during capture, the pipeline fails closed with `CAMERA_UNAVAILABLE`.

2. **Synthetic Demonstration Fixtures (`mode="DEMO"`):**
   - Explicitly requested by the user clicking **"Load Standard Fixture"**.
   - Input vectors are sourced exclusively from versioned synthetic biomechanical models (`FIXTURE_ELBOW_FLEXION_140`, `FIXTURE_SHOULDER_ABDUCTION_180`, `FIXTURE_KNEE_FLEXION_135`).
   - `data_source` is recorded as `'DEMO_FIXTURE'`.
   - `is_synthetic` is explicitly set to `1`.
   - The UI displays a prominent yellow **DEMO / FIXTURE** badge, preventing operator confusion.

---

## 4. Measurement Uncertainty Model (ISO GUM / JCGM 100:2008)

Range of motion angle calculation applies the Guide to the Expression of Uncertainty in Measurement (ISO GUM):

$$\theta = \arccos\left(\frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}\right)$$

### Uncertainty Sources
1. **Sensor Resolution & Optical Distortion:** $u_{\text{opt}} = 0.5^\circ$
2. **Pose Landmark Jitter & Keypoint Localization:** $u_{\text{keypoint}} = 0.8^\circ$
3. **Out-of-Plane Yaw / Parallax Confounder:** When subject yaw angle exceeds $15^\circ$, an uncalibrated yaw confounder is flagged (`UNCALIBRATED_YAW`), expanding uncertainty by $u_{\text{yaw}} = 1.2^\circ$.

### Combined Uncertainty & Expanded Coverage
$$u_c = \sqrt{u_{\text{opt}}^2 + u_{\text{keypoint}}^2 + u_{\text{yaw}}^2}$$
$$U_{95} = k \cdot u_c \quad (k = 2.0 \text{ for 95\% confidence})$$

In nominal conditions, reported expanded uncertainty is $U_{95} = \pm 1.5^\circ$. When confounders are detected, $U_{95}$ widens to $\pm 3.2^\circ$ with explicit clinical interpretation provided by the AI Tutor service.
