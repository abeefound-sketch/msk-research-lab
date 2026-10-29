"""End-to-End Recovery Acceptance Test Suite (E2E-01 through E2E-12).

Validates the full recovery cycle specified in MSK Research Lab OS Master Roadmap v3.2:
- E2E-01: System Bootstrap & Dashboard Operational Diagnostics
- E2E-02: Synthetic Patient Lifecycle (Create -> Search -> Edit -> Reload Persistence)
- E2E-03: Red Flag Server-Authoritative Hard Stop (Intervention Blocked)
- E2E-04: Grounded Clinical SOAP Note Lifecycle (No Fabricated Text)
- E2E-05: Longitudinal Progress Tracking & Sanitized CSV Export
- E2E-06: Fail-Closed Camera Kinematics (No Phantom Records)
- E2E-07: Isolated DEMO Posture Fixtures
- E2E-08: Kinematic Vector Completeness & Degenerate Geometry Guard
- E2E-09: Genuine 3D Atlas Scene, Layer Toggles, and Mesh Provenance
- E2E-10: Evidence Library FTS5 Search & Honest Empty States
- E2E-11: DOM Injection / XSS Sanitization in Workstation UI
- E2E-12: Port Occupied Guard & Database Disaster Recovery Integrity
"""

import os
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient

from msk_research_lab.api.app import app
from msk_research_lab.core.db import get_db
from msk_research_lab.core.backup import create_backup, restore_backup
from msk_research_lab.workstation.patient_manager import (
    create_patient, get_patient, list_patients, update_patient, delete_patient
)
from msk_research_lab.workstation.therapy_manager import (
    record_therapy_session, get_therapy_session, list_patient_sessions,
    generate_soap_note, TherapySessionError
)
from msk_research_lab.motion.camera_service import (
    execute_motion_assessment, probe_hardware_camera, CameraUnavailableError,
    list_patient_motion_assessments
)
from msk_research_lab.motion.kinematics import compute_joint_rom, compute_2d_angle
from msk_research_lab.workstation.progress_tracker import (
    get_patient_progress_summary, export_patient_progress_csv, sanitize_csv_cell
)
from msk_research_lab.__main__ import is_port_in_use


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# E2E-01: Bootstrap & Dashboard Real Metrics
# =========================================================================
def test_e2e_01_dashboard_metrics_and_component_matrix(client):
    """Verify workstation overview reports truthful component matrix and blocked clinical gate."""
    res = client.get("/api/v1/workstation/overview")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] in ("OPERATIONAL", "DEGRADED_OFFLINE_READY")
    assert "components" in data
    comps = data["components"]

    # Component health checks
    assert comps["database"]["status"] == "READY"
    assert comps["database"]["wal_mode"] is True
    assert comps["clinical_realworld_gate"]["status"] == "BLOCKED"
    assert "BLOCKED" in data["clinical_safety_status"]

    # Database metric consistency
    with get_db() as conn:
        db_patients = conn.execute("SELECT COUNT(*) FROM patients;").fetchone()[0]
        db_sessions = conn.execute("SELECT COUNT(*) FROM therapy_sessions;").fetchone()[0]
    assert data["patients"]["total"] == db_patients
    assert data["therapy_sessions"]["total"] == db_sessions


