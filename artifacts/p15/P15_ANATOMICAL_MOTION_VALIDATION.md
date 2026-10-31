# P15 Anatomical Motion & Shoulder Girdle Kinematic Validation
**MSK Research Lab OS — Milestone P15**  
**Role:** Principal Biomedical Visualization Engineer, OpenSim Biomechanics Engineer  
**Date:** 2026-10-31  
**Module:** [`shoulder_lab.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/biomechanics/shoulder_lab.py) / [`workstation_ui.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/workstation_ui.py)

---

## 1. Shoulder Complex Multi-Articulation Architecture

The human shoulder is an integrated kinematic chain of 4 articulations operating synchronously during upper limb elevation:

```mermaid
graph TD
    Axial["Axial Skeleton (Sternum & Thorax)"] -->|Sternoclavicular Joint (SC)| Clavicle["Clavicle (FMA13322)"]
    Clavicle -->|Acromioclavicular Joint (AC)| Scapula["Scapula (FMA13395)"]
    Axial -.->|Physiological Gliding Interface| Scapula
    Scapula -->|Glenohumeral Joint (GH)| Humerus["Humerus (FMA23130)"]
    Humerus -->|Elbow Articulation| Forearm["Forearm & Hand (Radius/Ulna)"]
```

### 1.1 Mathematical Kinematics of Elevation

1. **Glenohumeral (GH) Articulation:**
   - 3-DOF ball-and-socket model with instantaneous center of rotation located at humeral head centroid.
   - Coronal elevation component $\theta_{GH}$:
     $$\theta_{GH}(\theta) = \begin{cases} 
     \theta & \text{if } \theta \le 30^\circ \\
     30^\circ + \frac{2}{3}(\theta - 30^\circ) & \text{if } \theta > 30^\circ 
     \end{cases}$$
2. **Scapulothoracic (ST) Gliding Interface:**
   - Upward rotation component $\theta_{ST}$:
     $$\theta_{ST}(\theta) = \begin{cases} 
     0^\circ & \text{if } \theta \le 30^\circ \\
     \frac{1}{3}(\theta - 30^\circ) & \text{if } \theta > 30^\circ 
     \end{cases}$$
   - Coupled posterior tilt: $\theta_{ST,tilt}(\theta) = 0.2 \cdot \theta_{ST}(\theta)$.
3. **Sternoclavicular (SC) Joint:**
   - Elevation component $\theta_{SC} = 0.18 \cdot \theta$ (reaching $32.4^\circ$ at $180^\circ$).

---

## 2. Anatomical Mesh vs. Dynamic Action Line Epistemic Distinction

A critical scientific finding of Milestone P15 is the physical limitation of surface meshes derived from rigid BodyParts3D acquisitions:

> [!IMPORTANT]
> **Static Anatomical Mesh Realities:**
> BodyParts3D GLB meshes represent rigid anatomical surfaces frozen in a neutral resting posture. They do NOT contain volumetric finite-element muscle fibers, contractile motor units, or non-linear soft tissue deformation mechanics.
> 
> Parenting a rigid muscle mesh to a single moving bone causes unphysical penetration or disjointing; leaving it static fails to depict movement.

### 2.1 Dual-Representation Architecture (P15-A Implementation)

To maintain uncompromising scientific honesty while providing intuitive visual clarity, the workstation implements a **dual-representation paradigm**:

1. **Contextual Skeletal & Muscular Meshes (`STATIC_RESTING_ANATOMICAL_MESH`):**
   - High-resolution BodyParts3D GLB meshes provide realistic anatomical shape, volumetric contours, and spatial landmarks.
   - Clearly labeled in the UI as *Static Anatomical Meshes*.
2. **Dynamic 3D OpenSim Action Lines (`REPRESENTED_BY_OPENSIM_MUSCLE_PATH`):**
   - Dynamic 3D line visualizers connect anatomical origin and insertion anchor nodes parented directly to their respective bone frames (`shoulderClavicleGroup`, `shoulderScapulaGroup`, `shoulderHumerusGroup`).
   - Line coordinates update in real time during animation and timeline scrubbing.
   - Action line colors dynamically reflect normalized fiber length ($\tilde{l}_M$) using standardized KMSI color chips.

---

## 3. Kinematic Verification Oracle Benchmark

| Elevation Angle ($\theta$) | GH Elevation ($\theta_{GH}$) | ST Upward Rotation ($\theta_{ST}$) | SC Elevation ($\theta_{SC}$) | Total Verified Elevation | Kinematic Status |
|---|---|---|---|---|---|
| $0.0^\circ$ (Rest) | $0.0^\circ$ | $0.0^\circ$ | $0.0^\circ$ | $0.0^\circ$ | Neutral rest alignment |
| $30.0^\circ$ (Setting Limit) | $30.0^\circ$ | $0.0^\circ$ | $5.4^\circ$ | $30.0^\circ$ | Setting phase complete |
| $45.0^\circ$ (Early Abduction) | $40.0^\circ$ | $5.0^\circ$ | $8.1^\circ$ | $45.0^\circ$ | 2:1 coordination engaged |
| $90.0^\circ$ (Horizontal) | $70.0^\circ$ | $20.0^\circ$ | $16.2^\circ$ | $90.0^\circ$ | Acromial clearance preserved |
| $120.0^\circ$ (High Abduction) | $90.0^\circ$ | $30.0^\circ$ | $21.6^\circ$ | $120.0^\circ$ | Scapular platform active |
| $180.0^\circ$ (Overhead Full) | $130.0^\circ$ | $50.0^\circ$ | $32.4^\circ$ | $180.0^\circ$ | Maximum physiological reach |

All transformations verified with numerical tolerance $\epsilon < 10^{-6}$ in unit test [`test_p14_geometry_and_animation_oracle.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_p14_geometry_and_animation_oracle.py).
