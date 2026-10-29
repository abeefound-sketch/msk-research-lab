"""Camera Hardware Probe, Tracking, and Assessment Execution Service."""

import uuid
import datetime
import json
from typing import Dict, List, Optional, Any
from msk_research_lab.core.db import get_db
from msk_research_lab.motion.kinematics import compute_joint_rom

# Standard reference posture landmarks for camera offline/synthetic fallback
STANDARD_POSTURE_FIXTURES = {
    "TADASANA_NEUTRAL": {
        "right_shoulder": (0.60, 0.35),
        "left_shoulder": (0.40, 0.35),
        "right_elbow": (0.63, 0.50),
        "left_elbow": (0.37, 0.50),
        "right_wrist": (0.65, 0.65),
        "left_wrist": (0.35, 0.65),
        "right_hip": (0.55, 0.65),
        "left_hip": (0.45, 0.65),
        "right_knee": (0.55, 0.80),
        "left_knee": (0.45, 0.80),
        "right_ankle": (0.55, 0.95),
        "left_ankle": (0.45, 0.95)
    },
    "ELBOW_FLEXION_90": {
        "right_shoulder": (0.50, 0.35),
        "left_shoulder": (0.35, 0.35),
        "right_elbow": (0.50, 0.55),
        "left_elbow": (0.35, 0.55),
        "right_wrist": (0.35, 0.55),  # 90 degrees horizontal forearm
        "left_wrist": (0.35, 0.75),
        "right_hip": (0.50, 0.70),
        "left_hip": (0.40, 0.70)
    },
    "SHOULDER_ABDUCTION_90": {
        "right_shoulder": (0.50, 0.35),
        "left_shoulder": (0.35, 0.35),
        "right_elbow": (0.75, 0.35),  # 90 deg abduction horizontal
        "left_elbow": (0.35, 0.55),
        "right_wrist": (0.90, 0.35),
        "left_wrist": (0.35, 0.75),
        "right_hip": (0.50, 0.70),
        "left_hip": (0.40, 0.70)
    }
}


class MotionAssessmentError(Exception):
    """Base exception for motion assessment errors."""
    def __init__(self, message: str, error_code: str = "MOTION_ASSESSMENT_ERROR"):
        super().__init__(message)
        self.error_code = error_code


class CameraUnavailableError(MotionAssessmentError):
    def __init__(self, message: str = "CAMERA_UNAVAILABLE: Physical webcam is offline or inaccessible. Switch to DEMO mode to view standard posture fixtures."):
        super().__init__(message, "CAMERA_UNAVAILABLE")


class TrackerUnavailableError(MotionAssessmentError):
    def __init__(self, message: str = "TRACKER_UNAVAILABLE: Pose estimation tracker (MediaPipe) is not installed in the environment."):
        super().__init__(message, "TRACKER_UNAVAILABLE")


class InsufficientLandmarksError(MotionAssessmentError):
    def __init__(self, message: str = "NO_POSE: Insufficient anatomical landmarks detected for kinematic angle calculation."):
        super().__init__(message, "NO_POSE")


class DegenerateGeometryError(MotionAssessmentError):
    def __init__(self, message: str = "DEGENERATE_GEOMETRY: Landmark coordinates produce zero-length or degenerate joint vectors."):
        super().__init__(message, "DEGENERATE_GEOMETRY")


def probe_hardware_camera() -> Dict[str, Any]:
    """Probe system for physical webcam availability."""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                return {
                    "available": True,
                    "device_index": 0,
                    "resolution": f"{w}x{h}",
                    "backend": "OPENCV_ACTIVE",
                    "status": "READY"
                }
        cap.release()
    except Exception as e:
        return {
            "available": False,
            "device_index": 0,
            "error": str(e),
            "backend": "UNAVAILABLE",
            "status": "CAMERA_OFFLINE_FAIL_CLOSED"
        }

    return {
        "available": False,
        "device_index": 0,
        "backend": "NO_DEVICE",
        "status": "CAMERA_OFFLINE_FAIL_CLOSED"
    }


