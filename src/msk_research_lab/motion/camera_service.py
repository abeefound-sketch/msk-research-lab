"""Camera Hardware Probe, Tracking, and Assessment Execution Service."""

import uuid
import datetime
import json
from pathlib import Path
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


def _extract_live_pose(frame) -> Dict[str, Dict[str, float]]:
    """Extract 33-point anatomical landmarks from a live frame via MediaPipe Tasks or Solutions."""
    import cv2
    try:
        import mediapipe as mp
    except ImportError:
        raise TrackerUnavailableError(
            "TRACKER_UNAVAILABLE: MediaPipe pose tracking library is not installed in the active environment."
        )

    # 1. Try MediaPipe Tasks API (MediaPipe 1.0+)
    candidate_model_paths = [
        Path("2data/models/pose_landmarker_lite.task"),
        Path(__file__).resolve().parents[3] / "2data" / "models" / "pose_landmarker_lite.task",
        Path("C:/Users/tuanh/Downloads/msk-research-lab/2data/models/pose_landmarker_lite.task"),
        Path("C:/Users/tuanh/MSK-Pose-Vision-Bridge/configs/pose_landmarker_lite.task"),
        Path("/mnt/c/Users/tuanh/MSK-Pose-Vision-Bridge/configs/pose_landmarker_lite.task"),
    ]
    task_model = None
    for p in candidate_model_paths:
        try:
            if p.exists():
                task_model = str(p.resolve())
                break
        except Exception:
            pass

    if hasattr(mp, "tasks") and task_model:
        try:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision as mp_vision

            base_options = mp_python.BaseOptions(model_asset_path=task_model)
            options = mp_vision.PoseLandmarkerOptions(base_options=base_options, min_pose_detection_confidence=0.5)
            with mp_vision.PoseLandmarker.create_from_options(options) as landmarker:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                res = landmarker.detect(mp_img)
                if not res or not res.pose_landmarks:
                    raise InsufficientLandmarksError("NO_POSE: Human subject was not detected in camera frame.")
                raw = res.pose_landmarks[0]
                return {
                    "left_shoulder": {"x": raw[11].x, "y": raw[11].y, "z": raw[11].z, "visibility": getattr(raw[11], "visibility", 1.0)},
                    "right_shoulder": {"x": raw[12].x, "y": raw[12].y, "z": raw[12].z, "visibility": getattr(raw[12], "visibility", 1.0)},
                    "left_elbow": {"x": raw[13].x, "y": raw[13].y, "z": raw[13].z, "visibility": getattr(raw[13], "visibility", 1.0)},
                    "right_elbow": {"x": raw[14].x, "y": raw[14].y, "z": raw[14].z, "visibility": getattr(raw[14], "visibility", 1.0)},
                    "left_wrist": {"x": raw[15].x, "y": raw[15].y, "z": raw[15].z, "visibility": getattr(raw[15], "visibility", 1.0)},
                    "right_wrist": {"x": raw[16].x, "y": raw[16].y, "z": raw[16].z, "visibility": getattr(raw[16], "visibility", 1.0)},
                    "left_hip": {"x": raw[23].x, "y": raw[23].y, "z": raw[23].z, "visibility": getattr(raw[23], "visibility", 1.0)},
                    "right_hip": {"x": raw[24].x, "y": raw[24].y, "z": raw[24].z, "visibility": getattr(raw[24], "visibility", 1.0)},
                    "left_knee": {"x": raw[25].x, "y": raw[25].y, "z": raw[25].z, "visibility": getattr(raw[25], "visibility", 1.0)},
                    "right_knee": {"x": raw[26].x, "y": raw[26].y, "z": raw[26].z, "visibility": getattr(raw[26], "visibility", 1.0)},
                    "left_ankle": {"x": raw[27].x, "y": raw[27].y, "z": raw[27].z, "visibility": getattr(raw[27], "visibility", 1.0)},
                    "right_ankle": {"x": raw[28].x, "y": raw[28].y, "z": raw[28].z, "visibility": getattr(raw[28], "visibility", 1.0)},
                }
        except InsufficientLandmarksError:
            raise
        except Exception:
            pass

    # 2. Try legacy MediaPipe solutions.pose
    if hasattr(mp, "solutions") and hasattr(mp.solutions, "pose"):
        mp_pose = mp.solutions.pose
        with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)
            if not results or not results.pose_landmarks:
                raise InsufficientLandmarksError("NO_POSE: Human subject was not detected in camera frame.")
            raw = results.pose_landmarks.landmark
            return {
                "left_shoulder": {"x": raw[11].x, "y": raw[11].y, "z": raw[11].z, "visibility": raw[11].visibility},
                "right_shoulder": {"x": raw[12].x, "y": raw[12].y, "z": raw[12].z, "visibility": raw[12].visibility},
                "left_elbow": {"x": raw[13].x, "y": raw[13].y, "z": raw[13].z, "visibility": raw[13].visibility},
                "right_elbow": {"x": raw[14].x, "y": raw[14].y, "z": raw[14].z, "visibility": raw[14].visibility},
                "left_wrist": {"x": raw[15].x, "y": raw[15].y, "z": raw[15].z, "visibility": raw[15].visibility},
                "right_wrist": {"x": raw[16].x, "y": raw[16].y, "z": raw[16].z, "visibility": raw[16].visibility},
                "left_hip": {"x": raw[23].x, "y": raw[23].y, "z": raw[23].z, "visibility": raw[23].visibility},
                "right_hip": {"x": raw[24].x, "y": raw[24].y, "z": raw[24].z, "visibility": raw[24].visibility},
                "left_knee": {"x": raw[25].x, "y": raw[25].y, "z": raw[25].z, "visibility": raw[25].visibility},
                "right_knee": {"x": raw[26].x, "y": raw[26].y, "z": raw[26].z, "visibility": raw[26].visibility},
                "left_ankle": {"x": raw[27].x, "y": raw[27].y, "z": raw[27].z, "visibility": raw[27].visibility},
                "right_ankle": {"x": raw[28].x, "y": raw[28].y, "z": raw[28].z, "visibility": raw[28].visibility},
            }

    # If neither tracker is operational or model not found
    raise TrackerUnavailableError(
        "TRACKER_UNAVAILABLE: MediaPipe pose model or solution unavailable for inference."
    )


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

    # Extract 33-point pose landmarks from live video frame
    landmarks = _extract_live_pose(frame)

    eval_result = compute_joint_rom(
        landmarks=landmarks,
        joint_tested=joint_tested,
        side=side
    )

    mid = f"MOT-LIVE-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.utcnow().isoformat() + "Z"

    with get_db() as conn:
        conn.execute("""
            INSERT INTO motion_assessments (
                id, patient_id, session_id, joint_tested, side, measured_rom_deg,
                reference_rom_deg, rom_deficit_deg, uncertainty_u95_deg, tracking_confidence,
                quality_status, confounding_factors_json, landmarks_json, data_source,
                is_synthetic, assessed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'HARDWARE_CAMERA', 0, ?);
        """, (
            mid, patient_id, session_id, joint_tested, side,
            eval_result["measured_rom_deg"], eval_result["reference_rom_deg"],
            eval_result["rom_deficit_deg"], eval_result["uncertainty_u95_deg"],
            eval_result["tracking_confidence"], eval_result["quality_status"],
            json.dumps(eval_result["confounding_factors"]),
            json.dumps(landmarks), now
        ))

    eval_result["id"] = mid
    eval_result["patient_id"] = patient_id
    eval_result["session_id"] = session_id
    eval_result["data_source"] = "HARDWARE_CAMERA"
    eval_result["is_synthetic"] = False
    eval_result["mode"] = "LIVE"
    eval_result["assessed_at"] = now
    return eval_result


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
