"""REST API Routes for MSK Therapy Personal Workstation."""

import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse

from msk_research_lab.core.db import get_db
from msk_research_lab.workstation.patient_manager import (
    create_patient, get_patient, list_patients, update_patient, delete_patient,
    export_deidentified_research_record, PatientManagerError
)
from msk_research_lab.workstation.therapy_manager import (
    record_therapy_session, get_therapy_session, list_patient_sessions, generate_soap_note,
    TherapySessionError
)
from msk_research_lab.workstation.progress_tracker import (
    get_patient_progress_summary, export_patient_progress_csv
)
from msk_research_lab.motion.camera_service import (
    probe_hardware_camera, execute_motion_assessment, list_patient_motion_assessments,
    MotionAssessmentError
)
from msk_research_lab.ai_tutor.tutor import (
    explain_anatomical_structure, link_movement_to_muscles, explain_measurement_uncertainty,
    audit_session_completeness, search_evidence_library
)
from msk_research_lab.api.workstation_ui import render_workstation_ui

workstation_router = APIRouter(tags=["MSK Therapy Personal Workstation"])


@workstation_router.get("/workstation", response_class=HTMLResponse)
def get_workstation_page():
    """Render unified MSK Therapy Personal Workstation single-page application."""
    return HTMLResponse(content=render_workstation_ui())


@workstation_router.get("/api/v1/workstation/overview")
def get_workstation_overview():
    """Retrieve operational metrics for the workstation home dashboard."""
    with get_db() as conn:
        total_patients = conn.execute("SELECT COUNT(*) FROM patients;").fetchone()[0]
        active_patients = conn.execute("SELECT COUNT(*) FROM patients WHERE status = 'ACTIVE';").fetchone()[0]
        total_sessions = conn.execute("SELECT COUNT(*) FROM therapy_sessions;").fetchone()[0]
        total_motion_tests = conn.execute("SELECT COUNT(*) FROM motion_assessments;").fetchone()[0]
        total_documents = conn.execute("SELECT COUNT(*) FROM documents;").fetchone()[0]
        total_concepts = conn.execute("SELECT COUNT(*) FROM ontology_concepts;").fetchone()[0]
        total_models = conn.execute("SELECT COUNT(*) FROM models_3d;").fetchone()[0]

    camera_probe = probe_hardware_camera()

    tracker_available = False
    try:
        import mediapipe  # noqa
        tracker_available = True
    except ImportError:
        tracker_available = False

    components = {
        "database": {"status": "READY", "schema_version": 9, "wal_mode": True},
        "camera": {
            "status": "READY" if camera_probe.get("available") else "UNAVAILABLE",
            "details": camera_probe.get("status", "CAMERA_OFFLINE")
        },
        "pose_tracker": {
            "status": "READY" if tracker_available else "UNAVAILABLE",
            "backend": "mediapipe" if tracker_available else "DEMO_FIXTURES_ONLY"
        },
        "atlas_assets": {
            "status": "READY" if total_models > 0 else "UNAVAILABLE",
            "models_registered": total_models
        },
        "library_index": {
            "status": "READY" if total_documents > 0 else "DEGRADED",
            "documents_count": total_documents
        },
        "clinical_realworld_gate": {
            "status": "BLOCKED",
            "reason": "Educational and synthetic workstation only. No automated diagnosis or clinical deployment."
        }
    }

    overall_status = "OPERATIONAL" if (camera_probe.get("available") and tracker_available) else "DEGRADED_OFFLINE_READY"

    return {
        "status": overall_status,
        "system_version": "MSK Therapy Workstation 1.0 (Personal Offline)",
        "patients": {
            "total": total_patients,
            "active": active_patients
        },
        "therapy_sessions": {
            "total": total_sessions
        },
        "motion_assessments": {
            "total": total_motion_tests
        },
        "knowledge_library": {
            "documents": total_documents,
            "ontology_concepts": total_concepts,
            "3d_models": total_models
        },
        "camera_hardware": camera_probe,
        "components": components,
        "clinical_safety_status": "ENFORCED (No automated diagnosis; Clinical Real-World Gate = BLOCKED)"
    }


# ==========================================
# PATIENTS API
# ==========================================

@workstation_router.get("/api/v1/workstation/patients")
def api_list_patients(search: Optional[str] = None, status: Optional[str] = None):
    return list_patients(search=search, status=status)


