# MSK Research Lab OS v3.2 — UI Action & Control Matrix

**Date:** 2026-10-29  
**Version:** v3.2 Recovery  
**Target:** MSK Therapy Personal Workstation (`/workstation`)  
**Audit Policy:** 100% of visible interactive controls audited and categorized (`WORKING`, `DISABLED_WITH_REASON`, `FAIL`, `NOT_VERIFIED`). No mock buttons, no silent failures, no alerts masquerading as functional implementations.

---

## Control Inventory Summary

| Total Controls Audited | WORKING | DISABLED_WITH_REASON | FAIL | NOT_VERIFIED |
|---|---|---|---|---|
| **49** | **49** | **0** | **0** | **0** |

---

## Detailed Control Matrix by View

### 1. Home Dashboard (`#view-dashboard`)

| # | Selector / Label | Event Handler | Target API / Mechanism | Side Effect / State Update | Status | Verification Evidence |
|---|---|---|---|---|---|---|
| 1 | `.nav-item[1]` (Home Dashboard) | `onclick="switchView('dashboard')"` | Client DOM Switch | Shows `#view-dashboard`, updates topbar title | `WORKING` | Click switches view, updates `.active` class |
| 2 | `button` (+ Register New Patient) | `onclick="openNewPatientModal()"` | Client Modal DOM | Displays `#newPatientModal` | `WORKING` | Modal displays with clean input fields |
| 3 | `button` (+ Start Therapy Session) | `onclick="switchView('therapy')"` | Client DOM Switch | Displays `#view-therapy` | `WORKING` | Switches to therapy workspace |
| 4 | `button` (▶ Run Motion Assessment) | `onclick="switchView('motion')"` | Client DOM Switch | Displays `#view-motion` | `WORKING` | Switches to camera kinematics view |
| 5 | `button` (🔍 Explore 3D Anatomy) | `onclick="switchView('anatomy')"` | Client DOM Switch | Displays `#view-anatomy`, triggers 3D canvas | `WORKING` | WebGL canvas rendered |
| 6 | `button` (Re-probe Diagnostics) | `onclick="refreshOverview()"` | `GET /api/v1/workstation/overview` | Refreshes diagnostic matrix (Camera, Tracker, Atlas, Gate) | `WORKING` | Updates status pill and stat counters |

### 2. 3D Anatomy Atlas (`#view-anatomy`)

| # | Selector / Label | Event Handler | Target API / Mechanism | Side Effect / State Update | Status | Verification Evidence |
|---|---|---|---|---|---|---|
| 7 | `.nav-item[2]` (3D Anatomy Atlas) | `onclick="switchView('anatomy')"` | Client DOM Switch | Displays 3D Viewport, inits Three.js | `WORKING` | Three.js scene initialized |
| 8 | `#atlas-model-select` | `onchange="changeAtlasModel()"` | `GET /api/v1/atlas/scene/{id}`, `GET /models/{id}/file` | Loads authentic GLB into Three.js scene | `WORKING` | Switches between watercmy & spacejohnlf models |
| 9 | `#btn-reset-atlas` (Reset View) | `onclick="resetAtlasCamera()"` | Three.js Camera & OrbitControls | Resets camera to (0,0,4), target to (0,0,0) | `WORKING` | Camera vector resets smoothly |
| 10 | `#btn-toggle-muscles` | `onclick="toggleAtlasLayer('muscles')"` | Three.js Scene Graph | Toggles `musclesGroup.visible`, updates button label | `WORKING` | Meshes disappear/reappear, button updates |
| 11 | `#btn-toggle-meridians` | `onclick="toggleAtlasLayer('meridians')"` | Three.js Scene Graph | Toggles `meridiansGroup.visible`, updates button label | `WORKING` | Acupoints/lines toggle without alert() |
| 12 | `#anat-search-input` (Enter) | `onkeydown="searchAnatomyStructure()"` | `POST /api/v1/workstation/ai-tutor/explain-anatomy` | Displays structure definition and citations | `WORKING` | Enter key initiates search |
| 13 | `button` (Search Structure) | `onclick="searchAnatomyStructure()"` | `POST /api/v1/workstation/ai-tutor/explain-anatomy` | Queries ontology table, renders source citations | `WORKING` | Returns peer-reviewed literature citations |

### 3. Motion Assessment (`#view-motion`)

