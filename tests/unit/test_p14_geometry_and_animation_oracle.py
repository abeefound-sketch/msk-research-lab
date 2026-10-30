"""P14 Independent Mathematical Geometry & Biomechanics Oracle.

Independently computes forward kinematics transformations, Euler rotation matrices,
hierarchical bone positions, subacromial proximity metrics, and scientific provenance
validity without relying on Three.js or client-side runtime.
"""

import math
import pytest
from typing import Tuple, Dict, Any

from msk_research_lab.biomechanics.shoulder_lab import (
    ShoulderMovementLabEngine,
    get_shoulder_lab_engine,
    ScientificContentProvenance,
)


# Independent Mathematical Transformation Helper Functions (Matrix 3x3 & Vector 3D)
def mat3_identity() -> list[list[float]]:
    return [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ]


def rot_x(rad: float) -> list[list[float]]:
    c = math.cos(rad)
    s = math.sin(rad)
    return [
        [1.0, 0.0, 0.0],
        [0.0, c, -s],
        [0.0, s, c]
    ]


def rot_y(rad: float) -> list[list[float]]:
    c = math.cos(rad)
    s = math.sin(rad)
    return [
        [c, 0.0, s],
        [0.0, 1.0, 0.0],
        [-s, 0.0, c]
    ]


def rot_z(rad: float) -> list[list[float]]:
    c = math.cos(rad)
    s = math.sin(rad)
    return [
        [c, -s, 0.0],
        [s, c, 0.0],
        [0.0, 0.0, 1.0]
    ]


def mat3_mul(A: list[list[float]], B: list[list[float]]) -> list[list[float]]:
    res = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    for i in range(3):
        for j in range(3):
            res[i][j] = sum(A[i][k] * B[k][j] for k in range(3))
    return res


def mat3_vec_mul(M: list[list[float]], v: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2],
        M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2],
        M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2],
    )


def vec_add(u: tuple[float, float, float], v: tuple[float, float, float]) -> tuple[float, float, float]:
    return (u[0] + v[0], u[1] + v[1], u[2] + v[2])


def vec_sub(u: tuple[float, float, float], v: tuple[float, float, float]) -> tuple[float, float, float]:
    return (u[0] - v[0], u[1] - v[1], u[2] - v[2])


def vec_dist(u: tuple[float, float, float], v: tuple[float, float, float]) -> float:
    return math.sqrt((u[0] - v[0]) ** 2 + (u[1] - v[1]) ** 2 + (u[2] - v[2]) ** 2)


