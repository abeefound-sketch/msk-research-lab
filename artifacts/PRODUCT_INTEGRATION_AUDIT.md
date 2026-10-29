# PRODUCT INTEGRATION AUDIT & FORENSICS REPORT

**Task:** TASK 05P: Personal Offline Productization  
**Role:** Principal Software Architect + Staff Biomedical Software Engineer + Toolsmith + Independent QA Auditor  
**Date:** October 2026  
**Audited Systems:**
- **System A:** `MSK Research Lab OS` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`), Base Commit `2972171`
- **System B:** `MSK Biomechanics Workbench` (`/mnt/c/Users/tuanh/MSK-Biomechanics-Workbench`), Base Commit `9d2eb1a`
**Target Hardware:** Intel Core i7-5600U @ 2.60 GHz, 8 GB RAM, Intel HD Graphics 5500, Windows 10 x64 / WSL2  

---

## 1. REPOSITORY FORENSICS & BASELINE AUDIT

### 1.1 System A: MSK Research Lab OS
- **Location:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`)
- **Version:** 3.1.0-release
- **Git Status:** Branch `main`, commit `2972171`, working tree clean.
- **Automated Test Suite:** Independently reproduced via `/home/tuan/.venvs/msk-lab/bin/pytest tests/ -q`:
  - **157 passed, 1 warning in 193.41 s** (100% PASS, 0 failures, 0 errors).
- **Core Assets Verified:**
  - SQLite WAL database (`2data/db/lab.sqlite3`) with schema migrations.
  - Full-Text Search FTS5 virtual tables (`fts_document_locations`) indexing 279 documents.
  - Three.js WebGL 3D Anatomy Atlas (`calibrated_bp3d_torso`, skin anchors, acupuncture meridian paths).
  - Knowledge graph (`ontology_concepts`, `concept_aliases`, `graph_nodes`, `graph_edges`).
  - Tri-Ledger publication & immutable snapshot builds.
  - Therapy Delivery Bridge (`src/msk_research_lab/bridge/`).

### 1.2 System B: MSK Biomechanics Workbench
- **Location:** `C:\Users\tuanh\MSK-Biomechanics-Workbench` (`/mnt/c/Users/tuanh/MSK-Biomechanics-Workbench`)
- **Version:** task04g-release
- **Git Status:** Branch `task04g`, commit `9d2eb1a`, working tree clean.
- **Automated Test Suite:** Independently reproduced via `MSK-Pose-Vision-Bridge\.venv\Scripts\python.exe -m pytest tests/ -q`:
  - **71 passed, 1 skipped, 1 warning in 20.30 s** (100% PASS, 0 failures).
  - Single skipped test: `test_two_camera_hardware_execution` (correctly skipped due to single physical camera constraint).
- **Core Assets Verified:**
  - Real-camera capture engine (OpenCV DirectShow index 0) + MediaPipe Tasks Vision CPU delegate (`pose_landmarker_lite.task`).
  - Hardware benchmark: **23.03 FPS live streaming** (P50 latency 42.24 ms: 2.29 ms capture, 38.15 ms inference, 0.42 ms math).
  - 2D joint angle geometric oracles (elbow flexion, shoulder abduction/elevation).
  - Measurement quality engine (`HUMERAL_ELEVATION_CONFOUNDER`, out-of-plane yaw warning, GUM uncertainty budget $k=1.96$, Gaussian normality).
  - Clinical safety boundary interceptor with domain allowlist and prohibited action filter.
  - Keyed HMAC-SHA256 pseudonymization and isolated secret pepper.

---

## 2. RUNTIME & INTEROPERABILITY FORENSICS

### 2.1 The Two-Runtime Landscape
1. **Linux WSL2 Runtime (`/home/tuan/.venvs/msk-lab`):**
   - Python 3.10.12.
   - Contains: `fastapi`, `uvicorn`, `sqlite3`, `pypdf`, `python-docx`, `EbookLib`, `beautifulsoup4`, `lxml`.
   - Lacks: `opencv`, `mediapipe`. WSL2 lacks direct `/dev/video0` without Windows USBIP bridge.
2. **Windows Native Runtime (`C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv`):**
   - Python 3.11.9.
   - Contains: `opencv-contrib-python 5.0.0.93`, `mediapipe 1.2.0`, `opensim 4.6`, `fastapi 0.162.0`, `uvicorn 0.54.0`, `numpy 2.4.6`, `trimesh 5.2.0`, `playwright 1.64.1`.
   - Has direct access to physical webcam (`cv2.VideoCapture(0)`) via DirectShow.
   - **Cross-Import Verification:** Verified that Windows Python can natively import `msk_research_lab` modules (`db`, `app`, `atlas`, `library`, etc.) without error!