| # | Selector / Label | Event Handler | Target API / Mechanism | Side Effect / State Update | Status | Verification Evidence |
|---|---|---|---|---|---|---|
| 14 | `.nav-item[3]` (Motion Assessment) | `onclick="switchView('motion')"` | Client DOM Switch | Displays motion assessment view | `WORKING` | View switches seamlessly |
| 15 | `#btn-measure-rom` (Capture & Measure ROM) | `onclick="runMotionAssessment('LIVE')"` | `POST /api/v1/workstation/motion/assess` | Checks camera probe; fails closed if offline with helpful guidance | `WORKING` | In WSL, reports camera offline fail-closed |
| 16 | `#btn-demo-fixture` (Load Standard Fixture) | `onclick="runMotionAssessment('DEMO')"` | `POST /api/v1/workstation/motion/assess` | Calculates ROM from synthetic posture fixture, tags `FIXTURE_*` | `WORKING` | Returns angle, deficit, and ±U95 uncertainty |
| 17 | `#motion-joint-select` | Standard select | Client State | Selects movement (Elbow, Shoulder, Knee) | `WORKING` | Selects target joint angle parameters |
| 18 | `#motion-side-select` | Standard select | Client State | Selects Right vs. Left extremity | `WORKING` | Selects corresponding landmark keys |
| 19 | `#motion-patient-select` | Standard select | Client State | Binds motion assessment to patient profile | `WORKING` | Patient ID associated with test payload |

### 4. Patient Records (`#view-patients`)

| # | Selector / Label | Event Handler | Target API / Mechanism | Side Effect / State Update | Status | Verification Evidence |
|---|---|---|---|---|---|---|
| 20 | `.nav-item[4]` (Patient Records) | `onclick="switchView('patients')"` | Client DOM Switch | Displays patient records table | `WORKING` | Table renders with active profiles |
| 21 | `button` (+ Register Patient) | `onclick="openNewPatientModal()"` | Client Modal DOM | Opens `#newPatientModal` | `WORKING` | Registration modal opens |
| 22 | `#patient-search-box` | `oninput="filterPatients()"` | Client Filter & DOM | Filters by name/complaint with HTML escaping | `WORKING` | Instant search, safe against DOM injection |
| 23 | Table Action (Select) | `onclick="selectPatientForWorkflow(pid)"` | Client State | Selects active patient, switches to Therapy | `WORKING` | Binds patient ID across dropdowns |
| 24 | Table Action (View / Edit) | `onclick="viewPatientDetails(pid)"` | `GET /api/v1/workstation/patients/{id}` | Opens `#patientDetailModal` with form fields | `WORKING` | Modal displays all fields for review/editing |
| 25 | Modal Action (Register Patient) | `onclick="submitNewPatient()"` | `POST /api/v1/workstation/patients` | Validates, stores in SQLite `patients`, reloads | `WORKING` | New record created and visible in table |
| 26 | Modal Action (Cancel Register) | `onclick="closeNewPatientModal()"` | Client Modal DOM | Closes `#newPatientModal` | `WORKING` | Modal hides cleanly |
| 27 | Edit Modal (Save Changes) | `onclick="savePatientEdit()"` | `PUT /api/v1/workstation/patients/{pid}` | Updates SQLite `patients`, refreshes table | `WORKING` | Persisted changes verified after reload |
| 28 | Edit Modal (Discharge Patient) | `onclick="dischargeCurrentPatient()"` | `DELETE /api/v1/workstation/patients/{pid}` | Soft-deletes (sets status to DISCHARGED) | `WORKING` | Status badge updates to DISCHARGED |
| 29 | Edit Modal (Close) | `onclick="closePatientDetailModal()"` | Client Modal DOM | Closes `#patientDetailModal` | `WORKING` | Modal hides cleanly |

### 5. Therapy Workspace (`#view-therapy`)

