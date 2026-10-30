"""Metrological Camera Calibration, Lens Distortion Modeling, and Uncertainty Engine (ISO GUM / VIM)."""

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CameraIntrinsics:
    """Pinhole camera intrinsic parameters and Brown-Conrady distortion coefficients."""
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    k1: float = 0.0  # Radial distortion 1
    k2: float = 0.0  # Radial distortion 2
    p1: float = 0.0  # Tangential distortion 1
    p2: float = 0.0  # Tangential distortion 2
    k3: float = 0.0  # Radial distortion 3
    calibration_date: Optional[str] = None
    device_name: str = "GENERIC_PINHOLE_65DEG"

    @property
    def camera_matrix(self) -> List[List[float]]:
        """Return 3x3 camera matrix K."""
        return [
            [self.fx, 0.0, self.cx],
            [0.0, self.fy, self.cy],
            [0.0, 0.0, 1.0],
        ]

    @property
    def distortion_coeffs(self) -> List[float]:
        """Return [k1, k2, p1, p2, k3]."""
        return [self.k1, self.k2, self.p1, self.p2, self.k3]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CameraIntrinsics":
        return cls(**data)


def create_standard_intrinsics(
    width: int = 1280,
    height: int = 720,
    hfov_deg: float = 65.0,
    k1: float = -0.04,  # Moderate barrel distortion typical of standard wide webcams
    k2: float = 0.01,
    p1: float = 0.001,
    p2: float = 0.0005,
    k3: float = 0.0,
    device_name: str = "CALIBRATED_BENCHMARK_WEBCAM",
) -> CameraIntrinsics:
    """Create nominal calibrated intrinsic model from horizontal FOV and resolution."""
    fov_rad = math.radians(hfov_deg)
    fx = (width / 2.0) / math.tan(fov_rad / 2.0)
    fy = fx  # Square pixels
    cx = width / 2.0
    cy = height / 2.0

    return CameraIntrinsics(
        width=width,
        height=height,
        fx=fx,
        fy=fy,
        cx=cx,
        cy=cy,
        k1=k1,
        k2=k2,
        p1=p1,
        p2=p2,
        k3=k3,
        device_name=device_name,
    )


def distort_normalized_point(
    x: float,
    y: float,
    k1: float,
    k2: float,
    p1: float,
    p2: float,
    k3: float = 0.0,
) -> Tuple[float, float]:
    """Apply forward Brown-Conrady polynomial radial and tangential distortion.
    
    Given ideal normalized coordinates (x = X/Z, y = Y/Z):
    r^2 = x^2 + y^2
    radial_factor = 1 + k1*r^2 + k2*r^4 + k3*r^6
    x_dist = x * radial_factor + 2*p1*x*y + p2*(r^2 + 2*x^2)
    y_dist = y * radial_factor + p1*(r^2 + 2*y^2) + 2*p2*x*y
    """
    r2 = x * x + y * y
    radial = 1.0 + k1 * r2 + k2 * (r2 * r2) + k3 * (r2 * r2 * r2)
    x_dist = x * radial + 2.0 * p1 * x * y + p2 * (r2 + 2.0 * x * x)
    y_dist = y * radial + p1 * (r2 + 2.0 * y * y) + 2.0 * p2 * x * y
    return (x_dist, y_dist)


def undistort_normalized_point(
    x_dist: float,
    y_dist: float,
    k1: float,
    k2: float,
    p1: float,
    p2: float,
    k3: float = 0.0,
    iterations: int = 5,
) -> Tuple[float, float]:
    """Inverse distortion using fixed-point iteration."""
    x = x_dist
    y = y_dist
    for _ in range(iterations):
        r2 = x * x + y * y
        radial = 1.0 + k1 * r2 + k2 * (r2 * r2) + k3 * (r2 * r2 * r2)
        if abs(radial) < 1e-9:
            break
        delta_x = 2.0 * p1 * x * y + p2 * (r2 + 2.0 * x * x)
        delta_y = p1 * (r2 + 2.0 * y * y) + 2.0 * p2 * x * y
        x = (x_dist - delta_x) / radial
        y = (y_dist - delta_y) / radial
    return (x, y)


def pixel_to_normalized(px: float, py: float, K: CameraIntrinsics) -> Tuple[float, float]:
    """Convert pixel coordinates to normalized camera coordinates."""
    return ((px - K.cx) / K.fx, (py - K.cy) / K.fy)


