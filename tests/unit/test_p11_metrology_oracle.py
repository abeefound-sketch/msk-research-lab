"""P11 Metrological Oracle & Geometric Verification Test Suite.

Adversarially validates:
1. 6-DoF Levenberg-Marquardt PnP pose estimation against analytical ground truth.
2. Spatial covariance eigenvalues, planarity ratio, and condition number (DEF-32).
3. Brown-Conrady forward & backward lens distortion compensation (DEF-28).
4. Landmark noise sensitivity under Gaussian perturbation.
5. Strict fail-closed epistemic gating when calibration is absent.
"""

import math
import random
import pytest

from msk_research_lab.motion.calibration import (
    CameraIntrinsics,
    create_standard_intrinsics,
    distort_normalized_point,
    undistort_normalized_point,
)
from msk_research_lab.studio.calibrated_registration import (
    CANONICAL_FACIAL_3D_LANDMARKS,
    CalibratedRegistrationError,
    OpticalCalibrationContext,
    compute_landmark_spatial_conditioning,
    create_nominal_calibration_context,
    estimate_rigid_pose_from_landmarks,
    project_canonical_landmark,
    register_2d_reflexology_point_to_3d,
)
from msk_research_lab.studio.dien_chan import DienChanError, initialize_dien_chan_project


def test_spatial_conditioning_eigenvalues_and_coplanarity():
    """Verify DEF-32: 3D spatial covariance eigenvalues, condition number, and coplanarity ratio."""
    # 1. Non-coplanar canonical facial landmarks
    landmarks_3d = list(CANONICAL_FACIAL_3D_LANDMARKS.values())
    cond_num, planarity_ratio, evals = compute_landmark_spatial_conditioning(landmarks_3d)

    assert len(evals) == 3
    assert evals[0] >= evals[1] >= evals[2]
    assert evals[2] > 50.0  # Clear non-zero third dimension
    assert planarity_ratio > 0.05
    assert cond_num < 100.0  # Well conditioned 3D structure

    # 2. Perfectly coplanar landmarks (Z = 0)
    coplanar_pts = [
        (-50.0, -50.0, 0.0),
        (50.0, -50.0, 0.0),
        (50.0, 50.0, 0.0),
        (-50.0, 50.0, 0.0),
        (0.0, 0.0, 0.0),
    ]
    cop_cond, cop_planarity, cop_evals = compute_landmark_spatial_conditioning(coplanar_pts)
    assert cop_evals[2] < 1e-4
    assert cop_planarity < 1e-4
    assert cop_cond > 1e4  # High condition number / ill-conditioned depth


def test_distortion_compensation_roundtrip_oracle():
    """Verify DEF-28: Brown-Conrady forward distortion and inverse undistortion roundtrip."""
    k1 = -0.05
    k2 = 0.015
    p1 = 0.001
    p2 = -0.0008

    # Grid of normalized coordinates across typical sensor field
    for x in [-0.4, -0.2, 0.0, 0.2, 0.4]:
        for y in [-0.3, -0.1, 0.0, 0.1, 0.3]:
            xd, yd = distort_normalized_point(x, y, k1, k2, p1, p2)
            xu, yu = undistort_normalized_point(xd, yd, k1, k2, p1, p2, iterations=8)

            assert abs(xu - x) < 1e-5
            assert abs(yu - y) < 1e-5


