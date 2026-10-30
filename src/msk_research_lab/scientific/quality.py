"""Scientific Metrological Quality Decision Engine (DEF-36).

Provides standardized four-state measurement quality categorization:
- VALID: Passes all research tolerances and geometric sanity checks.
- DEGRADED: Usable for secondary research but with elevated uncertainty or minor confounders.
- REJECTED: Mathematically degenerate, corrupted, or exceeding tolerance thresholds.
- NOT_VERIFIED: Required hardware absent, missing input landmarks, or uncalibrated.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional


class MeasurementQualityDecision(str, Enum):
    """Rigorous metrological quality classification."""
    VALID = "VALID"
    DEGRADED = "DEGRADED"
    REJECTED = "REJECTED"
    NOT_VERIFIED = "NOT_VERIFIED"


def evaluate_kinematics_quality_decision(
    *,
    has_missing_landmarks: bool = False,
    is_degenerate: bool = False,
    tracking_confidence: float = 1.0,
    apparent_span_ratio: float = 1.0,
) -> Dict[str, Any]:
    """Evaluate 2D planar joint kinematics quality decision with explicit thresholds."""
    if has_missing_landmarks:
        return {
            "decision": MeasurementQualityDecision.NOT_VERIFIED.value,
            "justification": "Required anatomical landmark points missing from pose model.",
            "threshold_rules": "missing_landmarks == 0 required for verification",
        }

    if is_degenerate:
        return {
            "decision": MeasurementQualityDecision.REJECTED.value,
            "justification": "Degenerate zero-displacement vector between joint landmark vertices.",
            "threshold_rules": "vector_magnitude >= 1e-4 required",
        }

    # Tracking visibility threshold: 0.60; Torso yaw threshold: 0.85
    reasons = []
    if tracking_confidence < 0.60:
        reasons.append(f"Tracking confidence ({tracking_confidence:.2f}) < 0.60")
    if apparent_span_ratio < 0.85:
        reasons.append(f"Torso apparent span ratio ({apparent_span_ratio:.2f}) < 0.85 (out-of-plane yaw > 15 deg)")

    if reasons:
        return {
            "decision": MeasurementQualityDecision.DEGRADED.value,
            "justification": f"Degraded accuracy due to: {'; '.join(reasons)}.",
            "threshold_rules": "tracking_confidence >= 0.60 AND apparent_span_ratio >= 0.85 for VALID",
        }

    return {
        "decision": MeasurementQualityDecision.VALID.value,
        "justification": "All anatomical landmarks detected with nominal confidence and planar orientation.",
        "threshold_rules": "tracking_confidence >= 0.60 AND apparent_span_ratio >= 0.85",
    }


def evaluate_optical_registration_decision(
    *,
    is_calibrated: bool,
    max_residual_px: float,
    spatial_condition_number: float = 1.0,
    planarity_ratio: float = 0.5,
) -> Dict[str, Any]:
    """Evaluate 2D-to-3D optical registration quality decision with explicit thresholds."""
    if not is_calibrated:
        return {
            "decision": MeasurementQualityDecision.NOT_VERIFIED.value,
            "justification": "Epistemic guard active: uncalibrated optical context cannot project 2D to 3D.",
            "threshold_rules": "is_calibrated == True required",
        }

    if max_residual_px > 3.0:
        return {
            "decision": MeasurementQualityDecision.REJECTED.value,
            "justification": f"Maximum reprojection residual ({max_residual_px:.2f} px) exceeds rejection threshold (3.0 px).",
            "threshold_rules": "max_residual_px <= 3.0 required",
        }

    reasons = []
    if max_residual_px > 1.5:
        reasons.append(f"Reprojection residual ({max_residual_px:.2f} px) in marginal zone (1.5 - 3.0 px)")
    if spatial_condition_number > 500.0:
        reasons.append(f"Spatial condition number ({spatial_condition_number:.1f}) > 500.0 (near-degenerate depth)")
    if planarity_ratio < 0.01:
        reasons.append(f"Planarity ratio ({planarity_ratio:.4f}) < 0.01 (near-coplanar landmark ambiguity)")

    if reasons:
        return {
            "decision": MeasurementQualityDecision.DEGRADED.value,
            "justification": f"Marginal registration quality: {'; '.join(reasons)}.",
            "threshold_rules": "max_residual <= 1.5 px AND condition_number <= 500 AND planarity >= 0.01 for VALID",
        }

    return {
        "decision": MeasurementQualityDecision.VALID.value,
        "justification": "Low reprojection error and healthy 3D landmark spatial distribution.",
        "threshold_rules": "max_residual <= 1.5 px AND condition_number <= 500 AND planarity >= 0.01",
    }


def evaluate_stereo_triangulation_decision(
    *,
    hardware_available: bool,
    max_reprojection_error_px: float,
    baseline_mm: float,
) -> Dict[str, Any]:
    """Evaluate stereo triangulation measurement quality decision."""
    if not hardware_available:
        return {
            "decision": MeasurementQualityDecision.NOT_VERIFIED.value,
            "justification": "Physical dual-camera stereo hardware unavailable in active runtime environment.",
            "threshold_rules": "hardware_available == True required for live verification",
        }

    if max_reprojection_error_px > 2.5:
        return {
            "decision": MeasurementQualityDecision.REJECTED.value,
            "justification": f"Triangulation reprojection error ({max_reprojection_error_px:.2f} px) exceeds 2.5 px tolerance.",
            "threshold_rules": "max_reprojection_error_px <= 2.5 required",
        }

    if max_reprojection_error_px > 1.5 or baseline_mm < 50.0:
        return {
            "decision": MeasurementQualityDecision.DEGRADED.value,
            "justification": "Elevated triangulation residual or narrow optical baseline.",
            "threshold_rules": "max_reprojection_error <= 1.5 px AND baseline >= 50 mm for VALID",
        }

    return {
        "decision": MeasurementQualityDecision.VALID.value,
        "justification": "High-precision dual-camera triangulation within sub-pixel bounds.",
        "threshold_rules": "max_reprojection_error <= 1.5 px AND baseline >= 50 mm",
    }