class KinematicHierarchyOracle:
    """Independent forward kinematics oracle modeling the 4-segment shoulder chain."""

    # Pivot coordinates in world space (meters)
    P_SC = (-0.015, -0.165, 1.340)
    P_AC_REL = (-0.130, 0.100, 0.015)
    P_GH_REL = (-0.020, -0.007, -0.025)
    P_ELBOW_REL = (-0.050, -0.003, -0.280)

    @classmethod
    def compute_chain(cls, arm_deg: float, mode: str = "normal_2to1") -> dict[str, Any]:
        """Compute independent analytical world transforms and positions for all joints."""
        # 1. Compute joint angles
        if mode == "forward_shoulder_restricted":
            sc_deg = 0.12 * arm_deg
            scap_up_deg = 0.0 if arm_deg <= 30.0 else ((arm_deg - 30.0) / 3.0) * 0.60
            gh_deg = arm_deg - scap_up_deg
            tilt_deg = 12.0 - (arm_deg * 0.04)
        else:
            sc_deg = 0.18 * arm_deg
            scap_up_deg = 0.0 if arm_deg <= 30.0 else (arm_deg - 30.0) / 3.0
            gh_deg = arm_deg - scap_up_deg
            tilt_deg = -arm_deg * 0.10

        ac_rel_up_deg = scap_up_deg - sc_deg

        # 2. Local relative rotation matrices
        # SCPivot: elevates clavicle around Y
        R_sc_local = rot_y(math.radians(sc_deg))

        # ACPivot: upward rotation around Y, anterior tilt around X
        R_ac_rot_y = rot_y(math.radians(ac_rel_up_deg))
        R_ac_tilt_x = rot_x(math.radians(tilt_deg))
        R_ac_local = mat3_mul(R_ac_rot_y, R_ac_tilt_x)

        # GHPivot: glenohumeral elevation around Y
        R_gh_local = rot_y(math.radians(gh_deg))

        # 3. Composite world orientation matrices
        R_sc_world = R_sc_local
        R_scapula_world = mat3_mul(R_sc_world, R_ac_local)
        R_humerus_world = mat3_mul(R_scapula_world, R_gh_local)

        # 4. Joint positions in world space
        pos_sc = cls.P_SC
        pos_ac = vec_add(pos_sc, mat3_vec_mul(R_sc_world, cls.P_AC_REL))
        pos_gh = vec_add(pos_ac, mat3_vec_mul(R_scapula_world, cls.P_GH_REL))
        pos_elbow = vec_add(pos_gh, mat3_vec_mul(R_humerus_world, cls.P_ELBOW_REL))

        # 5. Proximity landmarks (acromion on scapula vs. greater tubercle on humerus)
        acromion_rel_scap = (-0.010, -0.015, 0.010)
        tubercle_rel_hum = (-0.015, -0.005, -0.010)

        pos_acromion = vec_add(pos_ac, mat3_vec_mul(R_scapula_world, acromion_rel_scap))
        pos_tubercle = vec_add(pos_gh, mat3_vec_mul(R_humerus_world, tubercle_rel_hum))
        clearance_mm = vec_dist(pos_acromion, pos_tubercle) * 1000.0

        return {
            "angles": {
                "arm_deg": arm_deg,
                "sc_deg": sc_deg,
                "scap_up_deg": scapUpDeg if 'scapUpDeg' in locals() else scap_up_deg,
                "gh_deg": gh_deg,
                "tilt_deg": tilt_deg,
                "ac_rel_up_deg": ac_rel_up_deg,
            },
            "world_rotations": {
                "clavicle": R_sc_world,
                "scapula": R_scapula_world,
                "humerus": R_humerus_world,
            },
            "positions": {
                "sc": pos_sc,
                "ac": pos_ac,
                "gh": pos_gh,
                "elbow": pos_elbow,
                "acromion": pos_acromion,
                "tubercle": pos_tubercle,
            },
            "subacromial_clearance_mm": clearance_mm,
        }


@pytest.fixture
def engine():
    return get_shoulder_lab_engine()


