"""Unit and Biomechanical Oracle Tests for Milestone P15.

Verifies:
1. Guided Learning Case Study scenes (6/6 scenes, narrative completeness, provenance).
2. OpenSim Muscle Dynamics calculations, attachment points, and delta lengths.
3. The 4 mandatory epistemic distinction tags for all muscle dynamics records.
4. Epistemic safety: baseline-only tagging under restricted comparison mode.
5. Motor Control Education 6 comprehensive topics and evidence references.
6. Mathematical consistency of muscle path lengths and fiber stretch.
"""

import pytest
from msk_research_lab.biomechanics.shoulder_lab import (
    ShoulderMovementLabEngine,
    get_shoulder_lab_engine,
    compute_kmsi_tag_and_color,
)


@pytest.fixture
def engine() -> ShoulderMovementLabEngine:
    return get_shoulder_lab_engine()


# ==============================================================================
# P15-D: Guided Learning Case Study Oracle Tests
# ==============================================================================

def test_p15_guided_learning_scenes_structure(engine: ShoulderMovementLabEngine):
    """Verify that all 6 structured scenes exist with valid schemas and sequential numbering."""
    scenes = engine.get_guided_learning_scenes()
    assert len(scenes) == 6, f"Expected 6 scenes, found {len(scenes)}"

    for idx, scene in enumerate(scenes):
        assert scene.scene_number == idx + 1
        assert scene.scene_id.startswith("scene_")
        assert len(scene.title) > 10
        assert len(scene.subtitle) > 5
        assert 0.0 <= scene.recommended_arm_elevation_deg <= 180.0
        assert scene.recommended_comparison_mode in ("normal_2to1", "forward_shoulder_restricted")
        assert len(scene.pedagogical_narrative) > 50
        assert len(scene.biomechanical_insights) >= 3
        assert len(scene.why_tension_returns_context) > 20
        assert len(scene.scientific_limitations) > 20
        assert len(scene.evidence_references) >= 2
        assert scene.provenance is not None
        assert scene.provenance.validation_status in ("VERIFIED_BASELINE_BENCHMARK", "EDUCATIONAL_ESTIMATE")


def test_p15_guided_learning_scene_pedagogical_alignment(engine: ShoulderMovementLabEngine):
    """Verify specific pedagogical targets across all 6 scenes."""
    scenes = engine.get_guided_learning_scenes()
    scene_map = {s.scene_number: s for s in scenes}

    # Scene 1: Anatomy & Neutral Rest
    s1 = scene_map[1]
    assert s1.recommended_arm_elevation_deg == 0.0
    assert s1.recommended_comparison_mode == "normal_2to1"
    assert s1.highlighted_structure_id == "FMA13395"
    assert "sternoclavicular" in s1.pedagogical_narrative.lower()

    # Scene 2: Normal 2:1 Elevation
    s2 = scene_map[2]
    assert s2.recommended_arm_elevation_deg == 90.0
    assert s2.recommended_comparison_mode == "normal_2to1"
    assert "2:1" in s2.title
    assert "subacromial" in s2.pedagogical_narrative.lower()

    # Scene 3: Restricted Scapular Rotation
    s3 = scene_map[3]
    assert s3.recommended_arm_elevation_deg == 90.0
    assert s3.recommended_comparison_mode == "forward_shoulder_restricted"
    assert "restricted" in s3.title.lower()
    assert "4:1" in s3.pedagogical_narrative
    assert s3.provenance.assumption_type == "HYPOTHETICAL_SCENARIO"
    assert "not a personal medical diagnosis" in s3.scientific_limitations.lower()

    # Scene 4: Muscle Mechanics & OpenSim Dynamics
    s4 = scene_map[4]
    assert s4.recommended_arm_elevation_deg == 120.0
    assert "fiber length" in s4.title.lower()
    assert s4.highlighted_structure_id == "FMA34680"

    # Scene 5: Motor Control & Sensory Loops
    s5 = scene_map[5]
    assert s5.recommended_arm_elevation_deg == 45.0
    assert "spindles" in s5.pedagogical_narrative.lower()
    assert "golgi tendon" in s5.pedagogical_narrative.lower()

    # Scene 6: The Core Question — Why Tension Returns
    s6 = scene_map[6]
    assert "tension returns" in s6.title.lower()
    assert "viscoelastic" in s6.pedagogical_narrative.lower()
    assert "thixotropy" in s6.pedagogical_narrative.lower()
    assert "habitual motor synergy" in s6.pedagogical_narrative.lower()
    assert "deliberate active movement practice" in s6.biomechanical_insights[2].lower()


