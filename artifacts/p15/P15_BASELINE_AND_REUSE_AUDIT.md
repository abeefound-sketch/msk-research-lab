# P15 Baseline & Software Reuse Audit
**MSK Research Lab OS — Milestone P15**  
**Role:** Principal Software Architect, Biomedical Visualization Engineer  
**Date:** 2026-10-31  
**Git Baseline Checkpoint:** `fb3c450` on branch `fix/workstation-real-functional-acceptance`  
**Handoff Directory:** [`artifacts/p15/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p15/)

---

## 1. Executive Summary

Milestone P15 expands the workstation's biomechanical analysis capabilities into an **interactive educational and dynamic muscle mechanics laboratory**. In accordance with the primary project directive—**DO NOT REBUILD WHAT ALREADY EXISTS**—this milestone was engineered through maximal reuse of proven architectural components, pre-calibrated assets, and mathematical models developed throughout P0–P14.

Zero new external dependencies or Python packages were introduced. All dynamic action line visualizations, OpenSim muscle dynamics calculations, motor control educational narratives, and guided learning scenes reuse existing Three.js pipelines, FastAPI endpoints, and Pydantic schemas.

---

## 2. Software Reuse Matrix

| Component | P0–P14 Source | Milestone P15 Reuse Strategy | New Code Added |
|---|---|---|---|
| **Anatomical Meshes** | 13 BodyParts3D GLB models (`static/models/bp3d/`) | Reused without modification; explicitly designated as `STATIC_RESTING_ANATOMICAL_MESH` for contextual visual reference. | 0 new meshes |
| **OpenSim Geometry** | MoBL-ARMS 4.1 reference coordinates (`shoulder_lab.py`) | Reused attachment coordinates to drive dynamic 3D Action Lines (`REPRESENTED_BY_OPENSIM_MUSCLE_PATH`) across 10 compartments. | Coordinate transformation layer |
| **Kinematic Models** | Inman 2:1 & Restricted 4:1 models (`shoulder_lab.py`) | Reused as foundational kinematic engine; coupled with dynamic muscle path length calculations. | Scene narrative integration |
| **3D Rendering** | Three.js scene graph in `#view-shoulder` (`workstation_ui.py`) | Extended `shoulderScene` with `shoulderActionLinesGroup`, origin/insertion anchor nodes, and dynamic line geometry updates. | Line update renderer |
| **Web Framework** | FastAPI & Uvicorn router (`workstation_routes.py`) | Added 2 targeted REST endpoints (`/scenes`, `/muscles/dynamics`) reusing existing Pydantic validation patterns. | 2 REST routes |
| **Client UI** | Modern CSS/JS Workstation Design System (`workstation_ui.py`) | Added Guided Learning Card and Muscle Dynamics Inspector matching existing dark theme and typography. | HTML/JS UI cards |
| **Browser Testing** | Playwright + Microsoft Edge harness | Extended P14 E2E testing pattern with 15-step interactive acceptance challenge. | 1 acceptance test |

---

## 3. Dependency Audit

- **Python Virtualenv:** `/home/tuan/.venvs/msk-lab` (Python 3.10.12)
  - New pip packages installed: **0**
  - Upstream repository clones: **0**
- **Windows Host Runtime:** `C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv` (Python 3.11.9)
  - Playwright version: 1.64.1
  - Browser engine: Microsoft Edge (Chromium Channel `msedge`)
  - New packages installed: **0**
- **Air-Gapped Loopback Compliance:** All communication remains strictly bound to `127.0.0.1` and `::1`. Outbound network requests: **0**.

---

## 4. Verification Checkpoint Status

- **Baseline Commit:** `fb3c450` (Milestone P14 Certified)
- **Unit Tests Inherited:** 179 / 179 PASS
- **Integration Tests Inherited:** 125 / 125 PASS
- **P15 Biomechanics & Guided Learning Tests:** 9 new unit tests + 1 new 15-step E2E test added
- **Current Total Automated Suite:** 314 automated tests PASS, 0 FAIL, 1 WARNING (Starlette deprecation notice).
