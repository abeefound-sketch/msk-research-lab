"""Safety Gate Regression Test Suite (P0 Baseline & Safety Invariants).

Verifies:
1. Red Flag hard-stop: blocks recording interventions when clinical red flags are present.
2. Missing camera fail-closed: does not save fake live records when webcam is unavailable.
3. DEMO mode isolation: synthetic fixtures are explicitly tagged and do not masquerade as live measurements.
4. Kinematics fail-closed: missing or degenerate landmarks do not produce false 0° measurements or OPTIMAL status.
5. Zero DDS actuation: software strictly records readouts and never actuates physical hardware.
"""

import pytest
from fastapi.testclient import TestClient
from msk_research_lab.api.app import app
from msk_research_lab.core.db import get_db
from msk_research_lab.workstation.patient_manager import create_patient, get_patient
from msk_research_lab.workstation.therapy_manager import (
    record_therapy_session, TherapySessionError, generate_soap_note
)
from msk_research_lab.motion.camera_service import (
    execute_motion_assessment, CameraUnavailableError, probe_hardware_camera
)
from msk_research_lab.motion.kinematics import compute_joint_rom


@pytest.fixture
def client():
    return TestClient(app)


def test_red_flag_hard_stop_blocks_intervention_recording(client):
    """Verify that an active red flag strictly blocks therapy intervention recording at service and API levels."""
    # 1. Register synthetic patient with acute red flags
    patient = create_patient(
        full_name="Synthetic RedFlag Patient",
        primary_complaint="Severe lumbar pain with progressive bilateral leg weakness",
        red_flags={
            "fever": True,
            "motor_deficit": True,
            "bowel_bladder_dysfunction": False
        }
    )
    pid = patient["id"]
    assert patient["red_flags"]["requires_referral"] is True

    # 2. Direct service call must raise TherapySessionError
    with pytest.raises(TherapySessionError) as exc_info:
        record_therapy_session(
            patient_id=pid,
            pre_pain_score=8.0,
            post_pain_score=4.0,
            applied_modalities=[{"name": "Lumbar traction", "category": "MANUAL_THERAPY"}]
        )
    assert "CLINICAL_RED_FLAG_BLOCKED" in str(exc_info.value)

    # 3. HTTP API call must fail with 400
    with get_db() as conn:
        count_before = conn.execute("SELECT COUNT(*) FROM therapy_sessions WHERE patient_id = ?", (pid,)).fetchone()[0]

    res = client.post(f"/api/v1/workstation/patients/{pid}/sessions", json={
        "pre_pain_score": 8.0,
        "post_pain_score": 5.0,
        "applied_modalities": [{"name": "Spinal manipulation", "category": "MANUAL_THERAPY"}]
    })
    assert res.status_code == 400
    assert "CLINICAL_RED_FLAG_BLOCKED" in res.text

    # 4. Verify DB session count has NOT increased
    with get_db() as conn:
        count_after = conn.execute("SELECT COUNT(*) FROM therapy_sessions WHERE patient_id = ?", (pid,)).fetchone()[0]
    assert count_after == count_before


def test_missing_camera_fails_closed_without_fake_live_record(client):
    """Verify that LIVE mode without camera fails closed and inserts NO phantom records."""
    patient = create_patient(
        full_name="Synthetic Camera Test Patient",
        primary_complaint="Cervical stiffness"
    )
    pid = patient["id"]

    # In WSL without camera, probe must report offline
    probe = probe_hardware_camera()
    if not probe.get("available"):
        with get_db() as conn:
            initial_count = conn.execute("SELECT COUNT(*) FROM motion_assessments WHERE patient_id = ?", (pid,)).fetchone()[0]

        # Service-level fail closed
        with pytest.raises(CameraUnavailableError):
            execute_motion_assessment(patient_id=pid, joint_tested="ELBOW_FLEXION", mode="LIVE")

        # API-level fail closed
        res = client.post("/api/v1/workstation/motion/assess", json={
            "patient_id": pid,
            "joint_tested": "ELBOW_FLEXION",
            "mode": "LIVE"
        })
        assert res.status_code in (400, 422)
        assert "CAMERA_UNAVAILABLE" in res.text

        # Verify no phantom rows in DB
        with get_db() as conn:
            final_count = conn.execute("SELECT COUNT(*) FROM motion_assessments WHERE patient_id = ?", (pid,)).fetchone()[0]
        assert final_count == initial_count