# ==============================================================================
# P15-B: OpenSim Muscle Dynamics Oracle Tests
# ==============================================================================

def test_p15_muscle_dynamics_catalog_completeness(engine: ShoulderMovementLabEngine):
    """Verify that muscle dynamics supports all 10 upper extremity compartments."""
    dynamics = engine.get_muscle_dynamics(arm_elevation_deg=0.0, comparison_mode="normal_2to1")
    assert len(dynamics) == 10

    muscle_names = {d.muscle_name for d in dynamics}
    expected = {"DELT1", "DELT2", "DELT3", "SUPSP", "INFSP", "SUBSC", "TMIN", "BICshort", "BIClong", "TRIlong"}
    assert muscle_names == expected

    for d in dynamics:
        assert d.category == "muscle"
        assert d.mesh_classification == "STATIC_RESTING_ANATOMICAL_MESH"
        assert d.path_classification == "REPRESENTED_BY_OPENSIM_MUSCLE_PATH"
        assert d.origin_frame in ("clavicle", "scapula", "humerus", "radius", "ulna")
        assert d.insertion_frame in ("clavicle", "scapula", "humerus", "radius", "ulna")
        assert len(d.origin_point_m) == 3
        assert len(d.insertion_point_m) == 3
        assert d.max_isometric_force_n > 0.0
        assert d.optimal_fiber_length_m > 0.0
        assert d.tendon_slack_length_m > 0.0


def test_p15_muscle_dynamics_four_mandatory_epistemic_badges(engine: ShoulderMovementLabEngine):
    """Verify that all muscle dynamics records carry the 4 mandatory distinction tags."""
    dynamics = engine.get_muscle_dynamics(arm_elevation_deg=60.0, comparison_mode="normal_2to1")
    for d in dynamics:
        assert d.length_change_tag == "MODELED_LENGTH_CHANGE"
        assert d.passive_force_tag == "MODELED_PASSIVE_FORCE"
        assert d.activation_measurement_status == "MUSCLE_ACTIVATION_NOT_MEASURED"
        assert d.illustration_status == "EDUCATIONAL_ILLUSTRATION"


def test_p15_muscle_dynamics_length_changes_oracle(engine: ShoulderMovementLabEngine):
    """Verify forward kinematics length changes for key agonist and antagonist muscles."""
    # DELT1 (Anterior Deltoid): Abductor/Flexor — shortens during elevation
    delt1_0 = engine.get_muscle_dynamics(muscle_id="DELT1", arm_elevation_deg=0.0, comparison_mode="normal_2to1")[0]
    delt1_90 = engine.get_muscle_dynamics(muscle_id="DELT1", arm_elevation_deg=90.0, comparison_mode="normal_2to1")[0]
    delt1_180 = engine.get_muscle_dynamics(muscle_id="DELT1", arm_elevation_deg=180.0, comparison_mode="normal_2to1")[0]

    assert delt1_0.delta_fiber_length_m == 0.0
    assert delt1_90.delta_fiber_length_m < 0.0, "DELT1 should shorten at 90° elevation"
    assert delt1_180.delta_fiber_length_m < delt1_90.delta_fiber_length_m, "DELT1 should shorten further at 180°"
    assert delt1_90.normalized_fiber_length < 1.0
    assert delt1_90.kmsi_tag == "SHORTENED"

    # DELT3 (Posterior Deltoid): Extensor — stretches during coronal elevation
    delt3_0 = engine.get_muscle_dynamics(muscle_id="DELT3", arm_elevation_deg=0.0, comparison_mode="normal_2to1")[0]
    delt3_90 = engine.get_muscle_dynamics(muscle_id="DELT3", arm_elevation_deg=90.0, comparison_mode="normal_2to1")[0]
    delt3_180 = engine.get_muscle_dynamics(muscle_id="DELT3", arm_elevation_deg=180.0, comparison_mode="normal_2to1")[0]

    assert delt3_90.delta_fiber_length_m > 0.0, "DELT3 should stretch at 90° elevation"
    assert delt3_180.delta_fiber_length_m > delt3_90.delta_fiber_length_m, "DELT3 should stretch further at 180°"
    assert delt3_180.normalized_fiber_length > 1.15
    assert delt3_180.passive_force_n > delt3_0.passive_force_n

    # INFSP (Infraspinatus): External Rotator — passive tension rises with elevation
    infsp_0 = engine.get_muscle_dynamics(muscle_id="INFSP", arm_elevation_deg=0.0, comparison_mode="normal_2to1")[0]
    infsp_90 = engine.get_muscle_dynamics(muscle_id="INFSP", arm_elevation_deg=90.0, comparison_mode="normal_2to1")[0]
    infsp_180 = engine.get_muscle_dynamics(muscle_id="INFSP", arm_elevation_deg=180.0, comparison_mode="normal_2to1")[0]

    assert infsp_180.passive_force_n > infsp_90.passive_force_n > infsp_0.passive_force_n


