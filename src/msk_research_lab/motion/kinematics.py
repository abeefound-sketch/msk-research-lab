"""Planar Joint Kinematics and Measurement Quality Engine with GUM Uncertainty."""

import math
from typing import Dict, List, Tuple, Optional, Any

from msk_research_lab.scientific.quality import (
    MeasurementQualityDecision,
    evaluate_kinematics_quality_decision,
)

NORMAL_ROM_REFERENCES = {
    "ELBOW_FLEXION": 140.0,
    "SHOULDER_ABDUCTION": 160.0,
    "SHOULDER_ELEVATION": 160.0,
    "KNEE_FLEXION": 135.0
}


def _get_point_xy(pt: Any) -> Tuple[float, float]:
    """Extract (x, y) coordinates from tuple, list, or MediaPipe dictionary."""
    if isinstance(pt, dict):
        return (float(pt.get("x", 0.0)), float(pt.get("y", 0.0)))
    if isinstance(pt, (list, tuple)) and len(pt) >= 2:
        return (float(pt[0]), float(pt[1]))
    return (0.0, 0.0)


def compute_2d_angle(
    a: Any,
    b: Any,
    c: Any
) -> float:
    """
    Calculate 2D planar angle at vertex b between vectors (a -> b) and (c -> b).
    Uses clamp [-1.0, 1.0] to avoid acos numerical domain errors.
    """
    pa = _get_point_xy(a)
    pb = _get_point_xy(b)
    pc = _get_point_xy(c)

    v1 = (pa[0] - pb[0], pa[1] - pb[1])
    v2 = (pc[0] - pb[0], pc[1] - pb[1])

    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(v1[0], v1[1])
    mag2 = math.hypot(v2[0], v2[1])

    if mag1 < 1e-6 or mag2 < 1e-6:
        return 0.0

    cos_val = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    angle_rad = math.acos(cos_val)
    return math.degrees(angle_rad)


