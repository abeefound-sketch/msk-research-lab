"""Unit tests for 2D Diện Chẩn Facial Atlas & Epistemic Guards (ATLAS-06 / R5-03 / R5-04)."""

import pytest
from msk_research_lab.studio.dien_chan import (
    initialize_dien_chan_project, record_reactive_observation, attempt_project_2d_to_3d,
    attempt_promote_reactive_to_global, DienChanError, STANDARD_DIEN_CHAN_BASELINE,
    SYNTHETIC_DIEN_CHAN_FRONT_SHA, SYNTHETIC_DIEN_CHAN_PROFILE_SHA
)
from msk_research_lab.studio.editor import get_studio_point, list_studio_points


def test_dien_chan_initialization_and_points():
    proj = initialize_dien_chan_project("proj_dien_chan_test")
    assert proj["project_id"] == "proj_dien_chan_test"
    assert proj["namespace"] == "DIEN_CHAN"

    pts = list_studio_points("proj_dien_chan_test", include_deleted=False)
    codes = {p["code"] for p in pts}
    assert "DC_19" in codes
    assert "DC_0" in codes
    assert "DC_14" in codes
    assert "DC_275" in codes

    dc_19 = [p for p in pts if p["code"] == "DC_19"][0]
    assert dc_19["dimensionality"] == "2D_IMAGE_PIXEL"
    assert dc_19["image_view"] == "FRONT"
    assert dc_19["image_sha256"] == SYNTHETIC_DIEN_CHAN_FRONT_SHA
    assert dc_19["x_px"] == 250.0
    assert dc_19["y_px"] == 310.0


def test_epistemic_guard_rejects_implicit_2d_to_3d():
    """ATLAS-06: 2D pixel coordinates cannot be implicitly converted to 3D without photogrammetric calibration."""
    initialize_dien_chan_project("proj_dien_chan_guard_test")
    pt_id = "proj_dien_chan_guard_test_dc_19"

    with pytest.raises(DienChanError, match="CANNOT_IMPLICITLY_PROJECT_2D_TO_3D"):
        attempt_project_2d_to_3d(pt_id, target_model_id="bodyparts3d_v4_ref_torso")


def test_epistemic_guard_rejects_reactive_to_global_promotion():
    """ATLAS-06 / R5-04: Session-specific reactive observations cannot become global fixed standards."""
    initialize_dien_chan_project("proj_dien_chan_guard_test")

    reactive_pt = record_reactive_observation(
        project_id="proj_dien_chan_guard_test",
        point_id="pt_reactive_01",
        code="DC_REACTIVE_01",
        canonical_label="Sinh huyệt thái dương",
        session_id="synth_session_20261023_01",
        session_timestamp="2026-10-23T08:00:00Z",
        image_sha256=SYNTHETIC_DIEN_CHAN_FRONT_SHA,
        image_view="FRONT",
        pixel_xy=(150.0, 120.0),
        notes="Hyper-sensitive point observed during experimental simulation."
    )
    assert reactive_pt["point_kind"] == "REACTIVE_OBSERVATION"
    assert reactive_pt["session_id"] == "synth_session_20261023_01"

    # Attempting to promote this reactive observation to a global standard must fail
    with pytest.raises(DienChanError, match="REACTIVE_OBSERVATION_CANNOT_BECOME_GLOBAL_FIXED"):
        attempt_promote_reactive_to_global("pt_reactive_01")


def test_privacy_guard_rejects_patient_pii():
    """Privacy guard rejects real patient PII in notes or labels."""
    initialize_dien_chan_project("proj_dien_chan_guard_test")

    with pytest.raises(DienChanError, match="Privacy violation"):
        record_reactive_observation(
            project_id="proj_dien_chan_guard_test",
            point_id="pt_pii_leak",
            code="DC_LEAK",
            canonical_label="Patient John Doe Finding",
            session_id="session_01",
            session_timestamp="2026-10-23T08:00:00Z",
            image_sha256=SYNTHETIC_DIEN_CHAN_FRONT_SHA,
            image_view="FRONT",
            pixel_xy=(100.0, 100.0),
            notes="Observed on Mr. Smith during morning session."
        )