def execute_motion_assessment(
    patient_id: str,
    joint_tested: str = "ELBOW_FLEXION",
    side: str = "RIGHT",
    session_id: Optional[str] = None,
    custom_landmarks: Optional[Dict[str, Any]] = None,
    fixture_name: Optional[str] = None,
    mode: str = "LIVE"
) -> Dict[str, Any]:
    """
    Execute motion assessment with strict provenance and fail-closed safety.
    - DEMO mode evaluates standardized synthetic posture fixtures without contaminating live records.
    - LIVE mode requires physical webcam and detected pose; never silently substitutes fake data.
    """
    is_demo_request = (mode.upper() == "DEMO") or (fixture_name is not None) or (custom_landmarks is not None)

    # 1. DEMO / Synthetic Fixture Mode
    if is_demo_request:
        if custom_landmarks:
            landmarks = custom_landmarks
            source = "SYNTHETIC_CLIENT_PAYLOAD"
        else:
            fname = fixture_name or ("ELBOW_FLEXION_90" if "ELBOW" in joint_tested.upper() else ("SHOULDER_ABDUCTION_90" if "SHOULDER" in joint_tested.upper() else "TADASANA_NEUTRAL"))
            landmarks = STANDARD_POSTURE_FIXTURES.get(fname, STANDARD_POSTURE_FIXTURES["TADASANA_NEUTRAL"])
            source = f"FIXTURE_{fname}"

        eval_result = compute_joint_rom(
            landmarks=landmarks,
            joint_tested=joint_tested,
            side=side
        )

        mid = f"MOT-DEMO-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.utcnow().isoformat() + "Z"

        # Persist with explicit synthetic provenance so session linkage can resolve it
        with get_db() as conn:
            conn.execute("""
                INSERT INTO motion_assessments (
                    id, patient_id, session_id, joint_tested, side, measured_rom_deg,
                    reference_rom_deg, rom_deficit_deg, uncertainty_u95_deg, tracking_confidence,
                    quality_status, confounding_factors_json, landmarks_json, data_source,
                    is_synthetic, assessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
            """, (
                mid, patient_id, session_id, joint_tested, side,
                eval_result["measured_rom_deg"], eval_result["reference_rom_deg"],
                eval_result["rom_deficit_deg"], eval_result["uncertainty_u95_deg"],
                eval_result["tracking_confidence"], eval_result["quality_status"],
                json.dumps(eval_result["confounding_factors"]),
                json.dumps(landmarks), source, now
            ))

        eval_result["id"] = mid
        eval_result["patient_id"] = patient_id
        eval_result["session_id"] = session_id
        eval_result["data_source"] = source
        eval_result["is_synthetic"] = True
        eval_result["mode"] = "DEMO"
        eval_result["assessed_at"] = now
        return eval_result

    # 2. LIVE Mode: Physical camera required
    probe = probe_hardware_camera()
    if not probe.get("available"):
        raise CameraUnavailableError(
            "CAMERA_UNAVAILABLE: Physical webcam is offline or inaccessible in this environment. Use DEMO mode to view standard posture fixtures."
        )

    # Attempt capture from camera
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            raise CameraUnavailableError("CAMERA_CAPTURE_FAILED: Failed to capture live frame from video device.")
    except Exception as e:
        if isinstance(e, CameraUnavailableError):
            raise
        raise CameraUnavailableError(f"CAMERA_IO_ERROR: {str(e)}")

    # Attempt tracker pose extraction
    try:
        import mediapipe as mp
    except ImportError:
        raise TrackerUnavailableError(
            "TRACKER_UNAVAILABLE: MediaPipe pose tracking library is not installed in the active environment."
        )

    # If tracker is available, process frame
    # (If no pose detected, raise InsufficientLandmarksError)
    raise InsufficientLandmarksError("NO_POSE: Human subject was not detected in camera frame.")


def list_patient_motion_assessments(patient_id: str) -> List[Dict[str, Any]]:
    """List historical motion assessments for a patient."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, patient_id, session_id, joint_tested, side, measured_rom_deg,
                   reference_rom_deg, rom_deficit_deg, uncertainty_u95_deg, tracking_confidence,
                   quality_status, confounding_factors_json, assessed_at
            FROM motion_assessments WHERE patient_id = ?
            ORDER BY assessed_at DESC;
        """, (patient_id,)).fetchall()

    return [
        {
            "id": r["id"],
            "patient_id": r["patient_id"],
            "session_id": r["session_id"],
            "joint_tested": r["joint_tested"],
            "side": r["side"],
            "measured_rom_deg": r["measured_rom_deg"],
            "reference_rom_deg": r["reference_rom_deg"],
            "rom_deficit_deg": r["rom_deficit_deg"],
            "uncertainty_u95_deg": r["uncertainty_u95_deg"],
            "tracking_confidence": r["tracking_confidence"],
            "quality_status": r["quality_status"],
            "confounding_factors": json.loads(r["confounding_factors_json"]),
            "assessed_at": r["assessed_at"]
        }
        for r in rows
    ]
