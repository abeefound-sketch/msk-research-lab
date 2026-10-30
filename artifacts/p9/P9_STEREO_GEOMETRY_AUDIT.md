# MSK RESEARCH LAB OS — P9-C STEREO GEOMETRY & EPIPOLAR KINEMATICS AUDIT

## 1. Executive Summary

- **Audit Date:** 2026-10-30
- **Auditor Role:** Computer Vision & Epipolar Geometry Auditor
- **Target Algorithms:** Direct Linear Transformation (DLT) Triangulation, Essential Matrix Projection, Reprojection Gating, and Angular Uncertainty.
- **Audit Verdict:** **PASS — MATHEMATICALLY SOUND & FAIL-CLOSED**

---

## 2. Epipolar Geometry & Triangulation Architecture

### 2.1 Pinhole Projection Formulation
For calibrated left camera $C_1$ and right camera $C_2$:
$$\mathbf{P}_1 = \mathbf{K}_1 [\mathbf{I} \mid \mathbf{0}], \quad \mathbf{P}_2 = \mathbf{K}_2 [\mathbf{R} \mid \mathbf{t}]$$

The Essential Matrix $\mathbf{E} = [\mathbf{t}]_\times \mathbf{R}$ satisfies the epipolar constraint:
$$\mathbf{x}_2^T \mathbf{K}_2^{-T} \mathbf{E} \mathbf{K}_1^{-1} \mathbf{x}_1 = 0$$

### 2.2 SVD / Nullspace DLT Solver
Given 2D correspondences $\mathbf{x}_1 = (u_1, v_1)$ and $\mathbf{x}_2 = (u_2, v_2)$, the algebraic system $\mathbf{A} \mathbf{X} = \mathbf{0}$ is formed:
$$\mathbf{A} = \begin{bmatrix}
u_1 \mathbf{p}_1^{3T} - \mathbf{p}_1^{1T} \\
v_1 \mathbf{p}_1^{3T} - \mathbf{p}_1^{2T} \\
u_2 \mathbf{p}_2^{3T} - \mathbf{p}_2^{1T} \\
v_2 \mathbf{p}_2^{3T} - \mathbf{p}_2^{2T}
\end{bmatrix}$$

The homogeneous 3D coordinate $\mathbf{X}$ is solved by finding the right singular vector corresponding to the minimal singular value of $\mathbf{A}$ via shifted inverse iteration on $\mathbf{M} = \mathbf{A}^T \mathbf{A}$ ([`_solve_nullspace_4x4`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/stereo.py#L105)).

---

## 3. Residual Error Gating

Physical biomechanics requires strict rejection of mismatched or occluded landmarks:
- Reprojection error is evaluated across both views:
  $$e = \frac{1}{2} \left( \|\mathbf{x}_1 - \pi_1(\mathbf{X})\| + \|\mathbf{x}_2 - \pi_2(\mathbf{X})\| \right)$$
- If $\max(e_A, e_B, e_C) > 2.50\text{ px}$, the assessment fails closed with `StereoMetrologyError`.
- Verified in [`tests/unit/test_stereo_kinematics.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_stereo_kinematics.py): landmark perturbations exceeding 2.5 px are immediately rejected.

---

## 4. Metrological Reliability Invariant

The audit confirms that the stereophotogrammetry pipeline correctly separates:
1. **Geometric Coordinate Invariance:** Proven rotation invariance for rigid 3D angle calculations.
2. **Empirical Optical Limits:** Explicitly quantified $\sigma_Z \propto \frac{Z^2}{f \cdot b} \sigma_d$ depth uncertainty and propagated angular error bounds $\sigma_\theta$.
3. **Hardware Gate Integrity:** Guaranteed fail-closed reporting of `BLOCKED (DUAL_CAMERA_UNAVAILABLE)` when physical multi-camera devices are not detected.
