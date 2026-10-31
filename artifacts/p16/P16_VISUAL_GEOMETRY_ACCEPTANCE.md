# P16 Visual Movement & 3D Geometry Acceptance Report
**MSK Research Lab OS — Milestone P16**  
**Role:** Biomedical Visualization Engineer, 3D WebGL Auditor  
**Date:** 2026-10-31  
**Target Milestone:** P16 Qualification  
**Module:** [`workstation_ui.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/workstation_ui.py) (Three.js Scene Graph & WebGL Pipeline)  

---

## 1. Executive Summary

Milestone P16 validated the real-time 3D rendering pipeline, kinematic scene graph transformations, dynamic action line tracking, and visual epistemic integrity of the Shoulder Movement Lab in native WebGL.

The audit verified:
1. Authentic parent-child scene graph transformations across sternoclavicular, acromioclavicular, and glenohumeral pivots.
2. Exact spatial tracking of dynamic action lines between moving bone attachment frames.
3. Absence of fake physiological muscle deformation on rigid resting anatomical meshes.
4. Transparent distinction between simulation benchmarks and in-vivo measurement.
5. Framing of subacromial clearance status as an educational proximity estimate rather than a clinical diagnosis.

---

## 2. 3D Kinematic Scene Graph Verification

```
ShoulderScene
 └── shoulderRootGroup
      ├── shoulderThoraxGroup (FMA7487 Thorax, FMA7857 Sternum) [STATIC WORLD BASE]
      └── shoulderSCPivot (Sternoclavicular Joint: Position [-0.015, -0.165, 1.340])
           ├── shoulderClavicleGroup (FMA13322 Clavicle) [ROTATES Y: scRad]
           └── shoulderACPivot (Acromioclavicular Joint: Position [-0.130, 0.100, 0.015])
                ├── shoulderScapulaGroup (FMA13395 Scapula) [ROTATES Y: acRelRad, X: tiltRad]
                └── shoulderGHPivot (Glenohumeral Joint: Position [-0.020, -0.007, -0.025])
                     ├── shoulderHumerusGroup (FMA23130 Humerus) [ROTATES Y: ghRad]
                     └── shoulderElbowPivot (Elbow Joint: Position [-0.050, -0.003, -0.280])
                          └── shoulderForearmGroup (FMA23464 Radius, FMA23467 Ulna)
```

### 2.1 Joint Transform Oracles & Numerical Alignment
At each arm elevation angle $\theta_{Arm} \in [0^\circ, 180^\circ]$:
- **SC Pivot:** $\mathcal{R}_y(\theta_{SC})$ where $\theta_{SC} = 0.18 \times \theta_{Arm}$ (Normal) or $0.12 \times \theta_{Arm}$ (Restricted).
- **AC Pivot:** $\mathcal{R}_y(\theta_{AC,rel})\mathcal{R}_x(\theta_{Tilt})$ where $\theta_{AC,rel} = \theta_{ST} - \theta_{SC}$.
- **GH Pivot:** $\mathcal{R}_y(\theta_{GH})$ where $\theta_{GH} = \theta_{Arm} - \theta_{ST}$.
- **Total World Scapula Rotation:** $\theta_{SC} + \theta_{AC,rel} = \theta_{ST}$ (Exact).
- **Total World Humerus Rotation:** $\theta_{SC} + \theta_{AC,rel} + \theta_{GH} = \theta_{Arm}$ (Exact).

---

## 3. Dynamic Action Line Anchoring & Verification

### 3.1 Spatial Attachment Coordinates (Bone Anchor Frames)

| Muscle Compartment | Origin Anchor Frame | Origin 3D Offset (m) | Insertion Anchor Frame | Insertion 3D Offset (m) | Verified Tracking Behavior |
|---|---|---|---|---|---|
| `DELT1` | `shoulderClavicleGroup` | `[-0.014, 0.011, 0.080]` | `shoulderHumerusGroup` | `[0.009, -0.119, 0.006]` | Origin elevates with clavicle; insertion moves with humerus. |
| `DELT2` | `shoulderScapulaGroup` | `[-0.011, -0.000, 0.006]` | `shoulderHumerusGroup` | `[0.005, -0.136, 0.006]` | Origin rotates with scapula; insertion moves with humerus. |
| `DELT3` | `shoulderScapulaGroup` | `[-0.056, 0.001, -0.025]` | `shoulderHumerusGroup` | `[0.002, -0.076, 0.010]` | Line elongates as humerus abducts coronally. |
| `SUPSP` | `shoulderScapulaGroup` | `[-0.044, -0.015, -0.059]` | `shoulderHumerusGroup` | `[0.003, 0.011, 0.026]` | Passes superior to humeral head; shortens during early abduction. |
| `INFSP` | `shoulderScapulaGroup` | `[-0.074, -0.055, -0.048]` | `shoulderHumerusGroup` | `[-0.009, 0.005, 0.024]` | Crosses posterior joint line; elongates during elevation. |
| `SUBSC` | `shoulderScapulaGroup` | `[-0.072, -0.039, -0.065]` | `shoulderHumerusGroup` | `[0.014, 0.008, -0.013]` | Crosses anterior subscapular fossa to lesser tubercle. |
| `TMIN` | `shoulderScapulaGroup` | `[-0.096, -0.081, -0.053]` | `shoulderHumerusGroup` | `[-0.001, -0.013, 0.022]` | Follows inferior lateral border of scapula to greater tubercle. |
| `BICshort`| `shoulderScapulaGroup` | `[0.013, -0.039, -0.026]` | `shoulderForearmGroup` | `[-0.002, -0.038, -0.002]` | Spans coracoid process across GH and elbow joints to radius. |
| `BIClong` | `shoulderScapulaGroup` | `[-0.031, -0.024, -0.013]` | `shoulderForearmGroup` | `[-0.002, -0.038, -0.002]` | Tracks from supraglenoid tubercle down bicipital groove. |
| `TRIlong` | `shoulderScapulaGroup` | `[-0.046, -0.041, -0.014]` | `shoulderForearmGroup` | `[-0.022, 0.010, -0.001]` | Tracks from infraglenoid tubercle across elbow to olecranon. |

### 3.2 Verification of Action Line Updates
During animation loop execution (`updateActionLinesGeometry()`):
1. `item.originAnchor.getWorldPosition(vStart)` extracts instantaneous world coordinate.
2. `item.insertAnchor.getWorldPosition(vEnd)` extracts instantaneous world coordinate.
3. Vertex position buffer attributes (`line.geometry.attributes.position`) are updated and flagged `needsUpdate = true`.
4. Visual inspection on Microsoft Edge confirms lines remain rigidly attached to bone surfaces without lagging, drifting, or popping.

---

## 4. Absence of Fake Physiological Muscle Deformation

A frequent pitfall in medical visualization is applying arbitrary vertex shaders or morph targets to make 3D muscle meshes "bulge" when bones move, pretending this represents physiological muscle contraction.

- **Scientific Honesty Audit:**
  - BodyParts3D GLB meshes are rigid static anatomical geometry acquired from resting cadaveric or radiological scans.
  - In `shoulder_lab.py` and `workstation_ui.py`, all 3D muscle meshes are strictly classified as:
    ```
    mesh_classification: "STATIC_RESTING_ANATOMICAL_MESH"
    ```
  - Zero arbitrary morph target bulging, vertex stretching, or fake procedural deformations are applied to the 3D meshes.
  - Length and tension dynamics are communicated exclusively through:
    1. Dynamic 3D Action Lines tracking bone frames (`SIMPLIFIED_ORIGIN_INSERTION_CONNECTOR`).
    2. Numerical readouts in `#muscle-dynamics-card` ($l_{MT}, l_M, \Delta l_M$).
    3. KMSI color chips (`#3498db` Shortened, `#95a5a6` Nominal, `#f39c12` Moderate Stretch, `#e74c3c` High Stretch).

---

## 5. UI Ergonomics & Subacromial Clearance Framing

- **Non-Diagnostic Clearance Framing:** Subacromial clearance readouts (`#readout-subacromial-status`) explicitly display `Adequate Clearance` or `Compromised (Impingement Risk)` with the subtitle:
  > *"Educational Hypothesis (Geometric Proximity Model)"*
- **Incremental vs. Cumulative Rhythm Readout:** Live Joint Angle card displays `#readout-rhythm-type` with both ratios:
  - At 0°: `Inc: Setting Phase (ST=0°) | Cum: Neutral 0°`
  - At 90° (Normal): `Inc: 2.0:1 (>30°) | Cum: 3.5:1`
  - At 90° (Restricted): `Inc: 4.0:1 (>30°) | Cum: 6.5:1`
- **P16-D Visual Geometry Gate: PASSED.**
