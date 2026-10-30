"""Unit tests for Stereo Photogrammetry, DLT Triangulation, and Kinematic Angle Recovery."""

import math
import pytest
from msk_research_lab.motion.stereo import (
    StereoCameraRig,
    StereoMetrologyError,
    compute_reprojection_error,
    create_standard_stereo_rig,
    project_3d_point,
    probe_physical_stereo_hardware,
    triangulate_joint_angle_3d,
    triangulate_point_dlt,
)


def test_stereo_camera_rig_geometry():
    """Verify stereo camera rig projection matrices, baseline, and essential matrix."""
    rig = create_standard_stereo_rig(baseline_mm=180.0, width=1280, height=720, hfov_deg=65.0)
    assert rig.baseline_mm == 180.0
    assert len(rig.left_projection_matrix) == 3
    assert len(rig.left_projection_matrix[0]) == 4
    assert len(rig.right_projection_matrix) == 3
    assert len(rig.right_projection_matrix[0]) == 4

    # P1 has 0 translation column
    assert rig.left_projection_matrix[0][3] == 0.0
    assert rig.left_projection_matrix[1][3] == 0.0
    assert rig.left_projection_matrix[2][3] == 0.0

    # Essential matrix is 3x3
    E = rig.essential_matrix
    assert len(E) == 3
    assert len(E[0]) == 3


def test_dlt_triangulation_and_reprojection_accuracy():
    """Verify DLT triangulation recovers exact 3D coordinates from noise-free stereo projection."""
    rig = create_standard_stereo_rig(baseline_mm=200.0)

    # Ground-truth point 1.5 meters in front of rig, slightly offset
    true_pt = (50.0, -80.0, 1500.0)  # mm

    pt_left = project_3d_point(true_pt, rig.left_projection_matrix)
    pt_right = project_3d_point(true_pt, rig.right_projection_matrix)

    # Disparity check: right camera is displaced horizontally, so x-coordinate should differ
    assert pt_left[0] != pt_right[0]
    # In horizontal parallel rig, y-coordinates lie on same epipolar line
    assert pytest.approx(pt_left[1], abs=1e-3) == pt_right[1]

    # Triangulate
    recovered_pt = triangulate_point_dlt(pt_left, pt_right, rig)

    assert pytest.approx(true_pt[0], abs=0.5) == recovered_pt[0]
    assert pytest.approx(true_pt[1], abs=0.5) == recovered_pt[1]
    assert pytest.approx(true_pt[2], abs=1.0) == recovered_pt[2]

    # Reprojection error should be near zero
    err = compute_reprojection_error(recovered_pt, pt_left, pt_right, rig)
    assert err < 0.05  # Sub-pixel accuracy


def test_3d_joint_angle_immunity_to_yaw():
    """Verify 3D stereo triangulation correctly recovers joint angle even when yaw-rotated."""
    rig = create_standard_stereo_rig(baseline_mm=200.0)

    # Construct joint with true 60 degree angle rotated by 30 deg yaw in 3D
    # Vertex B at (0, 0, 1200)
    B_true = (0.0, 0.0, 1200.0)
    # Segment 1 along Y: length 300 mm
    A_true = (0.0, 300.0, 1200.0)

    # Segment 2 at 60 deg, but rotated by 30 deg yaw
    # In joint plane: v = (300*sin(60), 300*cos(60), 0)
    # Rotated by yaw 30 deg: x' = x*cos(30), z' = z - x*sin(30)
    alpha = math.radians(60.0)
    yaw = math.radians(30.0)
    vx = 300.0 * math.sin(alpha)
    vy = 300.0 * math.cos(alpha)
    C_true = (vx * math.cos(yaw), vy, 1200.0 - vx * math.sin(yaw))

    # Project to left and right views
    P1 = rig.left_projection_matrix
    P2 = rig.right_projection_matrix

    a_l, a_r = project_3d_point(A_true, P1), project_3d_point(A_true, P2)
    b_l, b_r = project_3d_point(B_true, P1), project_3d_point(B_true, P2)
    c_l, c_r = project_3d_point(C_true, P1), project_3d_point(C_true, P2)

    # Triangulate
    res = triangulate_joint_angle_3d(a_l, b_l, c_l, a_r, b_r, c_r, rig)

    assert res["status"] == "VALID"
    # Recovered angle in 3D must be exactly 60 degrees, unaffected by 30 deg yaw!
    assert pytest.approx(60.0, abs=0.2) == res["angle_3d_deg"]
    assert res["reprojection_errors_px"]["max"] < 0.1


def test_reprojection_error_gating_rejects_corrupted_correspondence():
    """Verify pipeline fails closed when correspondence error exceeds threshold."""
    rig = create_standard_stereo_rig(baseline_mm=200.0)
    A = (0.0, 300.0, 1200.0)
    B = (0.0, 0.0, 1200.0)
    C = (200.0, 200.0, 1200.0)

    P1 = rig.left_projection_matrix
    P2 = rig.right_projection_matrix

    a_l, a_r = project_3d_point(A, P1), project_3d_point(A, P2)
    b_l, b_r = project_3d_point(B, P1), project_3d_point(B, P2)
    c_l, c_r = project_3d_point(C, P1), project_3d_point(C, P2)

    # Corrupt right coordinate by 15 pixels (simulating landmark mismatch or occlusion)
    c_r_corrupt = (c_r[0] + 15.0, c_r[1] + 10.0)

    with pytest.raises(StereoMetrologyError) as exc_info:
        triangulate_joint_angle_3d(a_l, b_l, c_l, a_r, b_r, c_r_corrupt, rig, max_reprojection_error_px=2.5)

    assert "reprojection error" in str(exc_info.value).lower()
    assert "exceeds tolerance" in str(exc_info.value).lower()


def test_physical_stereo_hardware_probe_blocked():
    """Verify hardware probe faithfully marks gate BLOCKED when physical dual cameras are unavailable."""
    res = probe_physical_stereo_hardware()
    # In WSL2 development environment, physical dual genlocked cameras are not present
    assert res["status"].startswith("BLOCKED") or res["status"] == "OPERATIONAL"
    if not res["stereo_hardware_available"]:
        assert "BLOCKED (DUAL_CAMERA_UNAVAILABLE)" in res["status"]
        assert "Single webcam / WSL2 environment detected" in res["reason"]
