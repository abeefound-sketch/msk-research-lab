"""Local-First AI Tutor, Evidence Retrieval, and SOAP Assistant."""

import json
from typing import Dict, List, Optional, Any
from msk_research_lab.core.db import get_db

# Static verified anatomical movement-to-muscle linkage database
MOVEMENT_ANATOMY_KNOWLEDGE = {
    "ELBOW_FLEXION": {
        "primary_agonists": ["Biceps brachii", "Brachialis"],
        "synergists": ["Brachioradialis", "Pronator teres"],
        "antagonists": ["Triceps brachii", "Anconeus"],
        "joint_classification": "Hinge joint (Ginglymus)",
        "innervation": "Musculocutaneous nerve (C5-C6), Radial nerve (C5-C6)",
        "clinical_significance": "Normal active ROM: 140-150 deg. Deficits often stem from capsular tightness or bicipital myofascial trigger points."
    },
    "SHOULDER_ABDUCTION": {
        "primary_agonists": ["Middle Deltoid", "Supraspinatus (initial 0-15 deg)"],
        "synergists": ["Anterior Deltoid", "Serratus anterior (scapular upward rotation)"],
        "antagonists": ["Pectoralis major", "Latissimus dorsi", "Teres major"],
        "joint_classification": "Ball-and-socket (Glenohumeral) with Scapulothoracic rhythm (2:1 ratio)",
        "innervation": "Axillary nerve (C5-C6), Suprascapular nerve (C5-C6)",
        "clinical_significance": "Painful arc between 60-120 deg indicates subacromial impingement or supraspinatus tendinopathy. Scapular elevation must be observed."
    },
    "SHOULDER_ELEVATION": {
        "primary_agonists": ["Anterior Deltoid", "Coracobrachialis", "Pectoralis major (clavicular)"],
        "synergists": ["Biceps brachii (long head)", "Serratus anterior"],
        "antagonists": ["Latissimus dorsi", "Teres major", "Posterior Deltoid"],
        "joint_classification": "Glenohumeral multi-axial articulation",
        "innervation": "Axillary nerve (C5-C6), Musculocutaneous nerve (C5-C7)",
        "clinical_significance": "Compensatory trunk extension or shoulder shrugging must be distinguished from true glenohumeral elevation."
    },
    "KNEE_FLEXION": {
        "primary_agonists": ["Biceps femoris", "Semitendinosus", "Semimembranosus"],
        "synergists": ["Gracilis", "Sartorius", "Gastrocnemius"],
        "antagonists": ["Quadriceps femoris (Rectus femoris, Vastus lateralis/medialis/intermedius)"],
        "joint_classification": "Modified hinge joint (Bicondylar)",
        "innervation": "Sciatic nerve (Tibial and Common Fibular divisions, L5-S2)",
        "clinical_significance": "Normal ROM: 135-145 deg. Limited by soft tissue approximation or hamstring contracture."
    }
}


def explain_anatomical_structure(name: str) -> Dict[str, Any]:
    """
    Retrieve structured anatomical explanation, origin, insertion, innervation,
    and associated document citations from the local database.
    """
    clean_name = name.strip()
    
    with get_db() as conn:
        # 1. Lookup concept in ontology_concepts and aliases
        concept_row = conn.execute("""
            SELECT c.concept_id, c.canonical_label, c.namespace, c.clinical_status,
                   a.value as alias_val
            FROM ontology_concepts c
            LEFT JOIN concept_aliases a ON c.concept_id = a.concept_id
            WHERE c.canonical_label LIKE ? OR a.value LIKE ? OR c.concept_id LIKE ?
            LIMIT 1;
        """, (f"%{clean_name}%", f"%{clean_name}%", f"%{clean_name}%")).fetchone()

        # 2. Search document library FTS5 for evidence passages
        doc_rows = []
        try:
            doc_rows = conn.execute("""
                SELECT d.original_filename, fts.heading, fts.body, dl.page_number
                FROM fts_document_locations fts
                JOIN documents d ON fts.document_id = d.id
                LEFT JOIN document_locations dl ON fts.location_id = dl.id
                WHERE fts_document_locations MATCH ?
                LIMIT 3;
            """, (clean_name,)).fetchall() if clean_name else []
        except Exception:
            doc_rows = []

    citations = [
        {
            "source_title": r["original_filename"],
            "section": r["heading"] or "General Musculoskeletal Section",
            "page": r["page_number"] or "N/A",
            "excerpt": (r["body"][:200] + "...") if len(r["body"]) > 200 else r["body"]
        }
        for r in doc_rows
    ]

    if concept_row:
        return {
            "name": concept_row["canonical_label"] or clean_name,
            "category": concept_row["namespace"] or "ANATOMICAL_CONCEPT",
            "clinical_status": concept_row["clinical_status"] or "VERIFIED",
            "definition": f"Verified structure in ontology namespace '{concept_row['namespace']}'.",
            "citations": citations,
            "found_in_ontology": True
        }
    else:
        # Fallback to general anatomical knowledge
        return {
            "name": clean_name,
            "category": "MUSCULOSKELETAL_STRUCTURE",
            "clinical_status": "DOCUMENTED",
            "definition": f"Anatomical structure '{clean_name}'. Consult local document library for primary references.",
            "citations": citations,
            "found_in_ontology": False
        }


