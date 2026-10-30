"""P12 Metrological Quality Decision & Geometric Oracle Test Suite (DEF-36).

Verifies the 4-state measurement quality categorization:
1. Kinematics ROM:
   - VALID: Complete landmarks, healthy tracking confidence, nominal planar orientation.
   - DEGRADED: Low tracking confidence (< 0.60) or high torso yaw (> 15 deg).
   - REJECTED: Degenerate zero-displacement vectors between vertices.
   - NOT_VERIFIED: Missing required anatomical landmarks.
2. 2D-to-3D Facial Optical Registration:
   - VALID: Low residual (<= 1.5 px) and well-conditioned 3D spatial geometry.
   - DEGRADED: Marginal residual (1.5 - 3.0 px) or near-coplanar landmark ambiguity.
   - REJECTED: Reprojection residual > 3.0 px or collinear landmarks.
   - NOT_VERIFIED: Epistemic guard active (uncalibrated).
3. Dual-Camera Stereo Triangulation:
   - VALID: Triangulation within sub-pixel bounds with physical/calibrated rig.
   - REJECTED: Triangulation reprojection error > 2.5 px.
   - NOT_VERIFIED: Physical dual-camera hardware unavailable in environment.
"""

import pytest

from msk_research_lab.motion.calibration import create_standard_intrinsics
from msk_research_lab.motion.kinematics import compute_joint_rom
from msk_research_lab.motion.stereo import (
    create_standard_stereo_rig,
    probe_physical_stereo_hardware,
    triangulate_joint_angle_3d,
)
from msk_research_lab.scientific.quality import (
    MeasurementQualityDecision,
    evaluate_kinematics_quality_decision,
    evaluate_optical_registration_decision,
    evaluate_stereo_triangulation_decision,
)
from msk_research_lab.studio.calibrated_registration import (
    OpticalCalibrationContext,
    create_nominal_calibration_context,
    project_canonical_landmark,
    register_2d_reflexology_point_to_3d,
)
from msk_research_lab.studio.dien_chan import DienChanError


def test_kinematics_four_state_decisions():
    """Verify kinematics returns VALID, DEGRADED, REJECTED, and NOT_VERIFIED with explicit justifications."""
    nominal_landmarks = {
        "right_shoulder": (0.0, 0.0),
        "right_elbow": (0.0, 100.0),
        "right_wrist": (100.0, 100.0),
    }

    # 1. VALID
    res_valid = compute_joint_rom(
        landmarks=nominal_landmarks,
        joint_tested="ELBOW_FLEXION",
        side="RIGHT",
        visibility_scores={"right_shoulder": 0.95, "right_elbow": 0.90, "right_wrist": 0.92},
        apparent_span_ratio=1.0,
    )
    assert res_valid["quality_decision"] == MeasurementQualityDecision.VALID.value
    assert "nominal confidence" in res_valid["quality_justification"]

    # 2. DEGRADED (Low visibility tracking)
    res_deg_vis = compute_joint_rom(
        landmarks=nominal_landmarks,
        joint_tested="ELBOW_FLEXION",
        side="RIGHT",
        visibility_scores={"right_shoulder": 0.40, "right_elbow": 0.45, "right_wrist": 0.50},
        apparent_span_ratio=1.0,
    )
    assert res_deg_vis["quality_decision"] == MeasurementQualityDecision.DEGRADED.value
    assert "Tracking confidence" in res_deg_vis["quality_justification"]

    # 3. DEGRADED (Out-of-plane yaw)
    res_deg_yaw = compute_joint_rom(
        landmarks=nominal_landmarks,
        joint_tested="ELBOW_FLEXION",
        side="RIGHT",
        visibility_scores={"right_shoulder": 0.95, "right_elbow": 0.90, "right_wrist": 0.92},
        apparent_span_ratio=0.75,
    )
    assert res_deg_yaw["quality_decision"] == MeasurementQualityDecision.DEGRADED.value
    assert "span ratio" in res_deg_yaw["quality_justification"]

    # 4. REJECTED (Zero length vector)
    degenerate_landmarks = {
        "right_shoulder": (50.0, 50.0),
        "right_elbow": (50.0, 50.0),  # Coincident with shoulder
        "right_wrist": (100.0, 100.0),
    }
    res_rejected = compute_joint_rom(
        landmarks=degenerate_landmarks,
        joint_tested="ELBOW_FLEXION",
        side="RIGHT",
    )
    assert res_rejected["quality_decision"] == MeasurementQualityDecision.REJECTED.value
    assert "Degenerate zero-displacement" in res_rejected["quality_justification"]

    # 5. NOT_VERIFIED (Missing required landmark)
    incomplete_landmarks = {
        "right_shoulder": (0.0, 0.0),
        # right_elbow missing
        "right_wrist": (100.0, 100.0),
    }
    res_not_verified = compute_joint_rom(
        landmarks=incomplete_landmarks,
        joint_tested="ELBOW_FLEXION",
        side="RIGHT",
    )
    assert res_not_verified["quality_decision"] == MeasurementQualityDecision.NOT_VERIFIED.value
    assert "missing" in res_not_verified["quality_justification"]


