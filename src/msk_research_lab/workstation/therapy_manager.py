"""Therapy Session Workspace & SOAP Documentation for MSK Personal Workstation."""

import json
import uuid
import datetime
from typing import Dict, List, Optional, Any
from msk_research_lab.core.db import get_db
from msk_research_lab.workstation.patient_manager import get_patient, update_patient


class TherapySessionError(Exception):
    """Custom exception for therapy session errors."""
    pass


MODALITY_EVIDENCE_MAP = {
    "THAI_MASSAGE": "TRADITIONAL_EMPIRICAL_DOCUMENTED",
    "MYOFASCIAL_RELEASE": "MODERATE_EVIDENCE_RCT",
    "DIEN_CHAN": "TRADITIONAL_EMPIRICAL_DOCUMENTED",
    "MANUAL_THERAPY": "HIGH_EVIDENCE_SYSTEMATIC_REVIEW",
    "ELECTROTHERAPY": "MODERATE_EVIDENCE_RCT"
}


def generate_soap_note(
    patient: Dict[str, Any],
    pre_pain: float,
    post_pain: float,
    pre_symptoms: str,
    post_symptoms: str,
    modalities: List[Dict[str, Any]],
    motion_assessments: List[Dict[str, Any]],
    dds_record: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """Generate structured SOAP clinical note draft based on objective session data."""
    # S - Subjective
    subj = (
        f"Chief Complaint: {patient.get('primary_complaint', 'N/A')}. "
        f"Pre-session pain score: {pre_pain}/10 (VAS). "
        f"Symptoms reported: {pre_symptoms or 'Standard regional muscular tension.'}. "
        f"Functional limitations noted: {patient.get('functional_limitations', 'None reported')}."
    )

    # O - Objective
    motion_strs = []
    for m in motion_assessments:
        deficit_str = f", deficit {m.get('rom_deficit_deg')}°" if m.get('rom_deficit_deg') is not None else ""
        conf = f" (Confidence: {m.get('tracking_confidence', 1.0):.2f}, Status: {m.get('quality_status', 'OPTIMAL')})"
        motion_strs.append(
            f"{m.get('joint_tested', 'Joint')} ({m.get('side', 'R')}): {m.get('measured_rom_deg')}° ±{m.get('uncertainty_u95_deg', 1.5)}°{deficit_str}{conf}"
        )
    motion_obj = "; ".join(motion_strs) if motion_strs else "No active camera kinematic motion measurements captured during session."

    mod_strs = []
    for mod in modalities:
        cat = mod.get("category", "MANUAL_THERAPY")
        ev = MODALITY_EVIDENCE_MAP.get(cat, "TRADITIONAL_EMPIRICAL_DOCUMENTED")
        dur = f" ({mod.get('duration_minutes', 15)} min)" if mod.get("duration_minutes") else ""
        mod_strs.append(f"{mod.get('name', 'Technique')} [{cat}, Evidence: {ev}]{dur}")
    modalities_obj = "; ".join(mod_strs) if mod_strs else "Manual physical therapy modalities applied."

    dds_obj = ""
    if dds_record and dds_record.get("device_used"):
        dds_obj = (
            f" Physical DDS bioelectric device readout documented: "
            f"Frequency: {dds_record.get('recorded_frequency_hz', 'N/A')} Hz, "
            f"Intensity: {dds_record.get('recorded_intensity_ma', 'N/A')} mA, "
            f"Patient reported sensation: '{dds_record.get('patient_sensation', 'Comfortable tingling')}'. "
            f"(Note: Parameters recorded for documentation only; software does not command device)."
        )

    obj = f"Kinematics: {motion_obj}. Modalities Applied: {modalities_obj}.{dds_obj}"

    # A - Assessment
    delta_pain = pre_pain - post_pain
    tolerance = "well tolerated without adverse reaction" if not (dds_record and dds_record.get("adverse_reaction")) else "discontinued due to patient discomfort"
    asmt = (
        f"Patient underwent planned conservative therapy, which was {tolerance}. "
        f"Immediate post-treatment pain score decreased by {delta_pain:.1f} points ({pre_pain} -> {post_pain}/10). "
        f"Post-treatment observation: {post_symptoms or 'Noticeable regional tissue softening and relaxed posture.'}."
    )

    # P - Plan
    plan = (
        "1. Recommend active gentle pain-free mobility within measured ROM. "
        "2. Adequate oral hydration and avoid prolonged sustained static postures. "
        "3. Review progress next scheduled session. "
        "4. Red flag education: contact medical provider immediately if radiating numbness or sharp acute pain develops."
    )

    return {
        "subjective": subj,
        "objective": obj,
        "assessment": asmt,
        "plan": plan
    }


def record_therapy_session(
    patient_id: str,
    pre_pain_score: float,
    post_pain_score: float,
    pre_symptoms_notes: str = "",
    post_symptoms_notes: str = "",
    motion_assessment_ids: Optional[List[str]] = None,
    related_anatomy: Optional[List[Dict[str, Any]]] = None,
    applied_modalities: Optional[List[Dict[str, Any]]] = None,
    dds_device_records: Optional[Dict[str, Any]] = None,
    soap_notes: Optional[Dict[str, str]] = None,
    operator_id: str = "OPERATOR",
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Record a comprehensive therapy session with objective telemetry and SOAP notes."""
    patient = get_patient(patient_id)
    sid = session_id or f"SES-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.utcnow().isoformat() + "Z"

    # Count prior sessions to assign session_number
    with get_db() as conn:
        count_row = conn.execute(
            "SELECT COUNT(*) FROM therapy_sessions WHERE patient_id = ?;", (patient_id,)
        ).fetchone()
        session_num = (count_row[0] if count_row else 0) + 1

    motion_ids = motion_assessment_ids or []
    rel_anat = related_anatomy or []
    modalities = applied_modalities or []
    
    # Process DDS device records
    dds = dds_device_records or {
        "device_used": False,
        "disclaimer": "Readout recorded manually for clinical documentation; workbench does NOT control hardware or prescribe stimulation"
    }

    # Fetch motion assessment details if IDs supplied
    motion_details = []
    if motion_ids:
        with get_db() as conn:
            placeholders = ",".join(["?"] * len(motion_ids))
            m_rows = conn.execute(
                f"SELECT * FROM motion_assessments WHERE id IN ({placeholders});", tuple(motion_ids)
            ).fetchall()
            for r in m_rows:
                motion_details.append({
                    "id": r["id"],
                    "joint_tested": r["joint_tested"],
                    "side": r["side"],
                    "measured_rom_deg": r["measured_rom_deg"],
                    "rom_deficit_deg": r["rom_deficit_deg"],
                    "uncertainty_u95_deg": r["uncertainty_u95_deg"],
                    "tracking_confidence": r["tracking_confidence"],
                    "quality_status": r["quality_status"]
                })

    # Generate or adopt SOAP note
    if not soap_notes or not soap_notes.get("subjective"):
        soap = generate_soap_note(
            patient=patient,
            pre_pain=float(pre_pain_score),
            post_pain=float(post_pain_score),
            pre_symptoms=pre_symptoms_notes,
            post_symptoms=post_symptoms_notes,
            modalities=modalities,
            motion_assessments=motion_details,
            dds_record=dds
        )
    else:
        soap = soap_notes

    with get_db() as conn:
        conn.execute("""
            INSERT INTO therapy_sessions (
                id, patient_id, session_number, session_date, pre_symptoms_notes,
                pre_pain_score, motion_assessment_ids_json, related_anatomy_json,
                applied_modalities_json, dds_device_records_json, post_pain_score,
                post_symptoms_notes, soap_subjective, soap_objective, soap_assessment,
                soap_plan, operator_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            sid, patient_id, session_num, now, pre_symptoms_notes.strip(),
            float(pre_pain_score), json.dumps(motion_ids), json.dumps(rel_anat),
            json.dumps(modalities), json.dumps(dds), float(post_pain_score),
            post_symptoms_notes.strip(), soap.get("subjective", ""), soap.get("objective", ""),
            soap.get("assessment", ""), soap.get("plan", ""), operator_id, now
        ))

        # Update motion_assessments session_id foreign linkage
        for mid in motion_ids:
            conn.execute("UPDATE motion_assessments SET session_id = ? WHERE id = ?;", (sid, mid))

    # Update patient current pain score to post_pain_score
    update_patient(patient_id, {"current_pain_score": float(post_pain_score)})

    return get_therapy_session(sid)


def get_therapy_session(session_id: str) -> Dict[str, Any]:
    """Retrieve full therapy session details by ID."""
    with get_db() as conn:
        row = conn.execute("""
            SELECT id, patient_id, session_number, session_date, pre_symptoms_notes,
                   pre_pain_score, motion_assessment_ids_json, related_anatomy_json,
                   applied_modalities_json, dds_device_records_json, post_pain_score,
                   post_symptoms_notes, soap_subjective, soap_objective, soap_assessment,
                   soap_plan, operator_id, created_at
            FROM therapy_sessions WHERE id = ?;
        """, (session_id,)).fetchone()

    if not row:
        raise TherapySessionError(f"Session with ID '{session_id}' not found.")

    return {
        "id": row["id"],
        "patient_id": row["patient_id"],
        "session_number": row["session_number"],
        "session_date": row["session_date"],
        "pre_symptoms_notes": row["pre_symptoms_notes"],
        "pre_pain_score": row["pre_pain_score"],
        "motion_assessment_ids": json.loads(row["motion_assessment_ids_json"]),
        "related_anatomy": json.loads(row["related_anatomy_json"]),
        "applied_modalities": json.loads(row["applied_modalities_json"]),
        "dds_device_records": json.loads(row["dds_device_records_json"]),
        "post_pain_score": row["post_pain_score"],
        "post_symptoms_notes": row["post_symptoms_notes"],
        "soap": {
            "subjective": row["soap_subjective"],
            "objective": row["soap_objective"],
            "assessment": row["soap_assessment"],
            "plan": row["soap_plan"]
        },
        "operator_id": row["operator_id"],
        "created_at": row["created_at"]
    }


def list_patient_sessions(patient_id: str) -> List[Dict[str, Any]]:
    """List all therapy sessions for a patient in chronological order."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, session_number, session_date, pre_pain_score, post_pain_score,
                   operator_id, created_at
            FROM therapy_sessions WHERE patient_id = ?
            ORDER BY session_number ASC;
        """, (patient_id,)).fetchall()

    return [
        {
            "id": r["id"],
            "session_number": r["session_number"],
            "session_date": r["session_date"],
            "pre_pain_score": r["pre_pain_score"],
            "post_pain_score": r["post_pain_score"],
            "pain_delta": r["pre_pain_score"] - r["post_pain_score"],
            "operator_id": r["operator_id"],
            "created_at": r["created_at"]
        }
        for r in rows
    ]
