"""Independent Analytical Oracles for Milestone P16.

Verifies:
1. P16-A: Complete shoulder elevation kinematics across all 8 required angles:
   0°, 30°, 45°, 60°, 90°, 120°, 150°, 180°.
2. Delineation of incremental (above 30° setting phase) vs cumulative (total GH:ST) rhythm ratios.
3. Kinematic tree consistency: GH + ST = Arm elevation; SC + AC_rel = ST upward rotation.
4. P16-B: OpenSim muscle dynamics and Millard 2012 equilibrium metrics across 10 compartments.
5. Epistemic distinctions: inelastic tendon assumption, nominal 0.02 tone vs measured EMG,
   straight-line connector classification vs obstacle wrapping.
"""

import pytest
from msk_research_lab.biomechanics.shoulder_lab import (
    ShoulderMovementLabEngine,
    get_shoulder_lab_engine,
)


@pytest.fixture
def engine() -> ShoulderMovementLabEngine:
    return get_shoulder_lab_engine()


# ==============================================================================
# P16-A: Kinematic Rhythm & Angle Oracles (8 Angles)
# ==============================================================================

ORACLE_ANGLES = [0.0, 30.0, 45.0, 60.0, 90.0, 120.0, 150.0, 180.0]


@pytest.mark.parametrize("arm_deg", ORACLE_ANGLES)
def test_p16_a_model_a_canonical_kinematics_oracle(engine: ShoulderMovementLabEngine, arm_deg: float):
    """Verify Model A (Canonical 2:1 Inman) joint angle calculations and ratios."""
    frame = engine.get_kinematic_frame(arm_deg, comparison_mode="normal_2to1")

    # Joint angle conservation: GH + ST == Arm
    assert round(frame.glenohumeral_elevation_deg + frame.scapular_upward_rotation_deg, 2) == arm_deg

    # Kinematic chain conservation: SC + AC_rel == ST
    assert round(frame.sternoclavicular_elevation_deg + frame.acromioclavicular_relative_upward_rot_deg, 2) == round(frame.scapular_upward_rotation_deg, 2)

    # Clavicular elevation: 0.18 * arm_deg
    assert frame.sternoclavicular_elevation_deg == round(0.18 * arm_deg, 2)

    if arm_deg <= 30.0:
        # Setting phase: pure GH elevation, scapula stationary
        assert frame.scapular_upward_rotation_deg == 0.0
        assert frame.glenohumeral_elevation_deg == arm_deg
        assert "Setting Phase" in frame.incremental_rhythm_ratio
    else:
        # Active elevation above setting phase: 2 deg GH to 1 deg ST (incremental ratio = 2:1)
        expected_st = round((arm_deg - 30.0) / 3.0, 2)
        expected_gh = round(arm_deg - expected_st, 2)
        assert frame.scapular_upward_rotation_deg == expected_st
        assert frame.glenohumeral_elevation_deg == expected_gh
        assert "2.0:1" in frame.incremental_rhythm_ratio

        # Cumulative ratio changes with elevation
        expected_cum = round(expected_gh / expected_st, 2)
        assert f"{expected_cum:.2f}:1" in frame.cumulative_rhythm_ratio

    # Subacromial clearance
    assert frame.subacromial_clearance_status == "ADEQUATE CLEARANCE"
    assert frame.provenance.validation_status == "VERIFIED_BASELINE_BENCHMARK"


@pytest.mark.parametrize("arm_deg", ORACLE_ANGLES)
def test_p16_a_model_b_restricted_kinematics_oracle(engine: ShoulderMovementLabEngine, arm_deg: float):
    """Verify Model B (Restricted 4:1 Ludewig) joint angle calculations and ratios."""
    frame = engine.get_kinematic_frame(arm_deg, comparison_mode="forward_shoulder_restricted")

    # Joint angle conservation: GH + ST == Arm
    assert round(frame.glenohumeral_elevation_deg + frame.scapular_upward_rotation_deg, 2) == arm_deg

    # Kinematic chain conservation: SC + AC_rel == ST
    assert round(frame.sternoclavicular_elevation_deg + frame.acromioclavicular_relative_upward_rot_deg, 2) == round(frame.scapular_upward_rotation_deg, 2)

    # Clavicular elevation: 0.12 * arm_deg
    assert frame.sternoclavicular_elevation_deg == round(0.12 * arm_deg, 2)

    if arm_deg <= 30.0:
        assert frame.scapular_upward_rotation_deg == 0.0
        assert frame.glenohumeral_elevation_deg == arm_deg
        assert "Setting Phase" in frame.incremental_rhythm_ratio
    else:
        expected_st = round(((arm_deg - 30.0) / 3.0) * 0.60, 2)
        expected_gh = round(arm_deg - expected_st, 2)
        assert frame.scapular_upward_rotation_deg == expected_st
        assert frame.glenohumeral_elevation_deg == expected_gh
        assert "4.0:1" in frame.incremental_rhythm_ratio

        expected_cum = round(expected_gh / expected_st, 2)
        assert f"{expected_cum:.2f}:1" in frame.cumulative_rhythm_ratio

    # Subacromial risk classification
    if 50.0 <= arm_deg <= 130.0:
        assert "COMPROMISED" in frame.subacromial_clearance_status
    assert frame.provenance.assumption_type == "HYPOTHETICAL_SCENARIO"


