"""P10-C Metrology Integrity, Collinear Landmark Rejection, and Rotated Projection Tests."""

import math
import pytest

from msk_research_lab.motion.calibration import create_standard_intrinsics
from msk_research_lab.motion.stereo import (
    compute_stereo_depth_uncertainty,
    evaluate_focal_length_depth_sensitivity,
    probe_physical_stereo_hardware,
)
from msk_research_lab.studio.calibrated_registration import (
    CANONICAL_FACIAL_3D_LANDMARKS,
    CalibratedRegistrationError,
    CameraIntrinsics,
    estimate_rigid_pose_from_landmarks,
    project_canonical_landmark,
    register_2d_reflexology_point_to_3d,
)
from msk_research_lab.studio.dien_chan import (
    DienChanError,
    attempt_project_2d_to_3d,
    initialize_dien_chan_project,
)


@pytest.fixture
def test_intrinsics():
    """Standard 720p webcam intrinsics."""
    return create_standard_intrinsics(width=1280, height=720)


def test_collinear_landmark_degeneracy_rejection(test_intrinsics):
    """Verify estimate_rigid_pose_from_landmarks fails closed on collinear landmarks (DEF-25)."""
    # 4 points along a straight vertical line X=0, Z=50
    collinear_3d = [
        (0.0, -30.0, 50.0),
        (0.0, -10.0, 50.0),
        (0.0, 10.0, 50.0),
        (0.0, 30.0, 50.0),
    ]
    # Projected 2D points at depth 500mm
    correspondences = []
    for pt in collinear_3d:
        u = test_intrinsics.cx + (pt[0] / 500.0) * test_intrinsics.fx
        v = test_intrinsics.cy + (pt[1] / 500.0) * test_intrinsics.fy
        correspondences.append((pt, (u, v)))

    with pytest.raises(CalibratedRegistrationError, match="collinear or lack 2D/3D spatial variance"):
        estimate_rigid_pose_from_landmarks(correspondences, test_intrinsics)


def test_rotated_camera_frame_depth_ray_projection(test_intrinsics):
    """Verify ray-surface projection uses true rotated camera-space depth (DEF-24)."""
    # Create pose with significant yaw (25 degrees) and pitch (10 degrees)
    yaw_deg = 25.0
    pitch_deg = 10.0
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)

    # Rotation matrix: Ry * Rx
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    R = [
        [cy, sy * sp, sy * cp],
        [0.0, cp, -sp],
        [-sy, cy * sp, cy * cp],
    ]
    t = [15.0, -10.0, 550.0]

    # Generate synthetic 2D correspondences for 6 canonical facial landmarks
    landmarks_keys = ["SELLION", "PRONASALE", "SUBNASALE", "GNATHION", "TRAGION_LEFT", "TRAGION_RIGHT"]
    correspondences = []
    for k in landmarks_keys:
        pt3 = CANONICAL_FACIAL_3D_LANDMARKS[k]
        # P_cam = R * pt3 + t
        pc_x = R[0][0] * pt3[0] + R[0][1] * pt3[1] + R[0][2] * pt3[2] + t[0]
        pc_y = R[1][0] * pt3[0] + R[1][1] * pt3[1] + R[1][2] * pt3[2] + t[1]
        pc_z = R[2][0] * pt3[0] + R[2][1] * pt3[1] + R[2][2] * pt3[2] + t[2]

        u = test_intrinsics.fx * (pc_x / pc_z) + test_intrinsics.cx
        v = test_intrinsics.fy * (pc_y / pc_z) + test_intrinsics.cy
        correspondences.append((pt3, (u, v)))

    # Estimate pose via Levenberg-Marquardt
    ctx = estimate_rigid_pose_from_landmarks(correspondences, test_intrinsics)
    assert ctx.mean_reprojection_residual_px < 0.2

    # Now project 2D pixel for Pronasale back to 3D
    pronasale_3d = CANONICAL_FACIAL_3D_LANDMARKS["PRONASALE"]
    pc_pro_x = R[0][0] * pronasale_3d[0] + R[0][1] * pronasale_3d[1] + R[0][2] * pronasale_3d[2] + t[0]
    pc_pro_y = R[1][0] * pronasale_3d[0] + R[1][1] * pronasale_3d[1] + R[1][2] * pronasale_3d[2] + t[1]
    pc_pro_z = R[2][0] * pronasale_3d[0] + R[2][1] * pronasale_3d[1] + R[2][2] * pronasale_3d[2] + t[2]

    u_pro = test_intrinsics.fx * (pc_pro_x / pc_pro_z) + test_intrinsics.cx
    v_pro = test_intrinsics.fy * (pc_pro_y / pc_pro_z) + test_intrinsics.cy

    reg_result = register_2d_reflexology_point_to_3d(
        point_id="DC_POINT_19",
        pixel_xy=(u_pro, v_pro),
        target_model_id="bp3d_facial_v1",
        calibration_context=ctx,
        nearest_landmark_hint="PRONASALE",
    )

    reg_3d = reg_result["registered_3d_mm"]
    # Rotated back-projection must recover Pronasale coordinates within 1.5mm
    assert abs(reg_3d[0] - pronasale_3d[0]) < 1.5
    assert abs(reg_3d[1] - pronasale_3d[1]) < 1.5
    assert abs(reg_3d[2] - pronasale_3d[2]) < 1.5


def test_focal_length_depth_sensitivity_analysis():
    """Verify focal length depth sensitivity table shows inverse linear scaling of sigma_Z (P10-C)."""
    table = evaluate_focal_length_depth_sensitivity(
        focals_px=[400.0, 800.0, 1600.0],
        baseline_mm=200.0,
        depth_mm=1000.0,
        disparity_std_px=0.5,
    )
    assert len(table) == 3
    # sigma_Z = (Z^2 / (f * b)) * sigma_d
    # For f=400: (1e6 / (400 * 200)) * 0.5 = 6.25 mm
    assert abs(table[0]["sigma_z_mm"] - 6.25) < 0.01
    # For f=800: 3.125 mm
    assert abs(table[1]["sigma_z_mm"] - 3.125) < 0.01
    # For f=1600: 1.562 mm
    assert abs(table[2]["sigma_z_mm"] - 1.562) < 0.01


def test_epistemic_and_hardware_gates_unbreached():
    """Verify CANNOT_IMPLICITLY_PROJECT_2D_TO_3D and PHYSICAL_STEREO_HARDWARE_GATE remain fail-closed."""
    initialize_dien_chan_project("proj_dien_chan_guard_test")
    with pytest.raises(DienChanError, match="CANNOT_IMPLICITLY_PROJECT_2D_TO_3D"):
        attempt_project_2d_to_3d("proj_dien_chan_guard_test_dc_19", target_model_id="bodyparts3d_torso")

    stereo_status = probe_physical_stereo_hardware()
    assert stereo_status["status"] == "BLOCKED (DUAL_CAMERA_UNAVAILABLE)"
    assert stereo_status["stereo_hardware_available"] is False
    assert stereo_status["physical_device_count"] < 2

    stereo_status = probe_physical_stereo_hardware()
    assert stereo_status["status"] == "BLOCKED (DUAL_CAMERA_UNAVAILABLE)"
    assert stereo_status["stereo_hardware_available"] is False
    assert stereo_status["physical_device_count"] < 2