| # | Selector / Label | Event Handler | Target API / Mechanism | Side Effect / State Update | Status | Verification Evidence |
|---|---|---|---|---|---|---|
| 30 | `.nav-item[5]` (Therapy Workspace) | `onclick="switchView('therapy')"` | Client DOM Switch | Displays therapy workspace | `WORKING` | View displays session form |
| 31 | `#therapy-patient-select` | `onchange="loadPatientForTherapy()"` | Client State & Red Flag check | Checks red flags, loads pre-pain & notes | `WORKING` | Red flag banner appears if acute flags present |
| 32 | `#therapy-pre-pain` | Input (number) | Session Payload | Pre-session VAS 0 - 10 | `WORKING` | Value validated on submit |
| 33 | `#therapy-post-pain` | Input (number) | Session Payload | Post-session VAS 0 - 10 | `WORKING` | Value validated on submit |
| 34 | `#therapy-pre-notes` | Textarea | Session Payload | Subjective complaint notes | `WORKING` | Grounded in SOAP subjective |
| 35 | `#therapy-post-notes` | Textarea | Session Payload | Objective response notes | `WORKING` | Grounded in SOAP assessment |
| 36 | `.modality-check` | Checkbox group | Session Payload | Classifies applied modalities by evidence | `WORKING` | Checked modalities formatted into objective |
| 37 | `#dds-utilized-check` | `onchange="toggleDDSInputs()"` | Client DOM toggle | Shows/hides DDS documentation inputs | `WORKING` | Input row appears/disappears |
| 38 | `#dds-freq` | Input (number) | Session Payload | Documentation only (Hz) | `WORKING` | Stored in `dds_device_records_json` |
| 39 | `#dds-intensity` | Input (number) | Session Payload | Documentation only (mA) | `WORKING` | Stored in `dds_device_records_json` |
| 40 | `#dds-sensation` | Input (text) | Session Payload | Patient reported sensation | `WORKING` | Stored in `dds_device_records_json` |
| 41 | `#btn-preview-soap` (Preview Grounded SOAP) | `onclick="previewSOAP()"` | `POST /patients/{id}/sessions/preview-soap` | Generates grounded SOAP draft without deductions | `WORKING` | Real draft rendered in preview box |
| 42 | `#btn-save-session` (Save Session) | `onclick="saveTherapySession()"` | `POST /patients/{id}/sessions` | Fails closed on red flags; stores in `therapy_sessions` | `WORKING` | Session saved, pain score updated, SOAP displayed |

### 6. Progress Tracking (`#view-progress`)

| # | Selector / Label | Event Handler | Target API / Mechanism | Side Effect / State Update | Status | Verification Evidence |
|---|---|---|---|---|---|---|
| 43 | `.nav-item[6]` (Progress Analytics) | `onclick="switchView('progress')"` | Client DOM Switch | Displays progress tracking view | `WORKING` | Progress view displayed |
| 44 | `#progress-patient-select` | `onchange="loadProgressData()"` | `GET /api/v1/workstation/patients/{pid}/progress` | Fetches session timeline, updates stats & chart | `WORKING` | Stats, chart bars, and timeline table populate |
| 45 | `button` (Export CSV) | `onclick="exportProgressCSV()"` | `GET /patients/{pid}/export/csv` | Initiates browser file download of CSV export | `WORKING` | Formatted, escaped CSV file downloaded |

### 7. Knowledge & AI Tutor (`#view-library`)

| # | Selector / Label | Event Handler | Target API / Mechanism | Side Effect / State Update | Status | Verification Evidence |
|---|---|---|---|---|---|---|
| 46 | `.nav-item[7]` (Knowledge & AI Tutor) | `onclick="switchView('library')"` | Client DOM Switch | Displays library & tutor view | `WORKING` | Library view displayed |
| 47 | `#lib-search-query` (Enter) | `onkeydown="executeLibrarySearch()"` | `GET /ai-tutor/search-library` | Queries FTS5 documents table | `WORKING` | Enter key triggers search |
| 48 | `button` (Search) | `onclick="executeLibrarySearch()"` | `GET /ai-tutor/search-library` | Displays matched literature excerpts & citations | `WORKING` | Excerpts with citations displayed safely |
| 49 | `#tutor-movement-select` | `onchange="executeMovementTutor()"` | `POST /ai-tutor/link-movement` | Renders agonists, synergists, joint type, innervation | `WORKING` | Structured anatomical linkage card displayed |

---

## Safety & Integrity Verification Rules

1. **DOM Injection (XSS) Prevention:** All dynamic data (`full_name`, `primary_complaint`, `id`, `status`, `title`, `snippet`, `citation`) passes through `escapeHtml()` before string concatenation or DOM innerHTML assignment.
2. **Red Flag Hard Stop:** Selecting a patient with `requires_referral == true` reveals an alert banner in the Therapy View and server rejects routine therapy session recording with HTTP 400.
3. **Fail-Closed Camera:** Live ROM measurement without a connected webcam fails closed with typed error `CAMERA_UNAVAILABLE` and guidance to switch to DEMO mode. No phantom measurements are inserted into the database.
4. **Authentic 3D Atlas:** The 3D Atlas uses Three.js and `GLTFLoader` with genuine calibrated assets. No geometric primitives (cylinders/spheres) are represented as authenticated anatomy. Layer toggling modifies real scene graph groups without `alert()`.
