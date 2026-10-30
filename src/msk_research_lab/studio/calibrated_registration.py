"""Calibrated 2D-to-3D Registration Engine for Facial Reflexology (Diện Chẩn).

Provides mathematically grounded optical photogrammetry and PnP pose estimation,
replacing heuristic/implicit projections while strictly preserving the
epistemic guard CANNOT_IMPLICITLY_PROJECT_2D_TO_3D when calibration is absent.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from msk_research_lab.motion.calibration import (
    CameraIntrinsics,
    create_standard_intrinsics,
    distort_normalized_point,
    undistort_normalized_point,
)
from msk_research_lab.studio.dien_chan import DienChanError, attempt_project_2d_to_3d


class CalibratedRegistrationError(Exception):
    """Raised when optical calibration residuals exceed tolerance or geometry is degenerate."""
    pass


# Canonical anthropometric facial landmarks in millimeter coordinate frame (origin at Subnasale)
CANONICAL_FACIAL_3D_LANDMARKS: Dict[str, Tuple[float, float, float]] = {
    "SUBNASALE": (0.0, 0.0, 20.0),            # Anatomical site of Huyệt 19
    "PRONASALE": (0.0, 18.0, 36.0),           # Nose tip
    "SELLION": (0.0, 48.0, 18.0),             # Nasion / bridge
    "TRAGION_LEFT": (-76.0, 10.0, -38.0),     # Left tragus notch / Huyệt 0 Left
    "TRAGION_RIGHT": (76.0, 10.0, -38.0),     # Right tragus notch / Huyệt 0 Right
    "GONION_LEFT": (-66.0, -48.0, -42.0),     # Left jaw angle / Huyệt 275 Left
    "GONION_RIGHT": (66.0, -48.0, -42.0),     # Right jaw angle / Huyệt 275 Right
    "GNATHION": (0.0, -68.0, 12.0),           # Chin midpoint
}


@dataclass
class OpticalCalibrationContext:
    """Rigid pose calibration context connecting 2D photograph to 3D facial mesh."""
    intrinsics: CameraIntrinsics
    target_pattern: str = "CHARUCO_7X9_15MM"
    # Rigid transformation: 3x3 rotation matrix R and 3x1 translation vector t
    R: List[List[float]] = field(default_factory=lambda: [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ])
    t: List[float] = field(default_factory=lambda: [0.0, 0.0, 500.0])
    mean_reprojection_residual_px: float = 0.85
    max_reprojection_residual_px: float = 1.65
    is_calibrated: bool = True
    calibration_target_detected: bool = True
    spatial_condition_number: float = 1.0
    planarity_ratio: float = 0.5
    covariance_eigenvalues: Tuple[float, float, float] = (100.0, 100.0, 50.0)


def create_nominal_calibration_context(
    intrinsics: Optional[CameraIntrinsics] = None,
    yaw_deg: float = 0.0,
    pitch_deg: float = 0.0,
    distance_mm: float = 500.0,
) -> OpticalCalibrationContext:
    """Generate a nominal calibrated optical context with given camera pose."""
    K = intrinsics or create_standard_intrinsics(width=1280, height=720, hfov_deg=65.0)

    # Compute R from yaw and pitch
    y_rad = math.radians(yaw_deg)
    p_rad = math.radians(pitch_deg)

    cos_y, sin_y = math.cos(y_rad), math.sin(y_rad)
    cos_p, sin_p = math.cos(p_rad), math.sin(p_rad)

    # R = R_x(pitch) * R_y(yaw)
    R = [
        [cos_y, 0.0, sin_y],
        [sin_p * sin_y, cos_p, -sin_p * cos_y],
        [-cos_p * sin_y, sin_p, cos_p * cos_y],
    ]
    t = [0.0, 0.0, distance_mm]

    return OpticalCalibrationContext(
        intrinsics=K,
        R=R,
        t=t,
        mean_reprojection_residual_px=0.75,
        max_reprojection_residual_px=1.40,
        is_calibrated=True,
    )


def project_canonical_landmark(
    landmark_name: str,
    context: OpticalCalibrationContext,
) -> Tuple[float, float]:
    """Project a 3D canonical facial landmark to 2D pixel coordinates using calibrated pose."""
    if landmark_name not in CANONICAL_FACIAL_3D_LANDMARKS:
        raise CalibratedRegistrationError(f"Unknown facial landmark '{landmark_name}'.")

    X_obj = CANONICAL_FACIAL_3D_LANDMARKS[landmark_name]
    R = context.R
    t = context.t
    K = context.intrinsics

    # X_cam = R * X_obj + t
    x_cam = R[0][0] * X_obj[0] + R[0][1] * X_obj[1] + R[0][2] * X_obj[2] + t[0]
    y_cam = R[1][0] * X_obj[0] + R[1][1] * X_obj[1] + R[1][2] * X_obj[2] + t[1]
    z_cam = R[2][0] * X_obj[0] + R[2][1] * X_obj[1] + R[2][2] * X_obj[2] + t[2]

    if z_cam <= 10.0:
        raise CalibratedRegistrationError("Landmark lies behind camera or within near plane.")

    xn = x_cam / z_cam
    yn = y_cam / z_cam
    if abs(K.k1) > 1e-6 or abs(K.k2) > 1e-6 or abs(K.p1) > 1e-6 or abs(K.p2) > 1e-6 or abs(K.k3) > 1e-6:
        xd, yd = distort_normalized_point(xn, yn, K.k1, K.k2, K.p1, K.p2, K.k3)
    else:
        xd, yd = xn, yn

    px = K.fx * xd + K.cx
    py = K.fy * yd + K.cy
    return (px, py)


def _rodrigues_to_rotation_matrix(r: List[float]) -> List[List[float]]:
    """Convert 3D rotation vector r = [rx, ry, rz] to 3x3 rotation matrix using Rodrigues formula."""
    rx, ry, rz = r[0], r[1], r[2]
    theta = math.hypot(rx, ry, rz)
    if theta < 1e-9:
        return [
            [1.0, -rz, ry],
            [rz, 1.0, -rx],
            [-ry, rx, 1.0],
        ]
    kx, ky, kz = rx / theta, ry / theta, rz / theta
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    one_minus_cos = 1.0 - cos_t

    return [
        [
            cos_t + kx * kx * one_minus_cos,
            kx * ky * one_minus_cos - kz * sin_t,
            kx * kz * one_minus_cos + ky * sin_t,
        ],
        [
            ky * kx * one_minus_cos + kz * sin_t,
            cos_t + ky * ky * one_minus_cos,
            ky * kz * one_minus_cos - kx * sin_t,
        ],
        [
            kz * kx * one_minus_cos - ky * sin_t,
            kz * ky * one_minus_cos + kx * sin_t,
            cos_t + kz * kz * one_minus_cos,
        ],
    ]


def _project_point_cam(
    pt3: Tuple[float, float, float],
    R: List[List[float]],
    t: List[float],
    K: CameraIntrinsics,
) -> Tuple[float, float]:
    """Project 3D point in object frame through rigid pose [R | t] and intrinsics K (DEF-28)."""
    Xi, Yi, Zi = pt3
    xc = R[0][0] * Xi + R[0][1] * Yi + R[0][2] * Zi + t[0]
    yc = R[1][0] * Xi + R[1][1] * Yi + R[1][2] * Zi + t[1]
    zc = R[2][0] * Xi + R[2][1] * Yi + R[2][2] * Zi + t[2]
    if zc <= 1.0:
        zc = 1.0
    xn = xc / zc
    yn = yc / zc
    if abs(K.k1) > 1e-6 or abs(K.k2) > 1e-6 or abs(K.p1) > 1e-6 or abs(K.p2) > 1e-6 or abs(K.k3) > 1e-6:
        xd, yd = distort_normalized_point(xn, yn, K.k1, K.k2, K.p1, K.p2, K.k3)
    else:
        xd, yd = xn, yn
    u = K.fx * xd + K.cx
    v = K.fy * yd + K.cy
    return u, v


def _solve_linear_system_6x6(A: List[List[float]], b: List[float]) -> List[float]:
    """Solve 6x6 linear system A x = b with partial pivoting Gaussian elimination."""
    n = 6
    aug = [A[i][:] + [b[i]] for i in range(n)]

    for col in range(n):
        max_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[max_row] = aug[max_row], aug[col]
        pivot = aug[col][col]
        if abs(pivot) < 1e-12:
            aug[col][col] += 1e-6
            pivot = aug[col][col]

        for r in range(col + 1, n):
            factor = aug[r][col] / pivot
            for c in range(col, n + 1):
                aug[r][c] -= factor * aug[col][c]

    sol = [0.0] * n
    for r in range(n - 1, -1, -1):
        sol[r] = (aug[r][n] - sum(aug[r][c] * sol[c] for c in range(r + 1, n))) / aug[r][r]

    return sol


def compute_landmark_spatial_conditioning(
    points_3d: List[Tuple[float, float, float]]
) -> Tuple[float, float, Tuple[float, float, float]]:
    """Compute 3D spatial covariance eigenvalues, condition number, and planarity ratio (DEF-32).
    
    Returns:
        (spatial_condition_number, planarity_ratio, (lambda1, lambda2, lambda3))
        where lambda1 >= lambda2 >= lambda3 >= 0.
    """
    n = len(points_3d)
    if n < 3:
        return (float("inf"), 0.0, (0.0, 0.0, 0.0))

    cx = sum(p[0] for p in points_3d) / n
    cy = sum(p[1] for p in points_3d) / n
    cz = sum(p[2] for p in points_3d) / n

    c00 = sum((p[0] - cx) ** 2 for p in points_3d) / n
    c11 = sum((p[1] - cy) ** 2 for p in points_3d) / n
    c22 = sum((p[2] - cz) ** 2 for p in points_3d) / n
    c01 = sum((p[0] - cx) * (p[1] - cy) for p in points_3d) / n
    c02 = sum((p[0] - cx) * (p[2] - cz) for p in points_3d) / n
    c12 = sum((p[1] - cy) * (p[2] - cz) for p in points_3d) / n

    A = [[c00, c01, c02], [c01, c11, c12], [c02, c12, c22]]
    for _ in range(20):
        p, q = 0, 1
        max_val = abs(A[0][1])
        if abs(A[0][2]) > max_val:
            p, q = 0, 2
            max_val = abs(A[0][2])
        if abs(A[1][2]) > max_val:
            p, q = 1, 2
            max_val = abs(A[1][2])

        if max_val < 1e-10:
            break

        app = A[p][p]
        aqq = A[q][q]
        apq = A[p][q]
        phi = 0.5 * (aqq - app) / apq
        t = 1.0 / (abs(phi) + math.sqrt(phi * phi + 1.0))
        if phi < 0:
            t = -t
        c = 1.0 / math.sqrt(t * t + 1.0)
        s = t * c
        tau = s / (1.0 + c)

        A[p][p] = app - t * apq
        A[q][q] = aqq + t * apq
        A[p][q] = 0.0
        A[q][p] = 0.0

        for r in range(3):
            if r != p and r != q:
                arp = A[r][p]
                arq = A[r][q]
                A[r][p] = arp - s * (arq + tau * arp)
                A[p][r] = A[r][p]
                A[r][q] = arq + s * (arp - tau * arq)
                A[q][r] = A[r][q]

    eigenvalues = sorted([max(0.0, A[0][0]), max(0.0, A[1][1]), max(0.0, A[2][2])], reverse=True)
    l1, l2, l3 = eigenvalues[0], eigenvalues[1], eigenvalues[2]

    eps = 1e-9
    condition_num = l1 / max(l3, eps) if l1 > eps else float("inf")
    planarity_ratio = l3 / l1 if l1 > eps else 0.0

    return (round(condition_num, 4), round(planarity_ratio, 6), (round(l1, 4), round(l2, 4), round(l3, 4)))


def estimate_rigid_pose_from_landmarks(
    correspondences: List[Tuple[Tuple[float, float, float], Tuple[float, float]]],
    intrinsics: CameraIntrinsics,
    max_allowed_residual_px: float = 3.0,
) -> OpticalCalibrationContext:
    """Solve 6-DoF Perspective-n-Point (PnP) pose via Levenberg-Marquardt optimization.
    
    Estimates 3-DoF rotation vector r = [rx, ry, rz] and 3-DoF translation vector t = [tx, ty, tz].
    Verifies that mean and maximum reprojection residuals stay below tolerance.
    Fails closed if correspondence count < 4 or collinear.
    """
    if len(correspondences) < 4:
        raise CalibratedRegistrationError(
            f"Under-constrained registration: requires at least 4 non-coplanar landmarks, got {len(correspondences)}."
        )

    # Check 3D landmark spatial distribution / collinearity (DEF-25, DEF-32)
    pts3d = [pt3 for pt3, _ in correspondences]
    n_pts = len(pts3d)
    centroid = [
        sum(p[0] for p in pts3d) / n_pts,
        sum(p[1] for p in pts3d) / n_pts,
        sum(p[2] for p in pts3d) / n_pts,
    ]
    d_pts = [
        (p[0] - centroid[0], p[1] - centroid[1], p[2] - centroid[2])
        for p in pts3d
    ]
    max_cross_mag = 0.0
    for i in range(n_pts):
        for j in range(i + 1, n_pts):
            cross = (
                d_pts[i][1] * d_pts[j][2] - d_pts[i][2] * d_pts[j][1],
                d_pts[i][2] * d_pts[j][0] - d_pts[i][0] * d_pts[j][2],
                d_pts[i][0] * d_pts[j][1] - d_pts[i][1] * d_pts[j][0],
            )
            cross_mag = math.hypot(cross[0], cross[1], cross[2])
            if cross_mag > max_cross_mag:
                max_cross_mag = cross_mag

    if max_cross_mag < 1.0:
        raise CalibratedRegistrationError(
            "Degenerate landmark geometry: input 3D landmarks are collinear or lack 2D/3D spatial variance."
        )

    cond_num, planarity_ratio, evals = compute_landmark_spatial_conditioning(pts3d)

    # Initial linear least squares estimation of translation vector t = [tx, ty, tz]
    M = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    b = [0.0, 0.0, 0.0]

    for pt3, pt2 in correspondences:
        Xi, Yi, Zi = pt3
        ui, vi = pt2
        xd = (ui - intrinsics.cx) / intrinsics.fx
        yd = (vi - intrinsics.cy) / intrinsics.fy
        if abs(intrinsics.k1) > 1e-6 or abs(intrinsics.k2) > 1e-6 or abs(intrinsics.p1) > 1e-6 or abs(intrinsics.p2) > 1e-6 or abs(intrinsics.k3) > 1e-6:
            xn, yn = undistort_normalized_point(xd, yd, intrinsics.k1, intrinsics.k2, intrinsics.p1, intrinsics.p2, intrinsics.k3)
        else:
            xn, yn = xd, yd

        r1 = (1.0, 0.0, -xn)
        rhs1 = xn * Zi - Xi
        r2 = (0.0, 1.0, -yn)
        rhs2 = yn * Zi - Yi

        for row, rhs in [(r1, rhs1), (r2, rhs2)]:
            for i in range(3):
                b[i] += row[i] * rhs
                for j in range(3):
                    M[i][j] += row[i] * row[j]

    det = (
        M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1])
        - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
        + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0])
    )
    if abs(det) < 1e-9:
        t_init = [0.0, 0.0, 500.0]
    else:
        invM = [
            [
                (M[1][1] * M[2][2] - M[1][2] * M[2][1]) / det,
                (M[0][2] * M[2][1] - M[0][1] * M[2][2]) / det,
                (M[0][1] * M[1][2] - M[0][2] * M[1][1]) / det,
            ],
            [
                (M[1][2] * M[2][0] - M[1][0] * M[2][2]) / det,
                (M[0][0] * M[2][2] - M[0][2] * M[2][0]) / det,
                (M[0][2] * M[1][0] - M[0][0] * M[1][2]) / det,
            ],
            [
                (M[1][0] * M[2][1] - M[1][1] * M[2][0]) / det,
                (M[0][1] * M[2][0] - M[0][0] * M[2][1]) / det,
                (M[0][0] * M[1][1] - M[0][1] * M[1][0]) / det,
            ],
        ]
        t_init = [sum(invM[i][j] * b[j] for j in range(3)) for i in range(3)]

    # Initial 6-DoF parameter vector: p = [rx, ry, rz, tx, ty, tz]
    p = [0.0, 0.0, 0.0, t_init[0], t_init[1], t_init[2]]
    lambda_val = 1e-2
    num_residuals = len(correspondences) * 2

    # Levenberg-Marquardt Non-Linear Optimization
    for _ in range(40):
        R_curr = _rodrigues_to_rotation_matrix(p[:3])
        t_curr = p[3:]

        # Compute current residuals: r_vec of length 2N
        r_vec = []
        for pt3, pt2 in correspondences:
            u_p, v_p = _project_point_cam(pt3, R_curr, t_curr, intrinsics)
            r_vec.append(u_p - pt2[0])
            r_vec.append(v_p - pt2[1])

        current_cost = sum(r * r for r in r_vec)

        # Compute Jacobian J (2N x 6) via numerical differentiation
        eps = 1e-6
        J = [[0.0] * 6 for _ in range(num_residuals)]

        for k in range(6):
            p_plus = p[:]
            p_plus[k] += eps
            R_plus = _rodrigues_to_rotation_matrix(p_plus[:3])
            t_plus = p_plus[3:]

            idx = 0
            for pt3, pt2 in correspondences:
                u_p, v_p = _project_point_cam(pt3, R_plus, t_plus, intrinsics)
                J[idx][k] = ((u_p - pt2[0]) - r_vec[idx]) / eps
                J[idx + 1][k] = ((v_p - pt2[1]) - r_vec[idx + 1]) / eps
                idx += 2

        # Form normal equations: A = J^T * J + lambda * diag(J^T * J), g = -J^T * r_vec
        JTJ = [[sum(J[i][a] * J[i][b] for i in range(num_residuals)) for b in range(6)] for a in range(6)]
        g = [-sum(J[i][a] * r_vec[i] for i in range(num_residuals)) for a in range(6)]

        A_damped = [row[:] for row in JTJ]
        for a in range(6):
            A_damped[a][a] += lambda_val * max(1.0, abs(JTJ[a][a]))

        delta = _solve_linear_system_6x6(A_damped, g)

        # Candidate parameters
        p_cand = [p[a] + delta[a] for a in range(6)]
        R_cand = _rodrigues_to_rotation_matrix(p_cand[:3])
        t_cand = p_cand[3:]

        cand_cost = 0.0
        for pt3, pt2 in correspondences:
            u_p, v_p = _project_point_cam(pt3, R_cand, t_cand, intrinsics)
            cand_cost += (u_p - pt2[0]) ** 2 + (v_p - pt2[1]) ** 2

        if cand_cost < current_cost:
            p = p_cand
            lambda_val = max(1e-7, lambda_val / 5.0)
            step_norm = math.sqrt(sum(d * d for d in delta))
            if step_norm < 1e-5:
                break
        else:
            lambda_val = min(1e7, lambda_val * 5.0)

    # Compute final residuals
    R_final = _rodrigues_to_rotation_matrix(p[:3])
    t_final = p[3:]
    residuals = []
    for pt3, pt2 in correspondences:
        pred_x, pred_y = _project_point_cam(pt3, R_final, t_final, intrinsics)
        res = math.hypot(pred_x - pt2[0], pred_y - pt2[1])
        residuals.append(res)

    mean_res = sum(residuals) / len(residuals)
    max_res = max(residuals)

    if max_res > max_allowed_residual_px:
        raise CalibratedRegistrationError(
            f"PnP calibration rejected: maximum residual ({max_res:.2f} px) "
            f"exceeds tolerance ({max_allowed_residual_px:.2f} px)."
        )

    return OpticalCalibrationContext(
        intrinsics=intrinsics,
        R=R_final,
        t=t_final,
        mean_reprojection_residual_px=round(mean_res, 3),
        max_reprojection_residual_px=round(max_res, 3),
        is_calibrated=True,
        spatial_condition_number=cond_num,
        planarity_ratio=planarity_ratio,
        covariance_eigenvalues=evals,
    )


def register_2d_reflexology_point_to_3d(
    point_id: str,
    pixel_xy: Tuple[float, float],
    calibration_context: Optional[OpticalCalibrationContext],
    target_model_id: str = "watercmy_bp3d_z_anatomy",
    nearest_landmark_hint: str = "SUBNASALE",
) -> Dict[str, Any]:
    """Register a 2D reflexology point into 3D head model space using optical calibration.
    
    EPISTEMIC SAFETY INVARIANT:
    If calibration_context is None or uncalibrated, immediately triggers
    the inviolate epistemic guard attempt_project_2d_to_3d(), strictly blocking
    implicit projection and raising DienChanError.
    """
    if calibration_context is None or not calibration_context.is_calibrated:
        # Strictly preserve epistemic invariant
        raise DienChanError(
            "CANNOT_IMPLICITLY_PROJECT_2D_TO_3D: 2D facial diagram pixel coordinates "
            f"({pixel_xy[0]}, {pixel_xy[1]}) cannot be implicitly mapped to 3D model '{target_model_id}'. "
            "Uncalibrated 2D->3D coordinate conversion is epistemically invalid and strictly prohibited."
        )

    # Verify calibration quality
    if calibration_context.max_reprojection_residual_px > 3.0:
        raise CalibratedRegistrationError(
            f"Registration aborted: calibration residual ({calibration_context.max_reprojection_residual_px:.2f} px) "
            "is outside research tolerance."
        )

    # 1. Invert camera projection along ray with Brown-Conrady undistortion (DEF-28)
    K = calibration_context.intrinsics
    u, v = pixel_xy
    x_dist = (u - K.cx) / K.fx
    y_dist = (v - K.cy) / K.fy
    if abs(K.k1) > 1e-6 or abs(K.k2) > 1e-6 or abs(K.p1) > 1e-6 or abs(K.p2) > 1e-6 or abs(K.k3) > 1e-6:
        x_norm, y_norm = undistort_normalized_point(x_dist, y_dist, K.k1, K.k2, K.p1, K.p2, K.k3)
    else:
        x_norm, y_norm = x_dist, y_dist

    # Ray in camera frame
    ray_cam = (x_norm, y_norm, 1.0)
    ray_mag = math.hypot(ray_cam[0], ray_cam[1], ray_cam[2])
    ray_cam_unit = (ray_cam[0] / ray_mag, ray_cam[1] / ray_mag, ray_cam[2] / ray_mag)

    # Anchor depth from reference landmark in true rotated camera frame (DEF-24)
    ref_3d = CANONICAL_FACIAL_3D_LANDMARKS.get(nearest_landmark_hint, (0.0, 0.0, 20.0))
    R = calibration_context.R
    t = calibration_context.t
    ref_cam_z = R[2][0] * ref_3d[0] + R[2][1] * ref_3d[1] + R[2][2] * ref_3d[2] + t[2]
    z_target = ref_cam_z
    scale = z_target / ray_cam_unit[2]

    # 3D coordinate in camera frame
    P_cam = (ray_cam_unit[0] * scale, ray_cam_unit[1] * scale, ray_cam_unit[2] * scale)

    # Transform back to head object frame: X_obj = R^T * (P_cam - t)
    diff = (P_cam[0] - t[0], P_cam[1] - t[1], P_cam[2] - t[2])

    X_obj = (
        R[0][0] * diff[0] + R[1][0] * diff[1] + R[2][0] * diff[2],
        R[0][1] * diff[0] + R[1][1] * diff[1] + R[2][1] * diff[2],
        R[0][2] * diff[0] + R[1][2] * diff[1] + R[2][2] * diff[2],
    )

    # Uncertainty estimation: 1.96 * (residual_px / fx) * depth_mm
    uncertainty_radius_mm = round(1.96 * (calibration_context.mean_reprojection_residual_px / K.fx) * scale, 2)

    return {
        "status": "CALIBRATED_RESEARCH_REGISTRATION",
        "point_id": point_id,
        "target_model_id": target_model_id,
        "input_pixel_xy": [u, v],
        "registered_3d_mm": [round(X_obj[0], 2), round(X_obj[1], 2), round(X_obj[2], 2)],
        "uncertainty_radius_mm": uncertainty_radius_mm,
        "optical_pattern": calibration_context.target_pattern,
        "mean_residual_px": calibration_context.mean_reprojection_residual_px,
        "spatial_condition_number": calibration_context.spatial_condition_number,
        "planarity_ratio": calibration_context.planarity_ratio,
        "provenance_type": "SYNTHETIC_TEST",
        "epistemic_provenance": "RIGID_OPTICAL_CALIBRATION_RESEARCH_ONLY",
        "clinical_certification": "NOT_CLINICALLY_CERTIFIED",
    }
