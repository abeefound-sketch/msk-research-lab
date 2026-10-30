# P14 OpenSim to Three.js 3D Transformation Pipeline Audit
**MSK Research Lab OS — Milestone P14**  
**Role:** Principal Biomedical Visualization Engineer, Scientific Software Auditor  
**Date:** 2026-10-30  
**Verification Method:** Analytical Mathematical Forward Kinematics Oracle  
**Test Suite:** `tests/unit/test_p14_geometry_and_animation_oracle.py` (17/17 PASS)  

---

## 1. Executive Summary

Milestone P14 performed an end-to-end mathematical audit of the 3D transformation pipeline:
$$\text{OpenSim / Model State} \longrightarrow \text{Joint Coordinates} \longrightarrow \text{Coordinate Mapping} \longrightarrow \text{Three.js Bone Pivots} \longrightarrow \text{Rendered Meshes}$$

The audit uncovered a subtle kinematic defect in P13's initial Three.js pivot implementation (cataloged as **DEF-42**), where clavicular motion had been applied around the vertical $Z$-axis (causing horizontal retraction) rather than the coronal $Y$-axis (causing vertical elevation). 

We formulated and proved an exact hierarchical rotation compensation model where:
1. Clavicle elevates around the coronal axis ($+Y$) by $\theta_{SC}$.
2. Acromioclavicular pivot rotates relative to the clavicle by $\theta_{AC,rel} = \theta_{ST} - \theta_{SC}$ around $+Y$, and tilts around $+X$ by $\theta_{tilt}$.
3. Glenohumeral pivot rotates relative to the scapula by $\theta_{GH} = \theta_{arm} - \theta_{ST}$ around $+Y$.
4. Composite world space orientations are proven to exactly equal $\theta_{SC}$ for the clavicle, $\theta_{ST}$ for the scapula, and $\theta_{arm}$ for the humerus at every angle from $0^\circ$ to $180^\circ$.

---

## 2. Coordinate System Mapping & Handedness

### 2.1 Anatomical RAS Convention (BodyParts3D 3.0)
BodyParts3D GLB assets are calibrated in meters with respect to a standard human anatomical scanning reference frame:
- **$+X$ (Right-to-Left):** Lateral left direction. Right shoulder structures have negative $X$ ($x \in [-0.25, -0.01]\text{ m}$).
- **$+Y$ (Posterior-to-Anterior):** Posterior direction is positive ($+Y$); Anterior (ventral) direction is negative ($-Y$). Sternum is anterior at $y \approx -0.19\text{ m}$; scapula is posterior at $y \approx 0.00\text{ m}$.
- **$+Z$ (Inferior-to-Superior):** Vertical axis. Superior (cranial) is positive ($+Z$); Inferior (caudal) is negative ($-Z$). Shoulder girdle spans $z \in [1.05, 1.36]\text{ m}$.

### 2.2 Three.js WebGL Scene Representation
Three.js uses a right-handed Cartesian coordinate system:
$$\vec{i} \times \vec{j} = \vec{k}$$
Because BodyParts3D GLB meshes were imported without altering local vertex winding, the scene camera was positioned to view the right shoulder girdle:
- **Camera Position:** $\vec{p}_{cam} = (-0.35, -0.65, 1.45)$ (Anterior-lateral-superior viewpoint).
- **Camera Target:** $\vec{p}_{target} = (-0.12, -0.05, 1.30)$ (Centered on the glenohumeral joint).

### 2.3 Motion in the Coronal (Frontal) Plane
In the anatomical RAS system, coronal arm elevation occurs in the $X-Z$ plane (lateral-vertical plane).
The axis perpendicular to the $X-Z$ plane is the $Y$-axis (anterior-posterior axis).
Applying a right-handed rotation around the $+Y$ axis:
$$\mathbf{R}_y(\theta) = \begin{pmatrix} \cos\theta & 0 & \sin\theta \\ 0 & 1 & 0 \\ -\sin\theta & 0 & \cos\theta \end{pmatrix}$$
For a limb segment hanging along $-Z$ ($\vec{v} = (0, 0, -1)$):
$$\mathbf{R}_y(\theta) \begin{pmatrix} 0 \\ 0 \\ -1 \end{pmatrix} = \begin{pmatrix} -\sin\theta \\ 0 \\ -\cos\theta \end{pmatrix}$$
- At $\theta = 0^\circ$: $(0, 0, -1)$ (Hanging vertically downward).
- At $\theta = 90^\circ$: $(-1, 0, 0)$ (Pointing laterally along $-X$, i.e. abducted to the right).
- At $\theta = 180^\circ$: $(0, 0, +1)$ (Pointing vertically overhead along $+Z$).

Thus, rotation about $+Y$ is mathematically verified as the coronal elevation axis for the right upper extremity.

---

## 3. Mathematical Hierarchy Formulation & Compensation

The anatomical upper extremity kinematic chain is a branched kinematic tree anchored to the thorax:
$$\text{Thorax} \xrightarrow{\mathbf{T}_{SC}} \text{Clavicle} \xrightarrow{\mathbf{T}_{AC}} \text{Scapula} \xrightarrow{\mathbf{T}_{GH}} \text{Humerus} \xrightarrow{\mathbf{T}_{Elbow}} \text{Forearm}$$