def link_movement_to_muscles(movement_name: str) -> Dict[str, Any]:
    """
    Map joint movement to participating muscles and anatomical stabilizers.
    """
    key = movement_name.upper().replace(" ", "_")
    knowledge = MOVEMENT_ANATOMY_KNOWLEDGE.get(key)
    if not knowledge:
        # Match substring
        for k, val in MOVEMENT_ANATOMY_KNOWLEDGE.items():
            if k in key or key in k:
                knowledge = val
                key = k
                break

    if not knowledge:
        knowledge = {
            "primary_agonists": ["Regional prime mover musculature"],
            "synergists": ["Regional synergists"],
            "antagonists": ["Regional antagonist group"],
            "joint_classification": "Synovial articulation",
            "innervation": "Spinal segmental innervation",
            "clinical_significance": "Verify movement plane and isolate joint kinematics."
        }

    # Retrieve citations from document library
    search_term = key.replace("_", " ")
    citations = []
    try:
        with get_db() as conn:
            doc_rows = conn.execute("""
                SELECT d.original_filename, fts.heading, fts.body
                FROM fts_document_locations fts
                JOIN documents d ON fts.document_id = d.id
                WHERE fts_document_locations MATCH ?
                LIMIT 2;
            """, (search_term,)).fetchall()

        citations = [
            {
                "source": r["original_filename"],
                "section": r["heading"] or "Kinematics",
                "excerpt": (r["body"][:180] + "...") if len(r["body"]) > 180 else r["body"]
            }
            for r in doc_rows
        ]
    except Exception:
        citations = []

    return {
        "movement": key,
        "anatomical_linkage": knowledge,
        "citations": citations,
        "educational_note": "Camera-based tracking isolates 2D projection angles; observe whether trunk compensation confounds true joint excursion."
    }


def explain_measurement_uncertainty(
    joint_tested: str,
    measured_rom: float,
    uncertainty_u95: float = 1.5,
    quality_status: str = "OPTIMAL",
    confounders: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Provide scientific explanation of the measurement error bounds and optical confounders.
    """
    c_list = confounders or []
    reasons = [
        "2D camera tracking quantizes joints into image pixels (spatial uncertainty ±0.5°).",
        "Pose landmark estimation introduces micro-jitter and operator posture variations (±0.8°)."
    ]

    if "HUMERAL_ELEVATION_CONFOUNDER" in c_list:
        reasons.append(
            "CRITICAL: Active arm elevation changes the contour of the deltoid and lifts the clavicle. "
            "This compresses apparent shoulder width in 2D perspective, confounding yaw rotation estimation."
        )

    if quality_status == "DEGRADED":
        reasons.append(
            "Degraded tracking status indicates partial landmark occlusion, low frame contrast, or high motion blur velocity."
        )

    return {
        "joint_tested": joint_tested,
        "measured_rom": measured_rom,
        "confidence_interval_95": f"[{measured_rom - uncertainty_u95:.1f}°, {measured_rom + uncertainty_u95:.1f}°]",
        "expanded_uncertainty": f"±{uncertainty_u95:.2f}° (k=1.96, Gaussian normal assumption)",
        "optical_factors": reasons,
        "clinical_advisory": "Treat camera angles as supportive screening estimates, not certified medical goniometry."
    }


def audit_session_completeness(patient: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Audit session documentation for missing fields or potential safety oversight.
    """
    missing_items = []
    safety_notes = []

    # Check red flags
    red_flags = patient.get("red_flags", {})
    if red_flags.get("requires_referral"):
        safety_notes.append("WARNING: Patient has active red flag condition. Document physician clearance before continuing manual therapy.")

    # Check post-pain score
    if session.get("post_pain_score") is None or (session.get("post_pain_score") == 0.0 and session.get("pre_pain_score", 0) > 4):
        missing_items.append("Post-session pain score verification recommended.")

    # Check modalities
    if not session.get("applied_modalities"):
        missing_items.append("No specific manual or massage modalities documented for this session.")

    return {
        "is_complete": len(missing_items) == 0,
        "missing_items": missing_items,
        "safety_advisories": safety_notes,
        "audit_status": "VALIDATED" if len(missing_items) == 0 else "ACTION_REQUIRED"
    }


def search_evidence_library(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Execute local RAG/FTS5 search across indexed clinical literature and textbooks.
    """
    if not query_text or not query_text.strip():
        return []

    try:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT d.id as doc_id, d.original_filename,
                       fts.heading, fts.body, dl.page_number
                FROM fts_document_locations fts
                JOIN documents d ON fts.document_id = d.id
                LEFT JOIN document_locations dl ON fts.location_id = dl.id
                WHERE fts_document_locations MATCH ?
                LIMIT ?;
            """, (query_text.strip(), limit)).fetchall()

        return [
            {
                "doc_id": r["doc_id"],
                "title": r["original_filename"],
                "citation": f"Local Document: {r['original_filename']}",
                "section": r["heading"] or "Clinical Section",
                "page_number": r["page_number"] or "N/A",
                "snippet": (r["body"][:250] + "...") if len(r["body"]) > 250 else r["body"]
            }
            for r in rows
        ]
    except Exception as e:
        return [{
            "doc_id": "ERR",
            "title": "Search Query Note",
            "citation": "FTS5 Search Notice",
            "section": "Notice",
            "page_number": "N/A",
            "snippet": f"No matches found for query '{query_text}'. Error: {str(e)}"
        }]