def test_p15_muscle_dynamics_restricted_scenario_safety(engine: ShoulderMovementLabEngine):
    """Verify that restricted comparison mode never displays baseline forces as scenario-adjusted."""
    restr_items = engine.get_muscle_dynamics(arm_elevation_deg=90.0, comparison_mode="forward_shoulder_restricted")
    for item in restr_items:
        assert item.validation_status == "NOT_VERIFIED_FOR_MODIFIED_POSTURE"
        assert "UNADJUSTED" in item.data_provenance
        assert "CAUTION" in item.scenario_note
        assert item.provenance.assumption_type == "HYPOTHETICAL_SCENARIO"


# ==============================================================================
# P15-C: Motor Control Education Oracle Tests
# ==============================================================================

def test_p15_motor_control_six_topics_completeness(engine: ShoulderMovementLabEngine):
    """Verify all 6 comprehensive motor control topics with physiological mechanisms and citations."""
    topics = engine.get_motor_control_education()
    assert len(topics) == 6

    expected_ids = {
        "motor_planning_and_coordination",
        "sensory_feedback_proprioception",
        "muscle_activation_motor_unit_recruitment",
        "motor_learning_neuroplasticity",
        "habitual_movement_patterns_synergies",
        "transient_tone_relief_vs_coordination",
    }
    actual_ids = {t.topic_id for t in topics}
    assert actual_ids == expected_ids

    for t in topics:
        assert len(t.title) > 10
        assert len(t.summary) > 20
        assert len(t.detailed_explanation) > 100
        assert len(t.physiological_mechanisms) >= 4
        assert len(t.clinical_educational_takeaway) > 30
        assert len(t.scientific_references) >= 2
        assert t.provenance is not None
        assert t.provenance.validation_status == "VERIFIED_BASELINE_BENCHMARK"


def test_p15_motor_control_epistemic_safety(engine: ShoulderMovementLabEngine):
    """Verify that motor control topics avoid medical diagnosis claims or unverified therapeutic promises."""
    topics = engine.get_motor_control_education()
    prohibited_claims = ["cures pain", "diagnostic test", "permanent fix guaranteed", "diagnoses impingement"]

    for t in topics:
        full_text = f"{t.summary} {t.detailed_explanation} {t.clinical_educational_takeaway}".lower()
        for claim in prohibited_claims:
            assert claim not in full_text, f"Found prohibited claim '{claim}' in topic {t.topic_id}"
        # Assert limitation documentation
        assert len(t.provenance.known_limitations) > 15


# ==============================================================================
# KMSI Color Chip Oracle Test
# ==============================================================================

def test_p15_kmsi_color_chips():
    """Verify normalized fiber length classification boundaries."""
    assert compute_kmsi_tag_and_color(None) == ("NOT_COMPUTED", "#7f8c8d")
    assert compute_kmsi_tag_and_color(0.75) == ("SHORTENED", "#3498db")
    assert compute_kmsi_tag_and_color(1.00) == ("NOMINAL_RESTING", "#95a5a6")
    assert compute_kmsi_tag_and_color(1.25) == ("MODERATE_STRETCH", "#f39c12")
    assert compute_kmsi_tag_and_color(1.45) == ("HIGH_STRETCH", "#e74c3c")