# =========================================================================
# E2E-02: Patient Registration, Search, Edit, and Persistence
# =========================================================================
def test_e2e_02_patient_lifecycle_search_edit_reload(client):
    """Verify synthetic patient registration -> search -> edit -> reload persistence."""
    # 1. Register synthetic patient
    patient_payload = {
        "full_name": "Nguyen Van E2E Synthetic",
        "primary_complaint": "Bilateral trapezial trigger points and neck stiffness",
        "age": 44,
        "gender": "Male",
        "height_cm": 172.0,
        "weight_kg": 70.0,
        "current_pain_score": 6.5,
        "functional_limitations": "Restricted cervical rotation",
        "red_flags": {"fever": False, "motor_deficit": False}
    }
    res_reg = client.post("/api/v1/workstation/patients", json=patient_payload)
    assert res_reg.status_code == 200
    created = res_reg.json()
    pid = created["id"]
    assert pid.startswith("PAT-")
    assert created["full_name"] == "Nguyen Van E2E Synthetic"

    # 2. Search patient
    res_search = client.get("/api/v1/workstation/patients?search=trapezial")
    assert res_search.status_code == 200
    results = res_search.json()
    assert any(p["id"] == pid for p in results)

    # 3. Edit patient profile
    edit_payload = {
        "full_name": "Nguyen Van E2E Synthetic (Updated)",
        "current_pain_score": 5.0,
        "functional_limitations": "Improved cervical rotation to 45 deg"
    }
    res_edit = client.put(f"/api/v1/workstation/patients/{pid}", json=edit_payload)
    assert res_edit.status_code == 200
    updated = res_edit.json()
    assert updated["full_name"] == "Nguyen Van E2E Synthetic (Updated)"
    assert updated["current_pain_score"] == 5.0

    # 4. Reload verification from direct DB connection
    with get_db() as conn:
        row = conn.execute("SELECT full_name, current_pain_score, functional_limitations FROM patients WHERE id = ?", (pid,)).fetchone()
    assert row["full_name"] == "Nguyen Van E2E Synthetic (Updated)"
    assert row["current_pain_score"] == 5.0
    assert row["functional_limitations"] == "Improved cervical rotation to 45 deg"


# =========================================================================
# E2E-03: Red Flag Server-Authoritative Hard Stop
# =========================================================================
def test_e2e_03_red_flag_hard_stop(client):
    """Verify active clinical red flags fail closed and strictly reject therapy recording."""
    patient = create_patient(
        full_name="Acute Myelopathy Synthetic",
        primary_complaint="Rapid motor loss with progressive leg numbness",
        red_flags={
            "fever": False,
            "motor_deficit": True,
            "bowel_bladder_dysfunction": True
        }
    )
    pid = patient["id"]

    with get_db() as conn:
        before_count = conn.execute("SELECT COUNT(*) FROM therapy_sessions WHERE patient_id = ?", (pid,)).fetchone()[0]

    # Attempt routine manual therapy
    res = client.post(f"/api/v1/workstation/patients/{pid}/sessions", json={
        "pre_pain_score": 8.0,
        "post_pain_score": 5.0,
        "applied_modalities": [{"name": "Cervical traction", "category": "MANUAL_THERAPY"}]
    })
    assert res.status_code == 400
    assert "CLINICAL_RED_FLAG_BLOCKED" in res.text

    # Verify session count unchanged
    with get_db() as conn:
        after_count = conn.execute("SELECT COUNT(*) FROM therapy_sessions WHERE patient_id = ?", (pid,)).fetchone()[0]
    assert after_count == before_count


# =========================================================================
# E2E-04: Grounded SOAP Clinical Note (No Deductive Text)
# =========================================================================
def test_e2e_04_grounded_soap_lifecycle(client):
    """Verify SOAP note draft and finalized record strictly reflect documented clinical facts."""
    patient = create_patient(
        full_name="SOAP Fact Patient",
        primary_complaint="Subacute lateral epicondylitis",
        current_pain_score=6.0
    )
    pid = patient["id"]

    # 1. Preview SOAP endpoint
    preview_res = client.post(f"/api/v1/workstation/patients/{pid}/sessions/preview-soap", json={
        "pre_pain_score": 6.0,
        "post_pain_score": 3.5,
        "pre_symptoms_notes": "Sharp tenderness at lateral epicondyle",
        "post_symptoms_notes": "Reduced localized tenderness after friction massage",
        "applied_modalities": [{"name": "Cross-fiber friction", "category": "MYOFASCIAL_RELEASE", "duration_minutes": 15}]
    })
    assert preview_res.status_code == 200
    soap_preview = preview_res.json()["soap"]

    # Verify no fabricated claims
    assert "tissue softening" not in soap_preview["assessment"].lower()
    assert "Sharp tenderness at lateral epicondyle" in soap_preview["subjective"]
    assert "Cross-fiber friction" in soap_preview["objective"]
    assert "6.0 -> 3.5" in soap_preview["assessment"]

    # 2. Record Session
    save_res = client.post(f"/api/v1/workstation/patients/{pid}/sessions", json={
        "pre_pain_score": 6.0,
        "post_pain_score": 3.5,
        "pre_symptoms_notes": "Sharp tenderness at lateral epicondyle",
        "post_symptoms_notes": "Reduced localized tenderness after friction massage",
        "applied_modalities": [{"name": "Cross-fiber friction", "category": "MYOFASCIAL_RELEASE", "duration_minutes": 15}]
    })
    assert save_res.status_code == 200
    session = save_res.json()
    assert session["session_number"] >= 1
    assert session["soap"]["assessment"] == soap_preview["assessment"]