@workstation_router.post("/api/v1/workstation/patients")
async def api_create_patient(request: Request):
    payload = await request.json()
    try:
        patient = create_patient(
            full_name=payload.get("full_name", ""),
            primary_complaint=payload.get("primary_complaint", ""),
            age=payload.get("age"),
            gender=payload.get("gender"),
            height_cm=payload.get("height_cm"),
            weight_kg=payload.get("weight_kg"),
            occupation=payload.get("occupation"),
            activity_level=payload.get("activity_level", "MODERATE"),
            medical_history=payload.get("medical_history", ""),
            pain_locations=payload.get("pain_locations", []),
            current_pain_score=float(payload.get("current_pain_score", 0.0)),
            radiating_symptoms=payload.get("radiating_symptoms", {}),
            functional_limitations=payload.get("functional_limitations", ""),
            red_flags=payload.get("red_flags", {})
        )
        return patient
    except PatientManagerError as e:
        raise HTTPException(status_code=400, detail=str(e))


@workstation_router.get("/api/v1/workstation/patients/{patient_id}")
def api_get_patient(patient_id: str):
    try:
        return get_patient(patient_id)
    except PatientManagerError as e:
        raise HTTPException(status_code=404, detail=str(e))


@workstation_router.put("/api/v1/workstation/patients/{patient_id}")
async def api_update_patient(patient_id: str, request: Request):
    payload = await request.json()
    try:
        return update_patient(patient_id, payload)
    except PatientManagerError as e:
        raise HTTPException(status_code=404, detail=str(e))


@workstation_router.delete("/api/v1/workstation/patients/{patient_id}")
def api_delete_patient(patient_id: str):
    try:
        delete_patient(patient_id)
        return {"status": "SUCCESS", "message": f"Patient '{patient_id}' status set to DISCHARGED."}
    except PatientManagerError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==========================================
# THERAPY SESSIONS API
# ==========================================

@workstation_router.get("/api/v1/workstation/patients/{patient_id}/sessions")
def api_list_patient_sessions(patient_id: str):
    return list_patient_sessions(patient_id)


@workstation_router.post("/api/v1/workstation/patients/{patient_id}/sessions")
async def api_record_therapy_session(patient_id: str, request: Request):
    payload = await request.json()
    try:
        session = record_therapy_session(
            patient_id=patient_id,
            pre_pain_score=float(payload.get("pre_pain_score", 0.0)),
            post_pain_score=float(payload.get("post_pain_score", 0.0)),
            pre_symptoms_notes=payload.get("pre_symptoms_notes", ""),
            post_symptoms_notes=payload.get("post_symptoms_notes", ""),
            motion_assessment_ids=payload.get("motion_assessment_ids", []),
            related_anatomy=payload.get("related_anatomy", []),
            applied_modalities=payload.get("applied_modalities", []),
            dds_device_records=payload.get("dds_device_records"),
            soap_notes=payload.get("soap_notes"),
            operator_id=payload.get("operator_id", "OPERATOR")
        )
        return session
    except (PatientManagerError, TherapySessionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@workstation_router.post("/api/v1/workstation/patients/{patient_id}/sessions/preview-soap")
async def api_preview_soap(patient_id: str, request: Request):
    payload = await request.json()
    try:
        patient = get_patient(patient_id)
        motion_ids = payload.get("motion_assessment_ids", [])
        motion_details = []
        if motion_ids:
            with get_db() as conn:
                placeholders = ",".join(["?"] * len(motion_ids))
                m_rows = conn.execute(
                    f"SELECT * FROM motion_assessments WHERE id IN ({placeholders});", tuple(motion_ids)
                ).fetchall()
                for r in m_rows:
                    motion_details.append(dict(r))

        soap = generate_soap_note(
            patient=patient,
            pre_pain=float(payload.get("pre_pain_score", 0.0)),
            post_pain=float(payload.get("post_pain_score", 0.0)),
            pre_symptoms=payload.get("pre_symptoms_notes", ""),
            post_symptoms=payload.get("post_symptoms_notes", ""),
            modalities=payload.get("applied_modalities", []),
            motion_assessments=motion_details,
            dds_record=payload.get("dds_device_records"),
            tolerance_notes=payload.get("tolerance_notes")
        )
        return {"status": "SUCCESS", "soap": soap}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@workstation_router.get("/api/v1/workstation/sessions/{session_id}")
def api_get_therapy_session(session_id: str):
    try:
        return get_therapy_session(session_id)
    except TherapySessionError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==========================================
# MOTION ASSESSMENT API
# ==========================================

@workstation_router.get("/api/v1/workstation/motion/probe")
def api_probe_camera():
    return probe_hardware_camera()


@workstation_router.post("/api/v1/workstation/motion/assess")
async def api_assess_motion(request: Request):
    payload = await request.json()
    patient_id = payload.get("patient_id")
    if not patient_id:
        raise HTTPException(
            status_code=400,
            detail={"message": "patient_id is required.", "error_code": "INVALID_INPUT", "provenance_category": "INVALID_INPUT"}
        )
    
    joint = payload.get("joint_tested", "ELBOW_FLEXION")
    side = payload.get("side", "RIGHT")
    session_id = payload.get("session_id")
    custom_landmarks = payload.get("custom_landmarks")
    fixture_name = payload.get("fixture_name")
    mode = payload.get("mode", "LIVE")

    try:
        return execute_motion_assessment(
            patient_id=patient_id,
            joint_tested=joint,
            side=side,
            session_id=session_id,
            custom_landmarks=custom_landmarks,
            fixture_name=fixture_name,
            mode=mode
        )
    except MotionAssessmentError as e:
        status = 422 if e.error_code in ("NO_POSE", "INSUFFICIENT_LANDMARKS", "DEGENERATE_GEOMETRY") else 400
        prov_cat = "NOT_MEASURABLE" if e.error_code in ("NO_POSE", "INSUFFICIENT_LANDMARKS", "DEGENERATE_GEOMETRY", "CAMERA_UNAVAILABLE") else "INVALID_INPUT"
        raise HTTPException(status_code=status, detail={"message": str(e), "error_code": e.error_code, "provenance_category": prov_cat})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": f"Motion assessment failed: {str(e)}", "error_code": "INTERNAL_ERROR", "provenance_category": "NOT_MEASURABLE"})


@workstation_router.get("/api/v1/workstation/patients/{patient_id}/motion")
def api_list_patient_motion(patient_id: str):
    return list_patient_motion_assessments(patient_id)


# ==========================================
# PROGRESS & ANALYTICS API
# ==========================================

@workstation_router.get("/api/v1/workstation/patients/{patient_id}/progress")
def api_get_patient_progress(patient_id: str):
    try:
        return get_patient_progress_summary(patient_id)
    except PatientManagerError as e:
        raise HTTPException(status_code=404, detail=str(e))


@workstation_router.get("/api/v1/workstation/patients/{patient_id}/export/csv")
def api_export_patient_csv(patient_id: str):
    try:
        csv_data = export_patient_progress_csv(patient_id)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=progress_{patient_id}.csv"}
        )
    except PatientManagerError as e:
        raise HTTPException(status_code=404, detail=str(e))


