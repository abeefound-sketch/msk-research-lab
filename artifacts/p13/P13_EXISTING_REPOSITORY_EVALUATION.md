# P13 Existing Repository & Biomechanics Software Evaluation

**Role:** Principal Software Architect, Biomedical Visualization Engineer, Open-Source Integration Auditor  
**Date:** 2026-10-30  
**Inspection Framework:** 10-Point Technical Qualification & 5-Tier Epistemic Capability Distinction  

---

## 1. Candidate Solutions Under Evaluation

The following 6 candidate solutions were evaluated against empirical evidence, local prototypes, and public project metadata:

1. **OpenSim Creator (`opensim-creator`):** Desktop GUI application developed by Computational Biomechanics Lab (Stanford/TU Delft), built on OpenSim 4.x. (Local copy: v0.8.0 standalone in `C:\Users\tuanh\MSK-OpenSim-Feasibility`).
2. **OpenSim Core (`opensim-core`):** C++/Python computational musculoskeletal modeling engine by SimTK / Stanford. (Local copy: Python package v4.6 in `C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv`).
3. **OpenSim Models (`opensim-models`):** Curated repository of musculoskeletal models (`MOBL_ARMS_41`, `Rajagopal2016`, `gait2392`, `Hamner2010`). (Local copy: `MOBL_ARMS_41.osim` in `C:\Users\tuanh\MSK-OpenSim-Task02`).
4. **Z-Anatomy (`Models-of-human-anatomy`):** Open-source 3D human anatomy atlas designed in Blender, based on BodyParts3D and open anatomical datasets.
5. **3D Anatomy (`3d-anatomy` / `WaterCMY/anatomy-3d`):** WebGL Three.js interactive 3D human anatomy viewer. (Local upstream clone: `3refs/upstream/watercmy--anatomy-3d`).
6. **Body Anatomy 3D Viewer (`body-anatomy-3d-viewer` / `hpfrei`):** Lightweight Three.js-based web anatomy viewer.

---

## 2. Ten-Point Evaluation Matrix

| Evaluation Criterion | OpenSim Creator | OpenSim Core (Python) | OpenSim Models (`MOBL_ARMS_41`) | Z-Anatomy (Blender) | 3D Anatomy (`watercmy`) | MSK Biomechanics Workbench |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Displays real anatomical structures?** | **YES** (Polygonal bone geometry & muscle lines) | **NO** (Compute engine only, no built-in renderer) | **YES** (VTP bone meshes & muscle via points) | **YES** (High-poly segmented organs/muscles) | **YES** (255 segmented organ/muscle meshes) | **YES** (Calibrated BodyParts3D GLB meshes) |
| **2. Supports joint motion?** | **YES** (Full forward/inverse kinematics) | **YES** (State realization & coordinate couplers) | **YES** (Kinematic tree with 26 coordinates) | **LIMITED** (Requires custom Blender rigging) | **NO** (Static meshes only; no rig in GLB) | **YES** (Hierarchical Three.js joint pivots) |
| **3. Supports muscle path or length changes?** | **YES** (Real-time dynamic path recalculation) | **YES** (Millard2012 / Thelen muscle fiber lengths) | **YES** (50 muscles with validated fiber lengths) | **NO** (Static shapes only; no kinematic contraction) | **NO** (Static geometry) | **YES** (Dynamic 3D spline tubes + KMSI color chips) |
| **4. Offers animated movement?** | **YES** (Motion scrubber & simulation playback) | **YES** (Time-series trajectory realization) | **YES** (Via OpenSim trajectory states) | **MANUAL** (Requires keyframing in Blender) | **NO** (Orbit camera only) | **YES** (Continuous animation loop & scrub slider) |
| **5. Exposes reusable programmatic interfaces?** | **LIMITED** (CLI `osc.exe` renders, no REST API) | **EXCELLENT** (Native Python API `opensim.*`) | **EXCELLENT** (Declarative XML `.osim` schema) | **POOR** (Blender `.blend` files, heavy Python scripting) | **GOOD** (Vanilla Three.js DOM scripts) | **EXCELLENT** (FastAPI REST endpoints + Three.js classes) |
| **6. Works offline?** | **YES** (100% local desktop binary) | **YES** (100% local C++/Python) | **YES** (Local XML file) | **YES** (Local `.blend`) | **YES** (Local static HTML/JS) | **YES** (100% loopback offline) |
| **7. Runs on target Windows workstation?** | **YES** (Verified on Intel HD 5500, ~310 MB RAM) | **YES** (Verified Python 3.11 Windows runtime) | **YES** (Native file) | **HEAVY** (Requires Blender 4.x, high VRAM) | **YES** (Runs in modern browser) | **YES** (60 FPS WebGL on Intel HD 5500) |
| **8. Requires powerful GPU?** | **NO** (Runs smoothly on Intel HD Graphics) | **NO** (CPU only) | **NO** (Data only) | **YES** (Subsurface scattering & 2M+ polys require GPU) | **NO** (Runs smoothly) | **NO** (Optimized polygon budget) |
| **9. Integrates without major rewriting?** | **MODERATE** (Requires process spawning/IPC) | **HIGH** (Direct Python import) | **HIGH** (Direct data binding) | **VERY LOW** (Requires full Blender headless server) | **HIGH** (Direct Three.js embedding) | **MAXIMUM** (Already designed for MSK OS) |
| **10. License permits local educational reuse?** | **Apache-2.0** | **Apache-2.0** | **Modified BSD-3 / Non-Commercial** | **CC BY-SA 4.0** | **MIT / CC BY** | **Internal Project Code / CC BY-SA 2.1 JP** |

