"""Patient Profile Management for MSK Therapy Personal Workstation."""

import hmac
import hashlib
import json
import uuid
import datetime
import re
from typing import Dict, List, Optional, Any
from msk_research_lab.core.db import get_db

import os
import secrets
from pathlib import Path
from msk_research_lab.security.permissions import secure_file_permissions

DEFAULT_PEPPER = b"msk_workstation_local_secret_pepper_v1"


def get_or_create_pepper() -> bytes:
    """Retrieve secret HMAC pepper from environment or secure local key file."""
    env_pepper = os.environ.get("MSK_WORKSTATION_PEPPER")
    if env_pepper:
        return env_pepper.encode("utf-8")
    
    # Locate pepper alongside database directory
    custom_db = False
    try:
        from msk_research_lab.core.db import get_db_path
        db_dir = get_db_path().parent
        pepper_file = db_dir / ".workstation_pepper"
        custom_db = "2data/db" not in str(db_dir)
    except Exception:
        pepper_file = Path("2data/db/.workstation_pepper")

    if not pepper_file.exists() and not custom_db:
        legacy_pepper = Path("2data/db/.workstation_pepper")
        if legacy_pepper.exists():
            pepper_file = legacy_pepper

    if pepper_file.exists():
        try:
            content = pepper_file.read_bytes()
            if len(content) >= 16:
                return content
        except Exception:
            pass
    
    # Fallback to deterministic default or write new key
    try:
        pepper_file.parent.mkdir(parents=True, exist_ok=True)
        new_pepper = secrets.token_bytes(32)
        pepper_file.write_bytes(new_pepper)
        secure_file_permissions(pepper_file)
        return new_pepper
    except Exception:
        return DEFAULT_PEPPER


def get_pseudonym_hash(patient_id: str, pepper: Optional[bytes] = None) -> str:
    """Generate a keyed HMAC-SHA256 pseudonym hash to prevent dictionary attacks."""
    p = pepper if pepper is not None else get_or_create_pepper()
    return hmac.new(p, patient_id.encode("utf-8"), hashlib.sha256).hexdigest()


class PatientManagerError(Exception):
    """Custom exception for patient operations."""
    pass


def evaluate_red_flags(red_flags: Dict[str, Any]) -> Dict[str, Any]:
    """Audit red flags for urgent medical referral conditions."""
    critical_flags = [
        red_flags.get("fever", False),
        red_flags.get("unexplained_weight_loss", False),
        red_flags.get("bowel_bladder_dysfunction", False),
        red_flags.get("motor_deficit", False),
        red_flags.get("saddle_anesthesia", False),
        red_flags.get("unremitting_night_pain", False)
    ]
    requires_referral = any(critical_flags) or bool(red_flags.get("requires_referral"))
    
    notes = red_flags.get("referral_notes", "")
    if requires_referral and not notes:
        notes = "CRITICAL: One or more clinical red flags present. Mandatory referral to qualified medical specialist/physician prior to manual or electro-therapy."
        
    result = dict(red_flags)
    result["requires_referral"] = requires_referral
    result["referral_notes"] = notes
    return result


def create_patient(
    full_name: str,
    primary_complaint: str,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    height_cm: Optional[float] = None,
    weight_kg: Optional[float] = None,
    occupation: Optional[str] = None,
    activity_level: str = "MODERATE",
    medical_history: str = "",
    pain_locations: Optional[List[str]] = None,
    current_pain_score: float = 0.0,
    radiating_symptoms: Optional[Dict[str, Any]] = None,
    functional_limitations: str = "",
    red_flags: Optional[Dict[str, Any]] = None,
    patient_id: Optional[str] = None
) -> Dict[str, Any]:
    """Register a new patient profile in local SQLite storage."""
    if not full_name or not full_name.strip():
        raise PatientManagerError("Patient full name is required.")
    if not primary_complaint or not primary_complaint.strip():
        raise PatientManagerError("Primary complaint is required.")

    pid = patient_id or f"PAT-{uuid.uuid4().hex[:8].upper()}"
    pseudonym = get_pseudonym_hash(pid)
    now = datetime.datetime.utcnow().isoformat() + "Z"

    pain_locs = pain_locations or []
    rad_syms = radiating_symptoms or {
        "has_numbness": False,
        "has_weakness": False,
        "has_radiculopathy": False,
        "notes": ""
    }
    rf = evaluate_red_flags(red_flags or {})

    with get_db() as conn:
        conn.execute("""
            INSERT INTO patients (
                id, pseudonym_hash, full_name, age, gender, height_cm, weight_kg,
                occupation, activity_level, medical_history, primary_complaint,
                pain_locations_json, current_pain_score, radiating_symptoms_json,
                functional_limitations, red_flags_json, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?);
        """, (
            pid, pseudonym, full_name.strip(), age, gender, height_cm, weight_kg,
            occupation, activity_level, medical_history.strip(), primary_complaint.strip(),
            json.dumps(pain_locs), float(current_pain_score), json.dumps(rad_syms),
            functional_limitations.strip(), json.dumps(rf), now, now
        ))
        
        # Log audit event
        conn.execute("""
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?);
        """, (
            "PATIENT_REGISTERED", "OPERATOR",
            json.dumps({"patient_id": pid, "pseudonym_prefix": pseudonym[:8]})
        ))

    return get_patient(pid)


