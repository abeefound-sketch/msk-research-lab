"""Metrology and uncertainty validation tests for Workstream P9-C."""

import math
import pytest

from msk_research_lab.motion.stereo import (
    StereoMetrologyError,
    compute_stereo_depth_uncertainty,
    create_standard_stereo_rig,
    probe_physical_stereo_hardware,
    project_3d_point,
    stereo_depth_sensitivity_table,
    triangulate_joint_angle_3d,
)


def test_depth_uncertainty_quadratic_scaling():
    """Verify stereo depth uncertainty scales quadratically with depth Z (sigma_Z proportional to Z^2)."""
    f = 1000.0  # px
    b = 200.0   # mm
    sigma_d = 0.5  # px

    # At Z = 1000 mm: sigma_Z = (1000^2 / (1000 * 200)) * 0.5 = 2.5 mm
    sigma_1000 = compute_stereo_depth_uncertainty(1000.0, b, f, sigma_d)
    assert pytest.approx(2.5, abs=1e-5) == sigma_1000

    # At Z = 2000 mm: sigma_Z = (2000^2 / (1000 * 200)) * 0.5 = 10.0 mm (exactly 4x!)
    sigma_2000 = compute_stereo_depth_uncertainty(2000.0, b, f, sigma_d)
    assert pytest.approx(10.0, abs=1e-5) == sigma_2000
    assert pytest.approx(4.0, abs=1e-5) == (sigma_2000 / sigma_1000)

    # At Z = 3000 mm: sigma_Z = (3000^2 / (1000 * 200)) * 0.5 = 22.5 mm (exactly 9x!)
    sigma_3000 = compute_stereo_depth_uncertainty(3000.0, b, f, sigma_d)
    assert pytest.approx(22.5, abs=1e-5) == sigma_3000
    assert pytest.approx(9.0, abs=1e-5) == (sigma_3000 / sigma_1000)


def test_depth_uncertainty_inverse_baseline_scaling():
    """Verify stereo depth uncertainty is inversely proportional to baseline (sigma_Z proportional to 1/b)."""
    f = 1000.0
    z = 1500.0
    sigma_d = 0.5

    sigma_b100 = compute_stereo_depth_uncertainty(z, baseline_mm=100.0, focal_length_px=f, disparity_std_px=sigma_d)
    sigma_b200 = compute_stereo_depth_uncertainty(z, baseline_mm=200.0, focal_length_px=f, disparity_std_px=sigma_d)
    sigma_b400 = compute_stereo_depth_uncertainty(z, baseline_mm=400.0, focal_length_px=f, disparity_std_px=sigma_d)

    # Doubling baseline halves uncertainty
    assert pytest.approx(sigma_b100 / 2.0, abs=1e-5) == sigma_b200
    assert pytest.approx(sigma_b200 / 2.0, abs=1e-5) == sigma_b400


def test_depth_uncertainty_parameter_validation():
    """Verify fail-closed parameter validation for degenerate geometry."""
    with pytest.raises(StereoMetrologyError):
        compute_stereo_depth_uncertainty(depth_z_mm=-10.0, baseline_mm=200.0, focal_length_px=1000.0)

    with pytest.raises(StereoMetrologyError):
        compute_stereo_depth_uncertainty(depth_z_mm=1000.0, baseline_mm=0.0, focal_length_px=1000.0)

    with pytest.raises(StereoMetrologyError):
        compute_stereo_depth_uncertainty(depth_z_mm=1000.0, baseline_mm=200.0, focal_length_px=-500.0)


def test_sensitivity_table_generation():
    """Verify empirical sensitivity table generates comprehensive baseline/depth matrix."""
    baselines = [100.0, 200.0, 300.0]
    depths = [1000.0, 2000.0, 3000.0]
    table = stereo_depth_sensitivity_table(baselines_mm=baselines, depths_mm=depths)

    assert len(table) == len(baselines) * len(depths)
    # Check that at same baseline, relative uncertainty increases with depth
    b100_rows = [r for r in table if r["baseline_mm"] == 100.0]
    assert b100_rows[0]["relative_uncertainty_pct"] < b100_rows[1]["relative_uncertainty_pct"]
    assert b100_rows[1]["relative_uncertainty_pct"] < b100_rows[2]["relative_uncertainty_pct"]


def test_joint_angle_uncertainty_propagation():
    """Verify angular uncertainty is propagated and distinguished from coordinate rotation invariance."""
    rig = create_standard_stereo_rig(baseline_mm=200.0)

    # Construct joint at 1.5m depth
    A = (0.0, 300.0, 1500.0)
    B = (0.0, 0.0, 1500.0)
    C = (300.0, 0.0, 1500.0)

    P1 = rig.left_projection_matrix
    P2 = rig.right_projection_matrix

    a_l, a_r = project_3d_point(A, P1), project_3d_point(A, P2)
    b_l, b_r = project_3d_point(B, P1), project_3d_point(B, P2)
    c_l, c_r = project_3d_point(C, P1), project_3d_point(C, P2)

    res = triangulate_joint_angle_3d(a_l, b_l, c_l, a_r, b_r, c_r, rig)

    assert res["status"] == "VALID"
    assert pytest.approx(90.0, abs=0.2) == res["angle_3d_deg"]
    assert res["mathematical_rotation_invariance"] is True
    assert res["is_immune_to_yaw"] is True
    assert res["metrological_depth_uncertainty_mm"] > 0.0
    assert res["estimated_angular_uncertainty_deg"] > 0.0
    assert "sigma_Z = Z^2 / (f * b)" in res["metrological_note"]


def test_probe_physical_hardware_preserves_blocked_invariant():
    """Verify physical hardware gate strictly preserves BLOCKED status when 2 cameras are not present."""
    probe = probe_physical_stereo_hardware()
    assert probe["required_device_count"] == 2
    if not probe["stereo_hardware_available"]:
        assert probe["status"] == "BLOCKED (DUAL_CAMERA_UNAVAILABLE)"
        assert "hardware gate remains BLOCKED" in probe["reason"]
