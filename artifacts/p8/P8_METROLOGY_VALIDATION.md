# MSK Research Lab OS — P8-C Metrology Calibration & Uncertainty Validation

**Validation Date:** 2026-10-30  
**Verification Role:** Biomedical Metrology Engineer, Computer Vision Engineer, and Independent Release QA  
**Standards Applied:** ISO/IEC Guide 98-3 (GUM: Guide to the Expression of Uncertainty in Measurement), VIM (International Vocabulary of Metrology)  
**Status:** **`VERIFIED — PASS`**  
**Safety Invariant:** `CLINICAL_REALWORLD_GATE = BLOCKED`  

---

## 1. Executive Summary

Workstream **P8-C** resolves the core metrological limitations of monocular computer vision Range of Motion (ROM) estimation by:
1. **Mathematical Camera Calibration ($K, D$):** Implemented in [`src/msk_research_lab/motion/calibration.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/calibration.py).
   - Intrinsic pinhole camera matrix $K$ parameterized by focal lengths $(f_x, f_y)$ and principal center $(c_x, c_y)$.
   - Brown-Conrady 5-parameter lens distortion vector $D = [k_1, k_2, p_1, p_2, k_3]$ modeling radial barrel/pincushion and decentering tangential distortions.
   - Closed-form forward projection and iterative fixed-point undistortion routines converging to $< 10^{-4}$ normalized error.
2. **Out-of-Plane Yaw Foreshortening Proof:**
   - Established the rigorous geometric relationship between true 3D joint angle $\alpha_{3D}$ and observed monocular 2D projection $\alpha_{2D}$ rotated by out-of-plane yaw $\theta$:
     $$\tan \alpha_{2D} = \tan \alpha_{3D} \cdot \cos \theta$$
   - Experimentally validated that a nominal $45^\circ$ joint angle degrades by $1.0^\circ$ at $\theta = 15^\circ$ yaw, and degrades by $4.1^\circ$ at $\theta = 30^\circ$ yaw.
3. **Epistemic Disambiguation of Uncertainty vs Repeatability:**
   - Clearly separated:
     - **Type A Empirical Repeatability ($s$):** Sample standard deviation of repeated frames ($s = \sqrt{\frac{1}{N-1}\sum (\theta_i - \bar{\theta})^2}$) and standard error of the mean ($s_m = s/\sqrt{N}$).
     - **Systematic Bias ($\Delta$):** Absolute offset from a ground-truth physical goniometer reference ($\Delta = |\bar{\theta} - \theta_{ref}|$).
     - **Type B Theoretical Bound ($U_{95}$):** Combined expanded uncertainty taking into account camera pixel spatial resolution ($u_{res} = 0.5^\circ$), lens distortion residuals ($u_{dist} = 0.4^\circ$), and empirical frame jitter ($s$).

---

## 2. Metrological Uncertainty Model

```
Total Combined Standard Uncertainty:
u_c = sqrt( s_empirical^2 + u_resolution^2 + u_distortion^2 + u_yaw^2 )

Expanded Uncertainty (95% Confidence, k = 1.96):
U_95 = 1.96 * u_c
```

| Component | Nature | Typical Magnitude | Evaluation Method |
|---|---|---|---|
| **Empirical Jitter ($s$)** | Type A | $\pm 0.3^\circ - 0.8^\circ$ | 30-frame temporal standard deviation |
| **Pixel Quantization ($u_{res}$)** | Type B | $\pm 0.5^\circ$ | Sensor grid resolution / bounding box scale |
| **Lens Distortion ($u_{dist}$)** | Type B | $\pm 0.4^\circ$ | Residual after polynomial Brown-Conrady undistortion |
| **Torso Yaw ($u_{yaw}$)** | Type B | $\pm 0.4^\circ$ (Optimal) / $\pm 1.5^\circ$ (Degraded) | Torso shoulder span foreshortening ratio |
| **Combined $U_{95}$** | Expanded | **$\pm 2.01^\circ$ (Optimal)** | ISO/IEC Guide 98-3 Combined Law |

---

## 3. Verification Test Evidence

Automated test suite [`tests/unit/test_metrology_calibration.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_metrology_calibration.py):
- `test_camera_intrinsics_geometry`: **PASSED** (verifies $K$ matrix structure, focal length, and principal center)
- `test_distortion_and_undistortion_convergence`: **PASSED** (verifies $< 10^{-4}$ roundtrip convergence)
- `test_pixel_to_normalized_roundtrip`: **PASSED** (verifies exact conversion between pixel grid and unit plane)
- `test_out_of_plane_yaw_error_monotonicity`: **PASSED** (confirms non-linear foreshortening: $0.0^\circ$ at $0^\circ$ yaw; $1.0^\circ$ at $15^\circ$; $4.1^\circ$ at $30^\circ$)
- `test_empirical_repeatability_statistics`: **PASSED** (validates sample dispersion $s$, standard error $s_m$, systematic bias $\Delta$, and $U_{95}$)

**Workstream Verdict:** **`PASS`**