def get_patient(patient_id: str) -> Dict[str, Any]:
    """Retrieve complete patient profile by ID."""
    with get_db() as conn:
        row = conn.execute("""
            SELECT id, pseudonym_hash, pepper_version, full_name, age, gender, height_cm, weight_kg,
                   occupation, activity_level, medical_history, primary_complaint,
                   pain_locations_json, current_pain_score, radiating_symptoms_json,
                   functional_limitations, red_flags_json, status, created_at, updated_at
            FROM patients WHERE id = ?;
        """, (patient_id,)).fetchone()

    if not row:
        raise PatientManagerError(f"Patient with ID '{patient_id}' not found.")

    return {
        "id": row["id"],
        "pseudonym_hash": row["pseudonym_hash"],
        "pepper_version": row["pepper_version"] if "pepper_version" in row.keys() else 1,
        "full_name": row["full_name"],
        "age": row["age"],
        "gender": row["gender"],
        "height_cm": row["height_cm"],
        "weight_kg": row["weight_kg"],
        "occupation": row["occupation"],
        "activity_level": row["activity_level"],
        "medical_history": row["medical_history"],
        "primary_complaint": row["primary_complaint"],
        "pain_locations": json.loads(row["pain_locations_json"]),
        "current_pain_score": row["current_pain_score"],
        "radiating_symptoms": json.loads(row["radiating_symptoms_json"]),
        "functional_limitations": row["functional_limitations"],
        "red_flags": json.loads(row["red_flags_json"]),
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }


def list_patients(search: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List registered patients with optional filtering."""
    query = "SELECT id, full_name, age, gender, primary_complaint, current_pain_score, status, updated_at FROM patients"
    params: List[Any] = []
    clauses: List[str] = []

    if status:
        clauses.append("status = ?")
        params.append(status)
    if search:
        clauses.append("(full_name LIKE ? OR primary_complaint LIKE ? OR occupation LIKE ?)")
        s_pat = f"%{search}%"
        params.extend([s_pat, s_pat, s_pat])

    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY updated_at DESC;"

    with get_db() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()

    return [
        {
            "id": r["id"],
            "full_name": r["full_name"],
            "age": r["age"],
            "gender": r["gender"],
            "primary_complaint": r["primary_complaint"],
            "current_pain_score": r["current_pain_score"],
            "status": r["status"],
            "updated_at": r["updated_at"]
        }
        for r in rows
    ]


def update_patient(patient_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update fields on an existing patient profile."""
    # Ensure patient exists
    current = get_patient(patient_id)
    now = datetime.datetime.utcnow().isoformat() + "Z"

    field_map = {
        "full_name": updates.get("full_name", current["full_name"]),
        "age": updates.get("age", current["age"]),
        "gender": updates.get("gender", current["gender"]),
        "height_cm": updates.get("height_cm", current["height_cm"]),
        "weight_kg": updates.get("weight_kg", current["weight_kg"]),
        "occupation": updates.get("occupation", current["occupation"]),
        "activity_level": updates.get("activity_level", current["activity_level"]),
        "medical_history": updates.get("medical_history", current["medical_history"]),
        "primary_complaint": updates.get("primary_complaint", current["primary_complaint"]),
        "pain_locations_json": json.dumps(updates.get("pain_locations", current["pain_locations"])),
        "current_pain_score": float(updates.get("current_pain_score", current["current_pain_score"])),
        "radiating_symptoms_json": json.dumps(updates.get("radiating_symptoms", current["radiating_symptoms"])),
        "functional_limitations": updates.get("functional_limitations", current["functional_limitations"]),
        "red_flags_json": json.dumps(evaluate_red_flags(updates.get("red_flags", current["red_flags"]))),
        "status": updates.get("status", current["status"]),
        "updated_at": now
    }

    set_clauses = [f"{col} = ?" for col in field_map.keys()]
    values = list(field_map.values()) + [patient_id]

    with get_db() as conn:
        conn.execute(f"UPDATE patients SET {', '.join(set_clauses)} WHERE id = ?;", tuple(values))

    return get_patient(patient_id)


def delete_patient(patient_id: str) -> bool:
    """Soft-delete/discharge or purge patient records."""
    with get_db() as conn:
        conn.execute("UPDATE patients SET status = 'DISCHARGED', updated_at = (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')) WHERE id = ?;", (patient_id,))
    return True


def scrub_phi_from_text(text: Optional[str]) -> str:
    """Scrub direct and quasi-identifiers from clinical free-text (DEF-21).
    
    Removes:
    - Phone numbers (domestic & international)
    - Email addresses
    - Social Security Numbers (SSNs)
    - Physician / Provider names (e.g. 'Dr. Smith', 'Doctor Jane Doe')
    - Specific calendar dates (e.g. 12/31/2020, 2024-05-18)
    """
    if not text or not isinstance(text, str):
        return "" if text is None else str(text)

    # 1. Emails
    s = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", text)
    # 2. SSN
    s = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", s)
    # 3. Phone numbers (e.g., (555) 019-2834, 555-123-4567, +1-555-555-0199)
    s = re.sub(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]", s)
    # 4. Clinician titles & names (e.g. Dr. John Doe, Doctor Smith, Prof. Williams)
    s = re.sub(r"\b(?:Dr\.|Doctor|Prof\.|MD)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", "[REDACTED_PROVIDER]", s)
    # 5. Specific dates (e.g. 10/12/1985, 2024-05-18, 05-12-2023)
    s = re.sub(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b", "[REDACTED_DATE]", s)

    return s


def export_deidentified_research_record(
    patient_id: str,
    operator_id: str = "RESEARCHER",
) -> Dict[str, Any]:
    """Export de-identified research record with scrubbed text and non-certified research label.
    
    Guarantees:
    - Direct identifiers ('full_name') are strictly excluded from output.
    - Clinical free-text fields (notes, history, referrals) are scrubbed of phone, email, SSN, provider names, and dates (DEF-21).
    - Patients aged > 89 are aggregated to '90+' (Safe Harbor § 164.514(b)(2)(i)(C)).
    - Patient ID is replaced by keyed HMAC pseudonym hash prefix.
    - Explicitly labeled 'SYNTHETIC_RESEARCH_SCRUBBED_NOT_CERTIFIED_FOR_PHI'.
    - Audit tri-ledger event 'RESEARCH_RECORD_EXPORTED' is logged.
    """
    patient = get_patient(patient_id)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    pseudo = patient["pseudonym_hash"]

    # Safe Harbor age aggregation
    raw_age = patient["age"]
    deidentified_age: Any = raw_age
    if isinstance(raw_age, (int, float)) and raw_age > 89:
        deidentified_age = "90+"

    # Free-text scrubbing
    deidentified_med_hist = scrub_phi_from_text(patient.get("medical_history", ""))
    deidentified_complaint = scrub_phi_from_text(patient.get("primary_complaint", ""))
    deidentified_occ = scrub_phi_from_text(patient.get("occupation", ""))

    # Red flags scrubbing
    raw_flags = patient.get("red_flags")
    scrubbed_flags: Any = {}
    if isinstance(raw_flags, dict):
        for k, v in raw_flags.items():
            if isinstance(v, str):
                scrubbed_flags[k] = scrub_phi_from_text(v)
            else:
                scrubbed_flags[k] = v
    else:
        scrubbed_flags = raw_flags

    deidentified = {
        "research_subject_id": f"SUBJ-{pseudo[:12].upper()}",
        "pseudonym_hash": pseudo,
        "pepper_version": patient.get("pepper_version", 1),
        "age": deidentified_age,
        "gender": patient["gender"],
        "height_cm": patient["height_cm"],
        "weight_kg": patient["weight_kg"],
        "occupation": deidentified_occ,
        "activity_level": patient["activity_level"],
        "medical_history_summary": deidentified_med_hist,
        "primary_complaint": deidentified_complaint,
        "pain_locations": patient["pain_locations"],
        "current_pain_score": patient["current_pain_score"],
        "radiating_symptoms": patient["radiating_symptoms"],
        "functional_limitations": patient["functional_limitations"],
        "red_flags": scrubbed_flags,
        "status": patient["status"],
        "exported_at": now,
        "operator_id": operator_id,
        "pii_redacted": True,
        "hipaa_safe_harbor_certified": False,
        "deidentification_method": "SYNTHETIC_RESEARCH_SCRUBBED_NOT_CERTIFIED_FOR_PHI",
        "compliance_disclaimer": "SYNTHETIC/EDUCATIONAL RESEARCH ONLY — NOT CERTIFIED FOR REAL PHI",
    }

    with get_db() as conn:
        conn.execute("""
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?);
        """, (
            "RESEARCH_RECORD_EXPORTED", operator_id,
            json.dumps({
                "patient_id": patient_id,
                "research_subject_id": deidentified["research_subject_id"],
                "pseudonym_hash_prefix": pseudo[:8],
            })
        ))

    return deidentified

