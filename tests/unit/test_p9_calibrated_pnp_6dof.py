"""Verification tests for P9-D 6-DoF Levenberg-Marquardt PnP Pose Estimation and Calibrated Registration."""

import math
import pytest

from msk_research_lab.motion.calibration import create_standard_intrinsics
from msk_research_lab.studio.calibrated_registration import (
    CANONICAL_FACIAL_3D_LANDMARKS,
    CalibratedRegistrationError,
    create_nominal_calibration_context,
    estimate_rigid_pose_from_landmarks,
    project_canonical_landmark,
    register_2d_reflexology_point_to_3d,
)
from msk_research_lab.studio.dien_chan import DienChanError


def test_6dof_pnp_recovers_rotated_poses():
    """Verify 6-DoF Levenberg-Marquardt optimizer accurately recovers 3D rotation and translation."""
    K = create_standard_intrinsics(width=1280, height=720, hfov_deg=65.0)

    test_cases = [
        {"yaw": 20.0, "pitch": 0.0, "dist": 550.0},
        {"yaw": 0.0, "pitch": 15.0, "dist": 500.0},
        {"yaw": 15.0, "pitch": 10.0, "dist": 600.0},
    ]

    for tc in test_cases:
        ctx_gt = create_nominal_calibration_context(
            intrinsics=K,
            yaw_deg=tc["yaw"],
            pitch_deg=tc["pitch"],
            distance_mm=tc["dist"],
        )

        corrs = []
        for name in ["SUBNASALE", "SELLION", "PRONASALE", "TRAGION_LEFT", "TRAGION_RIGHT", "GNATHION"]:
            pt3 = CANONICAL_FACIAL_3D_LANDMARKS[name]
            pt2 = project_canonical_landmark(name, ctx_gt)
            corrs.append((pt3, pt2))

        # Solve 6-DoF pose via Levenberg-Marquardt
        solved_ctx = estimate_rigid_pose_from_landmarks(corrs, K, max_allowed_residual_px=1.5)

        assert solved_ctx.is_calibrated is True
        assert solved_ctx.max_reprojection_residual_px < 0.20  # Sub-pixel convergence
        assert solved_ctx.mean_reprojection_residual_px < 0.10

        # Verify recovered translation t_z is close to ground truth distance
        assert pytest.approx(tc["dist"], abs=5.0) == solved_ctx.t[2]


def test_6dof_pnp_residual_gating_rejects_corrupted_correspondence():
    """Verify solver fails closed when correspondences contain large landmark tracking error."""
    K = create_standard_intrinsics(width=1280, height=720)
    ctx = create_nominal_calibration_context(intrinsics=K, yaw_deg=10.0, pitch_deg=5.0, distance_mm=500.0)

    corrs = []
    for name in ["SUBNASALE", "SELLION", "TRAGION_LEFT", "TRAGION_RIGHT"]:
        pt3 = CANONICAL_FACIAL_3D_LANDMARKS[name]
        pt2 = project_canonical_landmark(name, ctx)
        corrs.append((pt3, pt2))

    # Introduce 20 px perturbation to Subnasale
    pt3_0, pt2_0 = corrs[0]
    corrs[0] = (pt3_0, (pt2_0[0] + 20.0, pt2_0[1] + 15.0))

    with pytest.raises(CalibratedRegistrationError) as exc_info:
        estimate_rigid_pose_from_landmarks(corrs, K, max_allowed_residual_px=3.0)

    assert "residual" in str(exc_info.value).lower()
    assert "exceeds tolerance" in str(exc_info.value).lower()


def test_epistemic_guard_cannot_implicitly_project_2d_to_3d():
    """Verify server-authoritative invariant: uncalibrated 2D cannot be converted to 3D."""
    with pytest.raises(DienChanError) as exc:
        register_2d_reflexology_point_to_3d(
            point_id="proj_dien_chan_standard_dc_19",
            pixel_xy=(300.0, 400.0),
            calibration_context=None,
            target_model_id="watercmy_bp3d_z_anatomy",
        )
    assert "CANNOT_IMPLICITLY_PROJECT_2D_TO_3D" in str(exc.value)


def test_minimal_landmark_count_validation():
    """Verify solver strictly enforces >= 4 correspondences."""
    K = create_standard_intrinsics(width=1280, height=720)
    corrs_3 = [
        (CANONICAL_FACIAL_3D_LANDMARKS["SUBNASALE"], (640.0, 360.0)),
        (CANONICAL_FACIAL_3D_LANDMARKS["SELLION"], (640.0, 320.0)),
        (CANONICAL_FACIAL_3D_LANDMARKS["GNATHION"], (640.0, 420.0)),
    ]
    with pytest.raises(CalibratedRegistrationError) as exc:
        estimate_rigid_pose_from_landmarks(corrs_3, K)
    assert "at least 4 non-coplanar landmarks" in str(exc.value)


def test_subnasale_huyet19_3d_registration_under_rotated_pose():
    """Verify calibrated reflexology registration under yaw 15 deg and pitch 10 deg."""
    K = create_standard_intrinsics(width=1280, height=720)
    ctx = create_nominal_calibration_context(intrinsics=K, yaw_deg=15.0, pitch_deg=10.0, distance_mm=520.0)

    # Subnasale 2D position under rotated pose
    px_19, py_19 = project_canonical_landmark("SUBNASALE", ctx)

    res = register_2d_reflexology_point_to_3d(
        point_id="proj_dien_chan_standard_dc_19",
        pixel_xy=(px_19, py_19),
        calibration_context=ctx,
        target_model_id="watercmy_bp3d_z_anatomy",
        nearest_landmark_hint="SUBNASALE",
    )

    assert res["status"] == "CALIBRATED_RESEARCH_REGISTRATION"
    assert res["point_id"] == "proj_dien_chan_standard_dc_19"
    # Huyệt 19 3D coordinates should match canonical Subnasale within 1.0 mm
    subnasale_gt = CANONICAL_FACIAL_3D_LANDMARKS["SUBNASALE"]
    reg_3d = res["registered_3d_mm"]

    assert pytest.approx(subnasale_gt[0], abs=1.0) == reg_3d[0]
    assert pytest.approx(subnasale_gt[1], abs=1.0) == reg_3d[1]
    assert pytest.approx(subnasale_gt[2], abs=1.0) == reg_3d[2]
