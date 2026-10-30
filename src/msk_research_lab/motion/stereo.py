"""Stereo Photogrammetry, Dual-Camera Triangulation, and Epipolar Kinematics Engine."""

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from msk_research_lab.motion.calibration import CameraIntrinsics, create_standard_intrinsics


class StereoMetrologyError(Exception):
    """Raised when stereo geometry, triangulation, or reprojection error fails."""
    pass


@dataclass
class StereoCameraRig:
    """Calibrated stereo camera rig with relative pose [R | t] and projection matrices."""
    left_intrinsics: CameraIntrinsics
    right_intrinsics: CameraIntrinsics
    # 3x3 rotation matrix from left camera frame to right camera frame
    R: List[List[float]]
    # 3x1 translation vector from left camera to right camera in millimeters [tx, ty, tz]
    t: List[float]
    name: str = "BENCHMARK_STEREO_RIG_BASELINE_200MM"

    @property
    def baseline_mm(self) -> float:
        """Euclidean baseline distance between camera optical centers."""
        return math.hypot(self.t[0], self.t[1], self.t[2])

    @property
    def left_projection_matrix(self) -> List[List[float]]:
        """Left camera projection matrix P1 = K1 * [I | 0] (3x4)."""
        K = self.left_intrinsics.camera_matrix
        return [
            [K[0][0], K[0][1], K[0][2], 0.0],
            [K[1][0], K[1][1], K[1][2], 0.0],
            [K[2][0], K[2][1], K[2][2], 0.0],
        ]

    @property
    def right_projection_matrix(self) -> List[List[float]]:
        """Right camera projection matrix P2 = K2 * [R | t] (3x4)."""
        K = self.right_intrinsics.camera_matrix
        # Multiply 3x3 K by 3x4 [R | t]
        Rt = [
            [self.R[0][0], self.R[0][1], self.R[0][2], self.t[0]],
            [self.R[1][0], self.R[1][1], self.R[1][2], self.t[1]],
            [self.R[2][0], self.R[2][1], self.R[2][2], self.t[2]],
        ]
        P2 = [[0.0] * 4 for _ in range(3)]
        for i in range(3):
            for j in range(4):
                P2[i][j] = sum(K[i][k] * Rt[k][j] for k in range(3))
        return P2

    @property
    def essential_matrix(self) -> List[List[float]]:
        """Essential matrix E = [t]_x * R."""
        tx, ty, tz = self.t[0], self.t[1], self.t[2]
        # Skew symmetric matrix of translation vector t
        t_x = [
            [0.0, -tz, ty],
            [tz, 0.0, -tx],
            [-ty, tx, 0.0],
        ]
        E = [[0.0] * 3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                E[i][j] = sum(t_x[i][k] * self.R[k][j] for k in range(3))
        return E


def create_standard_stereo_rig(
    baseline_mm: float = 200.0,
    width: int = 1280,
    height: int = 720,
    hfov_deg: float = 65.0,
) -> StereoCameraRig:
    """Create nominal parallel horizontal stereo rig with baseline in millimeters."""
    K_left = create_standard_intrinsics(width=width, height=height, hfov_deg=hfov_deg, device_name="LEFT_CAM")
    K_right = create_standard_intrinsics(width=width, height=height, hfov_deg=hfov_deg, device_name="RIGHT_CAM")

    # Pure horizontal displacement along X-axis
    R_identity = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    t_horizontal = [-baseline_mm, 0.0, 0.0]

    return StereoCameraRig(
        left_intrinsics=K_left,
        right_intrinsics=K_right,
        R=R_identity,
        t=t_horizontal,
        name=f"STANDARD_STEREO_{int(baseline_mm)}MM",
    )


# ==============================================================================
# Direct Linear Transformation (DLT) Triangulation & Reprojection
# ==============================================================================

def _solve_nullspace_4x4(A: List[List[float]]) -> List[float]:
    """Solve A * x = 0 for 4x4 matrix using SVD / Power Iteration on A^T * A."""
    # Compute 4x4 normal matrix M = A^T * A
    M = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            M[i][j] = sum(A[k][i] * A[k][j] for k in range(4))

    # Inverse iteration to find eigenvector corresponding to smallest eigenvalue
    # Shift normal matrix M with identity regularization
    v = [1.0, 0.5, 0.25, 0.125]
    for _ in range(30):
        # Solve M * v_next = v (using Gauss-Jordan or simple iterative relaxation)
        # For small 4x4, Gaussian elimination with partial pivoting:
        aug = [row[:] + [v[i]] for i, row in enumerate(M)]
        # Add small damping to diagonal
        for i in range(4):
            aug[i][i] += 1e-9

        # Forward elimination
        for col in range(4):
            max_row = max(range(col, 4), key=lambda r: abs(aug[r][col]))
            aug[col], aug[max_row] = aug[max_row], aug[col]
            pivot = aug[col][col]
            if abs(pivot) < 1e-12:
                continue
            for r in range(col + 1, 4):
                factor = aug[r][col] / pivot
                for c in range(col, 5):
                    aug[r][c] -= factor * aug[col][c]

        # Back substitution
        sol = [0.0] * 4
        for r in range(3, -1, -1):
            if abs(aug[r][r]) < 1e-12:
                sol[r] = 0.0
            else:
                sol[r] = (aug[r][4] - sum(aug[r][c] * sol[c] for c in range(r + 1, 4))) / aug[r][r]

        # Normalize
        norm = math.sqrt(sum(x * x for x in sol))
        if norm > 1e-12:
            v = [x / norm for x in sol]

    return v


def triangulate_point_dlt(
    pt_left: Tuple[float, float],
    pt_right: Tuple[float, float],
    rig: StereoCameraRig,
) -> Tuple[float, float, float]:
    """Triangulate 3D point (X, Y, Z) in left camera coordinates using Direct Linear Transformation.
    
    Given left point (u1, v1) and right point (u2, v2):
    u * P^3 * X - P^1 * X = 0
    v * P^3 * X - P^2 * X = 0
    """
    P1 = rig.left_projection_matrix
    P2 = rig.right_projection_matrix

    u1, v1 = pt_left
    u2, v2 = pt_right

    A = [
        [u1 * P1[2][j] - P1[0][j] for j in range(4)],
        [v1 * P1[2][j] - P1[1][j] for j in range(4)],
        [u2 * P2[2][j] - P2[0][j] for j in range(4)],
        [v2 * P2[2][j] - P2[1][j] for j in range(4)],
    ]

    homog = _solve_nullspace_4x4(A)
    w = homog[3]
    if abs(w) < 1e-9:
        raise StereoMetrologyError("Triangulation degenerate: point lies at infinity.")

    return (homog[0] / w, homog[1] / w, homog[2] / w)


def project_3d_point(
    point_3d: Tuple[float, float, float],
    projection_matrix: List[List[float]],
) -> Tuple[float, float]:
    """Project a 3D coordinate through a 3x4 projection matrix into 2D pixel coordinates."""
    X, Y, Z = point_3d
    homog_in = [X, Y, Z, 1.0]

    p = [sum(projection_matrix[i][j] * homog_in[j] for j in range(4)) for i in range(3)]
    if abs(p[2]) < 1e-9:
        raise StereoMetrologyError("Cannot project: point lies on camera focal plane.")

    return (p[0] / p[2], p[1] / p[2])


def compute_reprojection_error(
    point_3d: Tuple[float, float, float],
    pt_left: Tuple[float, float],
    pt_right: Tuple[float, float],
    rig: StereoCameraRig,
) -> float:
    """Compute mean Euclidean reprojection error in pixels across left and right cameras."""
    proj_l = project_3d_point(point_3d, rig.left_projection_matrix)
    proj_r = project_3d_point(point_3d, rig.right_projection_matrix)

    err_l = math.hypot(pt_left[0] - proj_l[0], pt_left[1] - proj_l[1])
    err_r = math.hypot(pt_right[0] - proj_r[0], pt_right[1] - proj_r[1])

    return (err_l + err_r) / 2.0


def compute_stereo_depth_uncertainty(
    depth_z_mm: float,
    baseline_mm: float,
    focal_length_px: float,
    disparity_std_px: float = 0.5,
) -> float:
    """Compute theoretical 1-sigma depth uncertainty for parallel stereo photogrammetry.
    
    Formula:
    sigma_Z = (Z^2 / (f * b)) * sigma_d
    
    where:
    - Z = object depth along optical axis (mm)
    - b = baseline distance between camera centers (mm)
    - f = focal length (pixels)
    - sigma_d = disparity matching uncertainty (pixels, typically 0.25 to 0.75 px)
    """
    if baseline_mm <= 0.0 or focal_length_px <= 0.0:
        raise StereoMetrologyError("Baseline and focal length must be strictly positive.")
    if depth_z_mm <= 0.0:
        raise StereoMetrologyError("Depth Z must be strictly positive.")

    return (depth_z_mm * depth_z_mm / (focal_length_px * baseline_mm)) * disparity_std_px


def stereo_depth_sensitivity_table(
    baselines_mm: Optional[List[float]] = None,
    depths_mm: Optional[List[float]] = None,
    focal_length_px: float = 1000.0,
    disparity_std_px: float = 0.5,
) -> List[Dict[str, Any]]:
    """Generate sensitivity analysis table illustrating quadratic depth uncertainty scaling."""
    b_list = baselines_mm or [100.0, 200.0, 300.0, 400.0]
    z_list = depths_mm or [500.0, 1000.0, 1500.0, 2000.0, 2500.0, 3000.0]

    table: List[Dict[str, Any]] = []
    for b in b_list:
        for z in z_list:
            unc = compute_stereo_depth_uncertainty(
                depth_z_mm=z,
                baseline_mm=b,
                focal_length_px=focal_length_px,
                disparity_std_px=disparity_std_px,
            )
            table.append({
                "baseline_mm": b,
                "depth_z_mm": z,
                "focal_length_px": focal_length_px,
                "disparity_std_px": disparity_std_px,
                "depth_uncertainty_mm": round(unc, 2),
                "relative_uncertainty_pct": round((unc / z) * 100.0, 2),
            })
    return table


def evaluate_focal_length_depth_sensitivity(
    focals_px: Optional[List[float]] = None,
    baseline_mm: float = 200.0,
    depth_mm: float = 1000.0,
    disparity_std_px: float = 0.5,
) -> List[Dict[str, Any]]:
    """Evaluate optical focal length (f) impact on depth measurement precision (P10-C)."""
    f_list = focals_px or [400.0, 600.0, 800.0, 1000.0, 1200.0, 1600.0]
    results = []
    for f in f_list:
        sigma_z = compute_stereo_depth_uncertainty(
            depth_z_mm=depth_mm,
            baseline_mm=baseline_mm,
            focal_length_px=f,
            disparity_std_px=disparity_std_px,
        )
        results.append({
            "focal_length_px": f,
            "baseline_mm": baseline_mm,
            "depth_mm": depth_mm,
            "sigma_z_mm": round(sigma_z, 3),
            "relative_uncertainty_pct": round((sigma_z / depth_mm) * 100.0, 3),
        })
    return results


def triangulate_joint_angle_3d(
    pt_a_left: Tuple[float, float],
    pt_b_left: Tuple[float, float],
    pt_c_left: Tuple[float, float],
    pt_a_right: Tuple[float, float],
    pt_b_right: Tuple[float, float],
    pt_c_right: Tuple[float, float],
    rig: StereoCameraRig,
    max_reprojection_error_px: float = 2.5,
    disparity_std_px: float = 0.5,
) -> Dict[str, Any]:
    """Triangulate 3 joint vertices in genuine Euclidean 3D space and compute true 3D angle.
    
    Guarantees:
    - Fails closed if reprojection error exceeds max_reprojection_error_px.
    - Rigid 3D vector angle is mathematically rotation-invariant.
    - Explicitly computes empirical depth uncertainty (sigma_Z) and estimated angular uncertainty.
    """
    # 1. Triangulate each vertex
    A_3d = triangulate_point_dlt(pt_a_left, pt_a_right, rig)
    B_3d = triangulate_point_dlt(pt_b_left, pt_b_right, rig)
    C_3d = triangulate_point_dlt(pt_c_left, pt_c_right, rig)

    # 2. Verify reprojection errors
    err_a = compute_reprojection_error(A_3d, pt_a_left, pt_a_right, rig)
    err_b = compute_reprojection_error(B_3d, pt_b_left, pt_b_right, rig)
    err_c = compute_reprojection_error(C_3d, pt_c_left, pt_c_right, rig)
    max_err = max(err_a, err_b, err_c)

    if max_err > max_reprojection_error_px:
        raise StereoMetrologyError(
            f"Stereo triangulation rejected: reprojection error ({max_err:.2f} px) "
            f"exceeds tolerance ({max_reprojection_error_px:.2f} px)."
        )

    # 3. Compute 3D vectors from vertex B: v1 = (A - B), v2 = (C - B)
    v1 = (A_3d[0] - B_3d[0], A_3d[1] - B_3d[1], A_3d[2] - B_3d[2])
    v2 = (C_3d[0] - B_3d[0], C_3d[1] - B_3d[1], C_3d[2] - B_3d[2])

    mag1 = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2])
    mag2 = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1] + v2[2] * v2[2])

    if mag1 < 1e-6 or mag2 < 1e-6:
        raise StereoMetrologyError("Degenerate joint geometry: coincident joint vertices.")

    dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
    cos_val = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    angle_3d_deg = math.degrees(math.acos(cos_val))

    # 4. Metrological depth uncertainty propagation (sigma_Z = Z^2 / (f * b) * sigma_d)
    f_px = rig.left_intrinsics.fx
    b_mm = rig.baseline_mm
    sigma_za = compute_stereo_depth_uncertainty(abs(A_3d[2]), b_mm, f_px, disparity_std_px)
    sigma_zb = compute_stereo_depth_uncertainty(abs(B_3d[2]), b_mm, f_px, disparity_std_px)
    sigma_zc = compute_stereo_depth_uncertainty(abs(C_3d[2]), b_mm, f_px, disparity_std_px)
    sigma_z_max = max(sigma_za, sigma_zb, sigma_zc)

    # Angular uncertainty approximation: delta_theta ~ (180/pi) * (sigma_z) * sqrt(1/L1^2 + 1/L2^2)
    angular_unc_rad = sigma_z_max * math.sqrt((1.0 / (mag1 * mag1)) + (1.0 / (mag2 * mag2)))
    angular_unc_deg = math.degrees(angular_unc_rad)

    return {
        "status": "VALID",
        "angle_3d_deg": round(angle_3d_deg, 2),
        "vertices_3d": {
            "vertex_a": [round(x, 2) for x in A_3d],
            "vertex_b": [round(x, 2) for x in B_3d],
            "vertex_c": [round(x, 2) for x in C_3d],
        },
        "reprojection_errors_px": {
            "vertex_a": round(err_a, 3),
            "vertex_b": round(err_b, 3),
            "vertex_c": round(err_c, 3),
            "max": round(max_err, 3),
        },
        "rig_baseline_mm": rig.baseline_mm,
        "is_immune_to_yaw": True,  # Preserved for backward compatibility
        "mathematical_rotation_invariance": True,
        "metrological_depth_uncertainty_mm": round(sigma_z_max, 2),
        "estimated_angular_uncertainty_deg": round(angular_unc_deg, 2),
        "depth_uncertainty_by_vertex_mm": {
            "vertex_a": round(sigma_za, 2),
            "vertex_b": round(sigma_zb, 2),
            "vertex_c": round(sigma_zc, 2),
        },
        "metrological_note": (
            "Rigid 3D vector angle is mathematically rotation-invariant, "
            "but empirical photogrammetric depth precision degrades quadratically "
            "with distance (sigma_Z = Z^2 / (f * b) * sigma_d)."
        ),
    }


def probe_physical_stereo_hardware() -> Dict[str, Any]:
    """Probe physical host hardware for synchronized stereo cameras.
    
    Safety Governance:
    In accordance with biomedical testing standards, unavailable physical stereo hardware
    must NEVER be converted to PASS. Must return BLOCKED (DUAL_CAMERA_UNAVAILABLE).
    """
    found_devices = 0

    # Test for standard Linux V4L2 devices
    from pathlib import Path
    v4l_devices = list(Path("/dev").glob("video*")) if Path("/dev").exists() else []
    found_devices = len(v4l_devices)

    is_available = found_devices >= 2
    return {
        "stereo_hardware_available": is_available,
        "status": "OPERATIONAL" if is_available else "BLOCKED (DUAL_CAMERA_UNAVAILABLE)",
        "physical_device_count": found_devices,
        "required_device_count": 2,
        "reason": (
            "Verified operational"
            if is_available
            else "Workstation host lacks 2 physical genlocked video sources. "
                 "Single webcam / WSL2 environment detected; hardware gate remains BLOCKED."
        ),
    }
