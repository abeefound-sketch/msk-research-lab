"""Comprehensive Integration Tests for MSK Therapy Personal Workstation (Task 05P)."""

import pytest
from fastapi.testclient import TestClient
from msk_research_lab.api.app import app
from msk_research_lab.workstation.patient_manager import (
    create_patient, get_patient, list_patients, evaluate_red_flags, get_pseudonym_hash
)
from msk_research_lab.workstation.therapy_manager import (
    record_therapy_session, get_therapy_session, list_patient_sessions
)
from msk_research_lab.workstation.progress_tracker import (
    get_patient_progress_summary, export_patient_progress_csv
)
from msk_research_lab.motion.kinematics import (
    compute_2d_angle, evaluate_motion_quality, compute_joint_rom
)
from msk_research_lab.motion.camera_service import (
    probe_hardware_camera, execute_motion_assessment
)
from msk_research_lab.ai_tutor.tutor import (
    explain_anatomical_structure, link_movement_to_muscles, explain_measurement_uncertainty,
    audit_session_completeness, search_evidence_library
)


@pytest.fixture
def client():
    return TestClient(app)


# ==========================================
# 1. UNIT & LOGIC TESTS
# ==========================================

def test_patient_keyed_pseudonym_and_red_flags():
    """Verify keyed HMAC pseudonym and clinical red flag evaluator."""
    hash1 = get_pseudonym_hash("PAT-TEST-01")
    hash2 = get_pseudonym_hash("PAT-TEST-01")
    assert hash1 == hash2
    assert len(hash1) == 64

    # Red flag trigger
    rf_clean = evaluate_red_flags({"fever": False, "motor_deficit": False})
    assert rf_clean["requires_referral"] is False

    rf_danger = evaluate_red_flags({"fever": True, "motor_deficit": True})
    assert rf_danger["requires_referral"] is True
    assert "CRITICAL" in rf_danger["referral_notes"]


def test_motion_kinematics_and_confounders():
    """Verify 2D angle geometry, clamping, and humeral elevation confounder."""
    # Right angle: (0, 1) -> (0, 0) -> (1, 0) == 90 deg
    angle_90 = compute_2d_angle((0.0, 1.0), (0.0, 0.0), (1.0, 0.0))
    assert abs(angle_90 - 90.0) < 1e-4

    # Straight line: 180 deg
    angle_180 = compute_2d_angle((-1.0, 0.0), (0.0, 0.0), (1.0, 0.0))
    assert abs(angle_180 - 180.0) < 1e-4

    # Degenerate zero vector: does not throw, clamps gracefully
    angle_zero = compute_2d_angle((0.0, 0.0), (0.0, 0.0), (0.0, 0.0))
    assert angle_zero == 0.0

    # Test Humeral Elevation Confounder (elbow higher in frame than shoulder)
    landmarks = {
        "right_shoulder": (0.50, 0.50),
        "right_elbow": (0.50, 0.30),  # Higher in frame (y is smaller)
        "right_wrist": (0.50, 0.10)
    }
    eval_res = evaluate_motion_quality(landmarks, "SHOULDER_ABDUCTION", side="RIGHT")
    assert "HUMERAL_ELEVATION_CONFOUNDER" in eval_res["confounding_factors"]
    assert eval_res["uncertainty_budget"]["coverage_factor_k"] == 1.96
    assert eval_res["uncertainty_budget"]["distributional_assumption"] == "GAUSSIAN_ASYMPTOTIC_NORMAL"


def test_ai_tutor_rule_and_fts5_citations():
    """Verify AI Tutor structure lookup and movement linkage."""
    # Structure explain
    exp = explain_anatomical_structure("Trapezius")
    assert exp["name"] is not None
    assert "citations" in exp

    # Movement explain
    link = link_movement_to_muscles("SHOULDER_ABDUCTION")
    assert "Middle Deltoid" in link["anatomical_linkage"]["primary_agonists"]
    assert "Glenohumeral" in link["anatomical_linkage"]["joint_classification"]

    # Uncertainty explain
    unc = explain_measurement_uncertainty("ELBOW_FLEXION", 90.0, 1.5, "OPTIMAL")
    assert "±1.50°" in unc["expanded_uncertainty"]
    assert "confidence_interval_95" in unc


