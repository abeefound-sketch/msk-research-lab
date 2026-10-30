# MSK Research Lab OS — P10 Metrology & Geometry Independent Challenge

**Milestone:** P10  
**Verification Role:** Computer Vision & Metrology Engineer, Applied Mathematics Auditor  
**Target Files:**
- [`src/msk_research_lab/studio/calibrated_registration.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/studio/calibrated_registration.py)
- [`src/msk_research_lab/motion/stereo.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/stereo.py)
- [`src/msk_research_lab/studio/dien_chan.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/studio/dien_chan.py)
- [`tests/unit/test_p10_metrology_degeneracy.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_p10_metrology_degeneracy.py)

---

## 1. 6-DoF Levenberg-Marquardt Pose Optimization

The workstation uses a full 6-DoF non-linear Levenberg-Marquardt PnP solver to estimate rotation vector $\mathbf{r} \in \mathfrak{so}(3)$ and translation vector $\mathbf{t} \in \mathbb{R}^3$ from canonical anatomical landmarks (`SELLION`, `PRONASALE`, `SUBNASALE`, `GNATHION`, `TRAGION_LEFT`, `TRAGION_RIGHT`).

```
P_cam = R(r) * X_obj + t
u = fx * (X_cam / Z_cam) + cx
v = fy * (Y_cam / Z_cam) + cy
```

### Collinear Landmark Degeneracy Rejection (DEF-25)
- **Problem:** If input landmarks are collinear (lying on a single 1D axis, e.g. Sellion, Pronasale, Subnasale, Gnathion along the facial midline), rotation around that line is unconstrained mathematically. The Levenberg-Marquardt damping could converge to an arbitrary rotation.
- **Remediation:** Added 3D spatial variance and pairwise cross-product magnitude evaluation across centered landmark vectors:
  $$\mathbf{d}_i = \mathbf{X}_i - \bar{\mathbf{X}}$$
  $$\max_{i < j} \|\mathbf{d}_i \times \mathbf{d}_j\| \ge 1.0\text{ mm}^2$$
  If all pairwise cross-products vanish ($< 1.0\text{ mm}^2$), the solver fails closed immediately, raising:
  `CalibratedRegistrationError("Degenerate landmark geometry: input 3D landmarks are collinear or lack 2D/3D spatial variance.")`.

---

## 2. Rotated Camera-Frame Depth in Ray-Surface Projection (DEF-24)

### The Depth Error in P9
In P9, 2D reflexology back-projection computed target intersection depth as:
$$z_{target} = t_z + ref\_3d[2]$$
However, `ref_3d` is defined in the head object coordinate frame. Under head yaw or pitch, the actual depth of the reference landmark in the camera optical frame is:
$$Z_{cam} = (\mathbf{R} \mathbf{X}_{ref} + \mathbf{t})_z = R_{20} X + R_{21} Y + R_{22} Z + t_z$$
Using $t_z + ref\_3d[2]$ assumed $\mathbf{R} = \mathbf{I}$, producing depth errors whenever the head was rotated.

### Remediation & Verification
Updated `register_2d_reflexology_point_to_3d()` to compute true rotated camera depth:
```python
ref_cam_z = R[2][0] * ref_3d[0] + R[2][1] * ref_3d[1] + R[2][2] * ref_3d[2] + t[2]
z_target = ref_cam_z
scale = z_target / ray_cam_unit[2]
```
Verified in `test_rotated_camera_frame_depth_ray_projection` under yaw $25^\circ$ and pitch $10^\circ$, successfully reconstructing Pronasale 3D coordinates within $< 1.5$ mm tolerance.

---

## 3. Stereo Photogrammetry Depth Uncertainty & Sensitivity

Depth uncertainty for parallel stereo photogrammetry scales quadratically with depth and inversely with baseline and focal length:
$$\sigma_Z = \frac{Z^2}{f \cdot b} \sigma_d$$

### Focal Length Sensitivity Analysis Matrix ($b = 200\text{ mm}, Z = 1000\text{ mm}, \sigma_d = 0.5\text{ px}$)

| Focal Length ($f$) | Baseline ($b$) | Depth ($Z$) | Depth Uncertainty ($\sigma_Z$) | Relative Uncertainty |
| :---: | :---: | :---: | :---: | :---: |
| 400 px | 200 mm | 1000 mm | **6.250 mm** | 0.625% |
| 600 px | 200 mm | 1000 mm | **4.167 mm** | 0.417% |
| 800 px | 200 mm | 1000 mm | **3.125 mm** | 0.312% |
| 1000 px | 200 mm | 1000 mm | **2.500 mm** | 0.250% |
| 1200 px | 200 mm | 1000 mm | **2.083 mm** | 0.208% |
| 1600 px | 200 mm | 1000 mm | **1.562 mm** | 0.156% |

---

## 4. Epistemic Safety Invariants

1. **`CANNOT_IMPLICITLY_PROJECT_2D_TO_3D`:** Strictly blocks 2D-to-3D projection attempts whenever photogrammetric optical calibration context is absent.
2. **`PHYSICAL_STEREO_HARDWARE_GATE`:** Strictly reports `BLOCKED (DUAL_CAMERA_UNAVAILABLE)` on single-camera workstation hosts, preventing simulated stereo from claiming physical multi-sensor operation.
