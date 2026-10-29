"""Planar Joint Kinematics and Measurement Quality Engine with GUM Uncertainty."""

import math
from typing import Dict, List, Tuple, Optional, Any

NORMAL_ROM_REFERENCES = {
    "ELBOW_FLEXION": 140.0,
    "SHOULDER_ABDUCTION": 160.0,
    "SHOULDER_ELEVATION": 160.0,
    "KNEE_FLEXION": 135.0
}


def compute_2d_angle(
    a: Tuple[float, float],
    b: Tuple[float, float],
    c: Tuple[float, float]
) -> float:
    """
    Calculate 2D planar angle at vertex b between vectors (a -> b) and (c -> b).
    Uses clamp [-1.0, 1.0] to avoid acos numerical domain errors.
    """
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])

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
        sh_y = landmarks[shoulder_key][1]
        el_y = landmarks[elbow_key][1]
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

    return {
        "quality_status": quality_status,
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


def compute_joint_rom(
    landmarks: Dict[str, Tuple[float, float]],
    joint_tested: str,
    side: str = "RIGHT",
    visibility_scores: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Compute joint ROM angle, reference comparison, deficit, and uncertainty budget.
    """
    s = side.lower()
    measured_angle = 0.0

    if joint_tested == "ELBOW_FLEXION":
        sh = landmarks.get(f"{s}_shoulder", (0.0, 0.0))
        el = landmarks.get(f"{s}_elbow", (0.0, 0.0))
        wr = landmarks.get(f"{s}_wrist", (0.0, 0.0))
        measured_angle = compute_2d_angle(sh, el, wr)
    elif joint_tested in ("SHOULDER_ABDUCTION", "SHOULDER_ELEVATION"):
        hip = landmarks.get(f"{s}_hip", (0.0, 0.0))
        sh = landmarks.get(f"{s}_shoulder", (0.0, 0.0))
        el = landmarks.get(f"{s}_elbow", (0.0, 0.0))
        measured_angle = compute_2d_angle(hip, sh, el)
    elif joint_tested == "KNEE_FLEXION":
        hip = landmarks.get(f"{s}_hip", (0.0, 0.0))
        knee = landmarks.get(f"{s}_knee", (0.0, 0.0))
        ank = landmarks.get(f"{s}_ankle", (0.0, 0.0))
        measured_angle = compute_2d_angle(hip, knee, ank)
    else:
        # Generic angle fallback
        sh = landmarks.get(f"{s}_shoulder", (0.0, 0.0))
        el = landmarks.get(f"{s}_elbow", (0.0, 0.0))
        wr = landmarks.get(f"{s}_wrist", (0.0, 0.0))
        measured_angle = compute_2d_angle(sh, el, wr)

    ref_rom = NORMAL_ROM_REFERENCES.get(joint_tested, 140.0)
    deficit = max(0.0, ref_rom - measured_angle)

    quality = evaluate_motion_quality(
        landmarks=landmarks,
        joint_tested=joint_tested,
        side=side,
        apparent_span_ratio=1.0,
        visibility_scores=visibility_scores
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
        "warnings": quality["warnings"],
        "confounding_factors": quality["confounding_factors"],
        "uncertainty_budget": quality["uncertainty_budget"],
        "clinical_disclaimer": "2D planar camera estimate only. NOT validated for surgical or orthopedic diagnostic decisions."
    }
