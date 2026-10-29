# MSK Research Lab OS v3.2 — Workstation API Contract Matrix

**Date:** 2026-10-29  
**Version:** v3.2 Recovery  
**Target:** MSK Therapy Personal Workstation Endpoints (`/workstation` and `/api/v1/workstation/*`)  
**Safety Status:** Enforced Offline-First, Server-Authoritative Red-Flag Block, Fail-Closed Epistemics, Zero-PII Policy.

---

## 1. Overview & Architectural Invariants

1. **Fail-Closed Red-Flag Hard Stop:** Any attempt to record a routine therapy session (`POST /api/v1/workstation/patients/{id}/sessions`) for a patient exhibiting red flag symptoms (`requires_referral == True`) is unconditionally blocked with HTTP 400 (`CLINICAL_RED_FLAG_BLOCKED`).
2. **Provenance-Preserving Kinematics:** Live motion tests (`mode="LIVE"`) without verified hardware webcam input return typed error HTTP 400/422 (`CAMERA_UNAVAILABLE`). Synthetic fixtures are explicitly routed to `mode="DEMO"`, tagged with `FIXTURE_*` identifiers and stored with `data_source = 'DEMO_FIXTURE'` and `is_synthetic = 1`.
3. **No Speculative Clinical Generation:** SOAP notes only document clinically grounded inputs; empty or absent fields evaluate strictly to `"Not documented"`.
4. **CSV Injection Defense:** Progress CSV exports neutralize formula execution (`=`, `+`, `-`, `@`, `\t`, `\r`) via cell prepending (`'`).
5. **DOM Injection (XSS) Mitigation:** All endpoints returning user-controllable text are consumed by client UI handlers via strict HTML escaping (`escapeHtml()`).

---

## 2. API Contract Endpoints

