# P13 Local Software & 3D Asset Discovery Inventory

**Auditor / Roles:** Principal Software Architect, Biomedical Visualization Engineer, Open-Source Integration Engineer, Desktop QA  
**Date:** 2026-10-30  
**Inspection Mode:** Safe Read-Only Host & Environment Inspection  
**Constraint Invariant:** **DO NOT REBUILD WHAT ALREADY EXISTS. DO NOT CLONE UNNECESSARY REPOSITORIES.**

---

## 1. Executive Summary

A comprehensive, non-destructive inventory of the local Windows host (`C:\Users\tuanh`), WSL2 Linux environment (`/home/tuan`), and existing project workspace (`C:\Users\tuanh\Downloads\msk-research-lab`) was executed. 

**Key Finding:** The local workstation **already possesses** high-quality, verified open-source biomechanical and anatomical assets:
1. **OpenSim 4.6 Python Bindings:** Fully installed and operational in `C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv`.
2. **OpenSim Creator 0.8.0 Desktop Application:** Standalone Windows executable `osc.exe` extracted and operational in `C:\Users\tuanh\MSK-OpenSim-Feasibility\extracted\opensimcreator-0.8.0-windows-amd64\bin\osc.exe`.
3. **Upper Extremity Biomechanical Model (`MOBL_ARMS_41.osim`):** Verified Holzbaur/Saul model with 12 bodies, 26 coordinates, and 50 muscle compartments covering Rotator Cuff, Deltoids, Pectoralis Major, Latissimus Dorsi, Biceps, and Triceps in `C:\Users\tuanh\MSK-OpenSim-Task02\EVIDENCE\models\MOBL_ARMS_41.osim`.
4. **Pre-Computed OpenSim Shoulder Simulation Matrix:** 6 verified shoulder elevation stages ($0^\circ, 45^\circ, 90^\circ, 120^\circ, 150^\circ, 180^\circ$) with normalized fiber lengths, passive/active forces, and biomechanical states in `MUSCLE_RESPONSE_VALIDATION.csv`.
5. **Calibrated BodyParts3D Meshes:** 13 individual GLB models and 1 pre-assembled right arm GLB in `C:\Users\tuanh\MSK-Biomechanics-Workbench\frontend\assets\atlas\models\`, licensed under CC BY-SA 2.1 Japan, complete with anatomical metadata in `atlas_manifest.json`.
6. **Kinematic Rigging Architecture:** Proven Three.js hierarchical pivot structure (`thorax` $\to$ `sternoclavicularPivot` $\to$ `clavicle` $\to$ `acromioclavicularPivot` $\to$ `scapula` $\to$ `glenohumeralPivot` $\to$ `humerus` $\to$ `elbowPivot` $\to$ `forearm`) in `MSK-Biomechanics-Workbench/frontend/js/anatomy.js`.
7. **System Browser Automation:** Microsoft Edge (`msedge`) verified operational with Playwright on Windows without downloading new browser binaries.

**Zero new external clones or package downloads are required.** All P13 educational goals can be achieved by integrating and adapting these existing local assets.

---

## 2. Installed Software & Tooling Matrix (A1)

| Component | Installed / Present | Version / Path | Functional Status | Reusability Classification | Recommended Action |
| :--- | :---: | :--- | :---: | :---: | :--- |
| **OpenSim Core (Python)** | **YES** | v4.6<br>`C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv\Lib\site-packages\opensim` | **PASS** (Model realization verified) | `REUSE_EXISTING` | Reuse for biomechanical calculations and muscle state realization. |
| **OpenSim Creator (Desktop)** | **YES** | v0.8.0 (17.8 MB)<br>`C:\Users\tuanh\MSK-OpenSim-Feasibility\extracted\opensimcreator-0.8.0-windows-amd64\bin\osc.exe` | **PASS** (Rendered shoulder poses verified) | `REUSE_EXISTING` | Retain as optional external standalone desktop visualizer. |
| **Three.js** | **YES** | r128 / ES6<br>`src/msk_research_lab/api/static/vendor/three.min.js`<br>`MSK-Biomechanics-Workbench/frontend/vendor/three.min.js` | **PASS** (WebGL canvas rendering active) | `REUSE_EXISTING` | Primary 3D WebGL renderer for interactive educational visualization. |
| **GLTFLoader & OrbitControls** | **YES** | Three.js addons<br>`src/msk_research_lab/api/static/vendor/loaders/GLTFLoader.js`<br>`src/msk_research_lab/api/static/vendor/OrbitControls.js` | **PASS** (Orbit and GLTF loading verified) | `REUSE_EXISTING` | Interactive rotation, zoom, panning, and mesh ingestion. |
| **Python 3 (Windows)** | **YES** | v3.11.9<br>`C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe` | **PASS** (Host execution verified) | `REUSE_EXISTING` | Windows native runtime. |
| **Python 3 (WSL2)** | **YES** | v3.10.12<br>`/usr/bin/python3`, `.venv/bin/python` | **PASS** (284 tests passing) | `REUSE_EXISTING` | Fast test execution and development environment. |
| **Node.js & npm (WSL2)** | **YES** | Node v20.20.2, npm 10.8.2<br>`/home/tuan/.nvm/versions/node/v20.20.2/bin/node` | **PASS** | `REUSE_EXISTING` | Available for web tooling if needed. |
| **Node.js & npm (Windows)** | **YES** | Node v20<br>`C:\Program Files\nodejs\node.exe` | **PASS** | `REUSE_EXISTING` | Windows host web tooling. |
| **Git** | **YES** | Git 2.34.1 (WSL)<br>Git for Windows (`C:\Program Files\Git\cmd\git.exe`) | **PASS** | `REUSE_EXISTING` | Version control. |
| **MediaPipe** | **YES** | v1.2.0<br>`C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv` | **PASS** (Pose detection verified) | `REUSE_EXISTING` | Pose landmarking when needed. |
| **OpenCV** | **YES** | `opencv-contrib-python` v5.0.0.93<br>`C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv` | **PASS** | `REUSE_EXISTING` | Computer vision and calibration utilities. |
| **Trimesh** | **YES** | v5.2.0<br>`C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv` | **PASS** (Mesh geometry inspection) | `REUSE_EXISTING` | 3D mesh inspection and parsing. |
| **Playwright** | **YES** | v1.64.1<br>`C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv` | **PASS** (via `channel="msedge"`) | `REUSE_EXISTING` | Automated browser acceptance testing. |
| **Microsoft Edge** | **YES** | System Windows Edge | **PASS** (Playwright headless verified) | `REUSE_EXISTING` | Browser acceptance runtime (zero extra downloads). |
| **Blender** | **NO** | Not installed on PATH, Program Files, or WSL | `NOT_INSTALLED` | `OPTIONAL` | **Do not install.** glTF/GLB models and Three.js pivots suffice. |
| **Unreal / Unity** | **NO** | Not installed | `NOT_INSTALLED` | `INCOMPATIBLE` | **Do not install.** Violates hardware constraints and budget. |

---

## 3. Discovered Local Repositories Matrix (A2)

| Repository / Project | Location | Git Remote / Identity | Key Capabilities & Assets | Reusability Classification | Recommended Action |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **`MSK-Biomechanics-Workbench`** | `C:\Users\tuanh\MSK-Biomechanics-Workbench` | Local Git repository | • 13 calibrated BodyParts3D GLB assets<br>• Three.js `AnatomyViewer` with hierarchical pivots<br>• OpenSim dual-engine bridge<br>• Normalized muscle fiber length ($\tilde{l}_M$) coloring<br>• Dark-mode responsive UI | `REUSE_EXISTING` | **Primary architectural and asset donor.** Directly reuse assets, manifest, and kinematic pivot formulas. |
| **`MSK-OpenSim-Task02`** | `C:\Users\tuanh\MSK-OpenSim-Task02` | Local Git repository | • `MOBL_ARMS_41.osim` model<br>• `render_shoulder_angles.ps1`<br>• `MUSCLE_RESPONSE_VALIDATION.csv`<br>• Comparative evaluation of upper extremity models | `REUSE_EXISTING` | **Primary biomechanical simulation oracle.** Reuse validated shoulder elevation angles ($0^\circ - 180^\circ$) and muscle metrics. |
| **`MSK-Pose-Vision-Bridge`** | `C:\Users\tuanh\MSK-Pose-Vision-Bridge` | Local workspace | • `mskpose` package<br>• OpenSim dual-bridge realization<br>• Joint angle constraints & clamping<br>• Virtual environment with OpenSim 4.6, MediaPipe, OpenCV | `REUSE_EXISTING` | Reuse Python runtime environment and coordinate conversion logic. |
| **`MSK-OpenSim-Feasibility`** | `C:\Users\tuanh\MSK-OpenSim-Feasibility` | Local workspace | • OpenSim Creator 0.8.0 standalone (`osc.exe`)<br>• Rajagopal2016 model<br>• Pose screenshot scripts | `REUSE_EXISTING` | Retain as reference standalone visualizer. |
| **`watercmy--anatomy-3d`** | `3refs/upstream/watercmy--anatomy-3d` | `https://github.com/WaterCMY/anatomy-3d.git` | • Full body 3D anatomy viewer<br>• `models/anatomy.glb` (9.3 MB, 255 discrete meshes) | `REUSE_EXISTING` | Secondary comparative reference for general full-body anatomy. |
| **`spacejohnlf--tcm-acupoints`**| `3refs/upstream/spacejohnlf--tcm-acupoints` | `https://github.com/spacejohnlf/tcm-acupoints.git` | • 3D acupuncture point viewer<br>• `body.glb` (8.2 MB) | `REUSE_EXISTING` | Retain as current baseline surface reference model. |