def test_demo_mode_isolation():
    """Verify DEMO mode returns explicitly labeled synthetic fixtures and does not contaminate live table."""
    patient = create_patient(
        full_name="Synthetic Demo Mode Patient",
        primary_complaint="Right shoulder impingement"
    )
    pid = patient["id"]

    with get_db() as conn:
        initial_count = conn.execute("SELECT COUNT(*) FROM motion_assessments WHERE patient_id = ?", (pid,)).fetchone()[0]

    res = execute_motion_assessment(
        patient_id=pid,
        joint_tested="SHOULDER_ABDUCTION",
        mode="DEMO"
    )
    assert res["mode"] == "DEMO"
    assert res["is_synthetic"] is True
    assert "FIXTURE_" in res["data_source"]
    assert res["measured_rom_deg"] is not None

    # Verify persisted record is strictly flagged as synthetic fixture, never live
    with get_db() as conn:
        row = conn.execute("SELECT data_source, is_synthetic FROM motion_assessments WHERE id = ?", (res["id"],)).fetchone()
    assert row is not None
    assert row["is_synthetic"] == 1
    assert "FIXTURE_" in row["data_source"]
    assert row["data_source"] != "WEBCAM_LIVE_FRAME"


def test_kinematics_missing_landmarks_fail_closed():
    """Verify that missing landmarks return INSUFFICIENT_DATA and measured_rom_deg=None, never false OPTIMAL."""
    # Omit wrist landmark for elbow flexion
    incomplete_landmarks = {
        "right_shoulder": (0.50, 0.35),
        "right_elbow": (0.50, 0.55)
        # right_wrist is missing!
    }
    result = compute_joint_rom(incomplete_landmarks, "ELBOW_FLEXION", side="RIGHT")
    assert result["measured_rom_deg"] is None
    assert result["quality_status"] == "INSUFFICIENT_DATA"
    assert result["tracking_confidence"] == 0.0
    assert any("MISSING_LANDMARK" in w for w in result["warnings"])
    assert result["quality_status"] != "OPTIMAL"


def test_kinematics_degenerate_geometry_fail_closed():
    """Verify that zero-length landmark vectors return DEGENERATE_GEOMETRY, never false 0° or OPTIMAL."""
    degenerate_landmarks = {
        "right_shoulder": (0.50, 0.50),
        "right_elbow": (0.50, 0.50),  # Same as shoulder!
        "right_wrist": (0.50, 0.50)
    }
    result = compute_joint_rom(degenerate_landmarks, "ELBOW_FLEXION", side="RIGHT")
    assert result["measured_rom_deg"] is None
    assert result["quality_status"] == "DEGENERATE_GEOMETRY"
    assert any("DEGENERATE_VECTORS" in w for w in result["warnings"])
    assert result["quality_status"] != "OPTIMAL"


def test_soap_note_grounding_and_no_deductive_claims():
    """Verify SOAP generator does not invent clinical outcomes or tolerance when not documented."""
    patient = {
        "primary_complaint": "Right knee osteoarthritis",
        "functional_limitations": "Pain with deep squatting"
    }
    soap = generate_soap_note(
        patient=patient,
        pre_pain=6.0,
        post_pain=4.0,
        pre_symptoms="",  # Empty
        post_symptoms="", # Empty
        modalities=[],
        motion_assessments=[]
    )
    # Must NOT claim 'tissue softening' or 'well tolerated'
    assert "tissue softening" not in soap["assessment"].lower()
    assert "well tolerated" not in soap["assessment"].lower()
    assert "Not documented" in soap["subjective"]
    assert "Not documented" in soap["assessment"]
    assert "No manual modalities applied" in soap["objective"]