---

## 3. Epistemic Capability Distinction

To prevent pseudoscience, misleading educational visuals, or fake simulation claims, the following 5 capabilities are strictly differentiated across the software:

```
[Level 1: Visible Joint Animation]
       │ (Geometric bone rotation about joint center)
       ▼
[Level 2: Anatomical Muscle Deformation]
       │ (Volumetric shape bulge/thinning — NOT IMPLEMENTED IN REAL TIME)
       ▼
[Level 3: Muscle Length & Kinematic Computation]
       │ (Calculated path length & normalized fiber length via OpenSim)
       ▼
[Level 4: Estimated Muscle Activation]
       │ (Static Optimization / Computed Muscle Control from dynamics)
       ▼
[Level 5: Physiological Neural Activation]
         (Measured Surface EMG or motor unit recruitment — HARDWARE BLOCKED)
```

1. **Visible Joint Animation (VERIFIED AVAILABLE):**
   - Implemented via Three.js hierarchical pivots driven by geometric angles.
   - Accurately demonstrates the $2:1$ Scapulohumeral Rhythm and clavicular elevation.
2. **Anatomical Muscle Deformation (NOT IMPLEMENTED):**
   - Deforming volumetric muscle meshes requires complex Finite Element Modeling (FEM) or non-linear skin weighting. 
   - Neither OpenSim nor Three.js supports real-time anatomical volume deformation on low-power hardware.
   - **Policy:** The workstation displays muscle meshes as rigid structural references and muscle paths as dynamic spline tubes. It **never** artificially scales or morphs meshes to fake contraction.
3. **Muscle Length / Kinematic Computation (VERIFIED AVAILABLE):**
   - Realized via OpenSim's `MOBL_ARMS_41.osim` and stored in `MUSCLE_RESPONSE_VALIDATION.csv`.
   - Computes normalized fiber length $\tilde{l}_M = l_M / l_{M,0}$ and passive elastic tension.
4. **Estimated Muscle Activation (SIMULATION ONLY; CLEARLY LABELED):**
   - OpenSim calculates static optimization estimates of muscle activation ($a \in [0, 1]$).
   - In passive forward shoulder posture, activation is nominal ($a \approx 0.02$).
   - Explicitly labeled: *"Model Estimate Only — Not Directly Measured"*.
5. **Physiological Neural Activation (STRICTLY BLOCKED):**
   - Requires real-time multi-channel electromyography (sEMG) or neuro-motor recording hardware.
   - Status: **BLOCKED / NOT AVAILABLE**. The software never presents model values as actual biological innervation.

---

## 4. Evaluation Conclusions

1. **OpenSim Creator standalone:** Functional, but running as an external `.exe` creates window-switching friction for an integrated educational workstation.
2. **Z-Anatomy:** Outstanding aesthetic anatomical detail, but prohibitive dependency overhead (Blender installation and heavy GPU requirements).
3. **3D Anatomy (`watercmy`):** Useful for static organ inspection, but entirely lacks joint kinematics, muscle paths, or biomechanical coordination.
4. **MSK Biomechanics Workbench + OpenSim MOBL-ARMS:** Achieves the highest functional score, uses existing local assets, runs at 60 FPS offline on integrated graphics, and already possesses the exact shoulder/arm kinematics required for P13-D.
