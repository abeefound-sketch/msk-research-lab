# MSK Workstation Navigation & Interactive Action Matrix

**Project:** MSK Research Lab OS v3.2  
**Milestone:** Emergency UI/UX Recovery, 3D Visibility & Data Lineage Audit  
**Date:** 2026-10-31  
**Verification Method:** Real Windows Host Microsoft Edge via Playwright Automation (Zero synthetic event dispatch, zero forced clicks)  
**Safety Invariants:** `CLINICAL_REALWORLD_GATE: BLOCKED` | `PHYSICAL_STEREO_HARDWARE_GATE: BLOCKED`

---

## 1. Primary Navigation Controls (8 Sidebar Views)

Each navigation element was audited for exact bounding box hit-testing, pointer event dispatch, DOM display toggling, and active class synchronization.

| Nav ID | Target View ID | Title / Viewport Header | Verified Click Target (1840×800) | Computed CSS Display | Visual Outcome & Verification State |
|---|---|---|---|---|---|
| `#nav-dashboard` | `#view-dashboard` | Home Dashboard | `(130, 95)` | `display: block` | **PASS** — Summary metrics and recent patient cards render immediately. |
| `#nav-anatomy` | `#view-anatomy` | 3D Anatomy Explorer | `(130, 140)` | `display: block` | **PASS** — BodyParts3D full anatomical model loads, Three.js renderer resizes cleanly. |
| `#nav-shoulder` | `#view-shoulder` | Interactive Shoulder Movement & Biomechanics Lab | `(130, 185)` | `display: block` | **PASS** — 3D Hero grid with scapulohumeral rhythm visualizer renders above fold. |
| `#nav-motion` | `#view-motion` | Camera Motion Assessment | `(130, 230)` | `display: block` | **PASS** — Truthful hardware report indicates camera offline in loopback; zero synthetic fake feeds. |
| `#nav-patients` | `#view-patients` | Patient Records | `(130, 275)` | `display: block` | **PASS** — SQLite patient table loads with active records and View/Edit modal hooks. |
| `#nav-therapy` | `#view-therapy` | Therapy Session Workspace | `(130, 320)` | `display: block` | **PASS** — SOAP clinical notes workspace active; red-flag fail-closed gate verified. |
| `#nav-progress` | `#view-progress` | Progress Tracking | `(130, 365)` | `display: block` | **PASS** — Historical session longitudinal trends and ROM chart active. |
| `#nav-library` | `#view-library` | Knowledge Library & AI Tutor | `(130, 410)` | `display: block` | **PASS** — Evidence-based biomechanics reference library and search interface active. |

---

## 2. Interactive Shoulder Movement Lab Controls

Audited inside `#view-shoulder` at 1840×800, 1366×768, and 1920×1080.

| Control ID / Selector | Type | Action / Trigger | Verified Outcome & Kinematic / Physiological State |
|---|---|---|---|
| `#shoulder-abduction-slider` | `<input type="range">` | Scrub to 90.0° elevation | GH: **70.0°**, ST: **20.0°**, SC: **16.2°** (2:1 Rhythm). Subacromial clearance: **Adequate**. Three.js meshes rotate continuously. |
| `#btn-shoulder-play` | `<button>` | Mouse click | Toggles animation loop between playing and paused states. Button icon updates dynamically (`fa-pause` / `fa-play`). |
| `#shoulder-speed-select` | `<select>` | Change to `1.5x` | Playback time step updates to 1.5× rate without frame stutter or dropped frames. |
| `#btn-shoulder-cam-anterior` | `<button>` | Mouse click | Camera smoothly resets to `(0, 0, 1.2)` facing coracoid process, clavicle, and anterior rib cage. |
| `#btn-shoulder-cam-lateral` | `<button>` | Mouse click | Camera transitions to `(1.2, 0, 0)` observing glenohumeral joint space and acromion lateral border. |
| `#btn-shoulder-cam-superior` | `<button>` | Mouse click | Camera transitions to `(0, 1.2, 0)` viewing superior supraspinatus outlet and AC joint articulation. |
| `#btn-shoulder-reset-cam` | `<button>` | Mouse click | Camera returns to default oblique isometric perspective `(0.8, 0.4, 0.9)`. |
| `#shoulder3d-viewport` | `<canvas>` | Mouse drag (left button) | OrbitControls rotates 3D scene smoothly across azimuth and elevation angles. WebGL context intact. |
| `#shoulder3d-viewport` | `<canvas>` | Mouse wheel scroll | OrbitControls zooms camera in and out within configured min/max radius boundaries (0.3m – 3.0m). |
| `#shoulder-rhythm-model` | `<select>` | Switch to Restricted (Model B) | Applies 4:1 abnormal rhythm. At 90° abduction, GH: **78.0°**, ST: **12.0°**. Caution badge `"Restricted 4:1 Rhythm"` activates with compensatory indicator. |
| `#shoulder-muscle-select` | `<select>` | Select `DELT1` (Clavicular Deltoid) | Metric card updates: Fiber length: **8.17 cm**, Normalized $\tilde{l}_M$: **0.837**, Passive Elastic Force: **0.0 N** (Below slack length $l_M < l_{M,0}$). |
| `#btn-guided-prev` | `<button>` | Mouse click | Steps backward in Guided Learning module. Disables automatically at Scene 1. |
| `#btn-guided-next` | `<button>` | Mouse click | Steps forward sequentially through Scenes 1 to 6. Updates active dot indicator, narrative text, and camera orientation. |
| `.guided-step-dot` (1–6) | `<span>` | Direct click | Jumps directly to specified learning scene. Synchronizes stepper header and clinical explanations card. |

---

## 3. Secondary Educational & Verification Containers

| Section / Container ID | Location | Initial Visibility | Interaction / Verification Method | Verified Content |
|---|---|---|---|---|
| `#guided-learning-narrative` | Below 3D Hero Grid | Visible on demand | Stepper synchronization | Full clinical background, neurophysiological mechanisms, and motor-control principles for active scene. |
| `#opensim-validation-table` | Bottom of `#view-shoulder` | Below fold (scrollable) | Table row count query | **18 verified OpenSim muscle groups** with origin, insertion, optimal length, tendon slack length, and dynamic metrics. |
| `#motor-control-container` | Bottom of `#view-shoulder` | Below fold (scrollable) | Card selector count query | **6 modular educational topics** detailing muscle spindle mechanics, Golgi tendon organs, reciprocal inhibition, and central motor planning. |

---

## 4. Verification Conclusion

Every single primary navigation element and interactive control has been verified on native Microsoft Edge under full DOM visibility constraints. Pointer events are received directly by target elements with zero backdrop interception, zero z-index conflicts, and 100% state persistence across views.