@workstation_router.get("/api/v1/workstation/patients/{patient_id}/export/deidentified")
def api_export_patient_deidentified(patient_id: str, operator_id: str = "RESEARCHER"):
    """Export HIPAA-aligned de-identified patient research record."""
    try:
        return export_deidentified_research_record(patient_id, operator_id=operator_id)
    except PatientManagerError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==========================================
# AI TUTOR & KNOWLEDGE API
# ==========================================

@workstation_router.post("/api/v1/workstation/ai-tutor/explain-anatomy")
async def api_explain_anatomy(request: Request):
    payload = await request.json()
    name = payload.get("name", "")
    return explain_anatomical_structure(name)


@workstation_router.post("/api/v1/workstation/ai-tutor/link-movement")
async def api_link_movement(request: Request):
    payload = await request.json()
    movement = payload.get("movement", "ELBOW_FLEXION")
    return link_movement_to_muscles(movement)


@workstation_router.post("/api/v1/workstation/ai-tutor/explain-uncertainty")
async def api_explain_uncertainty(request: Request):
    payload = await request.json()
    joint = payload.get("joint_tested", "ELBOW_FLEXION")
    rom = float(payload.get("measured_rom", 90.0))
    u95 = float(payload.get("uncertainty_u95", 1.5))
    quality = payload.get("quality_status", "OPTIMAL")
    confounders = payload.get("confounders", [])
    return explain_measurement_uncertainty(joint, rom, u95, quality, confounders)


@workstation_router.post("/api/v1/workstation/ai-tutor/audit-session")
async def api_audit_session(request: Request):
    payload = await request.json()
    patient = payload.get("patient", {})
    session = payload.get("session", {})
    return audit_session_completeness(patient, session)


@workstation_router.get("/api/v1/workstation/ai-tutor/search-library")
def api_search_library(q: str = Query(..., min_length=2), limit: int = 5):
    return search_evidence_library(q, limit=limit)


# ==========================================
# BIOMECHANICS & SHOULDER MOVEMENT LAB API
# ==========================================