---

## 4. Discovered 3D Assets & Rigging Verification (A3)

| Asset File | Size | Format | Verified Anatomical Structure | Rigged / Animated in File | Kinematic Rigging Strategy | License & Attribution |
| :--- | :---: | :---: | :--- | :---: | :--- | :--- |
| `fma13322_clavicle.glb` | 101 KB | GLB | Right Clavicle (Collarbone) | No (Rigid Mesh) | Three.js `sternoclavicularPivot` (Z-axis rotation) | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma13395_scapula.glb` | 2.21 MB | GLB | Right Scapula (Shoulder Blade) | No (Rigid Mesh) | Three.js `acromioclavicularPivot` (Y-axis upward rotation) | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma23130_humerus.glb` | 319 KB | GLB | Right Humerus (Upper Arm Bone) | No (Rigid Mesh) | Three.js `glenohumeralPivot` (Elevation & rotation) | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma23464_radius.glb` | 56 KB | GLB | Right Radius (Forearm Lateral) | No (Rigid Mesh) | Three.js `elbowPivot` (Flexion / extension) | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma23467_ulna.glb` | 71 KB | GLB | Right Ulna (Forearm Medial) | No (Rigid Mesh) | Three.js `elbowPivot` (Flexion / extension) | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma7487_thorax.glb` | 390 KB | GLB | Body of Sternum (Thorax Base) | No (Rigid Mesh) | Fixed Ground Reference Frame | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma7857_thorax.glb` | 278 KB | GLB | Right First Rib (Thorax Base) | No (Rigid Mesh) | Fixed Ground Reference Frame | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma34680_delt1.glb` | 569 KB | GLB | Clavicular Deltoid (Anterior) | No (Rigid Mesh) | Rigid reference mesh + Dynamic Spline Path | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma34682_delt2.glb` | 581 KB | GLB | Acromial Deltoid (Middle) | No (Rigid Mesh) | Rigid reference mesh + Dynamic Spline Path | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma37684_bicshort.glb`| 545 KB | GLB | Biceps Brachii (Short Head) | No (Rigid Mesh) | Rigid reference mesh + Dynamic Spline Path | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma37686_biclong.glb` | 631 KB | GLB | Biceps Brachii (Long Head) | No (Rigid Mesh) | Rigid reference mesh + Dynamic Spline Path | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma37668_bra.glb` | 684 KB | GLB | Brachialis | No (Rigid Mesh) | Rigid reference mesh + Dynamic Spline Path | CC BY-SA 2.1 JP (BodyParts3D) |
| `fma37699_trilong.glb` | 773 KB | GLB | Triceps Brachii (Long Head) | No (Rigid Mesh) | Rigid reference mesh + Dynamic Spline Path | CC BY-SA 2.1 JP (BodyParts3D) |
| `right_arm_anatomy_assembly.glb` | 7.04 MB | GLB | Complete 13-structure assembly | No (Static Scene) | Pre-assembled reference | CC BY-SA 2.1 JP (BodyParts3D) |
| `MOBL_ARMS_41.osim` | 848 KB | OSIM | Holzbaur/Saul Upper Extremity | **Yes (Full OpenSim kinematic tree)** | Coupled Scapulohumeral Rhythm ($2:1$) via 13 constraints | Modified BSD-3 / Academic Non-Commercial |
| `MUSCLE_RESPONSE_VALIDATION.csv` | 14.2 KB | CSV | Shoulder Elevation Metrology | N/A (Data Oracle) | Direct lookup & continuous spline interpolation | Project Golden Artifact |

> [!IMPORTANT]
> **Rigged vs. Static Distinction:**
> As verified through binary inspection, the raw `.glb` files from BodyParts3D do **NOT** contain embedded skeletal armatures (skins) or animation tracks. 
> Instead, accurate anatomical motion is achieved through **hierarchical kinematic scene graph composition in Three.js**, where each rigid bone mesh is parented to anatomically positioned joint pivots (`sternoclavicularPivot`, `acromioclavicularPivot`, `glenohumeralPivot`, `elbowPivot`).
> Joint angles are driven directly by OpenSim's validated kinematic coordinate trajectories (`shoulder_elv`, `elv_angle`, `scElevationDeg`, `scapUpwardRotDeg`).

---

## 5. Decision Matrix & Action Plan

1. **Software Installation Policy:** **ZERO NEW INSTALLS.** No external npm packages, pip packages, Blender installations, or simulation engines need to be downloaded.
2. **Repository Policy:** **ZERO NEW CLONES.** Do not clone OpenSim, Z-Anatomy, or any candidate web repos. Everything required is already present across `MSK-Biomechanics-Workbench`, `MSK-OpenSim-Task02`, and `MSK-Pose-Vision-Bridge`.
3. **Asset Migration:** Copy the 13 BodyParts3D `.glb` files and `atlas_manifest.json` into the main project at `2data/models/atlas/` and expose them via FastAPI static mounts.
4. **Integration Architecture:** Proceed with **Option C & D (Existing Model & Animation Import + Minimal Adapter)**, embedding the verified shoulder lab directly into MSK Research Lab OS.
