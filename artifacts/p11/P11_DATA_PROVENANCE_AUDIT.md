# P11 SCIENTIFIC DATA PROVENANCE AUDIT
**MSK Research Lab OS — Standardized Four-State Measurement Provenance Framework**

- **Audit Date:** 2026-10-30
- **Auditor:** Biomedical Software Verification Engineer
- **Specification Module:** [`src/msk_research_lab/scientific/provenance.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/scientific/provenance.py)
- **Status:** ENFORCED & AUDITED

---

## 1. Executive Summary

In scientific research workstations, ambiguity between simulated synthetic data, uncalibrated approximations, and physical measurements represents an epistemological hazard. Milestone P11 resolves `DEF-30` by formalizing a four-state measurement provenance classification framework and embedding it into all kinematic evaluations, optical registrations, and database schemas.

---

## 2. Four-State Provenance Classification (`MeasurementProvenanceType`)

```python
class MeasurementProvenanceType(str, Enum):
    LIVE_MEASURED = "LIVE_MEASURED"
    SYNTHETIC_TEST = "SYNTHETIC_TEST"
    NOT_MEASURABLE = "NOT_MEASURABLE"
    INVALID_INPUT = "INVALID_INPUT"
```

### Definitions & Operational Criteria

1. **`LIVE_MEASURED`**:
   - **Definition:** Direct physical observation acquired from an online, authenticated, and calibrated sensor (e.g. physical camera or stereo rig).
   - **Requirements:** Hardware status `available=True`, physical frame read successful, tracker landmarks above confidence threshold.
   - **Clinical Certification:** `clinical_use_permitted: False` (Personal Offline / Research Only).

2. **`SYNTHETIC_TEST`**:
   - **Definition:** Simulated, modeled, or fixture-generated test data used for demonstration, algorithm verification, or benchmark comparison.
   - **Requirements:** Ingested from verified posture fixtures (e.g. `STANDARD_POSTURE_FIXTURES`) or procedural geometric representations. Explicitly tagged `is_synthetic: True`.

3. **`NOT_MEASURABLE`**:
   - **Definition:** Measurement requested but physically impossible to resolve due to sensor absence, target occlusion, or insufficient landmark confidence.
   - **Requirements:** Fails closed. Does NOT synthesize surrogate numbers.

4. **`INVALID_INPUT`**:
   - **Definition:** Numerical calculation aborted due to mathematically degenerate inputs (e.g. collinear landmarks, zero-length vectors, singular Jacobian).
   - **Requirements:** Raises specific domain exception (`DegenerateGeometryError`, `CalibratedRegistrationError`).

---

## 3. System-Wide Integration

- **Kinematics Engine:** [`src/msk_research_lab/motion/camera_service.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/motion/camera_service.py) outputs `provenance_type` (`SYNTHETIC_TEST` in DEMO mode; `LIVE_MEASURED` in verified physical webcam mode).
- **Facial Reflexology 2D-to-3D Registration:** [`src/msk_research_lab/studio/calibrated_registration.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/studio/calibrated_registration.py) outputs `provenance_type = SYNTHETIC_TEST` with spatial condition number and planarity ratio.
- **Database Schema:** `motion_assessments` table stores `provenance_category` and `is_synthetic` flag permanently.