### 2.2 Architectural Integration Strategy: Single Host Application
Instead of spawning multiple microservices or cloning a 3rd repository, we apply **Compression of Architecture**:
- **Host Application:** System A (`msk-research-lab`) hosts the unified **MSK Therapy Personal Workstation**.
- **Unified Engine:** Mount System B's biomechanics, real camera, and kinematic quality engines as an internal module or route hierarchy (`/api/v1/motion/...`, `/api/v1/biomechanics/...`).
- **Single Process Execution:** Windows Python runs the entire integrated workstation (FastAPI server, SQLite DB, 3D WebGL Atlas, camera feed, and local API) on `http://127.0.0.1:8000`.
- **Zero Cloud / Zero Microservices:** Single SQLite database, single web process, single port.

---

## 3. COMPONENT CLASSIFICATION MATRIX

| Component | Origin | Classification | Rationale & Action Plan |
|---|---|:---:|---|
| **SQLite WAL Database & Migrations** | System A | **REUSE** | Rock-solid persistence with WAL mode; add migrations for `patients` and `therapy_sessions`. |
| **Document Library & FTS5 Search** | System A | **REUSE** | Indexed 279 clinical and anatomical documents; provides instant local full-text search. |
| **3D Anatomy Atlas (Three.js)** | System A | **REUSE** | Authentic calibrated BP3D torso model, skin meshes, and acupuncture meridians directly usable. |
| **Ontology & Knowledge Graph** | System A | **REUSE** | Concept lookups, relationships, and citations ready for learning and therapy links. |
| **Real Camera & MediaPipe Engine** | System B | **REUSE** | 23.03 FPS live webcam capture with 33 landmarks; bridge into workstation motion route. |
| **2D Joint Kinematic Oracles** | System B | **REUSE** | Direct vector geometry for planar ROM with ISO 17025 / GUM uncertainty budget. |
| **Kinematic Quality & Confounder Engine** | System B | **REUSE** | Humeral elevation confounder detection and out-of-plane yaw alerts protect measurement validity. |
| **Clinical Safety Interceptor** | System B | **REUSE** | Prohibits automated diagnoses and spinal manipulations; preserves fail-closed safety. |
| **Keyed HMAC Privacy Engine** | System B | **REUSE** | Preclinical pseudonymization protecting patient records. |
| **Workstation Web UI & Dashboard** | System A | **ADAPT** | Expand single-page UI into multi-view Personal Workstation (Home, Anatomy, Motion, Patients, Therapy, Progress, Library). |
| **Therapy Delivery Bridge** | System A | **ADAPT** | Connect research packages directly into local patient therapy workflow. |
| **Patient Profile Schema & CRUD** | None | **MISSING** | Create `patients` table with medical history, pain score, functional limits, and red flags. |
| **Therapy Session Workspace Schema** | None | **MISSING** | Create `therapy_sessions` table with modalities (Thai, myofascial, Dien Chan, electrotherapy), DDS readouts, and SOAP note generator. |
| **Progress Tracking & Analytics** | None | **MISSING** | Implement progress timeline, delta ROM/pain calculators, and CSV export. |
| **AI Assisted Learning / Tutor** | None | **MISSING** | Build local rule/FTS5 assisted tutor for anatomy explanation and SOAP drafting without hallucinated diagnosis. |
| **One-Command Launcher** | None | **MISSING** | Build `start-msk.bat` and `start-msk.sh` with automated preflight diagnostics. |
| **Multi-Camera Hardware DLT** | System B | **REMOVE/DEFER** | Defer multi-camera 3D DLT until second physical camera exists; maintain single-camera fallback. |
| **Clinical Field Validation (Gate G9)** | Both | **REMOVE/DEFER** | Keep Gate G9 / F10 explicitly BLOCKED; label all demo data DEMO/SYNTHETIC. |

---

## 4. INTEGRATION CONCLUSION & NEXT STEPS

Both systems are intact, certified, and 100% passing their respective regression suites. The architectural path is clear:
1. Extend System A's database schema with Patient and Therapy Session tables.
2. Integrate System B's motion capture, landmark extraction, and safety modules into System A.
3. Build the unified single-page desktop dashboard featuring the 7 required application views.
4. Implement the offline AI Tutor / Clinical Assistant module.
5. Create the one-command launcher (`start-msk.bat` / `start-msk.sh`) and execute end-to-end acceptance tests.
