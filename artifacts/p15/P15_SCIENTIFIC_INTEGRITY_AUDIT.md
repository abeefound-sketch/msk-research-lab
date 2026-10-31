# P15 Scientific Integrity & Epistemic Guardrail Audit
**MSK Research Lab OS — Milestone P15**  
**Role:** Biomedical Software Safety Auditor, Scientific Verification Engineer  
**Date:** 2026-10-31  
**Project Path:** [`src/msk_research_lab/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/)

---

## 1. Permanent Safety Invariants Audit

The core safety invariants established in P0 and reinforced through P14 remain uncompromised and fully verified:

| Invariant Guard | Implementation Mechanism | P15 Verification Status |
|---|---|---|
| `CLINICAL_REALWORLD_GATE = BLOCKED` | Enforced at database, API, and UI levels. Clinical intervention tracking without IRB approval is strictly disallowed. | **VERIFIED BLOCKED** |
| `PHYSICAL_STEREO_HARDWARE_GATE = BLOCKED` | Physical multi-camera stereo acquisition hardware triggers fail-closed error. Synthetic fixtures only. | **VERIFIED BLOCKED** |
| `CANNOT_IMPLICITLY_PROJECT_2D_TO_3D = FAIL_CLOSED` | 2D video pose keypoints cannot be uncalibratedly back-projected to 3D Cartesian coordinates without direct stereo PnP calibration. | **VERIFIED FAIL-CLOSED** |
| `AIR_GAPPED_LOOPBACK_ONLY` | All HTTP, WebSocket, and assets served strictly on `127.0.0.1` and `::1`. Outbound external sockets blocked. | **VERIFIED 100% LOOPBACK** |

---

## 2. Epistemic Guardrail & Linguistic Claims Audit

To ensure the educational platform never misleads students, researchers, or clinicians into treating educational simulations as medical diagnostics, the codebase was audited for prohibited medical diagnostic claims:

### 2.1 Prohibited Claims Verification
- Searches for `"cures pain"`, `"permanent fix guaranteed"`, `"diagnostic test"`, `"diagnoses impingement"` returned **0 occurrences** across all source code, models, and educational texts.
- All 6 Guided Learning scenes and 6 Motor Control topics explicitly document scientific limitations:
  > *"Educational demonstration model based on rigid-body kinematic approximations. Subacromial proximity indicates geometric clearance changes, NOT a clinical diagnosis of impingement syndrome."*

### 2.2 Strict Delineation of Scenario-Specific Data
Under Model B (Restricted Scapulohumeral Rhythm):
- The engine does NOT guess or extrapolate altered muscle activations.
- All returned muscle dynamics records carry the explicit caveat tag `NOT_VERIFIED_FOR_MODIFIED_POSTURE`.
- The UI displays an amber warning banner cautioning researchers that values represent unadjusted baseline coordinates.

---

## 3. Provenance Schema Enforcement

Every endpoint in `/api/v1/biomechanics/shoulder/` delivers structured `ScientificContentProvenance` metadata conforming to:
- `source_model`: Explicit OpenSim model identifier (`MOBL_ARMS_41`, `INMAN_1944_CANONICAL`).
- `source_dataset`: Underlying reference database (`BodyParts3D 3.0`, `OpenSim 4.6`).
- `assumption_type`: Explicit categorization (`EMPIRICAL_LITERATURE`, `OPENSIM_SIMULATION`, `HYPOTHETICAL_SCENARIO`).
- `measurement_or_simulation`: Clear classification (`SIMULATION` vs `EMPIRICAL_MEASUREMENT`).
- `validation_status`: Benchmarked status (`VERIFIED_BASELINE_BENCHMARK`, `NOT_VERIFIED_FOR_MODIFIED_POSTURE`, `EDUCATIONAL_ESTIMATE`).
- `known_limitations`: Complete paragraph stating rigid bone simplifications, lack of soft tissue compliance, and exclusion of patient-specific scapular morphology.