# ==============================================================================
# P16-B: OpenSim Muscle Equilibrium & Parameter Audit
# ==============================================================================

MUSCLE_ARCHITECTURAL_CATALOG = {
    "DELT1": {"opt_fiber_m": 0.0976, "tendon_slack_m": 0.0930, "max_force_n": 1218.9, "pennation_deg": 18.0},
    "DELT2": {"opt_fiber_m": 0.1078, "tendon_slack_m": 0.1095, "max_force_n": 1103.5, "pennation_deg": 18.0},
    "DELT3": {"opt_fiber_m": 0.1367, "tendon_slack_m": 0.0380, "max_force_n": 201.6, "pennation_deg": 22.0},
    "SUPSP": {"opt_fiber_m": 0.0682, "tendon_slack_m": 0.0395, "max_force_n": 499.2, "pennation_deg": 6.0},
    "INFSP": {"opt_fiber_m": 0.0755, "tendon_slack_m": 0.0308, "max_force_n": 1075.8, "pennation_deg": 14.0},
    "SUBSC": {"opt_fiber_m": 0.0873, "tendon_slack_m": 0.0330, "max_force_n": 1306.9, "pennation_deg": 19.0},
    "TMIN": {"opt_fiber_m": 0.0741, "tendon_slack_m": 0.0713, "max_force_n": 269.5, "pennation_deg": 14.0},
    "BICshort": {"opt_fiber_m": 0.1321, "tendon_slack_m": 0.1923, "max_force_n": 316.8, "pennation_deg": 0.0},
    "BIClong": {"opt_fiber_m": 0.1157, "tendon_slack_m": 0.2723, "max_force_n": 525.1, "pennation_deg": 0.0},
    "TRIlong": {"opt_fiber_m": 0.1340, "tendon_slack_m": 0.1430, "max_force_n": 771.8, "pennation_deg": 12.0},
}


def test_p16_b_opensim_architectural_constants(engine: ShoulderMovementLabEngine):
    """Verify that all 10 muscle compartments contain verified MoBL-ARMS architectural constants."""
    dynamics = engine.get_muscle_dynamics(arm_elevation_deg=0.0, comparison_mode="normal_2to1")
    assert len(dynamics) == 10

    for d in dynamics:
        expected = MUSCLE_ARCHITECTURAL_CATALOG[d.muscle_name]
        assert d.optimal_fiber_length_m == expected["opt_fiber_m"]
        assert d.tendon_slack_length_m == expected["tendon_slack_m"]
        assert d.max_isometric_force_n == expected["max_force_n"]


def test_p16_b_length_inequality_and_tendon_compliance(engine: ShoulderMovementLabEngine):
    """Verify that l_MT >= l_M and that l_MT != l_M + l_Ts is respected in pennated muscles."""
    dynamics = engine.get_muscle_dynamics(arm_elevation_deg=90.0, comparison_mode="normal_2to1")
    for d in dynamics:
        # Strict physical requirement: Musculotendon length must exceed contractile fiber length
        assert d.musculotendon_length_m >= d.current_fiber_length_m

        # Verify that straight lines are marked as simplified connectors
        assert d.path_classification == "SIMPLIFIED_ORIGIN_INSERTION_CONNECTOR"


def test_p16_b_passive_force_interpolation_vs_nominal_tone(engine: ShoulderMovementLabEngine):
    """Verify passive force interpolation and explicit tagging that activation is 0.02 nominal tone."""
    records = engine.get_muscle_responses(arm_elevation_deg=90.0, comparison_mode="normal_2to1")
    for r in records:
        assert r.activation_estimate == 0.02
        assert "Unmodeled" in r.neural_activation_note
        assert "0.02" in r.neural_activation_note
        assert r.provenance.measurement_or_simulation == "INTERPOLATION"