# ==========================================
# 2. REST API INTEGRATION TESTS
# ==========================================

def test_workstation_page_and_overview(client):
    """Verify workstation UI and operational status endpoint."""
    res_ui = client.get("/workstation")
    assert res_ui.status_code == 200
    assert "MSK Therapy Personal Workstation" in res_ui.text
    assert "/static/vendor/three.min.js" in res_ui.text

    res_ov = client.get("/api/v1/workstation/overview")
    assert res_ov.status_code == 200
    ov = res_ov.json()
    assert ov["status"] == "OPERATIONAL"
    assert "patients" in ov
    assert "camera_hardware" in ov


def test_full_patient_therapy_lifecycle(client):
    """Test full cycle: Patient Registration -> Motion Assessment -> Therapy Session -> Progress -> CSV."""
    # 1. Register Patient
    p_data = {
        "full_name": "Tran Thi Integration",
        "primary_complaint": "Right chronic supraspinatus strain",
        "age": 38,
        "gender": "Female",
        "current_pain_score": 7.0,
        "functional_limitations": "Restricted abduction past 90 deg",
        "red_flags": {"fever": False}
    }
    res_p = client.post("/api/v1/workstation/patients", json=p_data)
    assert res_p.status_code == 200
    pat = res_p.json()
    pid = pat["id"]

    # 2. Run Motion Assessment in DEMO mode for offline test environment
    m_data = {
        "patient_id": pid,
        "joint_tested": "SHOULDER_ABDUCTION",
        "side": "RIGHT",
        "mode": "DEMO"
    }
    res_m = client.post("/api/v1/workstation/motion/assess", json=m_data)
    assert res_m.status_code == 200
    motion = res_m.json()
    mid = motion["id"]
    assert motion["measured_rom_deg"] > 0
    assert motion["uncertainty_u95_deg"] > 0

    # 3. Record Therapy Session
    s_data = {
        "pre_pain_score": 7.0,
        "post_pain_score": 3.0,
        "pre_symptoms_notes": "Sharp ache at 80 deg abduction",
        "post_symptoms_notes": "Pain-free reach to 110 deg",
        "motion_assessment_ids": [mid],
        "applied_modalities": [
            {"name": "Trigger point release", "category": "MYOFASCIAL_RELEASE", "duration_minutes": 20},
            {"name": "Passive mobilization", "category": "MANUAL_THERAPY", "duration_minutes": 10}
        ],
        "dds_device_records": {
            "device_used": True,
            "recorded_frequency_hz": 60.0,
            "recorded_intensity_ma": 14.0,
            "patient_sensation": "Comfortable rhythmic contraction"
        }
    }
    res_s = client.post(f"/api/v1/workstation/patients/{pid}/sessions", json=s_data)
    assert res_s.status_code == 200
    session = res_s.json()
    sid = session["id"]
    assert session["session_number"] >= 1
    assert "soap" in session
    assert "Subjective" in session["soap"]["subjective"] or len(session["soap"]["subjective"]) > 10

    # Verify patient current pain score was updated
    res_pat_check = client.get(f"/api/v1/workstation/patients/{pid}")
    assert res_pat_check.status_code == 200
    assert res_pat_check.json()["current_pain_score"] == 3.0

    # 4. Progress Summary
    res_prog = client.get(f"/api/v1/workstation/patients/{pid}/progress")
    assert res_prog.status_code == 200
    prog = res_prog.json()
    assert prog["total_pain_reduction"] == 4.0
    assert len(prog["pain_timeline"]) >= 1

    # 5. CSV Export
    res_csv = client.get(f"/api/v1/workstation/patients/{pid}/export/csv")
    assert res_csv.status_code == 200
    assert "MSK THERAPY WORKSTATION" in res_csv.text
    assert "Tran Thi Integration" in res_csv.text
    assert "SESSION TIMELINE" in res_csv.text


def test_motion_hardware_probe(client):
    """Verify camera probe endpoint returns structured fail-closed payload."""
    res = client.get("/api/v1/workstation/motion/probe")
    assert res.status_code == 200
    probe = res.json()
    assert "available" in probe
    assert "backend" in probe
    assert "status" in probe
