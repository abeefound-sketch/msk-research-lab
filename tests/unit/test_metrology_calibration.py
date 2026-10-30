"""Unit tests for Metrological Camera Calibration and ISO GUM Uncertainty Validation."""

import math
import pytest
from msk_research_lab.motion.calibration import (
    CameraIntrinsics,
    compute_projected_angle_under_yaw,
    create_standard_intrinsics,
    distort_normalized_point,
    evaluate_empirical_repeatability,
    normalized_to_pixel,
    pixel_to_normalized,
    undistort_normalized_point,
)


def test_camera_intrinsics_geometry():
    """Verify standard camera intrinsics matrix and FOV focal length calculation."""
    K = create_standard_intrinsics(width=1920, height=1080, hfov_deg=70.0)
    assert K.width == 1920
    assert K.height == 1080
    assert K.cx == 960.0
    assert K.cy == 540.0
    assert K.fx > 1000.0  # ~1371 pixels for 70 deg FOV
    assert K.fy == K.fx

    mat = K.camera_matrix
    assert len(mat) == 3
    assert mat[0][0] == K.fx
    assert mat[0][2] == K.cx
    assert mat[1][1] == K.fy
    assert mat[1][2] == K.cy
    assert mat[2][2] == 1.0


def test_distortion_and_undistortion_convergence():
    """Verify forward distortion and fixed-point undistortion roundtrip."""
    k1 = -0.05  # Barrel distortion
    k2 = 0.01
    p1 = 0.001
    p2 = 0.0005

    # Near center of frame (normalized coords ~0.1, 0.1)
    x_orig, y_orig = 0.15, -0.12
    x_dist, y_dist = distort_normalized_point(x_orig, y_orig, k1, k2, p1, p2)

    # Inverted
    x_rec, y_rec = undistort_normalized_point(x_dist, y_dist, k1, k2, p1, p2, iterations=10)

    assert pytest.approx(x_orig, abs=1e-4) == x_rec
    assert pytest.approx(y_orig, abs=1e-4) == y_rec


def test_pixel_to_normalized_roundtrip():
    """Verify bidirectional conversion between sensor pixels and normalized image plane."""
    K = create_standard_intrinsics(width=1280, height=720, hfov_deg=65.0)
    px, py = 850.0, 420.0
    nx, ny = pixel_to_normalized(px, py, K)
    px_rec, py_rec = normalized_to_pixel(nx, ny, K)

    assert pytest.approx(px, abs=1e-5) == px_rec
    assert pytest.approx(py, abs=1e-5) == py_rec


def test_out_of_plane_yaw_error_monotonicity():
    """Verify out-of-plane yaw introduces non-linear projection foreshortening (tan alpha_2D = tan alpha_3D * cos theta)."""
    true_angle = 45.0  # Non-axial angle sensitive to foreshortening

    # At 0 degrees yaw, planar angle is exactly preserved
    proj_0 = compute_projected_angle_under_yaw(true_angle, yaw_deg=0.0)
    assert pytest.approx(45.0, abs=1e-4) == proj_0

    # At 15 degrees yaw, foreshortening compresses horizontal projection
    proj_15 = compute_projected_angle_under_yaw(true_angle, yaw_deg=15.0)
    error_15 = abs(proj_15 - true_angle)
    assert error_15 > 0.5  # ~1.0 degree foreshortening error

    # At 30 degrees yaw, projection error increases substantially
    proj_30 = compute_projected_angle_under_yaw(true_angle, yaw_deg=30.0)
    error_30 = abs(proj_30 - true_angle)
    assert error_30 > error_15
    assert error_30 > 3.5  # ~4.1 degrees error at 30 deg yaw


def test_empirical_repeatability_statistics():
    """Verify ISO GUM statistical evaluation across repeated trials."""
    # Simulated 30-frame repeated measurement with known noise and 0.5 deg bias
    reference_angle = 90.0
    samples = [90.5 + 0.3 * math.sin(i * 0.7) for i in range(30)]

    res = evaluate_empirical_repeatability(samples, reference_angle=reference_angle)

    assert res["is_statistically_valid"] is True
    assert res["sample_size"] == 30
    assert pytest.approx(90.5, abs=0.1) == res["mean_rom_deg"]
    assert res["std_dev_deg"] > 0.1
    assert res["std_error_deg"] < res["std_dev_deg"]
    assert pytest.approx(0.5, abs=0.1) == res["systematic_bias_deg"]
    assert res["u95_combined_deg"] > res["std_dev_deg"]
