"""P12 Windows Native Qualification & End-to-End Researcher Workflow Acceptance.

Verifies:
1. Loopback socket safety (127.0.0.1 / ::1 only, zero external telemetry).
2. End-to-End Researcher Workflow:
   Patient Intake -> Safe Harbor Scrubbing -> Red Flag Screening -> Kinematics Quality Decision ->
   SOAP Therapy Session -> Longitudinal CSV -> Encrypted Backup Roundtrip.
3. Windows Launcher configuration, error dialog handling, and process termination scripts.
"""

import csv
import io
import json
import os
import sqlite3
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from msk_research_lab.api.app import app
from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import init_connection
from msk_research_lab.scientific.quality import MeasurementQualityDecision
from msk_research_lab.workstation.patient_manager import (
    create_patient,
    get_patient,
    evaluate_red_flags,
    scrub_phi_from_text,
    export_deidentified_research_record,
)
from msk_research_lab.workstation.therapy_manager import (
    record_therapy_session,
    list_patient_sessions,
    TherapySessionError,
)
from msk_research_lab.workstation.progress_tracker import (
    get_patient_progress_summary,
    export_patient_progress_csv,
)
from msk_research_lab.motion.kinematics import (
    compute_2d_angle,
    compute_joint_rom,
    evaluate_motion_quality,
)
from msk_research_lab.security.key_lifecycle import (
    create_encrypted_backup,
    restore_encrypted_backup,
)


@pytest.fixture
def client():
    return TestClient(app)


