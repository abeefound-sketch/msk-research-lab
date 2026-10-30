"""Unit tests for Calibrated 2D/3D Facial Reflexology Registration and Epistemic Invariants."""

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
from msk_research_lab.studio.dien_chan import DienChanError, initialize_dien_chan_project


def test_canonical_facial_landmarks_topology():
    """Verify presence and symmetry of canonical 3D facial landmarks."""
    assert "SUBNASALE" in CANONICAL_FACIAL_3D_LANDMARKS
    assert "PRONASALE" in CANONICAL_FACIAL_3D_LANDMARKS
    assert "TRAGION_LEFT" in CANONICAL_FACIAL_3D_LANDMARKS
    assert "TRAGION_RIGHT" in CANONICAL_FACIAL_3D_LANDMARKS

    # Check bilateral symmetry: Tragion X-coordinates should be equal and opposite
    t_left = CANONICAL_FACIAL_3D_LANDMARKS["TRAGION_LEFT"]
    t_right = CANONICAL_FACIAL_3D_LANDMARKS["TRAGION_RIGHT"]
    assert pytest.approx(-t_left[0], abs=1e-3) == t_right[0]
    assert pytest.approx(t_left[1], abs=1e-3) == t_right[1]
    assert pytest.approx(t_left[2], abs=1e-3) == t_right[2]


def test_project_canonical_landmark_validity():
    """Verify calibrated projection maps 3D coordinates into sensor viewport."""
    ctx = create_nominal_calibration_context(distance_mm=600.0)
    px, py = project_canonical_landmark("SUBNASALE", ctx)

    # Subnasale at X=0 should project close to camera principal center cx
    assert pytest.approx(ctx.intrinsics.cx, abs=5.0) == px
    # py should be within sensor height [0, 720]
    assert 0.0 < py < 720.0


def test_estimate_rigid_pose_residual_gating():
    """Verify pose estimation accepts tight correspondences and rejects noisy inputs."""
    K = create_standard_intrinsics(width=1280, height=720)
    ctx = create_nominal_calibration_context(intrinsics=K, distance_mm=500.0)

    # Generate synthetic noise-free correspondences
    corrs = []
    for name in ["SUBNASALE", "SELLION", "TRAGION_LEFT", "TRAGION_RIGHT", "GNATHION"]:
        pt3 = CANONICAL_FACIAL_3D_LANDMARKS[name]
        pt2 = project_canonical_landmark(name, ctx)
        corrs.append((pt3, pt2))

    # Pose estimation on valid correspondences
    est_ctx = estimate_rigid_pose_from_landmarks(corrs, K, max_allowed_residual_px=3.0)
    assert est_ctx.is_calibrated is True
    assert est_ctx.max_reprojection_residual_px < 2.0

    # Corrupt one landmark by 25 pixels
    corrs_corrupted = list(corrs)
    pt3_corrupt, pt2_corrupt = corrs_corrupted[0]
    corrs_corrupted[0] = (pt3_corrupt, (pt2_corrupt[0] + 25.0, pt2_corrupt[1] + 15.0))

    with pytest.raises(CalibratedRegistrationError) as exc_info:
        estimate_rigid_pose_from_landmarks(corrs_corrupted, K, max_allowed_residual_px=3.0)

    assert "residual" in str(exc_info.value).lower()
    assert "exceeds tolerance" in str(exc_info.value).lower()


def test_epistemic_guard_strictly_enforced_without_calibration():
    """Verify CANNOT_IMPLICITLY_PROJECT_2D_TO_3D invariant fails closed when calibration is absent."""
    # Attempting registration with calibration_context = None MUST raise DienChanError
    with pytest.raises(DienChanError) as exc_info:
        register_2d_reflexology_point_to_3d(
            point_id="proj_dien_chan_standard_dc_19",
            pixel_xy=(250.0, 310.0),
            calibration_context=None,
            target_model_id="watercmy_bp3d_z_anatomy",
        )

    assert "CANNOT_IMPLICITLY_PROJECT_2D_TO_3D" in str(exc_info.value)


def test_calibrated_reflexology_point_registration_success():
    """Verify calibrated registration produces genuine 3D coordinates with uncertainty radius."""
    K = create_standard_intrinsics(width=1280, height=720)
    ctx = create_nominal_calibration_context(intrinsics=K, distance_mm=550.0)

    # Project Huyệt 19 (Subnasale) to 2D
    px_subnasale, py_subnasale = project_canonical_landmark("SUBNASALE", ctx)

    # Register 2D pixel to 3D head model
    res = register_2d_reflexology_point_to_3d(
        point_id="proj_dien_chan_standard_dc_19",
        pixel_xy=(px_subnasale, py_subnasale),
        calibration_context=ctx,
        target_model_id="watercmy_bp3d_z_anatomy",
        nearest_landmark_hint="SUBNASALE",
    )

    assert res["status"] == "CALIBRATED_RESEARCH_REGISTRATION"
    assert res["epistemic_provenance"] == "RIGID_OPTICAL_CALIBRATION_RESEARCH_ONLY"
    assert res["clinical_certification"] == "NOT_CLINICALLY_CERTIFIED"
    assert "registered_3d_mm" in res
    # Registered 3D position should match Subnasale ground truth
    x_rec, y_rec, z_rec = res["registered_3d_mm"]
    assert pytest.approx(CANONICAL_FACIAL_3D_LANDMARKS["SUBNASALE"][0], abs=1.5) == x_rec
    assert pytest.approx(CANONICAL_FACIAL_3D_LANDMARKS["SUBNASALE"][1], abs=1.5) == y_rec
    assert pytest.approx(CANONICAL_FACIAL_3D_LANDMARKS["SUBNASALE"][2], abs=1.5) == z_rec
    assert res["uncertainty_radius_mm"] > 0.0