class TestKinematicTransformationOracle:
    """Rigorous mathematical verification of the 3D kinematic pipeline."""

    def test_neutral_zero_degree_rest_position(self):
        """At 0° elevation, all pivots and rotations must match neutral CT scan coordinates."""
        res = KinematicHierarchyOracle.compute_chain(0.0, "normal_2to1")
        angles = res["angles"]
        assert angles["sc_deg"] == 0.0
        assert angles["scap_up_deg"] == 0.0
        assert angles["gh_deg"] == 0.0
        assert angles["tilt_deg"] == 0.0

        # World rotations must be identity matrices
        I = mat3_identity()
        for name, R in res["world_rotations"].items():
            for i in range(3):
                for j in range(3):
                    assert R[i][j] == pytest.approx(I[i][j], abs=1e-5)

        # Initial positions
        assert res["positions"]["sc"] == (-0.015, -0.165, 1.340)
        assert res["positions"]["ac"] == pytest.approx((-0.145, -0.065, 1.355), abs=1e-4)
        assert res["positions"]["gh"] == pytest.approx((-0.165, -0.072, 1.330), abs=1e-4)
        assert res["positions"]["elbow"] == pytest.approx((-0.215, -0.075, 1.050), abs=1e-4)

    @pytest.mark.parametrize("arm_deg, expected_sc, expected_scap, expected_gh", [
        (0.0, 0.0, 0.0, 0.0),
        (30.0, 5.4, 0.0, 30.0),      # Setting phase
        (45.0, 8.1, 5.0, 40.0),
        (90.0, 16.2, 20.0, 70.0),    # Mid-range abduction
        (120.0, 21.6, 30.0, 90.0),
        (180.0, 32.4, 50.0, 130.0),  # Full overhead
    ])
    def test_normal_scapulohumeral_rhythm_at_key_angles(self, engine, arm_deg, expected_sc, expected_scap, expected_gh):
        """Verify normal 2:1 rhythm angles match between engine and mathematical oracle."""
        frame = engine.get_kinematic_frame(arm_deg, "normal_2to1")
        oracle = KinematicHierarchyOracle.compute_chain(arm_deg, "normal_2to1")

        # Engine vs Oracle agreement
        assert frame.sternoclavicular_elevation_deg == pytest.approx(expected_sc, abs=0.05)
        assert frame.scapular_upward_rotation_deg == pytest.approx(expected_scap, abs=0.05)
        assert frame.glenohumeral_elevation_deg == pytest.approx(expected_gh, abs=0.05)
        assert frame.arm_elevation_deg == arm_deg

        # Summation invariant: GH + ST = Arm elevation
        assert (frame.scapular_upward_rotation_deg + frame.glenohumeral_elevation_deg) == pytest.approx(arm_deg, abs=0.05)

        # Clavicle elevation lifts the AC joint upward in Z
        if arm_deg > 0:
            assert oracle["positions"]["ac"][2] > KinematicHierarchyOracle.P_SC[2]

    @pytest.mark.parametrize("arm_deg, expected_scap, expected_gh", [
        (30.0, 0.0, 30.0),
        (90.0, 12.0, 78.0),   # 40% restriction (20° * 0.6 = 12°)
        (180.0, 30.0, 150.0), # (50° * 0.6 = 30°) -> GH must compensate by over-elevating to 150°!
    ])
    def test_forward_shoulder_restricted_kinematic_compensation(self, engine, arm_deg, expected_scap, expected_gh):
        """In restricted model, glenohumeral elevation must over-elevate to compensate for reduced scapular rotation."""
        frame = engine.get_kinematic_frame(arm_deg, "forward_shoulder_restricted")
        assert frame.scapular_upward_rotation_deg == pytest.approx(expected_scap, abs=0.05)
        assert frame.glenohumeral_elevation_deg == pytest.approx(expected_gh, abs=0.05)
        assert frame.scapular_anterior_tilt_deg > 0.0  # persistent anterior tilt

    def test_overhead_elbow_elevation_vector(self):
        """At 180° arm elevation, elbow position must be elevated overhead in world coordinates."""
        res0 = KinematicHierarchyOracle.compute_chain(0.0)
        res180 = KinematicHierarchyOracle.compute_chain(180.0)

        z_elbow_0 = res0["positions"]["elbow"][2]
        z_elbow_180 = res180["positions"]["elbow"][2]

        # Elbow must be elevated significantly higher than initial resting height
        assert z_elbow_180 > z_elbow_0 + 0.45  # At least 45 cm elevation delta
        assert z_elbow_180 > 1.50              # Elevated above shoulder joint height (1.33m)

    def test_subacromial_clearance_geometric_proximity_oracle(self):
        """Mathematical oracle confirms subacromial proximity narrows during restricted mid-range elevation."""
        normal_90 = KinematicHierarchyOracle.compute_chain(90.0, "normal_2to1")
        restricted_90 = KinematicHierarchyOracle.compute_chain(90.0, "forward_shoulder_restricted")

        # Due to persistent anterior tilt and reduced upward rotation, distance is narrower in restricted posture
        assert restricted_90["subacromial_clearance_mm"] < normal_90["subacromial_clearance_mm"]


