# P13 Integration Architecture: Interactive Anatomy & Biomechanics Workstation

**Auditor / Architect:** Principal Software Architect, Biomedical Visualization Engineer  
**Date:** 2026-10-30  
**Status:** ARCHITECTURAL SPECIFICATION & DESIGN  

---

## 1. System Topology & Data Flow

The integration architecture embeds the Shoulder Movement Lab into the established MSK Research Lab OS workstation, maintaining complete offline isolation and strict local loopback execution:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MSK WORKSTATION CLIENT (BROWSER)                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    SHOULDER MOVEMENT LAB VIEW                         │  │
│  │                                                                       │  │
│  │  ┌───────────────────────────┐  ┌──────────────────────────────────┐  │  │
│  │  │   Three.js 3D Viewport    │  │     Interactive Control Panel    │  │  │
│  │  │ • OrbitControls (Pan/Zoom)│  │ • Play / Pause / Step Controls   │  │  │
│  │  │ • Hierarchical Pivots:    │  │ • Animation Speed (0.25x - 2.0x) │  │  │
│  │  │   - SC Pivot (Clavicle)   │  │ • Timeline Scrubber (0° - 180°)  │  │  │
│  │  │   - AC Pivot (Scapula)    │  │ • Layer Toggles (Bones/Muscles)  │  │  │
│  │  │   - GH Pivot (Humerus)    │  │ • Comparison Selector            │  │  │
│  │  │ • 13 BodyParts3D Meshes   │  │ • Angle Readout Displays         │  │  │
│  │  │ • Raycaster Selection     │  │ • Anatomical Description Box     │  │  │
│  │  └─────────────▲─────────────┘  └────────────────▲─────────────────┘  │  │
│  └────────────────┼─────────────────────────────────┼────────────────────┘  │
└───────────────────┼─────────────────────────────────┼───────────────────────┘
                    │ GLB Assets                      │ JSON Trajectories /
                    │ via HTTP GET                    │ Annotations
┌───────────────────┴─────────────────────────────────┴───────────────────────┐
│                   FASTAPI BACKEND (LOCAL LOOPBACK 127.0.0.1)                 │
│                                                                             │
│  ┌───────────────────────────────┐  ┌────────────────────────────────────┐  │
│  │    Static Asset Mount         │  │  Biomechanics REST API Router      │  │
│  │  `/static/atlas/models/*`     │  │  `/api/v1/biomechanics/shoulder/*` │  │
│  │  • BodyParts3D GLB Meshes     │  │  • `GET /manifest`                 │  │
│  │  • `atlas_manifest.json`      │  │  • `GET /kinematics/trajectory`    │  │
│  │                               │  │  • `GET /muscles/response`         │  │
│  │                               │  │  • `GET /comparisons`              │  │
│  │                               │  │  • `GET /annotations/{id}`        │  │
│  └───────────────▲───────────────┘  └────────────────▲───────────────────┘  │
└──────────────────┼───────────────────────────────────┼──────────────────────┘
                   │                                   │
┌──────────────────┴───────────────────────────────────┴───────────────────────┐
│                    LOCAL STORAGE & VERIFIED DATA ORACLES                     │
│                                                                             │
│  • `2data/models/atlas/`: 13 CC BY-SA 2.1 JP BodyParts3D GLB Files          │
│  • `src/msk_research_lab/biomechanics/shoulder_lab.py`: Trajectory Engine    │
│  • OpenSim `MOBL_ARMS_41` Verified Kinematic Dataset (0° - 180° Elevation)  │
│  • Safe Harbor / Offline SQLite Registry Database                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Anatomical Kinematic Scene Graph

The Three.js scene graph models the genuine anatomical articulation of the human shoulder girdle:

```
threeScene
  └── AnatomyRoot (Position offset: [0.15, -0.05, 0.0])
        ├── thoraxGroup (Fixed Reference Body)
        │     ├── FMA7487 (Sternum Body)
        │     └── FMA7857 (Right 1st Rib)
        │
        └── sternoclavicularPivot (Joint J_sc at [-0.015, -0.165, 1.340])
              │ [Rotates Z-axis: Clavicular Elevation / Depression]
              │
              ├── clavicleGroup (Offset [+0.015, +0.165, -1.340])
              │     └── FMA13322 (Right Clavicle)
              │
              └── acromioclavicularPivot (Joint J_ac at [-0.130, +0.100, +0.015])
                    │ [Rotates Y-axis: Scapular Upward / Downward Rotation]
                    │
                    ├── scapulaGroup (Offset [+0.145, +0.065, -1.355])
                    │     └── FMA13395 (Right Scapula)
                    │
                    └── glenohumeralPivot (Joint J_gh at [-0.020, -0.007, -0.025])
                          │ [Rotates Y-axis & X-axis: Humeral Elevation & Plane]
                          │
                          ├── humerusGroup (Offset [+0.165, +0.072, -1.330])
                          │     └── FMA23130 (Right Humerus)
                          │
                          └── elbowPivot (Joint J_hu at [-0.050, -0.003, -0.280])
                                │ [Rotates X-axis: Forearm Flexion / Extension]
                                │
                                └── forearmGroup (Offset [+0.215, +0.075, -1.050])
                                      ├── FMA23464 (Radius)
                                      └── FMA23467 (Ulna)
```

