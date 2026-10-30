"""Unit tests for P13 Shoulder Movement Lab biomechanical engine and REST endpoints."""

import pytest
from fastapi.testclient import TestClient

from msk_research_lab.api.app import app
from msk_research_lab.biomechanics.shoulder_lab import (
    ShoulderMovementLabEngine,
    get_shoulder_lab_engine,
    compute_kmsi_tag_and_color,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def engine():
    return get_shoulder_lab_engine()


class TestShoulderMovementLabEngine:
    """Verifies OpenSim-grounded kinematics, muscle responses, and epistemic annotations."""

    def test_manifest_loads_thirteen_structures(self, engine):
        manifest = engine.get_manifest()
        assert "structures" in manifest
        structures = manifest["structures"]
        assert len(structures) >= 13

        # Verify key bones and muscles are present
        assert "FMA13395" in structures  # Scapula
        assert "FMA13322" in structures  # Clavicle
        assert "FMA23130" in structures  # Humerus
        assert "FMA34680" in structures  # Deltoid Anterior
        assert "FMA34682" in structures  # Deltoid Middle
        assert "FMA37684" in structures  # Biceps Short Head
        assert "FMA37699" in structures  # Triceps Long Head

        # Verify dataset attribution
        assert "BodyParts3D" in manifest.get("dataset", "")
        assert "Creative Commons Attribution-Share Alike" in manifest.get("license", "")

    def test_inman_scapulohumeral_rhythm_kinematics(self, engine):
        # Setting phase: 0° to 30° should have 0° scapular upward rotation
        f0 = engine.get_kinematic_frame(0.0, "normal_2to1")
        assert f0.arm_elevation_deg == 0.0
        assert f0.scapular_upward_rotation_deg == 0.0
        assert f0.sternoclavicular_elevation_deg == 0.0
        assert f0.glenohumeral_elevation_deg == 0.0

        f30 = engine.get_kinematic_frame(30.0, "normal_2to1")
        assert f30.scapular_upward_rotation_deg == 0.0
        assert f30.glenohumeral_elevation_deg == 30.0
        assert f30.sternoclavicular_elevation_deg == pytest.approx(5.4, 0.01)

        # Mid-range: 90° elevation -> (90-30)/3 = 20° scapular rotation, 70° glenohumeral
        f90 = engine.get_kinematic_frame(90.0, "normal_2to1")
        assert f90.scapular_upward_rotation_deg == pytest.approx(20.0, 0.01)
        assert f90.glenohumeral_elevation_deg == pytest.approx(70.0, 0.01)
        assert f90.sternoclavicular_elevation_deg == pytest.approx(16.2, 0.01)
        assert f90.subacromial_clearance_status == "ADEQUATE CLEARANCE"

        # Full overhead: 180° elevation -> (180-30)/3 = 50° scapular rotation, 130° glenohumeral
        f180 = engine.get_kinematic_frame(180.0, "normal_2to1")
        assert f180.scapular_upward_rotation_deg == pytest.approx(50.0, 0.01)
        assert f180.glenohumeral_elevation_deg == pytest.approx(130.0, 0.01)
        assert f180.sternoclavicular_elevation_deg == pytest.approx(32.4, 0.01)

    def test_forward_shoulder_restricted_comparison(self, engine):
        # In restricted forward shoulder posture, scapular upward rotation is restricted by 40%
        # At 90°: normal is 20°, restricted is 20 * 0.6 = 12°
        f90_restr = engine.get_kinematic_frame(90.0, "forward_shoulder_restricted")
        assert f90_restr.scapular_upward_rotation_deg == pytest.approx(12.0, 0.01)
        assert f90_restr.glenohumeral_elevation_deg == pytest.approx(78.0, 0.01)
        assert f90_restr.scapular_anterior_tilt_deg > 0.0  # persistent anterior tilt
        assert "COMPROMISED" in f90_restr.subacromial_clearance_status

    def test_trajectory_array_generation(self, engine):
        traj = engine.get_full_trajectory("normal_2to1", step_deg=5.0)
        assert len(traj) == 37  # 0, 5, 10, ... 180 = 37 points
        assert traj[0].arm_elevation_deg == 0.0
        assert traj[-1].arm_elevation_deg == 180.0

    def test_muscle_response_interpolation(self, engine):
        responses_90 = engine.get_muscle_responses(90.0)
        assert len(responses_90) > 0

        # Verify deltoid anterior (DELT1)
        delt1 = next((m for m in responses_90 if m.muscle_name == "DELT1"), None)
        assert delt1 is not None
        assert delt1.normalized_fiber_length < 1.0  # shortens during arm elevation
        assert delt1.kmsi_tag in {"SHORTENED", "NOMINAL_RESTING", "MODERATE_STRETCH"}

        # Verify pectoralis major sternal (PECM2)
        pecm2 = next((m for m in responses_90 if m.muscle_name == "PECM2"), None)
        assert pecm2 is not None
        assert pecm2.normalized_fiber_length > 1.3  # significantly stretched
        assert pecm2.kmsi_tag in {"MODERATE_STRETCH", "HIGH_STRETCH"}
        assert pecm2.passive_force_n > 50.0  # significant passive elastic tension

    def test_kmsi_color_classifier(self):
        assert compute_kmsi_tag_and_color(0.75)[0] == "SHORTENED"
        assert compute_kmsi_tag_and_color(1.00)[0] == "NOMINAL_RESTING"
        assert compute_kmsi_tag_and_color(1.25)[0] == "MODERATE_STRETCH"
        assert compute_kmsi_tag_and_color(1.55)[0] == "HIGH_STRETCH"
        assert compute_kmsi_tag_and_color(None)[0] == "NOT_COMPUTED"

    def test_comparative_models_evidence_disclaimer(self, engine):
        models = engine.get_comparative_models()
        assert len(models) == 2
        m_ids = [m.model_id for m in models]
        assert "normal_2to1" in m_ids
        assert "forward_shoulder_restricted" in m_ids

        # Ensure explicit non-diagnostic medical caution is present
        restricted = next(m for m in models if m.model_id == "forward_shoulder_restricted")
        assert "does NOT by itself constitute clinical diagnosis" in restricted.clinical_caution

    def test_evidence_based_annotations_citations(self, engine):
        # Scapula annotation
        scapula_anno = engine.get_annotation("FMA13395")
        assert scapula_anno is not None
        assert "Inman" in str(scapula_anno.evidence_sources)
        assert "Ludewig" in str(scapula_anno.evidence_sources)
        assert "Rigid body" in scapula_anno.model_assumptions
        assert "does not measure soft tissue friction" in scapula_anno.scientific_limitations

        # Deltoid annotation
        delt_anno = engine.get_annotation("FMA34680")
        assert delt_anno is not None
        assert "Millard2012" in delt_anno.model_assumptions
        assert "does NOT measure electromyographic firing rate" in delt_anno.scientific_limitations


class TestShoulderMovementLabApiEndpoints:
    """Verifies REST API endpoints for the Shoulder Movement Lab."""

    def test_api_manifest_endpoint(self, client):
        res = client.get("/api/v1/biomechanics/shoulder/manifest")
        assert res.status_code == 200
        data = res.json()
        assert "structures" in data
        assert len(data["structures"]) >= 13

    def test_api_kinematics_frame_endpoint(self, client):
        res = client.get("/api/v1/biomechanics/shoulder/kinematics/frame?arm_elevation_deg=90.0&comparison_mode=normal_2to1")
        assert res.status_code == 200
        data = res.json()
        assert data["arm_elevation_deg"] == 90.0
        assert data["scapular_upward_rotation_deg"] == 20.0
        assert data["glenohumeral_elevation_deg"] == 70.0

    def test_api_kinematics_trajectory_endpoint(self, client):
        res = client.get("/api/v1/biomechanics/shoulder/kinematics/trajectory?comparison_mode=normal_2to1&step_deg=10.0")
        assert res.status_code == 200
        traj = res.json()
        assert len(traj) == 19
        assert traj[0]["arm_elevation_deg"] == 0.0
        assert traj[-1]["arm_elevation_deg"] == 180.0

    def test_api_muscles_response_endpoint(self, client):
        res = client.get("/api/v1/biomechanics/shoulder/muscles/response?arm_elevation_deg=60.0")
        assert res.status_code == 200
        muscles = res.json()
        assert len(muscles) > 0
        assert any(m["muscle_name"] == "DELT1" for m in muscles)

    def test_api_comparisons_endpoint(self, client):
        res = client.get("/api/v1/biomechanics/shoulder/comparisons")
        assert res.status_code == 200
        models = res.json()
        assert len(models) == 2

    def test_api_annotations_endpoint(self, client):
        res = client.get("/api/v1/biomechanics/shoulder/annotations/FMA13395")
        assert res.status_code == 200
        anno = res.json()
        assert anno["name"] == "Right Scapula (Shoulder Blade)"
        assert len(anno["evidence_sources"]) >= 2

        # 404 for invalid structure
        res_invalid = client.get("/api/v1/biomechanics/shoulder/annotations/INVALID_XYZ")
        assert res_invalid.status_code == 404

    def test_api_model_file_serving(self, client):
        # Request valid GLB model file
        res = client.get("/api/v1/biomechanics/shoulder/models/fma13322_clavicle.glb")
        assert res.status_code == 200
        assert len(res.content) == 103756
        assert res.headers["content-type"] == "model/gltf-binary"

        # Request missing model file returns 404
        res_missing = client.get("/api/v1/biomechanics/shoulder/models/nonexistent.glb")
        assert res_missing.status_code == 404

        # Request with path traversal attempt or non-whitelisted extension returns 400 or 404
        res_traversal = client.get("/api/v1/biomechanics/shoulder/models/../../etc/passwd")
        assert res_traversal.status_code in {400, 404}
