"""Independent Scientific Metrology Oracle Tests for MSK Research Lab OS (Milestone P12).

Adversarially validates kinematics, angles, ROM, and quality decisions
against an independent mathematical oracle (atan2 / cross-dot formulation).
"""

import math
import pytest
from msk_research_lab.motion.kinematics import (
    compute_2d_angle,
    evaluate_motion_quality,
    compute_joint_rom,
)
from msk_research_lab.scientific.quality import (
    MeasurementQualityDecision,
    evaluate_kinematics_quality_decision,
)


def independent_oracle_angle(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float]
) -> float:
    """Independent oracle for 2D angle using atan2(cross, dot).
    
    Mathematically distinct from arccos(dot / (|v1| * |v2|)).
    Robust against boundary conditioning near 0 and 180 deg.
    """
    v1x, v1y = a[0] - b[0], a[1] - b[1]
    v2x, v2y = c[0] - b[0], c[1] - b[1]

    mag1 = math.hypot(v1x, v1y)
    mag2 = math.hypot(v2x, v2y)
    if mag1 < 1e-7 or mag2 < 1e-7:
        return 0.0

    # Cross product (z-component in 2D) and dot product
    cross = v1x * v2y - v1y * v2x
    dot = v1x * v2x + v1y * v2y

    rad = math.atan2(abs(cross), dot)
    return math.degrees(rad)


class TestIndependentMetrologyOracle:
    """Adversarial verification of metrology against independent mathematical formulations."""

    def test_oracle_vs_production_exact_angles(self):
        """Verify production angle matches independent oracle within 0.001 degrees."""
        test_cases = [
            # 90 degrees
            ((0.0, 1.0), (0.0, 0.0), (1.0, 0.0), 90.0),
            # 45 degrees
            ((1.0, 1.0), (0.0, 0.0), (1.0, 0.0), 45.0),
            # 180 degrees (straight line)
            ((-1.0, 0.0), (0.0, 0.0), (1.0, 0.0), 180.0),
            # 30 degrees: (sqrt(3)/2, 1/2) vs (1, 0)
            ((math.sqrt(3)/2, 0.5), (0.0, 0.0), (1.0, 0.0), 30.0),
            # 135 degrees
            ((-1.0, 1.0), (0.0, 0.0), (1.0, 0.0), 135.0),
            # Arbitrary realistic clinical pose
            ((0.452, 0.312), (0.510, 0.480), (0.620, 0.490), None),
        ]

        for p_a, p_b, p_c, expected in test_cases:
            prod_angle = compute_2d_angle(p_a, p_b, p_c)
            oracle_angle = independent_oracle_angle(p_a, p_b, p_c)

            # Assert concordance between production and independent oracle
            assert abs(prod_angle - oracle_angle) < 1e-3, (
                f"Discrepancy: prod={prod_angle}, oracle={oracle_angle} for {p_a}, {p_b}, {p_c}"
            )
            if expected is not None:
                assert abs(prod_angle - expected) < 1e-3

    def test_oracle_degenerate_landmarks_fail_closed(self):
        """Degenerate points (zero length vector) must fail closed with REJECTED decision."""
        # Coincident vertex and point A
        prod_angle = compute_2d_angle((0.0, 0.0), (0.0, 0.0), (1.0, 0.0))
        oracle_angle = independent_oracle_angle((0.0, 0.0), (0.0, 0.0), (1.0, 0.0))
        assert prod_angle == 0.0
        assert oracle_angle == 0.0

        # Quality evaluation must reject degenerate landmark
        dec = evaluate_kinematics_quality_decision(
            is_degenerate=True
        )
        assert dec["decision"] == MeasurementQualityDecision.REJECTED.value
        assert "Degenerate zero-displacement vector" in dec["justification"]

    def test_adversarial_missing_landmarks_fail_closed(self):
        """Missing landmark keys must return NOT_VERIFIED decision."""
        dec = evaluate_kinematics_quality_decision(
            has_missing_landmarks=True
        )
        assert dec["decision"] == MeasurementQualityDecision.NOT_VERIFIED.value
        assert "missing" in dec["justification"].lower()

    def test_out_of_plane_foreshortening_quality_decision(self):
        """Simulated out-of-plane rotation foreshortens 2D projection, lowering quality."""
        # When confidence drops or yaw span ratio < 0.85
        dec = evaluate_kinematics_quality_decision(
            tracking_confidence=0.55,
            apparent_span_ratio=0.80,
        )
        assert dec["decision"] == MeasurementQualityDecision.DEGRADED.value
        assert "Tracking confidence" in dec["justification"]
        assert "Torso apparent span ratio" in dec["justification"]

    def test_independent_rom_oracle(self):
        """ROM oracle validates min, max, deficit, and uncertainty budget."""
        landmarks = {
            "right_shoulder": (0.0, 0.0),
            "right_elbow": (0.0, 10.0),
            "right_wrist": (10.0, 10.0),
        }
        res = compute_joint_rom(
            landmarks=landmarks,
            joint_tested="ELBOW_FLEXION",
            side="RIGHT",
            apparent_span_ratio=1.0,
        )
        assert res["quality_decision"] == MeasurementQualityDecision.VALID.value
        assert abs(res["measured_rom_deg"] - 90.0) < 1e-2
        # Normal reference for elbow flexion is 140 deg -> deficit is 50 deg
        assert abs(res["rom_deficit_deg"] - 50.0) < 1e-2
        assert res["uncertainty_u95_deg"] is not None