def test_6dof_pnp_pose_estimation_and_distortion_accuracy():
    """Verify 6-DoF pose recovery from synthetic correspondence with lens distortion."""
    intrinsics = create_standard_intrinsics(
        width=1280, height=720, hfov_deg=65.0,
        k1=-0.04, k2=0.01, p1=0.001, p2=0.0005
    )

    # Use ground truth pose: distance 520 mm, yaw 5 deg, pitch -3 deg
    gt_context = create_nominal_calibration_context(
        intrinsics=intrinsics,
        yaw_deg=5.0,
        pitch_deg=-3.0,
        distance_mm=520.0,
    )

    # Generate synthetic 2D correspondences with distortion
    correspondences = []
    for name in ["SUBNASALE", "PRONASALE", "SELLION", "TRAGION_LEFT", "TRAGION_RIGHT", "GONION_LEFT", "GONION_RIGHT", "GNATHION"]:
        pt3 = CANONICAL_FACIAL_3D_LANDMARKS[name]
        u, v = project_canonical_landmark(name, gt_context)
        correspondences.append((pt3, (u, v)))

    # Estimate pose via Levenberg-Marquardt
    estimated = estimate_rigid_pose_from_landmarks(correspondences, intrinsics, max_allowed_residual_px=2.5)

    assert estimated.is_calibrated is True
    assert estimated.mean_reprojection_residual_px < 1.0
    assert estimated.spatial_condition_number < 100.0
    assert estimated.planarity_ratio > 0.05
    # Translation Z should be closely recovered
    assert abs(estimated.t[2] - 520.0) < 5.0


def test_monte_carlo_noise_perturbation_tolerance():
    """Stress test LM solver against zero-mean Gaussian landmark noise."""
    random.seed(42)
    intrinsics = create_standard_intrinsics(width=1280, height=720, hfov_deg=65.0)
    nominal = create_nominal_calibration_context(intrinsics=intrinsics, distance_mm=500.0)

    correspondences = []
    for name in ["SUBNASALE", "PRONASALE", "SELLION", "TRAGION_LEFT", "TRAGION_RIGHT", "GONION_LEFT", "GONION_RIGHT", "GNATHION"]:
        pt3 = CANONICAL_FACIAL_3D_LANDMARKS[name]
        u, v = project_canonical_landmark(name, nominal)
        # Add 0.5 pixel Gaussian noise
        u_noisy = u + random.gauss(0.0, 0.4)
        v_noisy = v + random.gauss(0.0, 0.4)
        correspondences.append((pt3, (u_noisy, v_noisy)))

    estimated = estimate_rigid_pose_from_landmarks(correspondences, intrinsics, max_allowed_residual_px=3.0)
    assert estimated.is_calibrated is True
    assert estimated.mean_reprojection_residual_px < 1.5


def test_calibrated_registration_with_distortion_compensation():
    """Verify 2D-to-3D registration applies lens distortion compensation and returns provenance."""
    intrinsics = create_standard_intrinsics(
        width=1280, height=720,
        k1=-0.04, k2=0.01, p1=0.001, p2=0.0005
    )
    context = create_nominal_calibration_context(intrinsics=intrinsics, distance_mm=500.0)

    # Project Subnasale to 2D
    u, v = project_canonical_landmark("SUBNASALE", context)

    # Register back to 3D
    reg = register_2d_reflexology_point_to_3d(
        point_id="dc_19_philtrum",
        pixel_xy=(u, v),
        calibration_context=context,
        target_model_id="watercmy_bp3d_z_anatomy",
        nearest_landmark_hint="SUBNASALE",
    )

    assert reg["status"] == "CALIBRATED_RESEARCH_REGISTRATION"
    assert reg["provenance_type"] == "SYNTHETIC_TEST"
    assert reg["spatial_condition_number"] >= 1.0
    assert "planarity_ratio" in reg
    # Recovered coordinate should match Subnasale (0.0, 0.0, 20.0) within 1.5 mm
    rec_x, rec_y, rec_z = reg["registered_3d_mm"]
    assert abs(rec_x - 0.0) < 1.5
    assert abs(rec_y - 0.0) < 1.5
    assert abs(rec_z - 20.0) < 1.5


def test_epistemic_inviolability_uncalibrated_fails_closed():
    """Verify that uncalibrated or absent context strictly triggers CANNOT_IMPLICITLY_PROJECT_2D_TO_3D."""
    with pytest.raises(DienChanError) as exc_info:
        register_2d_reflexology_point_to_3d(
            point_id="dc_0_ear",
            pixel_xy=(300.0, 400.0),
            calibration_context=None,
        )
    assert "CANNOT_IMPLICITLY_PROJECT_2D_TO_3D" in str(exc_info.value)
