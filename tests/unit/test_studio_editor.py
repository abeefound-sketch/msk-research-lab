"""Unit tests for Private Atlas Studio Editor & Lineage (ATLAS-05 / R5-01 / R5-02)."""

import pytest
from msk_research_lab.studio.project import (
    create_project, get_project, list_projects, bump_project_version, StudioProjectError
)
from msk_research_lab.studio.editor import (
    add_studio_point, get_studio_point, list_studio_points, move_studio_point,
    delete_studio_point, undo_last_action, StudioEditorError
)


def test_create_project_and_namespace_guard():
    proj = create_project(
        project_id="proj_tcm_custom_01",
        title="Custom TCM Point Research",
        namespace="TCM",
        description="Private draft points"
    )
    assert proj["project_id"] == "proj_tcm_custom_01"
    assert proj["namespace"] == "TCM"
    assert proj["version"] == 1

    # Invalid namespace rejected
    with pytest.raises(StudioProjectError, match="Invalid namespace"):
        create_project(
            project_id="proj_invalid_ns",
            title="Bad Namespace",
            namespace="UNRECOGNIZED_TRADITION"
        )

    # Collision guard: reserved anatomy prefixes rejected
    with pytest.raises(StudioProjectError, match="violates namespace boundary"):
        create_project(
            project_id="FMA:50123_stolen_concept",
            title="Attempted FMA Hijack",
            namespace="TCM"
        )


def test_add_3d_point_valid_and_invalid_barycentric():
    create_project(
        project_id="proj_tcm_test",
        title="TCM Test",
        namespace="TCM"
    )

    # Valid 3D point (barycentric sum = 1.0)
    pt = add_studio_point(
        project_id="proj_tcm_test",
        point_id="pt_tcm_01",
        code="CUSTOM_GB21_ALT",
        canonical_label="Alternative GB21",
        dimensionality="3D_SURFACE",
        point_kind="FIXED_EDUCATIONAL",
        model_id="bodyparts3d_v4_ref_torso",
        mesh_sha256="a" * 64,
        surface_xyz=(-97.5, 475.0, -45.0),
        face_index=412,
        barycentric=(0.333333, 0.333333, 0.333334),
        notes="Clinical trial variant."
    )
    assert pt["point_id"] == "pt_tcm_01"
    assert pt["barycentric_u"] == pytest.approx(0.333333)

    # Invalid barycentric sum (0.5 + 0.1 + 0.1 = 0.7 != 1.0)
    with pytest.raises(StudioEditorError, match="barycentric"):
        add_studio_point(
            project_id="proj_tcm_test",
            point_id="pt_bad_bary",
            code="BAD_BARY",
            canonical_label="Corrupt Triangle",
            dimensionality="3D_SURFACE",
            model_id="bodyparts3d_v4_ref_torso",
            mesh_sha256="a" * 64,
            surface_xyz=(0, 0, 0),
            face_index=1,
            barycentric=(0.5, 0.1, 0.1)
        )


def test_move_delete_and_undo_point():
    create_project(
        project_id="proj_undo_test",
        title="Undo Test",
        namespace="TRIGGER_POINT"
    )

    pt = add_studio_point(
        project_id="proj_undo_test",
        point_id="pt_tp_01",
        code="TP_TRAP_01",
        canonical_label="Trapezius Upper Trigger Point",
        dimensionality="3D_SURFACE",
        model_id="bodyparts3d_v4_ref_torso",
        mesh_sha256="b" * 64,
        surface_xyz=(-80.0, 470.0, -40.0),
        face_index=100,
        barycentric=(0.5, 0.25, 0.25)
    )

    # Move point
    moved = move_studio_point(
        "pt_tp_01",
        surface_xyz=(-85.0, 472.0, -42.0),
        face_index=102,
        barycentric=(0.4, 0.3, 0.3)
    )
    assert moved["surface_x"] == pytest.approx(-85.0)

    # Undo move
    undo_res = undo_last_action("proj_undo_test")
    assert undo_res["undone_action"] == "MOVE_POINT"

    reverted = get_studio_point("pt_tp_01")
    assert reverted["surface_x"] == pytest.approx(-80.0)
    assert reverted["face_index"] == 100

    # Delete point
    delete_studio_point("pt_tp_01")
    assert get_studio_point("pt_tp_01")["is_deleted"] == 1
    assert len(list_studio_points("proj_undo_test", include_deleted=False)) == 0

    # Undo delete
    undo_res2 = undo_last_action("proj_undo_test")
    assert undo_res2["undone_action"] == "DELETE_POINT"
    assert get_studio_point("pt_tp_01")["is_deleted"] == 0