### Muscle Path Alignment
Muscles are positioned in anatomical registration:
- **Deltoid Clavicular Head (`FMA34680`):** Anchored to Clavicle and Humerus.
- **Deltoid Acromial Head (`FMA34682`):** Anchored to Acromion Process and Deltoid Tuberosity.
- **Biceps Brachii (`FMA37684`, `FMA37686`):** Originates from Coracoid Process and Supraglenoid Tubercle, inserting to Radial Tuberosity.
- **Brachialis (`FMA37668`):** Anterior mid-humerus to coronoid process.
- **Triceps Brachii (`FMA37699`):** Infraglenoid tubercle of scapula to olecranon.

---

## 3. Mathematical Kinematic Coupler Equations

The shoulder elevation motion follows the verified Inman 2:1 Scapulohumeral Rhythm derived from `MOBL_ARMS_41.osim`:

Let $\theta_{\text{arm}} \in [0^\circ, 180^\circ]$ be the total shoulder elevation angle:

1. **Clavicular Elevation ($\theta_{\text{sc}}$ at Sternoclavicular Joint):**
   $$\theta_{\text{sc}}(\theta_{\text{arm}}) = 0.18 \times \theta_{\text{arm}} \quad (\text{yielding } \approx 32.4^\circ \text{ elevation at full } 180^\circ \text{ arm raise})$$

2. **Scapular Upward Rotation ($\theta_{\text{ac}}$ at Acromioclavicular / Scapulothoracic Joint):**
   $$\theta_{\text{ac}}(\theta_{\text{arm}}) = \begin{cases} 
   0^\circ & \theta_{\text{arm}} \le 30^\circ \quad (\text{Setting Phase}) \\
   \frac{1}{3} \times (\theta_{\text{arm}} - 30^\circ) & \theta_{\text{arm}} > 30^\circ \quad (\text{yielding } 50.0^\circ \text{ upward rotation at } 180^\circ)
   \end{cases}$$

3. **Glenohumeral Humeral Elevation ($\theta_{\text{gh}}$):**
   $$\theta_{\text{gh}}(\theta_{\text{arm}}) = \theta_{\text{arm}} - \theta_{\text{ac}}(\theta_{\text{arm}}) \quad (\text{yielding } 130.0^\circ \text{ at full } 180^\circ \text{ arm raise})$$

4. **Forward Shoulder Posture (Impingement / Restricted Comparison Model):**
   In the comparative "Forward Shoulder Posture" state:
   - Scapular resting pose is anteriorly tilted $+12.0^\circ$ and internally rotated $+8.0^\circ$.
   - Scapular upward rotation is restricted by $40\%$: $\theta_{\text{ac,restricted}} = 0.60 \times \theta_{\text{ac}}$.
   - Glenohumeral space narrows earlier in elevation (subacromial clearance reduced).
   - This comparison demonstrates why restricted scapular movement increases subacromial proximity, without claiming diagnostic pathology.

---

## 4. API Endpoints Specification

1. `GET /api/v1/biomechanics/shoulder/manifest`
   - Returns metadata for all 13 anatomical structures (FMA IDs, names, categories, bound extents, source file paths, and license attribution).
2. `GET /api/v1/biomechanics/shoulder/kinematics/trajectory`
   - Returns time-series angle arrays ($0^\circ$ to $180^\circ$ in $1^\circ$ increments) for normal and restricted scapulohumeral rhythms.
3. `GET /api/v1/biomechanics/shoulder/muscles/response`
   - Returns OpenSim-calculated muscle metrics (fiber length, optimal length, $\tilde{l}_M$, passive force, and state) from `MUSCLE_RESPONSE_VALIDATION.csv`.
4. `GET /api/v1/biomechanics/shoulder/comparisons`
   - Returns descriptions and parameters for:
     - Model A: Normal Scapulohumeral Rhythm ($2:1$).
     - Model B: Forward Shoulder / Restricted Scapular Upward Rotation.
5. `GET /api/v1/biomechanics/shoulder/annotations/{structure_id}`
   - Returns structured evidence-based educational text separating anatomical facts, kinematics, and scientific research citations.
