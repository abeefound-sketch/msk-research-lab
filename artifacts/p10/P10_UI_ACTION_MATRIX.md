# MSK Research Lab OS — P10 UI Action Matrix

**Milestone:** P10  
**Interface Verified:** Offline Workstation UI (`http://127.0.0.1:8000/`)  
**Scope:** 49 Interactive Browser Controls across 6 Clinical & Research Panels  
**Acceptance Criteria:** Every control performs real state mutation, database persistence, API readback, or anatomical rendering. Zero click-dummy controls permitted.

---

## Interactive Control Verification Table

| Control # | Panel / Workflow | DOM Selector / Control ID | Action Performed | Backend Mutation / Verification Evidence | Verdict |
| :---: | :--- | :--- | :--- | :--- | :---: |
| 1 | Patient Management | `#btn-new-patient` | Modal trigger | Opens create profile dialog | **VERIFIED** |
| 2 | Patient Management | `#patient-full-name` | Text input | Populates patient full name | **VERIFIED** |
| 3 | Patient Management | `#patient-age` | Numeric input | Populates patient age (triggers Safe Harbor 90+ aggregation) | **VERIFIED** |
| 4 | Patient Management | `#patient-gender` | Select dropdown | Mutates gender field | **VERIFIED** |
| 5 | Patient Management | `#patient-height` | Numeric input | Persists height_cm in DB | **VERIFIED** |
| 6 | Patient Management | `#patient-weight` | Numeric input | Persists weight_kg in DB | **VERIFIED** |
| 7 | Patient Management | `#patient-complaint` | Text area | Input primary symptom; scrubbed on export | **VERIFIED** |
| 8 | Patient Management | `#patient-history` | Text area | Medical history; scrubbed of provider/phone/date | **VERIFIED** |
| 9 | Patient Management | `#patient-save-btn` | POST `/api/v1/workstation/patients` | Inserts record, generates HMAC pseudonym, logs audit | **VERIFIED** |
| 10 | Patient Management | `#patient-search-input`| Dynamic query | Filters SQLite patient table by pseudonym / query | **VERIFIED** |
| 11 | Patient Management | `#patient-export-btn` | GET `/export/deidentified` | Returns JSON de-identified research record | **VERIFIED** |
| 12 | Patient Management | `#patient-discharge-btn`| Soft delete | Updates patient status to `DISCHARGED` | **VERIFIED** |
| 13 | Clinical SOAP | `#soap-subjective` | Text area | Updates SOAP subjective narrative | **VERIFIED** |
| 14 | Clinical SOAP | `#soap-objective` | Text area | Updates physical examination findings | **VERIFIED** |
| 15 | Clinical SOAP | `#soap-assessment` | Text area | Records research diagnostic hypothesis | **VERIFIED** |
| 16 | Clinical SOAP | `#soap-plan` | Text area | Records therapeutic exercise protocol | **VERIFIED** |
| 17 | Clinical SOAP | `#soap-save-btn` | POST `/soap-notes` | Persists versioned SOAP note in SQLite | **VERIFIED** |
| 18 | Pain & VAS Scale | `#vas-slider` | Range input (0–10) | Live updates numerical VAS rating display | **VERIFIED** |
| 19 | Pain & VAS Scale | `#vas-location-select`| Multi-select | Links pain ratings to specific anatomical zones | **VERIFIED** |
| 20 | Pain & VAS Scale | `#vas-save-btn` | POST `/pain-scores` | Persists temporal pain assessment event | **VERIFIED** |
| 21 | Range of Motion | `#rom-joint-select` | Select dropdown | Selects cervical / shoulder / lumbar / knee joint | **VERIFIED** |
| 22 | Range of Motion | `#rom-plane-select` | Select dropdown | Selects sagittal / frontal / transverse plane | **VERIFIED** |
| 23 | Range of Motion | `#rom-angle-input` | Numeric input | Ingests measured angle in degrees | **VERIFIED** |
| 24 | Range of Motion | `#rom-save-btn` | POST `/rom-measurements`| Persists kinematics data point | **VERIFIED** |
| 25 | Red Flags Screening | `#flag-fever` | Checkbox toggle | Flags fever / constitutional symptoms | **VERIFIED** |
| 26 | Red Flags Screening | `#flag-weight-loss` | Checkbox toggle | Flags unexplained weight loss | **VERIFIED** |
| 27 | Red Flags Screening | `#flag-night-pain` | Checkbox toggle | Flags severe unremitting night pain | **VERIFIED** |
| 28 | Red Flags Screening | `#flag-neurological` | Checkbox toggle | Flags progressive motor weakness | **VERIFIED** |
| 29 | Red Flags Screening | `#flag-notes` | Text area | Referral notes; scrubbed of physician names | **VERIFIED** |
| 30 | Red Flags Screening | `#red-flags-save-btn`| POST `/red-flags` | Updates safety flags; displays urgency banner | **VERIFIED** |
| 31 | 3D Anatomical Atlas | `#layer-skeleton` | Checkbox toggle | Toggles skeletal mesh visibility in Three.js | **VERIFIED** |
| 32 | 3D Anatomical Atlas | `#layer-muscles` | Checkbox toggle | Toggles muscular layer visibility | **VERIFIED** |
| 33 | 3D Anatomical Atlas | `#layer-fascia` | Checkbox toggle | Toggles superficial fascia layer | **VERIFIED** |
| 34 | 3D Anatomical Atlas | `#layer-meridians` | Checkbox toggle | Renders 14 bilateral acupuncture trajectories | **VERIFIED** |
| 35 | 3D Anatomical Atlas | `#preset-anterior` | Button click | Sets camera to anterior anatomical view | **VERIFIED** |
| 36 | 3D Anatomical Atlas | `#preset-posterior`| Button click | Sets camera to posterior view | **VERIFIED** |
| 37 | 3D Anatomical Atlas | `#preset-lateral-l` | Button click | Sets camera to left lateral view | **VERIFIED** |
| 38 | 3D Anatomical Atlas | `#preset-lateral-r` | Button click | Sets camera to right lateral view | **VERIFIED** |
| 39 | 3D Anatomical Atlas | `#model-selector` | Select dropdown | Switches between BodyParts3D and TCM mannequin | **VERIFIED** |
| 40 | Diện Chẩn Studio | `#dc-point-input` | Text query | Selects facial reflexology point (e.g. 19, 61) | **VERIFIED** |
| 41 | Diện Chẩn Studio | `#dc-project-btn` | Epistemic guard | Blocked without calibration context | **VERIFIED** |
| 42 | Diện Chẩn Studio | `#dc-calibrated-reg`| 6-DoF LM PnP | Solves pose; projects 2D to 3D with uncertainty | **VERIFIED** |
| 43 | Stereo Metrology | `#stereo-probe-btn` | Hardware probe | Queries physical cameras; returns `BLOCKED` | **VERIFIED** |
| 44 | Stereo Metrology | `#stereo-baseline` | Number slider | Updates baseline parameter in sensitivity table | **VERIFIED** |
| 45 | Stereo Metrology | `#stereo-focal` | Number slider | Updates focal length; calculates $\sigma_Z$ | **VERIFIED** |
| 46 | Key Management | `#btn-rotate-pepper`| POST `/rotate-pepper`| Two-phase key rotation with audit event | **VERIFIED** |
| 47 | Key Management | `#btn-recover-pepper`| GET `/recover-pepper` | Resynchronizes key from `.key_vault` | **VERIFIED** |
| 48 | Disaster Recovery | `#btn-backup-now` | POST `/backup` | Creates encrypted `MSKENC02` AES-GCM archive | **VERIFIED** |
| 49 | Disaster Recovery | `#btn-restore-file` | POST `/restore` | Validates staging, checks integrity, restores | **VERIFIED** |

**Summary:** 49/49 interactive UI controls confirmed fully functional and backed by real computational logic and storage persistence.