| # | HTTP Method & Path | Purpose | Input Parameters / Body | Validation Rules & Safety Gates | Success Response | Error Codes & Fail-Closed Behavior | Database / System Side Effects |
|---|---|---|---|---|---|---|---|
| 1 | `GET /workstation` | Unified Personal Workstation SPA | None | None | `200 OK` (text/html) Single-page application | `500` if template render fails | Read-only |
| 2 | `GET /api/v1/workstation/overview` | Workstation Diagnostics & Metrics | None | None | `200 OK` (JSON): system status, component health, aggregate counters, safety status | `500` on database error | Read-only query across `patients`, `therapy_sessions`, `motion_assessments`, `documents`, `models_3d` |
| 3 | `GET /api/v1/workstation/patients` | Search & List Patient Profiles | `search`: string (optional)<br>`status`: string (optional) | String sanitized; case-insensitive substring search | `200 OK` (JSON array): List of patient profiles | None (empty list if no match) | Read-only query on `patients` table |
| 4 | `POST /api/v1/workstation/patients` | Register New Synthetic Patient | JSON: `full_name` (required), `primary_complaint` (required), demographics, pain score, red flags | `full_name` must be non-empty; `current_pain_score` clamped 0.0–10.0; red flags evaluated | `200 OK` (JSON): Created patient record with generated `id` (UUID4) | `400 Bad Request` if name or complaint missing | `INSERT INTO patients` (with `created_at`, `status='ACTIVE'`, `is_synthetic=1`) |
| 5 | `GET /api/v1/workstation/patients/{id}` | Get Patient Details | Path `id`: string (UUID4) | Patient must exist in database | `200 OK` (JSON): Complete patient profile | `404 Not Found` if patient ID does not exist | Read-only |
| 6 | `PUT /api/v1/workstation/patients/{id}` | Update Patient Record | Path `id`: string<br>JSON: Partial update dictionary | Target patient must exist; pain score clamped 0.0–10.0 | `200 OK` (JSON): Updated patient profile | `404 Not Found` if patient ID invalid | `UPDATE patients SET ... WHERE id = ?` |
| 7 | `DELETE /api/v1/workstation/patients/{id}` | Discharge Patient Record | Path `id`: string (UUID4) | Soft-delete only; sets `status = 'DISCHARGED'` | `200 OK` (JSON): `{"status": "SUCCESS", "message": "..."}` | `404 Not Found` if patient ID does not exist | `UPDATE patients SET status = 'DISCHARGED' WHERE id = ?` |
| 8 | `GET /api/v1/workstation/patients/{id}/sessions` | List Patient Therapy Sessions | Path `id`: string (UUID4) | Patient existence verified | `200 OK` (JSON array): Chronological sessions | `404 Not Found` if patient missing | Read-only query on `therapy_sessions` |
| 9 | `POST /api/v1/workstation/patients/{id}/sessions` | Record Therapy Session | Path `id`: string<br>JSON: `pre_pain_score`, `post_pain_score`, notes, modalities, DDS records | **Gate P0 Enforced:** If patient has active red flags (`requires_referral == True`), session is rejected | `200 OK` (JSON): Saved therapy session record with generated grounded SOAP note | `400 Bad Request` with `detail: "CLINICAL_RED_FLAG_BLOCKED..."` if red flags present | `INSERT INTO therapy_sessions`; `UPDATE patients SET current_pain_score = ?` |
| 10 | `POST /api/v1/workstation/patients/{id}/sessions/preview-soap` | Preview Grounded SOAP Note | Path `id`: string<br>JSON: Session draft parameters | Evaluates session draft parameters without persisting | `200 OK` (JSON): `{"status": "SUCCESS", "soap": "..."}` | `400 Bad Request` if patient ID invalid | Read-only generation |
| 11 | `GET /api/v1/workstation/sessions/{session_id}` | Get Session Details | Path `session_id`: string | Session ID existence verified | `200 OK` (JSON): Full session record | `404 Not Found` if session missing | Read-only query on `therapy_sessions` |
| 12 | `GET /api/v1/workstation/motion/probe` | Hardware Camera Diagnostic | None | Probes OS video interfaces (`/dev/video*`, OpenCV VideoCapture) | `200 OK` (JSON): `{"available": bool, "status": str, "details": str}` | None (fails open reporting unavailable) | Hardware device enumeration |
| 13 | `POST /api/v1/workstation/motion/assess` | Run Kinematic ROM Assessment | JSON: `patient_id`, `joint_tested`, `side`, `mode` (`LIVE` or `DEMO`), `fixture_name` | In `LIVE` mode: fails closed if camera offline. In `DEMO` mode: runs synthetic posture fixture | `200 OK` (JSON): Kinematic assessment with ROM angle, normal ROM, deficit, U95 uncertainty | `400 Bad Request` (`CAMERA_UNAVAILABLE`); `422 Unprocessable` (`NO_POSE`, `INSUFFICIENT_LANDMARKS`) | `INSERT INTO motion_assessments` (with `data_source` and `is_synthetic`) |
| 14 | `GET /api/v1/workstation/patients/{id}/motion` | List Patient Motion Assessments | Path `id`: string (UUID4) | Patient ID validated | `200 OK` (JSON array): List of motion tests | None (empty list if no tests) | Read-only query on `motion_assessments` |
| 15 | `GET /api/v1/workstation/patients/{id}/progress` | Longitudinal Progress Summary | Path `id`: string (UUID4) | Patient existence verified | `200 OK` (JSON): Session counts, initial/current/delta pain scores, percent improvement, session timeline | `404 Not Found` if patient ID missing | Read-only aggregation over `therapy_sessions` |
| 16 | `GET /api/v1/workstation/patients/{id}/export/csv` | Export Progress Data to CSV | Path `id`: string (UUID4) | Patient existence verified; CSV cells sanitized against formula injection | `200 OK` (`text/csv` attachment): RFC 4180 compliant CSV stream | `404 Not Found` if patient ID missing | Read-only stream export |
| 17 | `POST /api/v1/workstation/ai-tutor/explain-anatomy` | Anatomical Structure Query | JSON: `name`: string | Concept lookup in SQLite ontology graph | `200 OK` (JSON): Structured explanation with peer-reviewed literature citations | None (grounded "No definition found" if absent) | Read-only query on `ontology_concepts` and `citations` |
| 18 | `POST /api/v1/workstation/ai-tutor/link-movement` | Movement Biomechanics Linkage | JSON: `movement`: string | Movement lookup in biomechanics registry | `200 OK` (JSON): Agonist, synergist, antagonist muscles, joint classification, nerve roots | None (returns default schema if unknown) | Read-only biomechanical model lookup |
| 19 | `POST /api/v1/workstation/ai-tutor/explain-uncertainty` | Measurement Uncertainty Explanation | JSON: `joint_tested`, `measured_rom`, `uncertainty_u95`, `quality_status`, `confounders` | Validates numerical ranges; generates ISO GUM compliant interpretation | `200 OK` (JSON): Natural language uncertainty breakdown with clinical implications | None | Computational synthesis |
| 20 | `POST /api/v1/workstation/ai-tutor/audit-session` | SOAP Documentation Audit | JSON: `patient`, `session` | Audits documentation for completeness, objective measurements, red flag follow-up | `200 OK` (JSON): Score (0–100), missing elements, clinical quality notes | None | Computational audit |
| 21 | `GET /api/v1/workstation/ai-tutor/search-library` | Evidence Library Search | `q`: query string (min 2 chars)<br>`limit`: int (default 5) | Query executed against SQLite FTS5 index on documents | `200 OK` (JSON array): Matched documents with title, excerpt, and DOI/PMID citation | None (empty list if no match) | FTS5 full-text search on `documents_fts` |
| 22 | `GET /api/v1/atlas/scene/{model_id}` | 3D Atlas Scene Configuration | Path `model_id`: string (`watercmy_bp3d_z_anatomy` or `spacejohnlf_tcm_acupoints`) | Model must exist in `models_3d` registry | `200 OK` (JSON): Model metadata, camera position, layer manifest, source attribution | `404 Not Found` if model unrecognized | Read-only query on `models_3d` |
| 23 | `GET /models/{model_id}/file` | Serve Authentic 3D GLB Asset | Path `model_id`: string | Validated model asset on disk | `200 OK` (`model/gltf-binary`): Authentic binary GLTF 2.0 stream | `404 Not Found` if file missing | Read-only filesystem stream |