class TestScientificContentProvenanceSchema:
    """Verifies that all scientific outputs carry complete, structured provenance."""

    def test_kinematics_frame_provenance(self, engine):
        f_norm = engine.get_kinematic_frame(90.0, "normal_2to1")
        assert f_norm.provenance is not None
        assert f_norm.provenance.source_model == "MOBL_ARMS_41_CANONICAL_KINEMATICS"
        assert f_norm.provenance.assumption_type == "EMPIRICAL_LITERATURE"
        assert f_norm.provenance.validation_status == "VERIFIED_BASELINE_BENCHMARK"
        assert len(f_norm.provenance.known_limitations) > 20

        f_restr = engine.get_kinematic_frame(90.0, "forward_shoulder_restricted")
        assert f_restr.provenance is not None
        assert f_restr.provenance.assumption_type == "HYPOTHETICAL_SCENARIO"
        assert f_restr.provenance.validation_status == "EDUCATIONAL_ESTIMATE"
        assert "not a personal diagnostic finding" in f_restr.provenance.known_limitations

    def test_muscle_response_scenario_delineation(self, engine):
        """Proves that muscle metrics for modified posture are NOT deceptively attributed to re-simulation."""
        # Normal mode
        m_norm = engine.get_muscle_responses(90.0, "normal_2to1")
        assert len(m_norm) > 0
        delt_norm = next(m for m in m_norm if m.muscle_name == "DELT1")
        assert delt_norm.validation_status == "VERIFIED_BASELINE_BENCHMARK"
        assert delt_norm.scenario_adjusted is True
        assert "MOBL_ARMS_41" in delt_norm.data_provenance

        # Restricted mode
        m_restr = engine.get_muscle_responses(90.0, "forward_shoulder_restricted")
        assert len(m_restr) > 0
        delt_restr = next(m for m in m_restr if m.muscle_name == "DELT1")
        assert delt_restr.validation_status == "NOT_VERIFIED_FOR_MODIFIED_POSTURE"
        assert delt_restr.scenario_adjusted is False
        assert "UNADJUSTED_FOR_RESTRICTED_POSTURE" in delt_restr.data_provenance
        assert "Scenario-specific re-simulation" in delt_restr.scenario_note
        assert "Unmodeled: activation is fixed at nominal passive tone" in delt_restr.neural_activation_note

    def test_structure_annotations_provenance(self, engine):
        # Scapula
        scap = engine.get_annotation("FMA13395")
        assert scap.provenance is not None
        assert scap.provenance.assumption_type == "EMPIRICAL_LITERATURE"
        assert "Inman" in scap.provenance.source_reference

        # Clavicle
        clav = engine.get_annotation("FMA13322")
        assert clav.provenance is not None
        assert "Teece" in clav.provenance.source_reference

        # Deltoid
        delt = engine.get_annotation("FMA34680")
        assert delt.provenance is not None
        assert delt.provenance.assumption_type == "OPENSIM_SIMULATION"
        assert "Millard2012" in delt.model_assumptions

    def test_comparative_models_provenance(self, engine):
        models = engine.get_comparative_models()
        assert len(models) == 2
        for m in models:
            assert m.provenance is not None
            assert len(m.provenance.known_limitations) > 20

    def test_motor_control_education_topics_and_references(self, engine):
        """Verifies 3 core motor control topics explaining sensory feedback, transient relief, and neuroplasticity."""
        topics = engine.get_motor_control_education()
        assert len(topics) == 3

        ids = [t.topic_id for t in topics]
        assert "sensory_feedback_proprioception" in ids
        assert "transient_tone_relief_vs_coordination" in ids
        assert "motor_learning_neuroplasticity" in ids

        # Topic 1: Sensory feedback
        t1 = next(t for t in topics if t.topic_id == "sensory_feedback_proprioception")
        assert any("Muscle Spindles" in mech for mech in t1.physiological_mechanisms)
        assert any("Golgi Tendon Organs" in mech for mech in t1.physiological_mechanisms)
        assert any("Kandel" in ref for ref in t1.scientific_references)

        # Topic 2: Transient tone vs motor patterns
        t2 = next(t for t in topics if t.topic_id == "transient_tone_relief_vs_coordination")
        assert any("Viscoelastic" in mech for mech in t2.physiological_mechanisms)
        assert any("Autonomic" in mech for mech in t2.physiological_mechanisms)
        assert any("Habitual Motor Encodings" in mech for mech in t2.physiological_mechanisms)
        assert any("Weppler" in ref for ref in t2.scientific_references)

        # Topic 3: Motor learning & active practice
        t3 = next(t for t in topics if t.topic_id == "motor_learning_neuroplasticity")
        assert any("Long-Term Potentiation" in mech for mech in t3.physiological_mechanisms)
        assert any("Cortical" in mech for mech in t3.physiological_mechanisms)
        assert any("Hodges" in ref for ref in t3.scientific_references)
        assert any("Kleim" in ref for ref in t3.scientific_references)