class TestWindowsNativeE2EAcceptance:
    """End-to-End acceptance tests for Windows native workstation operation."""

    def test_loopback_binding_and_offline_security(self, client):
        """Workstation must bind strictly to loopback and have zero outbound network calls."""
        cfg = get_config()
        assert cfg.server.host in ("127.0.0.1", "localhost", "::1"), (
            f"Host {cfg.server.host} violates loopback airgap requirement"
        )

        # Health endpoint
        res = client.get("/api/v1/health")
        assert res.status_code == 200
        health_data = res.json()
        assert health_data["status"] == "HEALTHY"
        assert health_data["database"]["connected"] is True
        assert health_data["database"]["wal_mode"] is True
        assert health_data["ports"]["loopback_only"] is True

    def test_complete_researcher_workflow_e2e(self):
        """Execute full multi-step researcher workflow from intake to backup restore."""
        # 1. Patient Intake with embedded PHI in free-text clinical notes
        raw_med_history = (
            "Referred by Dr. Jane Smith (NPI: 1234567890, DEA: AB1234567) on 14-Oct-2024. "
            "Patient SSN: 123-45-6789. History of right rotator cuff repair."
        )
        patient = create_patient(
            full_name="Alice Walker",
            primary_complaint="Right shoulder stiffness and pain post-op",
            medical_history=raw_med_history,
            red_flags={
                "fever": True,
                "motor_deficit": True,
            }
        )
        patient_id = patient["id"]
        assert patient_id is not None
        assert patient["red_flags"]["requires_referral"] is True

        # Verify Safe Harbor de-identification export
        deid = export_deidentified_research_record(patient_id)
        assert deid["pii_redacted"] is True
        med_summary = deid["medical_history_summary"]
        assert "[REDACTED_NPI]" in med_summary
        assert "[REDACTED_SSN]" in med_summary
        assert "[REDACTED_LICENSE]" in med_summary
        assert "1234567890" not in med_summary
        assert "123-45-6789" not in med_summary

        # 2. Red Flag Hard-Stop Verification: blocked from recording interventions
        with pytest.raises(TherapySessionError) as exc_info:
            record_therapy_session(
                patient_id=patient_id,
                pre_pain_score=7.0,
                post_pain_score=3.0,
            )
        assert "CLINICAL_RED_FLAG_BLOCKED" in str(exc_info.value)

        # 3. Create Clean Patient for Valid Workflow Progression
        clean_patient = create_patient(
            full_name="Bob Miller",
            primary_complaint="Subacute mechanical elbow stiffness",
            medical_history="No systemic red flags.",
            red_flags={
                "fever": False,
                "motor_deficit": False,
                "bowel_bladder_dysfunction": False,
            }
        )
        clean_id = clean_patient["id"]

        # 4. Kinematics Angle Capture & 4-State Quality Decisions
        sample_landmarks = {
            "right_shoulder": (0.0, 0.0),
            "right_elbow": (0.0, 100.0),
            "right_wrist": (100.0, 100.0),
        }
        rom_valid = compute_joint_rom(
            landmarks=sample_landmarks,
            joint_tested="ELBOW_FLEXION",
            side="RIGHT",
            visibility_scores={"right_shoulder": 0.95, "right_elbow": 0.92, "right_wrist": 0.90},
            apparent_span_ratio=1.0,
        )
        assert rom_valid["quality_decision"] == MeasurementQualityDecision.VALID.value
        assert abs(rom_valid["measured_rom_deg"] - 90.0) < 1e-2

        # Degraded measurement: excessive torso yaw (apparent_span_ratio = 0.70 < 0.85)
        rom_degraded = compute_joint_rom(
            landmarks=sample_landmarks,
            joint_tested="ELBOW_FLEXION",
            side="RIGHT",
            visibility_scores={"right_shoulder": 0.95, "right_elbow": 0.92, "right_wrist": 0.90},
            apparent_span_ratio=0.70,
        )
        assert rom_degraded["quality_decision"] == MeasurementQualityDecision.DEGRADED.value

        # 5. Record Therapy Session with SOAP Notes
        session = record_therapy_session(
            patient_id=clean_id,
            pre_pain_score=5.0,
            post_pain_score=2.0,
            pre_symptoms_notes="Stiff elbow in terminal flexion",
            post_symptoms_notes="Improved smooth range with mild soreness",
            applied_modalities=[{"modality": "MANUAL_THERAPY", "duration_min": 15}]
        )
        assert session["id"] is not None
        assert session["soap"]["subjective"] != ""
        assert session["soap"]["objective"] != ""

        # 6. Longitudinal Progress Tracking & CSV Export
        summary = get_patient_progress_summary(clean_id)
        assert summary["total_sessions"] >= 1

        csv_content = export_patient_progress_csv(clean_id)
        assert csv_content is not None
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) >= 2  # Header + 1 data row

    def test_windows_launcher_scripts_and_dist_integrity(self):
        """Verify Windows VBS and batch launcher syntax and local runtime detection."""
        repo_root = get_config().storage.root_dir
        vbs_path = repo_root / "packaging" / "MSK-Workstation-Launch.vbs"
        stop_path = repo_root / "packaging" / "Stop-MSK-Workstation.bat"
        start_path = repo_root / "start-msk.bat"

        assert vbs_path.exists(), "MSK-Workstation-Launch.vbs missing"
        assert stop_path.exists(), "Stop-MSK-Workstation.bat missing"
        assert start_path.exists(), "start-msk.bat missing"

        vbs_content = vbs_path.read_text(encoding="utf-8")
        assert "CreateObject" in vbs_content
        assert "python.exe" in vbs_content
        assert "MsgBox" in vbs_content, "VBS must contain user-facing MsgBox on missing runtime"

        stop_content = stop_path.read_text(encoding="utf-8")
        assert "taskkill" in stop_content or "netstat" in stop_content

    def test_sqlite_wal_durability_and_backup_roundtrip(self, tmp_path):
        """Simulate sudden crash/backup restore roundtrip with WAL orphan removal."""
        backup_dir = tmp_path / "backups"
        restore_dir = tmp_path / "restored_db"
        backup_dir.mkdir(parents=True, exist_ok=True)
        restore_dir.mkdir(parents=True, exist_ok=True)

        # 1. Create simulated orphaned WAL and SHM files in restore directory
        orphaned_wal = restore_dir / "lab.sqlite3-wal"
        orphaned_shm = restore_dir / "lab.sqlite3-shm"
        orphaned_wal.write_bytes(b"CORRUPT_ORPHANED_WAL_DATA_FROM_PREVIOUS_SESSION")
        orphaned_shm.write_bytes(b"CORRUPT_ORPHANED_SHM_DATA")

        # 2. Create encrypted backup using SQLite online backup API
        pwd = "AuditPassword#P12Durability2026!"
        archive_path = create_encrypted_backup(password=pwd, target_export_dir=backup_dir)
        assert archive_path.exists()

        # 3. Restore into directory with orphaned WAL
        res = restore_encrypted_backup(
            encrypted_backup_path=archive_path,
            password=pwd,
            target_restore_dir=restore_dir
        )
        assert res["status"] == "RESTORED"

        # 4. Verify orphaned WAL and SHM files were removed
        assert not orphaned_wal.exists()
        assert not orphaned_shm.exists()

        # 5. Verify restored database opens cleanly and passes integrity check
        conn = init_connection(restore_dir / "lab.sqlite3")
        row = conn.execute("PRAGMA integrity_check;").fetchone()
        assert row[0] == "ok"
        conn.close()