---

## 3. Data Schema Definitions

### Synthetic Patient Record Schema (`patients`)
```json
{
  "id": "urn:uuid:f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "full_name": "Synthetic Test Patient",
  "pseudonym_hash": "a1b2c3d4e5f6...",
  "primary_complaint": "Right elbow medial epicondylitis",
  "age": 42,
  "gender": "M",
  "height_cm": 178.0,
  "weight_kg": 75.0,
  "occupation": "Desk Worker / Programmer",
  "activity_level": "MODERATE",
  "medical_history": "No prior surgeries.",
  "pain_locations": ["Right medial elbow"],
  "current_pain_score": 6.0,
  "radiating_symptoms": {"present": false, "description": ""},
  "functional_limitations": "Pain with gripping and keyboard use.",
  "red_flags": {
    "fever_chills": false,
    "unexplained_weight_loss": false,
    "history_of_cancer": false,
    "severe_night_pain": false,
    "progressive_neurological_deficit": false,
    "bowel_bladder_dysfunction": false,
    "requires_referral": false,
    "referral_reason": ""
  },
  "status": "ACTIVE",
  "created_at": "2026-10-29T10:00:00Z",
  "updated_at": "2026-10-29T10:00:00Z",
  "is_synthetic": 1
}
```

### Motion Assessment Record Schema (`motion_assessments`)
```json
{
  "id": "urn:uuid:7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
  "patient_id": "urn:uuid:f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "session_id": null,
  "joint_tested": "ELBOW_FLEXION",
  "side": "RIGHT",
  "measured_rom_deg": 138.5,
  "normal_rom_deg": 145.0,
  "deficit_deg": 6.5,
  "uncertainty_u95": 1.5,
  "quality_status": "OPTIMAL",
  "confounders": ["NORMAL_LIGHTING", "FRONTAL_PLANE_ALIGNED"],
  "data_source": "DEMO_FIXTURE",
  "fixture_name": "FIXTURE_ELBOW_FLEXION_140",
  "created_at": "2026-10-29T10:05:00Z",
  "is_synthetic": 1
}
```