from msk_research_lab.biomechanics.shoulder_lab import get_shoulder_lab_engine


@workstation_router.get("/api/v1/biomechanics/shoulder/manifest")
def api_get_shoulder_manifest():
    """Retrieve registered BodyParts3D anatomical structures and coordinate metadata."""
    engine = get_shoulder_lab_engine()
    return engine.get_manifest()


@workstation_router.get("/api/v1/biomechanics/shoulder/kinematics/frame")
def api_get_shoulder_frame(
    arm_elevation_deg: float = Query(0.0, ge=0.0, le=180.0),
    comparison_mode: str = Query("normal_2to1")
):
    """Calculate joint rotations for a specific arm elevation angle."""
    engine = get_shoulder_lab_engine()
    return engine.get_kinematic_frame(arm_elevation_deg, comparison_mode=comparison_mode)


@workstation_router.get("/api/v1/biomechanics/shoulder/kinematics/trajectory")
def api_get_shoulder_trajectory(
    comparison_mode: str = Query("normal_2to1"),
    step_deg: float = Query(1.0, ge=0.5, le=10.0)
):
    """Retrieve full continuous trajectory frames from 0 to 180 degrees."""
    engine = get_shoulder_lab_engine()
    return engine.get_full_trajectory(comparison_mode=comparison_mode, step_deg=step_deg)


@workstation_router.get("/api/v1/biomechanics/shoulder/muscles/response")
def api_get_shoulder_muscles(
    arm_elevation_deg: float = Query(0.0, ge=0.0, le=180.0),
    comparison_mode: str = Query("normal_2to1")
):
    """Retrieve interpolated OpenSim muscle fiber lengths, forces, and KMSI classifications."""
    engine = get_shoulder_lab_engine()
    return engine.get_muscle_responses(arm_elevation_deg, comparison_mode=comparison_mode)


@workstation_router.get("/api/v1/biomechanics/shoulder/comparisons")
def api_get_shoulder_comparisons():
    """Retrieve comparative movement models (Normal 2:1 vs Forward Shoulder Restrained)."""
    engine = get_shoulder_lab_engine()
    return engine.get_comparative_models()


@workstation_router.get("/api/v1/biomechanics/shoulder/guided/scenes")
def api_get_guided_learning_scenes():
    """Retrieve 6 structured educational scenes for Guided Learning Case Study."""
    engine = get_shoulder_lab_engine()
    return engine.get_guided_learning_scenes()


@workstation_router.get("/api/v1/biomechanics/shoulder/muscles/dynamics")
def api_get_muscle_dynamics(
    muscle_id: Optional[str] = Query(None),
    arm_elevation_deg: float = Query(0.0, ge=0.0, le=180.0),
    comparison_mode: str = Query("normal_2to1")
):
    """Retrieve OpenSim muscle dynamics details with attachment points, fiber changes, and epistemic tags."""
    engine = get_shoulder_lab_engine()
    return engine.get_muscle_dynamics(
        muscle_id=muscle_id,
        arm_elevation_deg=arm_elevation_deg,
        comparison_mode=comparison_mode
    )


@workstation_router.get("/api/v1/biomechanics/shoulder/motor-control")
def api_get_motor_control_education():
    """Retrieve evidence-based educational topics on motor control, sensory feedback, and movement learning."""
    engine = get_shoulder_lab_engine()
    return engine.get_motor_control_education()


@workstation_router.get("/api/v1/biomechanics/shoulder/annotations/{structure_id}")
def api_get_shoulder_annotation(structure_id: str):
    """Retrieve evidence-based educational annotation for a specific structure."""
    engine = get_shoulder_lab_engine()
    anno = engine.get_annotation(structure_id)
    if not anno:
        raise HTTPException(status_code=404, detail=f"No annotation found for structure '{structure_id}'.")
    return anno


@workstation_router.get("/api/v1/biomechanics/shoulder/models/{filename}")
def api_serve_shoulder_model(filename: str):
    """Securely serve BodyParts3D GLB model files from 2data/models/atlas/."""
    safe_name = Path(filename).name
    if not safe_name.lower().endswith((".glb", ".json", ".csv")):
        raise HTTPException(status_code=400, detail="Invalid model file extension.")
    engine = get_shoulder_lab_engine()
    file_path = engine.atlas_dir / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Model file '{safe_name}' not found.")
    media_type = "model/gltf-binary" if safe_name.endswith(".glb") else "application/json"
    return FileResponse(path=file_path, media_type=media_type)

