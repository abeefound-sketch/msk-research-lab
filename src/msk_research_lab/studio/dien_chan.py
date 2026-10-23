"""Diện Chẩn 2D Facial Atlas Annotation & Epistemic Guards (ATLAS-06 / R5-03 / R5-04).

Enforces:
  1. Image SHA-256 & pixel coordinates (x_px, y_px) for front/profile facial maps.
  2. Epistemic Guard: 2D pixel locators CANNOT be implicitly converted to 3D without
     calibrated photogrammetric landmark registration.
  3. Strict separation of Fixed Educational References vs Session-Specific Reactive Observations.
  4. Epistemic Guard: A reactive observation point cannot be promoted to a universal global standard.
  5. Privacy Guard: Synthetic session IDs only; real patient identifiers/PII prohibited.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from msk_research_lab.studio.project import get_project, create_project, StudioProjectError
from msk_research_lab.studio.editor import add_studio_point, get_studio_point, StudioEditorError


# Standard Reference Diện Chẩn Baseline Fixture Points (Prof. Bùi Quốc Châu)
STANDARD_DIEN_CHAN_BASELINE = [
    {
        "code": "DC_19",
        "canonical_label": "Huyệt 19 (Nhân trung / Subnasal)",
        "view": "FRONT",
        "pixel_xy": (250.0, 310.0),
        "notes": "Located at the upper third junction of the philtrum; sympathetic excitation point.",
    },
    {
        "code": "DC_0",
        "canonical_label": "Huyệt 0 (Khuyết trước bình tai / Tragus Notch)",
        "view": "PROFILE",
        "pixel_xy": (185.0, 290.0),
        "notes": "Located at the anterior notch of the tragus; homeostasis regulator point.",
    },
    {
        "code": "DC_14",
        "canonical_label": "Huyệt 14 (Dưới dái tai / Infra-auricular)",
        "view": "PROFILE",
        "pixel_xy": (195.0, 340.0),
        "notes": "Located below earlobe behind jaw angle; submandibular drainage.",
    },
    {
        "code": "DC_275",
        "canonical_label": "Huyệt 275 (Góc hàm / Mandibular angle)",
        "view": "PROFILE",
        "pixel_xy": (210.0, 370.0),
        "notes": "Located near mandibular angle and sternocleidomastoid anterior border.",
    }
]

# Synthetic reference facial chart SHA-256
SYNTHETIC_DIEN_CHAN_FRONT_SHA = "6a4a159f80164e2e28383a1523423719992d9d9685e1320ef424e650059f3cb5"
SYNTHETIC_DIEN_CHAN_PROFILE_SHA = "7b5b260e91275f3f39494b2634534820003e0e0796f2431fa535f761160a4dc6"

PATIENT_PII_PATTERNS = [
    re.compile(r"\b(mr\.|mrs\.|ms\.)\s+[A-Z][a-z]+", re.IGNORECASE),
    re.compile(r"\bpatient\s+(id|name|phone|ssn)\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), # SSN
    re.compile(r"\b\d{9,12}\b"),          # National ID / phone
]


class DienChanError(Exception):
    """Exception raised for Diện Chẩn epistemic and data integrity violations."""
    pass


def initialize_dien_chan_project(
    project_id: str = "proj_dien_chan_standard",
    title: str = "Diện Chẩn Standard Facial Reflexology Atlas",
) -> Dict[str, Any]:
    """Create and seed the standard Diện Chẩn 2D reference project."""
    proj = get_project(project_id)
    if not proj:
        proj = create_project(
            project_id=project_id,
            title=title,
            namespace="DIEN_CHAN",
            description="Standard 2D Facial reflexology maps with pinned image SHA-256 and pixel locators.",
            base_image_sha256=SYNTHETIC_DIEN_CHAN_FRONT_SHA,
            license="CC-BY-NC-SA 4.0 (Educational)"
        )

    # Seed baseline fixed points
    for item in STANDARD_DIEN_CHAN_BASELINE:
        pt_id = f"{project_id}_{item['code'].lower()}"
        if not get_studio_point(pt_id):
            img_sha = SYNTHETIC_DIEN_CHAN_FRONT_SHA if item["view"] == "FRONT" else SYNTHETIC_DIEN_CHAN_PROFILE_SHA
            add_studio_point(
                project_id=project_id,
                point_id=pt_id,
                code=item["code"],
                canonical_label=item["canonical_label"],
                dimensionality="2D_IMAGE_PIXEL",
                point_kind="FIXED_EDUCATIONAL",
                image_sha256=img_sha,
                image_view=item["view"],
                pixel_xy=item["pixel_xy"],
                notes=item["notes"]
            )

    return get_project(project_id)


def record_reactive_observation(
    *,
    project_id: str,
    point_id: str,
    code: str,
    canonical_label: str,
    session_id: str,
    session_timestamp: str,
    image_sha256: str,
    image_view: str,
    pixel_xy: Tuple[float, float],
    notes: str,
) -> Dict[str, Any]:
    """Record a session-specific reactive finding (Sinh huyệt / reactive sensitive point)."""
    # Privacy check: reject patient PII
    for pat in PATIENT_PII_PATTERNS:
        if pat.search(notes) or pat.search(canonical_label) or pat.search(session_id):
            raise DienChanError(
                "Privacy violation: Real patient PII detected in observation record. "
                "Only de-identified synthetic session IDs and research observations permitted."
            )

    return add_studio_point(
        project_id=project_id,
        point_id=point_id,
        code=code,
        canonical_label=canonical_label,
        dimensionality="2D_IMAGE_PIXEL",
        point_kind="REACTIVE_OBSERVATION",
        session_id=session_id,
        session_timestamp=session_timestamp,
        image_sha256=image_sha256,
        image_view=image_view,
        pixel_xy=pixel_xy,
        notes=notes
    )


def attempt_project_2d_to_3d(point_id: str, target_model_id: str) -> None:
    """Epistemic Guard (ATLAS-06): Reject automatic/implicit 2D chart to 3D projection."""
    pt = get_studio_point(point_id)
    if not pt:
        raise DienChanError(f"Point '{point_id}' not found.")

    if pt["dimensionality"] == "2D_IMAGE_PIXEL":
        raise DienChanError(
            "CANNOT_IMPLICITLY_PROJECT_2D_TO_3D: 2D facial diagram pixel coordinates "
            f"({pt['x_px']}, {pt['y_px']}) cannot be implicitly mapped to 3D model '{target_model_id}'. "
            "Uncalibrated 2D->3D coordinate conversion is epistemically invalid and strictly prohibited."
        )


def attempt_promote_reactive_to_global(point_id: str) -> None:
    """Epistemic Guard (ATLAS-06 / R5-04): Reactive observations cannot become global fixed points."""
    pt = get_studio_point(point_id)
    if not pt:
        raise DienChanError(f"Point '{point_id}' not found.")

    if pt["point_kind"] == "REACTIVE_OBSERVATION":
        raise DienChanError(
            "REACTIVE_OBSERVATION_CANNOT_BECOME_GLOBAL_FIXED: "
            f"Point '{pt['code']}' is a session-specific reactive finding from session '{pt['session_id']}'. "
            "Individual clinical or session observations cannot be promoted to universal educational standards."
        )