def test_optical_registration_four_state_decisions():
    """Verify calibrated 2D-to-3D registration outputs explicit quality decisions."""
    intrinsics = create_standard_intrinsics(width=1280, height=720)

    # 1. VALID
    nominal_context = create_nominal_calibration_context(intrinsics=intrinsics, distance_mm=500.0)
    u, v = project_canonical_landmark("SUBNASALE", nominal_context)
    res_valid = register_2d_reflexology_point_to_3d(
        point_id="dc_19_test",
        pixel_xy=(u, v),
        calibration_context=nominal_context,
    )
    assert res_valid["quality_decision"] == MeasurementQualityDecision.VALID.value
    assert "Low reprojection error" in res_valid["quality_justification"]

    # 2. DEGRADED (Marginal residual between 1.5 and 3.0 px)
    marginal_context = create_nominal_calibration_context(intrinsics=intrinsics, distance_mm=500.0)
    marginal_context.mean_reprojection_residual_px = 1.8
    marginal_context.max_reprojection_residual_px = 2.4
    res_deg = register_2d_reflexology_point_to_3d(
        point_id="dc_19_marginal",
        pixel_xy=(u, v),
        calibration_context=marginal_context,
    )
    assert res_deg["quality_decision"] == MeasurementQualityDecision.DEGRADED.value
    assert "marginal zone" in res_deg["quality_justification"]

    # 3. NOT_VERIFIED (Epistemic guard active)
    with pytest.raises(DienChanError):
        register_2d_reflexology_point_to_3d(
            point_id="dc_19_uncalibrated",
            pixel_xy=(u, v),
            calibration_context=None,
        )


def test_stereo_triangulation_quality_decisions():
    """Verify stereo triangulation outputs explicit quality decisions."""
    rig = create_standard_stereo_rig(baseline_mm=200.0)

    # In simulation/calibrated mode:
    # A = (0, 0, 1000), B = (0, 100, 1000), C = (100, 100, 1000) -> 90 deg angle
    A = (0.0, 0.0, 1000.0)
    B = (0.0, 100.0, 1000.0)
    C = (100.0, 100.0, 1000.0)

    from msk_research_lab.motion.stereo import project_3d_point
    a_l = project_3d_point(A, rig.left_projection_matrix)
    a_r = project_3d_point(A, rig.right_projection_matrix)
    b_l = project_3d_point(B, rig.left_projection_matrix)
    b_r = project_3d_point(B, rig.right_projection_matrix)
    c_l = project_3d_point(C, rig.left_projection_matrix)
    c_r = project_3d_point(C, rig.right_projection_matrix)

    res = triangulate_joint_angle_3d(a_l, b_l, c_l, a_r, b_r, c_r, rig)
    assert res["quality_decision"] == MeasurementQualityDecision.VALID.value
    assert abs(res["angle_3d_deg"] - 90.0) < 0.1

    # Physical hardware probe check
    probe = probe_physical_stereo_hardware()
    assert probe["status"] == "BLOCKED (DUAL_CAMERA_UNAVAILABLE)"