def normalized_to_pixel(nx: float, ny: float, K: CameraIntrinsics) -> Tuple[float, float]:
    """Convert normalized camera coordinates to pixel coordinates."""
    return (nx * K.fx + K.cx, ny * K.fy + K.cy)


# ==============================================================================
# Metrological Uncertainty Validation Protocol
# ==============================================================================

def compute_projected_angle_under_yaw(
    true_angle_deg: float,
    yaw_deg: float,
    pitch_deg: float = 0.0,
) -> float:
    """Calculate apparent 2D monocular angle when planar joint is rotated out-of-plane.
    
    In-plane vectors:
    v1 = [0, 1, 0] (e.g. upper arm along Y)
    v2 = [sin(alpha), cos(alpha), 0] (e.g. forearm flexed at true angle alpha)
    
    When rotated by yaw (rotation around Y-axis) and pitch (around X-axis):
    v' = R_x(pitch) * R_y(yaw) * v
    The projected 2D vectors onto image plane are (v'_x, v'_y).
    """
    alpha = math.radians(true_angle_deg)
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)

    # Rotation matrix R_y(yaw):
    # [ cos(y)  0  sin(y) ]
    # [    0    1    0    ]
    # [-sin(y)  0  cos(y) ]
    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    cos_p, sin_p = math.cos(pitch), math.sin(pitch)

    # v1 = [0, 1, 0]
    # R_y * v1 = [0, 1, 0]
    # R_x * [0, 1, 0] = [0, cos(p), -sin(p)]
    v1_proj = (0.0, cos_p)

    # v2 = [sin(alpha), cos(alpha), 0]
    # R_y * v2 = [sin(alpha)*cos(y), cos(alpha), -sin(alpha)*sin(y)]
    # Apply R_x:
    v2_y_rot = cos_y * math.sin(alpha)
    v2_p_y = cos_p * math.cos(alpha) - sin_p * (-sin_y * math.sin(alpha))
    v2_proj = (v2_y_rot, v2_p_y)

    mag1 = math.hypot(v1_proj[0], v1_proj[1])
    mag2 = math.hypot(v2_proj[0], v2_proj[1])

    if mag1 < 1e-7 or mag2 < 1e-7:
        return 0.0

    dot = v1_proj[0] * v2_proj[0] + v1_proj[1] * v2_proj[1]
    cos_app = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_app))


def evaluate_empirical_repeatability(
    repeated_samples: List[float],
    reference_angle: Optional[float] = None,
    u_resolution: float = 0.5,
    u_distortion: float = 0.4,
) -> Dict[str, Any]:
    """Perform rigorous ISO Guide 98-3 (GUM) uncertainty analysis distinguishing
    Type A empirical sample dispersion from Type B theoretical bounds.
    """
    n = len(repeated_samples)
    if n < 2:
        val = repeated_samples[0] if n == 1 else 0.0
        return {
            "sample_size": n,
            "mean_rom_deg": val,
            "std_dev_deg": 0.0,
            "std_error_deg": 0.0,
            "max_spread_deg": 0.0,
            "systematic_bias_deg": abs(val - reference_angle) if reference_angle is not None else None,
            "u95_theoretical_deg": 2.01,
            "u95_combined_deg": 2.01,
            "is_statistically_valid": False,
        }

    mean_val = sum(repeated_samples) / n
    variance = sum((x - mean_val) ** 2 for x in repeated_samples) / (n - 1)
    s = math.sqrt(variance)  # Type A standard uncertainty (empirical repeatability)
    std_error = s / math.sqrt(n)
    spread = max(repeated_samples) - min(repeated_samples)

    # Systematic bias against reference if known
    bias = abs(mean_val - reference_angle) if reference_angle is not None else None

    # Combined GUM Uncertainty (Type A + Type B)
    # u_c^2 = s^2 + u_res^2 + u_dist^2
    u_combined = math.sqrt(s**2 + u_resolution**2 + u_distortion**2)
    coverage_k = 1.96  # Gaussian 95% confidence interval
    u95_combined = round(coverage_k * u_combined, 2)

    return {
        "sample_size": n,
        "mean_rom_deg": round(mean_val, 2),
        "std_dev_deg": round(s, 3),
        "std_error_deg": round(std_error, 3),
        "max_spread_deg": round(spread, 3),
        "reference_angle_deg": reference_angle,
        "systematic_bias_deg": round(bias, 3) if bias is not None else None,
        "type_a_empirical_s": round(s, 3),
        "type_b_resolution": u_resolution,
        "type_b_distortion": u_distortion,
        "u95_combined_deg": u95_combined,
        "is_statistically_valid": True,
    }