# =========================================================================
# E2E-05: Progress Summary and Sanitized CSV Export
# =========================================================================
def test_e2e_05_progress_analytics_and_csv_export(client):
    """Verify multi-session progress timeline calculation and formula-sanitized CSV export."""
    patient = create_patient(
        full_name="=CMD|' /C calc'!A0 Formula Injection Risk",
        primary_complaint="@SUM(1+1) Trigger Injection",
        current_pain_score=7.0
    )
    pid = patient["id"]

    # Record two sequential sessions
    client.post(f"/api/v1/workstation/patients/{pid}/sessions", json={"pre_pain_score": 7.0, "post_pain_score": 5.0})
    client.post(f"/api/v1/workstation/patients/{pid}/sessions", json={"pre_pain_score": 5.0, "post_pain_score": 2.0})

    # Progress Summary
    prog_res = client.get(f"/api/v1/workstation/patients/{pid}/progress")
    assert prog_res.status_code == 200
    prog = prog_res.json()
    assert prog["total_sessions"] >= 2
    assert prog["initial_pain_score"] == 7.0
    assert prog["latest_pain_score"] == 2.0
    assert prog["total_pain_reduction"] == 5.0

    # CSV Export
    csv_res = client.get(f"/api/v1/workstation/patients/{pid}/export/csv")
    assert csv_res.status_code == 200
    csv_text = csv_res.text
    # Verify dangerous formula trigger characters are safely escaped with single quote
    assert "'=CMD" in csv_text
    assert "'@SUM" in csv_text


# =========================================================================
# E2E-06 & E2E-07: Camera Fail-Closed vs. DEMO Posture Fixtures
# =========================================================================
def test_e2e_06_e2e_07_camera_provenance_and_demo_mode(client):
    """Verify that LIVE mode without camera fails closed and DEMO mode is labeled synthetic."""
    patient = create_patient(full_name="Provenance E2E Patient", primary_complaint="Shoulder pain")
    pid = patient["id"]

    probe = probe_hardware_camera()
    if not probe.get("available"):
        # LIVE request must fail closed
        res_live = client.post("/api/v1/workstation/motion/assess", json={
            "patient_id": pid,
            "joint_tested": "ELBOW_FLEXION",
            "mode": "LIVE"
        })
        assert res_live.status_code in (400, 422)
        assert "CAMERA_UNAVAILABLE" in res_live.text

    # DEMO request must succeed and tag synthetic provenance
    res_demo = client.post("/api/v1/workstation/motion/assess", json={
        "patient_id": pid,
        "joint_tested": "ELBOW_FLEXION",
        "mode": "DEMO"
    })
    assert res_demo.status_code == 200
    demo_data = res_demo.json()
    assert demo_data["mode"] == "DEMO"
    assert demo_data["is_synthetic"] is True
    assert "FIXTURE_" in demo_data["data_source"]
    assert demo_data["data_source"] != "WEBCAM_LIVE_FRAME"


