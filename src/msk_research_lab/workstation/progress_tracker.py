"""Progress Tracking and Multi-Session Longitudinal Analytics."""

import csv
import io
import json
from typing import Dict, List, Any
from msk_research_lab.core.db import get_db
from msk_research_lab.workstation.patient_manager import get_patient


def get_patient_progress_summary(patient_id: str) -> Dict[str, Any]:
    """Compile comprehensive longitudinal progress metrics across all sessions."""
    patient = get_patient(patient_id)

    with get_db() as conn:
        # Fetch all therapy sessions
        sessions = conn.execute("""
            SELECT id, session_number, session_date, pre_pain_score, post_pain_score,
                   created_at
            FROM therapy_sessions WHERE patient_id = ?
            ORDER BY session_number ASC;
        """, (patient_id,)).fetchall()

        # Fetch all motion assessments
        motion_rows = conn.execute("""
            SELECT id, session_id, joint_tested, side, measured_rom_deg, reference_rom_deg,
                   rom_deficit_deg, uncertainty_u95_deg, tracking_confidence, quality_status,
                   assessed_at
            FROM motion_assessments WHERE patient_id = ?
            ORDER BY assessed_at ASC;
        """, (patient_id,)).fetchall()

    pain_timeline = []
    for s in sessions:
        pain_timeline.append({
            "session_number": s["session_number"],
            "date": s["session_date"],
            "pre_pain": s["pre_pain_score"],
            "post_pain": s["post_pain_score"],
            "delta": round(s["pre_pain_score"] - s["post_pain_score"], 2)
        })

    # Group motion assessments by joint and side
    rom_trajectories: Dict[str, List[Dict[str, Any]]] = {}
    for m in motion_rows:
        key = f"{m['joint_tested']}_{m['side']}"
        if key not in rom_trajectories:
            rom_trajectories[key] = []
        rom_trajectories[key].append({
            "date": m["assessed_at"],
            "measured_rom": m["measured_rom_deg"],
            "reference_rom": m["reference_rom_deg"],
            "deficit": m["rom_deficit_deg"],
            "uncertainty_u95": m["uncertainty_u95_deg"],
            "quality_status": m["quality_status"]
        })

    # Aggregate overall stats
    initial_pain = pain_timeline[0]["pre_pain"] if pain_timeline else patient["current_pain_score"]
    latest_pain = pain_timeline[-1]["post_pain"] if pain_timeline else patient["current_pain_score"]
    total_pain_reduction = round(initial_pain - latest_pain, 2)

    return {
        "patient_id": patient_id,
        "full_name": patient["full_name"],
        "primary_complaint": patient["primary_complaint"],
        "total_sessions": len(sessions),
        "initial_pain_score": initial_pain,
        "latest_pain_score": latest_pain,
        "total_pain_reduction": total_pain_reduction,
        "pain_timeline": pain_timeline,
        "rom_trajectories": rom_trajectories,
        "status": patient["status"]
    }


def export_patient_progress_csv(patient_id: str) -> str:
    """Generate structured CSV export of all therapy sessions and measurements."""
    summary = get_patient_progress_summary(patient_id)
    output = io.StringIO()
    writer = csv.writer(output)

    # Header section
    writer.writerow(["MSK THERAPY WORKSTATION - CLINICAL PROGRESS REPORT"])
    writer.writerow(["Patient ID", summary["patient_id"]])
    writer.writerow(["Full Name", summary["full_name"]])
    writer.writerow(["Primary Complaint", summary["primary_complaint"]])
    writer.writerow(["Total Sessions", summary["total_sessions"]])
    writer.writerow(["Total Pain Reduction (VAS)", summary["total_pain_reduction"]])
    writer.writerow([])

    # Sessions table
    writer.writerow(["SESSION TIMELINE"])
    writer.writerow(["Session #", "Date", "Pre-Pain (0-10)", "Post-Pain (0-10)", "Pain Delta"])
    for pt in summary["pain_timeline"]:
        writer.writerow([pt["session_number"], pt["date"], pt["pre_pain"], pt["post_pain"], pt["delta"]])
    writer.writerow([])

    # ROM table
    writer.writerow(["MOTION ASSESSMENT TRAJECTORIES"])
    writer.writerow(["Joint & Side", "Assessment Date", "Measured ROM (deg)", "Normal Reference", "Deficit (deg)", "Uncertainty U95 (deg)", "Quality Status"])
    for joint_key, records in summary["rom_trajectories"].items():
        for r in records:
            writer.writerow([
                joint_key, r["date"], r["measured_rom"], r["reference_rom"], r["deficit"], r["uncertainty_u95"], r["quality_status"]
            ])

    return output.getvalue()
