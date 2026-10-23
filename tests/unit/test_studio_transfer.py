"""Unit tests for Studio JSON Transfer, Roundtrip & Validation (ATLAS-05 / R5-05)."""

import pytest
from msk_research_lab.studio.project import create_project
from msk_research_lab.studio.editor import add_studio_point
from msk_research_lab.studio.transfer import (
    export_studio_project, import_studio_project, compute_project_diff, TransferError
)


def test_studio_export_and_import_roundtrip():
    create_project(
        project_id="proj_transfer_src",
        title="Transfer Source Project",
        namespace="THAI_SEN",
        description="Thai Sen line points",
        license="CC-BY-4.0"
    )

    add_studio_point(
        project_id="proj_transfer_src",
        point_id="pt_sen_01",
        code="SEN_ITHA_01",
        canonical_label="Sen Itha Navel Start",
        dimensionality="3D_SURFACE",
        model_id="bodyparts3d_v4_ref_torso",
        mesh_sha256="c" * 64,
        surface_xyz=(0.0, 300.0, 50.0),
        face_index=12,
        barycentric=(0.5, 0.5, 0.0),
        notes="1 fingerwidth lateral to navel."
    )

    # Export
    bundle = export_studio_project("proj_transfer_src")
    assert bundle["schema_version"] == "3.0.0"
    assert bundle["project"]["project_id"] == "proj_transfer_src"
    assert len(bundle["points"]) == 1
    assert "points_sha256" in bundle

    # Import into target project
    bundle["project"]["project_id"] = "proj_transfer_tgt"
    bundle["points"][0]["project_id"] = "proj_transfer_tgt"
    bundle["points"][0]["point_id"] = "pt_sen_tgt_01"

    import_res = import_studio_project(bundle, overwrite_existing=True)
    assert import_res["status"] == "IMPORTED"
    assert import_res["imported_point_count"] == 1


def test_import_rejects_corrupt_barycentric():
    corrupt_bundle = {
        "schema_version": "3.0.0",
        "project": {
            "project_id": "proj_corrupt",
            "title": "Corrupt Topology",
            "namespace": "TCM",
            "license": "MIT"
        },
        "points": [
            {
                "point_id": "pt_corrupt_01",
                "code": "BAD_TRI",
                "canonical_label": "Bad Triangle",
                "dimensionality": "3D_SURFACE",
                "mesh_sha256": "d" * 64,
                "barycentric_u": 0.8,
                "barycentric_v": 0.8,
                "barycentric_w": 0.8, # Sum = 2.4 != 1.0!
            }
        ]
    }

    with pytest.raises(TransferError, match="corrupt barycentric"):
        import_studio_project(corrupt_bundle)


def test_import_rejects_forbidden_license():
    bad_lic_bundle = {
        "schema_version": "3.0.0",
        "project": {
            "project_id": "proj_pirated",
            "title": "Pirated Asset Project",
            "namespace": "TCM",
            "license": "PIRATED_COPY"
        },
        "points": []
    }

    with pytest.raises(TransferError, match="forbidden or revoked"):
        import_studio_project(bad_lic_bundle)


def test_compute_diff():
    create_project(
        project_id="proj_diff_base",
        title="Base Diff Project",
        namespace="CUSTOM_RESEARCH"
    )
    add_studio_point(
        project_id="proj_diff_base",
        point_id="pt_d1",
        code="P1",
        canonical_label="Point 1",
        dimensionality="2D_IMAGE_PIXEL",
        image_sha256="e" * 64,
        image_view="FRONT",
        pixel_xy=(10.0, 20.0)
    )
    add_studio_point(
        project_id="proj_diff_base",
        point_id="pt_d2",
        code="P2",
        canonical_label="Point 2",
        dimensionality="2D_IMAGE_PIXEL",
        image_sha256="e" * 64,
        image_view="FRONT",
        pixel_xy=(30.0, 40.0)
    )

    # Comparison payload has P1 modified, P2 removed, and P3 added
    comp_payload = {
        "points": [
            {
                "code": "P1",
                "canonical_label": "Point 1 Modified",
                "dimensionality": "2D_IMAGE_PIXEL",
                "x_px": 15.0, # shifted from 10.0
                "y_px": 20.0
            },
            {
                "code": "P3",
                "canonical_label": "Point 3 New",
                "dimensionality": "2D_IMAGE_PIXEL",
                "x_px": 50.0,
                "y_px": 60.0
            }
        ]
    }

    diff = compute_project_diff("proj_diff_base", comp_payload)
    assert "P3" in diff["added_codes"]
    assert "P2" in diff["removed_codes"]
    assert len(diff["modified_points"]) == 1
    assert diff["modified_points"][0]["code"] == "P1"
    assert diff["total_diff_count"] == 3