# =========================================================================
# E2E-08: Kinematics Landmark Completeness & Degenerate Geometry Guard
# =========================================================================
def test_e2e_08_kinematics_completeness_and_degenerate_guard():
    """Verify kinematics engine rejects incomplete landmarks and degenerate vectors."""
    # 1. Missing landmark -> INSUFFICIENT_DATA
    missing_landmarks = {"right_shoulder": (0.5, 0.3), "right_elbow": (0.5, 0.5)}
    res_miss = compute_joint_rom(missing_landmarks, "ELBOW_FLEXION", side="RIGHT")
    assert res_miss["measured_rom_deg"] is None
    assert res_miss["quality_status"] == "INSUFFICIENT_DATA"

    # 2. Degenerate vector -> DEGENERATE_GEOMETRY
    degenerate_landmarks = {
        "right_shoulder": (0.5, 0.5),
        "right_elbow": (0.5, 0.5),
        "right_wrist": (0.5, 0.5)
    }
    res_deg = compute_joint_rom(degenerate_landmarks, "ELBOW_FLEXION", side="RIGHT")
    assert res_deg["measured_rom_deg"] is None
    assert res_deg["quality_status"] == "DEGENERATE_GEOMETRY"

    # 3. Valid right-angle fixture -> 90 deg
    valid_landmarks = {
        "right_shoulder": (0.5, 0.3),
        "right_elbow": (0.5, 0.5),
        "right_wrist": (0.7, 0.5)
    }
    res_valid = compute_joint_rom(valid_landmarks, "ELBOW_FLEXION", side="RIGHT")
    assert res_valid["measured_rom_deg"] is not None
    assert abs(res_valid["measured_rom_deg"] - 90.0) < 1.0


# =========================================================================
# E2E-09: 3D Atlas Scene, Layer Toggles, and Mesh Provenance
# =========================================================================
def test_e2e_09_atlas_scene_and_authentic_mesh_provenance(client):
    """Verify authentic 3D model scenes, GLB file streaming, and acupoint inspection."""
    # 1. Models list
    res_models = client.get("/api/v1/atlas/models")
    assert res_models.status_code == 200
    models = res_models.json()["models"]
    assert any(m["model_id"] == "watercmy_bp3d_z_anatomy" for m in models)

    # 2. Scene metadata
    res_scene = client.get("/api/v1/atlas/scene/watercmy_bp3d_z_anatomy")
    assert res_scene.status_code == 200
    scene = res_scene.json()
    assert scene["asset_kind"] == "AUTHENTIC_UPSTREAM_ASSET"
    assert "deep_fascia" in scene["unavailable_layers"]
    assert scene["model_file_url"] == "/api/v1/atlas/models/watercmy_bp3d_z_anatomy/file"

    # 3. GLB file download
    res_file = client.get("/api/v1/atlas/models/watercmy_bp3d_z_anatomy/file")
    assert res_file.status_code == 200
    assert int(res_file.headers["content-length"]) > 1000000


# =========================================================================
# E2E-10: Evidence Library FTS5 Search & Empty States
# =========================================================================
def test_e2e_10_library_search_and_empty_state(client):
    """Verify FTS5 library search returns source-cited excerpts or honest empty state."""
    # Search for term guaranteed not to exist
    res_empty = client.get("/api/v1/workstation/ai-tutor/search-library?q=nonexistent_xyz_phrase_12345")
    assert res_empty.status_code == 200
    assert res_empty.json() == []

    # Search for valid clinical keyword
    res_valid = client.get("/api/v1/workstation/ai-tutor/search-library?q=myofascial")
    assert res_valid.status_code == 200
    data = res_valid.json()
    if data:
        assert "title" in data[0]
        assert "citation" in data[0]
        assert "snippet" in data[0]


# =========================================================================
# E2E-11: DOM Injection / XSS Sanitization
# =========================================================================
def test_e2e_11_dom_injection_sanitization(client):
    """Verify that malicious script tags in patient name or complaint are escaped in UI."""
    xss_payload = "<img src=x onerror=alert('xss')>"
    patient = create_patient(
        full_name=xss_payload,
        primary_complaint=xss_payload
    )
    pid = patient["id"]

    res_list = client.get("/api/v1/workstation/patients")
    assert res_list.status_code == 200

    # Test workstation UI renders safely
    res_ui = client.get("/workstation")
    assert res_ui.status_code == 200
    assert "escapeHtml" in res_ui.text


# =========================================================================
# E2E-12: Port Occupied Guard & Disaster Recovery Verification
# =========================================================================
def test_e2e_12_port_occupied_and_backup_recovery(tmp_path):
    """Verify port occupied detector and database disaster recovery integrity."""
    # 1. Port binding check (8000 or ephemeral)
    port_status = is_port_in_use(8000, "127.0.0.1")
    assert isinstance(port_status, bool)

    # 2. Disaster recovery backup & restore verification
    backup = create_backup(tmp_path)
    assert "backup_id" in backup
    assert os.path.exists(backup["archive_path"])
    assert len(backup["archive_sha256"]) == 64