def evaluate_motion_quality(
    landmarks: Dict[str, Tuple[float, float]],
    joint_tested: str,
    side: str = "RIGHT",
    apparent_span_ratio: float = 1.0,
    visibility_scores: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Evaluate biomechanical measurement quality, confounders, and GUM uncertainty budget.
    """
    warnings: List[str] = []
    confounders: List[str] = []
    quality_status = "OPTIMAL"

    vis_scores = visibility_scores or {}
    avg_visibility = (
        sum(vis_scores.values()) / len(vis_scores) if vis_scores else 1.0
    )

    if avg_visibility < 0.60:
        quality_status = "DEGRADED"
        warnings.append("LOW_LANDMARK_VISIBILITY: Average tracking confidence below 0.60.")

    # Confounder 1: Out-of-plane yaw
    if apparent_span_ratio < 0.85:
        if quality_status == "OPTIMAL":
            quality_status = "DEGRADED"
        warnings.append("EXCESSIVE_TORSO_YAW: Suspected out-of-plane torso rotation > 15 deg.")

    # Confounder 2: Humeral elevation altering deltoid contour
    # Check if elbow is higher in frame (smaller y in normalized coords) than shoulder
    shoulder_key = f"{side.lower()}_shoulder"
    elbow_key = f"{side.lower()}_elbow"
    if shoulder_key in landmarks and elbow_key in landmarks:
        sh_y = _get_point_xy(landmarks[shoulder_key])[1]
        el_y = _get_point_xy(landmarks[elbow_key])[1]
        if el_y < sh_y:  # Elbow elevated above shoulder
            confounders.append("HUMERAL_ELEVATION_CONFOUNDER")
            warnings.append(
                "Active humeral elevation alters deltoid surface contour; shoulder span yaw estimate is confounded."
            )

    # GUM Uncertainty Budget (ISO/IEC Guide 98-3)
    # Combined standard uncertainty components:
    u_resolution = 0.5   # Camera spatial quantization
    u_operator = 0.8     # Pose jitter / operator variation
    u_yaw = 1.5 if apparent_span_ratio < 0.85 else 0.4
    u_combined = math.sqrt(u_resolution**2 + u_operator**2 + u_yaw**2)

    coverage_factor_k = 1.96  # 95% confidence level
    expanded_uncertainty_u95 = round(coverage_factor_k * u_combined, 2)

    q_dec = evaluate_kinematics_quality_decision(
        has_missing_landmarks=False,
        is_degenerate=False,
        tracking_confidence=round(avg_visibility, 3),
        apparent_span_ratio=apparent_span_ratio,
    )

    return {
        "quality_status": quality_status,
        "quality_decision": q_dec["decision"],
        "quality_justification": q_dec["justification"],
        "warnings": warnings,
        "confounding_factors": confounders,
        "tracking_confidence": round(avg_visibility, 3),
        "uncertainty_budget": {
            "combined_standard_uncertainty_deg": round(u_combined, 2),
            "coverage_factor_k": coverage_factor_k,
            "expanded_uncertainty_u95_deg": expanded_uncertainty_u95,
            "distributional_assumption": "GAUSSIAN_ASYMPTOTIC_NORMAL"
        }
    }


REQUIRED_LANDMARKS = {
    "ELBOW_FLEXION": ("shoulder", "elbow", "wrist"),
    "SHOULDER_ABDUCTION": ("hip", "shoulder", "elbow"),
    "SHOULDER_ELEVATION": ("hip", "shoulder", "elbow"),
    "KNEE_FLEXION": ("hip", "knee", "ankle")
}


def compute_joint_rom(
    landmarks: Dict[str, Tuple[float, float]],
    joint_tested: str,
    side: str = "RIGHT",
    visibility_scores: Optional[Dict[str, float]] = None,
    apparent_span_ratio: Optional[float] = None
) -> Dict[str, Any]:
    """
    Compute joint ROM angle, reference comparison, deficit, and uncertainty budget.
    Fails closed when required anatomical landmarks are missing or degenerate.
    """
    s = side.lower()
    ref_rom = NORMAL_ROM_REFERENCES.get(joint_tested, 140.0)

    # 1. Landmark completeness validation
    req_parts = REQUIRED_LANDMARKS.get(joint_tested, ("shoulder", "elbow", "wrist"))
    req_keys = [f"{s}_{part}" for part in req_parts]
    missing = [k for k in req_keys if k not in landmarks or landmarks[k] is None]

    if missing:
        q_dec = evaluate_kinematics_quality_decision(has_missing_landmarks=True)
        return {
            "joint_tested": joint_tested,
            "side": side,
            "measured_rom_deg": None,
            "reference_rom_deg": ref_rom,
            "rom_deficit_deg": None,
            "uncertainty_u95_deg": None,
            "tracking_confidence": 0.0,
            "quality_status": "INSUFFICIENT_DATA",
            "quality_decision": q_dec["decision"],
            "quality_justification": q_dec["justification"],
            "warnings": [f"MISSING_LANDMARK: Required key '{k}' missing from pose tracking." for k in missing],
            "confounding_factors": ["INCOMPLETE_LANDMARK_SET"],
            "uncertainty_budget": {
                "combined_standard_uncertainty_deg": None,
                "coverage_factor_k": 1.96,
                "expanded_uncertainty_u95_deg": None,
                "distributional_assumption": "UNCERTAINTY_NOT_VALIDATED"
            },
            "clinical_disclaimer": "2D planar camera estimate only. NOT validated for surgical or orthopedic diagnostic decisions."
        }

    pt_a = _get_point_xy(landmarks[req_keys[0]])
    pt_b = _get_point_xy(landmarks[req_keys[1]])
    pt_c = _get_point_xy(landmarks[req_keys[2]])

    # 2. Degenerate vector check
    v1 = (pt_a[0] - pt_b[0], pt_a[1] - pt_b[1])
    v2 = (pt_c[0] - pt_b[0], pt_c[1] - pt_b[1])
    mag1 = math.hypot(v1[0], v1[1])
    mag2 = math.hypot(v2[0], v2[1])

    if mag1 < 1e-4 or mag2 < 1e-4:
        q_dec = evaluate_kinematics_quality_decision(is_degenerate=True)
        return {
            "joint_tested": joint_tested,
            "side": side,
            "measured_rom_deg": None,
            "reference_rom_deg": ref_rom,
            "rom_deficit_deg": None,
            "uncertainty_u95_deg": None,
            "tracking_confidence": 0.0,
            "quality_status": "DEGENERATE_GEOMETRY",
            "quality_decision": q_dec["decision"],
            "quality_justification": q_dec["justification"],
            "warnings": ["DEGENERATE_VECTORS: Landmark coordinates have zero displacement between adjacent joint points."],
            "confounding_factors": ["DEGENERATE_GEOMETRY"],
            "uncertainty_budget": {
                "combined_standard_uncertainty_deg": None,
                "coverage_factor_k": 1.96,
                "expanded_uncertainty_u95_deg": None,
                "distributional_assumption": "UNCERTAINTY_NOT_VALIDATED"
            },
            "clinical_disclaimer": "2D planar camera estimate only. NOT validated for surgical or orthopedic diagnostic decisions."
        }

    measured_angle = compute_2d_angle(pt_a, pt_b, pt_c)
    deficit = max(0.0, ref_rom - measured_angle)
    span_ratio = apparent_span_ratio if apparent_span_ratio is not None else 1.0

    quality = evaluate_motion_quality(
        landmarks=landmarks,
        joint_tested=joint_tested,
        side=side,
        apparent_span_ratio=span_ratio,
        visibility_scores=visibility_scores
    )

    if apparent_span_ratio is None:
        quality["confounding_factors"].append("UNCALIBRATED_YAW")

    q_dec = evaluate_kinematics_quality_decision(
        has_missing_landmarks=False,
        is_degenerate=False,
        tracking_confidence=quality["tracking_confidence"],
        apparent_span_ratio=span_ratio,
    )

    return {
        "joint_tested": joint_tested,
        "side": side,
        "measured_rom_deg": round(measured_angle, 2),
        "reference_rom_deg": ref_rom,
        "rom_deficit_deg": round(deficit, 2),
        "uncertainty_u95_deg": quality["uncertainty_budget"]["expanded_uncertainty_u95_deg"],
        "tracking_confidence": quality["tracking_confidence"],
        "quality_status": quality["quality_status"],
        "quality_decision": q_dec["decision"],
        "quality_justification": q_dec["justification"],
        "warnings": quality["warnings"],
        "confounding_factors": quality["confounding_factors"],
        "uncertainty_budget": quality["uncertainty_budget"],
        "clinical_disclaimer": "2D planar camera estimate only. NOT validated for surgical or orthopedic diagnostic decisions."
    }