### 3.1 Pivot Origins in World Space
From anatomical landmark registration:
- **Sternoclavicular Joint (SC):** $\vec{p}_{SC} = (-0.015, -0.165, 1.340)\text{ m}$
- **Acromioclavicular Joint (AC) relative to SC:** $\Delta\vec{p}_{AC} = (-0.130, 0.100, 0.015)\text{ m}$
  - Absolute AC rest position: $\vec{p}_{AC} = (-0.145, -0.065, 1.355)\text{ m}$
- **Glenohumeral Joint (GH) relative to AC:** $\Delta\vec{p}_{GH} = (-0.020, -0.007, -0.025)\text{ m}$
  - Absolute GH rest position: $\vec{p}_{GH} = (-0.165, -0.072, 1.330)\text{ m}$
- **Elbow Joint relative to GH:** $\Delta\vec{p}_{Elbow} = (-0.050, -0.003, -0.280)\text{ m}$
  - Absolute Elbow rest position: $\vec{p}_{Elbow} = (-0.215, -0.075, 1.050)\text{ m}$

### 3.2 Hierarchical Relative Angle Compensation
Because `shoulderACPivot` is a child of `shoulderSCPivot` in the scene graph, any rotation applied to `shoulderSCPivot` is inherited by `shoulderACPivot`.

To ensure that the world-space scapular upward rotation matches the clinical target $\theta_{ST}$:
$$\theta_{world,scapula} = \theta_{SC} + \theta_{AC,relative} \equiv \theta_{ST}$$
$$\implies \theta_{AC,relative} = \theta_{ST} - \theta_{SC}$$

Similarly, because `shoulderGHPivot` is a child of `shoulderACPivot`:
$$\theta_{world,humerus} = \theta_{world,scapula} + \theta_{GH} \equiv \theta_{arm}$$
$$\implies \theta_{world,humerus} = \theta_{ST} + \theta_{GH} = \theta_{arm}$$
$$\implies \theta_{GH} = \theta_{arm} - \theta_{ST}$$

### 3.3 Proof of Exactness at Key Kinematic States

| Total Arm Elevation ($\theta_{arm}$) | SC Elevation ($\theta_{SC}$) | Scapular Upward Rot ($\theta_{ST}$) | AC Relative Rot ($\theta_{AC,rel}$) | GH Elevation ($\theta_{GH}$) | World Humerus Angle | World Scapula Angle |
|---|---|---|---|---|---|---|
| **0.0°** | 0.00° | 0.00° | 0.00° | 0.00° | **0.00°** | **0.00°** |
| **30.0°** (Setting) | 5.40° | 0.00° | -5.40° | 30.00° | **30.00°** | **0.00°** |
| **45.0°** | 8.10° | 5.00° | -3.10° | 40.00° | **45.00°** | **5.00°** |
| **90.0°** (Mid-range) | 16.20° | 20.00° | +3.80° | 70.00° | **90.00°** | **20.00°** |
| **120.0°** | 21.60° | 30.00° | +8.40° | 90.00° | **120.00°** | **30.00°** |
| **180.0°** (Overhead) | 32.40° | 50.00° | +17.60° | 130.00° | **180.00°** | **50.00°** |

**Conclusion:** At every angle, the mathematical forward kinematics agree with clinical theory with zero residual error.

---

## 4. Verification of Forward Shoulder Compensatory Mechanics

In the Forward Shoulder Restricted comparison model:
- Scapular upward rotation is restricted by 40%: $\theta_{ST} = 0.60 \times \frac{arm - 30^\circ}{3}$.
- At $90^\circ$ elevation: $\theta_{ST} = 12.0^\circ$ (instead of $20.0^\circ$).
- To reach $90^\circ$ total elevation: $\theta_{GH} = 90^\circ - 12^\circ = 78.0^\circ$ (instead of $70.0^\circ$).
- At $180^\circ$ full overhead elevation: $\theta_{ST} = 30.0^\circ$ (instead of $50.0^\circ$).
- The glenohumeral joint must over-elevate to $\theta_{GH} = 150.0^\circ$ (instead of $130.0^\circ$)!

This captures the recognized clinical compensation principle: when the scapula fails to rotate upward, the glenohumeral joint undergoes hyper-mobility and excessive shear to achieve functional overhead reach.

---

## 5. Verification Against Independent Mathematical Oracle

The test suite `tests/unit/test_p14_geometry_and_animation_oracle.py` executes 17 formal verification tests:
1. `test_neutral_zero_degree_rest_position`: Confirms identity matrix at 0° and exact anatomical coordinates.
2. `test_normal_scapulohumeral_rhythm_at_key_angles`: Tests 0°, 30°, 45°, 90°, 120°, 180° against oracle predictions.
3. `test_forward_shoulder_restricted_kinematic_compensation`: Confirms compensatory over-elevation.
4. `test_overhead_elbow_elevation_vector`: Proves the elbow vector elevates from $z = 1.05\text{ m}$ to $z = 1.61\text{ m}$ overhead.
5. `test_subacromial_clearance_geometric_proximity_oracle`: Proves minimum proximity between acromion and greater tubercle occurs between 60° and 120° in restricted posture.
6. Schema and provenance tests (12 tests) confirming all outputs contain valid metadata.

**Result: 17 / 17 PASS (100%).**
