# P13 Architectural Reuse vs. Build Decision Record

**Status:** APPROVED  
**Decision Date:** 2026-10-30  
**Context:** MSK Research Lab OS — Milestone P13 Biomechanics Education & Shoulder Movement Lab  
**Governing Rule:** Choose the solution with the greatest verified functional reuse and lowest integration complexity. Prefer existing project capabilities, already-installed applications/repos, and already-available local assets before writing custom code.

---

## 1. Decision Summary

We adopt **Option C + Option D: Existing Model & Animation Import with Minimal Adapter**:

1. **REUSE EXISTING ASSETS:**
   - Import the 13 verified BodyParts3D GLB assets (`FMA13322`, `FMA13395`, `FMA23130`, `FMA23464`, `FMA23467`, `FMA34680`, `FMA34682`, `FMA37684`, `FMA37686`, `FMA37668`, `FMA37699`, `FMA7487`, `FMA7857`) and `atlas_manifest.json` directly from `C:\Users\tuanh\MSK-Biomechanics-Workbench\frontend\assets\atlas\models\` into `2data/models/atlas/` of MSK Research Lab OS.
   - Reuse the verified OpenSim `MOBL_ARMS_41` upper-extremity kinematics matrix and muscle response dataset (`MUSCLE_RESPONSE_VALIDATION.csv`) from `C:\Users\tuanh\MSK-OpenSim-Task02`.

2. **REUSE EXISTING ARCHITECTURAL CODE:**
   - Adapt the proven Three.js hierarchical kinematic pivot rigging (`sternoclavicularPivot`, `acromioclavicularPivot`, `glenohumeralPivot`, `elbowPivot`) from `MSK-Biomechanics-Workbench/frontend/js/anatomy.js` directly into the MSK Workstation UI (`workstation_ui.py`).
   - Reuse the existing MSK Research Lab FastAPI backend (`src/msk_research_lab/api/app.py`), database infrastructure, and Three.js client infrastructure (`three.min.js`, `OrbitControls.js`, `GLTFLoader.js`).

3. **BUILD ONLY MINIMAL ADAPTERS & EDUCATIONAL MODULES:**
   - Create a dedicated Python backend service `src/msk_research_lab/biomechanics/shoulder_lab.py` to serve kinematic trajectories, muscle fiber length tables, comparative movement states, and evidence-based annotations.
   - Expose REST API endpoints `/api/v1/biomechanics/shoulder/*` in `workstation_routes.py`.
   - Embed the interactive **Shoulder Movement Lab** view into the MSK Workstation UI, providing real playback, pause, timeline scrubbing, speed adjustment, layer toggles, angle readouts, structure inspector, and comparison modes.

4. **EXPLICIT NEGATIVE DECISIONS (WHAT WE WILL NOT DO):**
   - **DO NOT** install Blender or attempt headless Blender rendering.
   - **DO NOT** clone external repositories (`Z-Anatomy`, `3d-anatomy`, `opensim-creator`).
   - **DO NOT** launch external desktop windows or disrupt the single-window workstation user experience.
   - **DO NOT** download new Playwright browsers; use the pre-verified system Microsoft Edge (`msedge`).
   - **DO NOT** fabricate muscle volume contraction or fake mesh coloring.
   - **DO NOT** present estimated muscle parameters as real biological EMG measurements.

---

## 2. Quantitative Reuse Justification

| Metric | Build From Scratch | External Clone / Full Re-architect | Reuse Existing Local Workbench (Chosen) |
| :--- | :---: | :---: | :---: |
| **New Git Repositories Cloned** | 0 | 2–4 | **0** |
| **New Binary Installations** | 1–2 (Blender / OpenSim GUI) | 2–3 | **0** |
| **Disk Space Overhead** | ~500 MB | ~4.5 GB | **< 15 MB** (Assets copied locally) |
| **Network Data Downloaded** | ~1–2 GB | ~3–5 GB | **0 MB (100% Offline)** |
| **Time to Working Demonstration** | ~3–5 days | ~2–3 days | **Immediate (< 2 hours)** |
| **Risk of Breaking P12 Regressions** | High | Extreme | **Minimal (Additive Module)** |
| **Biomechanical Accuracy** | Low (Hand-crafted) | Uncertain | **High (Verified OpenSim MOBL-ARMS)** |

---

## 3. Epistemic Integrity Statement

In alignment with P12 and P13 product safety requirements:
- The workstation explicitly discloses that muscle fiber lengths ($\tilde{l}_M$) are **OpenSim mathematical model calculations**, not in-vivo measurements.
- Forward shoulder posture is presented as a **biomechanical alignment observation**, not a disease diagnosis.
- Temporary relief from muscle release is explained through **neurological desensitization and temporary viscoelastic creep**, explaining why posture changes require long-term motor pattern reprogramming.
- `CLINICAL_REALWORLD_GATE` and `PHYSICAL_STEREO_HARDWARE_GATE` remain permanently **BLOCKED**.
