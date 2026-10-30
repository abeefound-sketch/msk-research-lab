# MSK RESEARCH LAB OS — P9-C INDEPENDENT METROLOGY VALIDATION REPORT

## 1. Executive Summary

- **Validation Date:** 2026-10-30
- **Auditor Role:** Metrology Verification Engineer & Biomedical Software Safety Auditor
- **Target Module:** [`src/msk_research_lab/motion/stereo.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/stereo.py)
- **Scope:** Resolution of P8-Metrology Defect DEF-11 / Metrological Distinction between Mathematical Coordinate Rotation Invariance and Empirical Stereo Photogrammetry Depth Uncertainty ($\sigma_Z$).
- **Validation Verdict:** **PASS — METROLOGICALLY DEFENDED & VERIFIED**

---

## 2. Metrological Theory: Coordinate Invariance vs. Empirical Uncertainty

### 2.1 The Mathematical Claim vs. Empirical Reality
In P8 documentation, the 3D joint angle calculation was marked as `"is_immune_to_yaw": True`. While it is mathematically true that the inner product of two rigid vectors:
$$\cos\theta = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$
is invariant under 3D Euclidean rotation ($R \in \mathrm{SO}(3)$), this invariance assumes ground-truth noiseless 3D coordinates.

In physical stereo photogrammetry:
1. **Depth Uncertainty Scaling:**
   $$\sigma_Z = \frac{Z^2}{f \cdot b} \cdot \sigma_d$$
   Uncertainty in reconstructed depth coordinates increases **quadratically** with object distance $Z$ and inversely with stereo baseline $b$.
2. **Out-of-Plane Yaw Effect:**
   When a patient limb rotates in out-of-plane yaw, anatomical landmarks suffer sensor foreshortening, feature compression across pixels, and epipolar matching noise, increasing disparity uncertainty $\sigma_d$.
3. **Propagated Angular Uncertainty:**
   Depth uncertainty at distal vertices produces angular measurement uncertainty:
   $$\sigma_\theta \approx \frac{180}{\pi} \cdot \sigma_{Z,\max} \cdot \sqrt{\frac{1}{L_1^2} + \frac{1}{L_2^2}}$$

---

## 3. Empirical Sensitivity Table ($\sigma_Z$ vs $Z$ and $b$)

Simulated with nominal sensor focal length $f = 1000\text{ px}$ and standard disparity matching variance $\sigma_d = 0.5\text{ px}$:

| Baseline $b$ (mm) | Depth $Z$ (mm) | Depth Uncertainty $\sigma_Z$ (mm) | Relative Depth Error $\sigma_Z / Z$ (%) |
| :---: | :---: | :---: | :---: |
| 100.0 | 500.0 | 1.25 mm | 0.25% |
| 100.0 | 1000.0 | 5.00 mm | 0.50% |
| 100.0 | 1500.0 | 11.25 mm | 0.75% |
| 100.0 | 2000.0 | 20.00 mm | 1.00% |
| 100.0 | 3000.0 | 45.00 mm | 1.50% |
| **200.0** | 500.0 | 0.62 mm | 0.12% |
| **200.0** | 1000.0 | 2.50 mm | 0.25% |
| **200.0** | 1500.0 | 5.62 mm | 0.37% |
| **200.0** | 2000.0 | 10.00 mm | 0.50% |
| **200.0** | 3000.0 | 22.50 mm | 0.75% |
| 400.0 | 1000.0 | 1.25 mm | 0.12% |
| 400.0 | 2000.0 | 5.00 mm | 0.25% |
| 400.0 | 3000.0 | 11.25 mm | 0.38% |

---

## 4. Hardware Gate Verification

The physical hardware probe [`probe_physical_stereo_hardware()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/stereo.py#L324) was audited:
- On hosts lacking dual genlocked video devices (e.g. single webcam or WSL2):
  - Returns `status: "BLOCKED (DUAL_CAMERA_UNAVAILABLE)"`
  - Returns `stereo_hardware_available: false`
  - Fails closed; never permits uncalibrated 3D motion claims in production.

---

## 5. Verification Test Evidence

Verified via [`tests/unit/test_p9_metrology_uncertainty.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_p9_metrology_uncertainty.py):
- `test_depth_uncertainty_quadratic_scaling`: PASSED (confirmed exact 4x uncertainty at 2x distance).
- `test_depth_uncertainty_inverse_baseline_scaling`: PASSED (confirmed inverse baseline proportionality).
- `test_depth_uncertainty_parameter_validation`: PASSED.
- `test_sensitivity_table_generation`: PASSED.
- `test_joint_angle_uncertainty_propagation`: PASSED.
- `test_probe_physical_hardware_preserves_blocked_invariant`: PASSED.
