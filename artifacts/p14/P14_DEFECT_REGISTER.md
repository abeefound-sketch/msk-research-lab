# P14 Defect Register & Verification Log
**MSK Research Lab OS — Milestone P14**  
**Role:** Independent Release QA, Software Verification Engineer  
**Date:** 2026-10-30  

---

## 1. Summary of Defect Remediations

| Defect ID | Severity | Subsystem | Description | Root Cause | Status | Verification Evidence |
|---|---|---|---|---|---|---|
| **DEF-42** | HIGH | 3D Visualization / Kinematics | Clavicular rotation applied to vertical $Z$-axis instead of coronal $Y$-axis, causing horizontal retraction rather than elevation. | In anatomical RAS coordinates ($+Z$ superior, $+Y$ posterior), coronal elevation occurs around the $Y$-axis. Applying rotation to $Z$ did not change vertical height. | **RESOLVED** | `test_p14_geometry_and_animation_oracle.py::test_normal_scapulohumeral_rhythm_at_key_angles` (PASS) |
| **DEF-43** | HIGH | Biomechanics / Metrology | Deceptive attribution of baseline OpenSim muscle forces to the Forward Shoulder restricted movement scenario. | REST endpoint `/api/v1/biomechanics/shoulder/muscles/response` lacked scenario context; baseline numbers were displayed without caveats. | **RESOLVED** | `test_p14_geometry_and_animation_oracle.py::test_muscle_response_scenario_delineation` (PASS); Playwright E2E verifies `[BASELINE (UNADJUSTED)]` badge |

---

## 2. Detailed Defect Analysis & Fixes

### DEF-42 (HIGH): Clavicular Rotation Axis in Three.js Scene Graph
- **Discovered In:** Milestone P14-B 3D Transformation Pipeline Audit.
- **Problem Description:**  
  When arm elevation progressed from 0° to 180°, the sternoclavicular elevation angle was calculated as `scDeg = 0.18 * armDeg` (reaching 32.4° at 180°). In `src/msk_research_lab/api/workstation_ui.py`, line 2160 had:
  ```javascript
  shoulderSCPivot.rotation.z = (scDeg * Math.PI) / 180.0;
  ```
  Because the anatomical vertical axis in BodyParts3D is $+Z$, rotating around $Z$ rotated the clavicle in the horizontal (transverse) plane, producing retraction rather than coronal elevation. The lateral end of the clavicle (AC joint) remained at a constant vertical height $z = 1.340\text{ m}$.
- **Mathematical Resolution:**
  1. Coronal elevation occurs about the $Y$-axis:
     ```javascript
     shoulderSCPivot.rotation.y = (scDeg * Math.PI) / 180.0;
     ```
  2. Because `shoulderACPivot` is a child of `shoulderSCPivot`, it inherits the clavicular elevation. To keep the world-space upward rotation of the scapula exactly equal to the target $\theta_{ST}$:
     $$\theta_{AC,relative} = \theta_{ST} - \theta_{SC}$$
     ```javascript
     const acRelUpDeg = scapUpDeg - scDeg;
     shoulderACPivot.rotation.y = (acRelUpDeg * Math.PI) / 180.0;
     shoulderACPivot.rotation.x = (tiltDeg * Math.PI) / 180.0;
     ```
  3. The humerus pivot rotates relative to the scapula by $\theta_{GH} = \theta_{arm} - \theta_{ST}$:
     ```javascript
     shoulderGHPivot.rotation.y = (ghDeg * Math.PI) / 180.0;
     ```
- **Verification:**  
  Independent mathematical oracle verified that:
  - World clavicle rotation equals $\theta_{SC}$ ($32.4^\circ$ at $180^\circ$).
  - World scapula rotation equals $\theta_{ST}$ ($50.0^\circ$ at $180^\circ$).
  - World humerus rotation equals $\theta_{arm}$ ($180.0^\circ$ at $180^\circ$).
  - All 17 oracle unit tests pass.

---

### DEF-43 (HIGH): Deceptive Muscle Force Attribution Under Modified Posture Scenario
- **Discovered In:** Milestone P14-A Scientific Model Validity Audit.
- **Problem Description:**  
  In P13, selecting Comparative Model B ("Forward Shoulder / Restricted Scapular Upward Rotation") dynamically altered skeletal kinematics and displayed subacromial narrowing. However, the OpenSim monitored muscle table continued to display normalized fiber length and passive force values derived exclusively from healthy baseline `MOBL_ARMS_41` coordinates without notifying the user that these values were unadjusted for the altered posture.
- **Ethical & Scientific Risk:**  
  Violated the non-negotiable rule: *"Do not conflate model-predicted muscle force with measured muscle activation; do not display incompatible muscle force data as if it were recalculated for the modified posture."*
- **Engineering Resolution:**
  1. Extended `src/msk_research_lab/biomechanics/shoulder_lab.py`:
     Updated `get_muscle_responses(arm_elevation_deg, comparison_mode="normal_2to1")`.
  2. If `comparison_mode == "forward_shoulder_restricted"`:
     - `data_provenance = "BASELINE_MOBL_ARMS_MODEL_ESTIMATE; UNADJUSTED_FOR_RESTRICTED_POSTURE"`
     - `validation_status = "NOT_VERIFIED_FOR_MODIFIED_POSTURE"`
     - `scenario_adjusted = False`
     - `scenario_note = "CAUTION: OpenSim muscle metrics reflect baseline anatomical kinematics (MOBL_ARMS_41). Scenario-specific re-simulation for restricted scapular geometry has not been performed."`
  3. Extended `src/msk_research_lab/api/workstation_routes.py`:
     Route accepts `comparison_mode: str = Query("normal_2to1")`.
  4. Updated `src/msk_research_lab/api/workstation_ui.py`:
     When restricted mode is active, the muscle table renders an explicit amber badge on every row: `[BASELINE (UNADJUSTED)]` with warning tooltip.
- **Verification:**  
  Verified via unit test `test_muscle_response_scenario_delineation` and Playwright browser test `test_p14_shoulder_educational_browser_acceptance`.

---

## 3. Cumulative Defect Status

All defects DEF-01 through DEF-43 are **100% RESOLVED**. Zero known unresolved defects remain in the codebase.
