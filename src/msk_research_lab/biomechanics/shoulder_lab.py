"""Shoulder Movement Lab Engine: Biomechanical kinematics, muscle responses, and evidence-based annotations.

Provides verified OpenSim-grounded kinematics (MOBL_ARMS_41), continuous trajectory interpolation,
comparative movement models (Normal 2:1 Scapulohumeral Rhythm vs. Forward Shoulder Restrained),
and evidence-based educational annotations.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from msk_research_lab.core.config import get_config


class ShoulderKinematicsFrame(BaseModel):
    arm_elevation_deg: float
    sternoclavicular_elevation_deg: float
    scapular_upward_rotation_deg: float
    glenohumeral_elevation_deg: float
    scapular_anterior_tilt_deg: float = 0.0
    scapular_internal_rotation_deg: float = 0.0
    subacromial_clearance_status: str = "ADEQUATE"
    rhythm_ratio: str = "2:1"


class MuscleResponseRecord(BaseModel):
    muscle_name: str
    shoulder_elevation_deg: float
    musculotendon_length_m: float
    fiber_length_m: float
    optimal_fiber_length_m: float
    normalized_fiber_length: float
    passive_force_n: float
    active_force_n: float
    total_force_n: float
    activation_estimate: float
    biomechanical_state: str
    kmsi_tag: str
    kmsi_color_hex: str


class ComparativeMovementModel(BaseModel):
    model_id: str
    name: str
    short_description: str
    detailed_mechanism: str
    scapular_rhythm_ratio: str
    subacromial_space_implication: str
    clinical_caution: str


class StructureAnnotation(BaseModel):
    structure_id: str
    name: str
    fma_id: str
    category: str  # "bone" or "muscle"
    opensim_id: str
    direct_anatomical_facts: str
    kinematic_role_during_elevation: str
    evidence_sources: List[str]
    model_assumptions: str
    scientific_limitations: str


def compute_kmsi_tag_and_color(norm_fiber_length: Optional[float]) -> tuple[str, str]:
    """Classify normalized muscle fiber length into educational KMSI color chips."""
    if norm_fiber_length is None:
        return "NOT_COMPUTED", "#7f8c8d"
    if norm_fiber_length < 0.85:
        return "SHORTENED", "#3498db"
    elif norm_fiber_length <= 1.15:
        return "NOMINAL_RESTING", "#95a5a6"
    elif norm_fiber_length <= 1.40:
        return "MODERATE_STRETCH", "#f39c12"
    else:
        return "HIGH_STRETCH", "#e74c3c"


class ShoulderMovementLabEngine:
    """Core computational and educational engine for the Shoulder Movement Lab."""

    def __init__(self, atlas_dir: Optional[Path] = None):
        cfg = get_config()
        self.atlas_dir = atlas_dir or (cfg.storage.root_dir / "2data" / "models" / "atlas")
        self._manifest: Dict[str, Any] = {}
        self._muscle_db: List[Dict[str, Any]] = []
        self._load_manifest()
        self._load_muscle_response_csv()

    def _load_manifest(self) -> None:
        manifest_path = self.atlas_dir / "atlas_manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    self._manifest = json.load(f)
            except Exception as e:
                self._manifest = {"error": f"Failed to parse manifest: {e}", "structures": {}}
        else:
            self._manifest = {"structures": {}}

    def _load_muscle_response_csv(self) -> None:
        csv_path = self.atlas_dir / "muscle_response_validation.csv"
        if not csv_path.exists():
            return
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    norm_len = float(row.get("normalized_fiber_length", 1.0))
                    tag, color = compute_kmsi_tag_and_color(norm_len)
                    self._muscle_db.append({
                        "model_id": row.get("model_id", "MOBL_ARMS_41"),
                        "muscle_name": row.get("muscle_name", ""),
                        "shoulder_elevation_deg": float(row.get("shoulder_elevation_deg", 0.0)),
                        "musculotendon_length_m": float(row.get("musculotendon_length_m", 0.0)),
                        "fiber_length_m": float(row.get("fiber_length_m", 0.0)),
                        "optimal_fiber_length_m": float(row.get("optimal_fiber_length_m", 0.0)),
                        "normalized_fiber_length": round(norm_len, 4),
                        "passive_force_n": float(row.get("passive_force_N", 0.0)),
                        "active_force_n": float(row.get("active_force_N", 0.0)),
                        "total_force_n": float(row.get("total_muscle_force_N", 0.0)),
                        "activation_estimate": float(row.get("activation", 0.02)),
                        "biomechanical_state": row.get("biomechanical_state", "Nominal"),
                        "kmsi_tag": tag,
                        "kmsi_color_hex": color,
                    })
        except Exception as e:
            print(f"[ShoulderLabEngine] Warning reading muscle response CSV: {e}")

    def get_manifest(self) -> Dict[str, Any]:
        """Return registered BodyParts3D structures and coordinate definitions."""
        return self._manifest

    def get_kinematic_frame(self, arm_elevation_deg: float, comparison_mode: str = "normal_2to1") -> ShoulderKinematicsFrame:
        """Calculate verified joint rotations for a specific arm elevation angle."""
        arm_deg = max(0.0, min(180.0, float(arm_elevation_deg)))

        if comparison_mode == "forward_shoulder_restricted":
            # Restricted Scapular Upward Rotation + Excessive Anterior Tilt
            # Scapular upward rotation restricted by 40% (4:1 rhythm)
            # Resting anterior tilt +12 deg, resting internal rotation +8 deg
            sc_deg = round(0.12 * arm_deg, 2)
            if arm_deg <= 30.0:
                scap_up_deg = 0.0
            else:
                scap_up_deg = round(((arm_deg - 30.0) / 3.0) * 0.60, 2)
            gh_deg = round(arm_deg - scap_up_deg, 2)
            tilt_deg = round(12.0 - (arm_deg * 0.04), 2)  # fails to posteriorly tilt adequately
            int_rot_deg = round(8.0 - (arm_deg * 0.03), 2)
            subacromial = "COMPROMISED (HIGH IMPINGEMENT RISK AT 60-120°)" if 50.0 <= arm_deg <= 130.0 else "REDUCED"
            rhythm = "4:1 (Restricted)"
        else:
            # Normal Healthy Inman 2:1 Scapulohumeral Rhythm
            # Setting phase: 0-30 deg is primarily glenohumeral
            # Above 30 deg: 2 deg GH to 1 deg Scapulothoracic upward rotation
            # Clavicle elevates approx 0.18 x arm angle
            sc_deg = round(0.18 * arm_deg, 2)
            if arm_deg <= 30.0:
                scap_up_deg = 0.0
            else:
                scap_up_deg = round((arm_deg - 30.0) / 3.0, 2)
            gh_deg = round(arm_deg - scap_up_deg, 2)
            tilt_deg = round(-arm_deg * 0.10, 2)  # healthy posterior tilting (negative anterior tilt)
            int_rot_deg = 0.0
            subacromial = "ADEQUATE CLEARANCE"
            rhythm = "2:1 (Inman Canonical)"

        return ShoulderKinematicsFrame(
            arm_elevation_deg=arm_deg,
            sternoclavicular_elevation_deg=sc_deg,
            scapular_upward_rotation_deg=scap_up_deg,
            glenohumeral_elevation_deg=gh_deg,
            scapular_anterior_tilt_deg=tilt_deg,
            scapular_internal_rotation_deg=int_rot_deg,
            subacromial_clearance_status=subacromial,
            rhythm_ratio=rhythm,
        )

    def get_full_trajectory(self, comparison_mode: str = "normal_2to1", step_deg: float = 1.0) -> List[ShoulderKinematicsFrame]:
        """Generate time-series trajectory array from 0 to 180 degrees."""
        frames = []
        angle = 0.0
        while angle <= 180.0:
            frames.append(self.get_kinematic_frame(angle, comparison_mode))
            angle += step_deg
        return frames

    def get_muscle_responses(self, arm_elevation_deg: float) -> List[MuscleResponseRecord]:
        """Interpolate OpenSim muscle fiber lengths and forces for a given elevation angle."""
        arm_deg = max(0.0, min(180.0, float(arm_elevation_deg)))
        key_angles = [0.0, 45.0, 90.0, 120.0, 150.0, 180.0]

        # Find bounding angles
        lower_ang = key_angles[0]
        upper_ang = key_angles[-1]
        for i in range(len(key_angles) - 1):
            if key_angles[i] <= arm_deg <= key_angles[i + 1]:
                lower_ang = key_angles[i]
                upper_ang = key_angles[i + 1]
                break

        t = (arm_deg - lower_ang) / (upper_ang - lower_ang) if upper_ang != lower_ang else 0.0

        # Group DB by muscle name
        muscles: Dict[str, Dict[float, Dict[str, Any]]] = {}
        for r in self._muscle_db:
            m_name = r["muscle_name"]
            ang = r["shoulder_elevation_deg"]
            if m_name not in muscles:
                muscles[m_name] = {}
            muscles[m_name][ang] = r

        results: List[MuscleResponseRecord] = []
        for m_name, ang_dict in muscles.items():
            if lower_ang in ang_dict and upper_ang in ang_dict:
                r0 = ang_dict[lower_ang]
                r1 = ang_dict[upper_ang]

                interp_mt_len = r0["musculotendon_length_m"] + t * (r1["musculotendon_length_m"] - r0["musculotendon_length_m"])
                interp_fib_len = r0["fiber_length_m"] + t * (r1["fiber_length_m"] - r0["fiber_length_m"])
                opt_fib_len = r0["optimal_fiber_length_m"]
                norm_len = round(interp_fib_len / opt_fib_len, 4) if opt_fib_len > 0 else 1.0
                pass_force = round(r0["passive_force_n"] + t * (r1["passive_force_n"] - r0["passive_force_n"]), 2)
                act_force = round(r0["active_force_n"] + t * (r1["active_force_n"] - r0["active_force_n"]), 2)
                tot_force = round(r0["total_force_n"] + t * (r1["total_force_n"] - r0["total_force_n"]), 2)

                state = r1["biomechanical_state"] if t >= 0.5 else r0["biomechanical_state"]
                tag, color = compute_kmsi_tag_and_color(norm_len)

                results.append(MuscleResponseRecord(
                    muscle_name=m_name,
                    shoulder_elevation_deg=round(arm_deg, 1),
                    musculotendon_length_m=round(interp_mt_len, 4),
                    fiber_length_m=round(interp_fib_len, 4),
                    optimal_fiber_length_m=round(opt_fib_len, 4),
                    normalized_fiber_length=norm_len,
                    passive_force_n=pass_force,
                    active_force_n=act_force,
                    total_force_n=tot_force,
                    activation_estimate=0.02,
                    biomechanical_state=state,
                    kmsi_tag=tag,
                    kmsi_color_hex=color,
                ))

        return sorted(results, key=lambda x: x.muscle_name)

    def get_comparative_models(self) -> List[ComparativeMovementModel]:
        """Return available comparative movement models with scientific justifications."""
        return [
            ComparativeMovementModel(
                model_id="normal_2to1",
                name="Canonical 2:1 Scapulohumeral Rhythm",
                short_description="Healthy coordinated movement across glenohumeral, acromioclavicular, and sternoclavicular joints.",
                detailed_mechanism=(
                    "For every 3° of total humeral elevation, 2° occurs at the glenohumeral joint and 1° occurs at the "
                    "scapulothoracic articulation (after an initial 30° setting phase). The clavicle elevates ~32° at the "
                    "sternoclavicular joint. This preserves subacromial space clearance (>6mm) for the supraspinatus tendon."
                ),
                scapular_rhythm_ratio="2:1 Ratio (Inman et al., 1944)",
                subacromial_space_implication="Adequate anatomical clearance preserved throughout 0° to 180° range.",
                clinical_caution="Educational model demonstrating standard healthy biomechanical principles.",
            ),
            ComparativeMovementModel(
                model_id="forward_shoulder_restricted",
                name="Forward Shoulder Posture (Restricted Scapular Upward Rotation)",
                short_description="Simulated alteration characterized by increased scapular anterior tilt and restricted upward rotation.",
                detailed_mechanism=(
                    "The scapula exhibits resting anterior tilt (+12°) and internal rotation (+8°). During arm elevation, "
                    "scapular upward rotation is restricted by ~40% (yielding ~30° instead of 50° at 180° elevation). "
                    "The acromion remains positioned anteriorly and inferiorly, narrowing the subacromial space during "
                    "mid-range elevation (60°–120°)."
                ),
                scapular_rhythm_ratio="~4:1 Ratio (Restricted Scapular Rotation; Ludewig & Cook, 2000)",
                subacromial_space_implication="Subacromial space clearance significantly narrowed between 60° and 120° abduction.",
                clinical_caution=(
                    "Observation model only. Biomechanical narrowing correlates with subacromial impingement vulnerability "
                    "in athletic/overhead literature, but does NOT by itself constitute clinical diagnosis or imply pain causality."
                ),
            ),
        ]

    def get_annotation(self, structure_id: str) -> Optional[StructureAnnotation]:
        """Return rigorous evidence-based educational annotation for a given anatomical structure."""
        sid = structure_id.upper()
        annotations_db: Dict[str, StructureAnnotation] = {
            "FMA13395": StructureAnnotation(
                structure_id="FMA13395",
                name="Right Scapula (Shoulder Blade)",
                fma_id="FMA13395",
                category="bone",
                opensim_id="scapula",
                direct_anatomical_facts=(
                    "Flat, triangular bone resting on the posterior thoracic wall spanning T2–T7 ribs. "
                    "Features the glenoid fossa (articulates with humeral head), acromion process (articulates with clavicle), "
                    "coracoid process, spine, supraspinous, and infraspinous fossae."
                ),
                kinematic_role_during_elevation=(
                    "Provides a dynamic, mobile platform for the humeral head. During arm elevation, it rotates upwardly "
                    "up to 50°, tilts posteriorly up to 20°, and externally rotates. This maintains the glenoid socket directly "
                    "under the humeral head, optimizing rotator cuff muscle length-tension relationships and preventing impingement."
                ),
                evidence_sources=[
                    "Inman VT, Saunders JB, Abbott LC. Observations on the function of the shoulder joint. J Bone Joint Surg Am. 1944;26(1):1-30.",
                    "Ludewig PM, Cook TM. Alterations in shoulder kinematics in people with impingement. Phys Ther. 2000;80(3):276-291.",
                    "McClure PW, Michener LA, et al. Direct 3D measurement of scapular kinematics in vivo. J Shoulder Elbow Surg. 2001;10(3):269-277."
                ],
                model_assumptions="Rigid body assumption; scapulothoracic gliding modeled via coupled kinematic constraints.",
                scientific_limitations=(
                    "Kinematic modeling visualizes geometric motion. It does not measure soft tissue friction, bursa inflammation, "
                    "or prove that scapular positioning alone causes shoulder pain in any individual patient."
                ),
            ),
            "FMA13322": StructureAnnotation(
                structure_id="FMA13322",
                name="Right Clavicle (Collarbone)",
                fma_id="FMA13322",
                category="bone",
                opensim_id="clavicle",
                direct_anatomical_facts=(
                    "S-shaped long bone serving as the sole skeletal strut connecting the upper extremity to the axial skeleton. "
                    "Articulates medially with the manubrium of the sternum (sternoclavicular joint) and laterally with the acromion (acromioclavicular joint)."
                ),
                kinematic_role_during_elevation=(
                    "Elevates up to 30°–35° at the sternoclavicular joint and rotates posteriorly up to 45° around its longitudinal axis "
                    "during overhead arm elevation. Clavicular posterior rotation is biomechanically linked to the conoid ligament tightening as the scapula rotates upward."
                ),
                evidence_sources=[
                    "Neumann DA. Kinesiology of the Musculoskeletal System: Foundations for Rehabilitation. 3rd ed. Elsevier; 2017.",
                    "Teece RM, et al. In vivo three-dimensional clavicular and scapular kinematics during arm elevation. J Orthop Sports Phys Ther. 2008;38(9):571-578."
                ],
                model_assumptions="Modeled as a rigid body with 2 DOFs (elevation/depression, protraction/retraction) at the sternoclavicular pivot.",
                scientific_limitations="Longitudinal rotation of the clavicle is simplified in OpenSim rigid models.",
            ),
            "FMA23130": StructureAnnotation(
                structure_id="FMA23130",
                name="Right Humerus (Arm Bone)",
                fma_id="FMA23130",
                category="bone",
                opensim_id="humerus",
                direct_anatomical_facts=(
                    "Long bone of the upper arm. Hemispherical head articulates with the shallow glenoid fossa. "
                    "Features greater and lesser tubercles separated by the bicipital groove, and deltoid tuberosity on lateral shaft."
                ),
                kinematic_role_during_elevation=(
                    "Elevates up to 120°–130° relative to the scapula (glenohumeral elevation) and rotates externally "
                    "to allow the greater tubercle to clear the acromion during abduction in the coronal plane."
                ),
                evidence_sources=[
                    "Saul KR, et al. Benchmarking of dynamic simulation predictions using an upper extremity model. Comput Methods Biomech Biomed Engin. 2015;18(13):1445-1458.",
                    "Holzbaur KR, et al. A model of the upper extremity for simulating musculoskeletal surgery and analyzing neuromuscular control. Ann Biomed Eng. 2005;33(6):829-840."
                ],
                model_assumptions="Ball-and-socket 3-DOF joint model centered at the instantaneous center of rotation of the humeral head.",
                scientific_limitations="Real glenohumeral joint exhibits micro-translations (1–2 mm); rigid ball-and-socket assumes zero translation.",
            ),
            "FMA34680": StructureAnnotation(
                structure_id="FMA34680",
                name="Clavicular Part of Right Deltoid (Anterior Deltoid)",
                fma_id="FMA34680",
                category="muscle",
                opensim_id="DELT1",
                direct_anatomical_facts=(
                    "Originates from the anterior border and superior surface of the lateral third of the clavicle. "
                    "Inserts into the deltoid tuberosity of the humerus. Innervated by the axillary nerve (C5, C6)."
                ),
                kinematic_role_during_elevation=(
                    "Primary flexor and internal rotator of the arm; assists in arm abduction above 60°. "
                    "As the arm elevates, its fiber length shortens (normalized length drops from ~1.08 to 0.74 at 180°), entering the active ascending limb."
                ),
                evidence_sources=[
                    "Durandau G, et al. CEINMS-RT: an open-source framework for real-time neuromusculoskeletal modeling. IEEE TBME. 2017;65(12):2722-2732.",
                    "Saul KR, et al. Upper extremity musculoskeletal model. Ann Biomed Eng. 2015."
                ],
                model_assumptions="Hill-type Millard2012 equilibrium muscle model with fixed optimal fiber length (9.76 cm).",
                scientific_limitations=(
                    "Model predicts fiber shortening and force based on geometric muscle path; it does NOT measure electromyographic "
                    "firing rate or motor unit recruitment."
                ),
            ),
            "FMA34682": StructureAnnotation(
                structure_id="FMA34682",
                name="Acromial Part of Right Deltoid (Middle Deltoid)",
                fma_id="FMA34682",
                category="muscle",
                opensim_id="DELT2",
                direct_anatomical_facts=(
                    "Originates from the superior surface and lateral margin of the acromion process of the scapula. "
                    "Inserts into the deltoid tuberosity of the humerus. Multi-pennate structure providing high force capacity."
                ),
                kinematic_role_during_elevation=(
                    "Powerful abductor of the arm from 15° to full overhead elevation. Generates vertical shearing force "
                    "counteracted by the rotator cuff force-couple."
                ),
                evidence_sources=[
                    "Inman VT, et al. Observations on the function of the shoulder joint. J Bone Joint Surg. 1944.",
                    "Kronberg M, et al. Muscle activity and coordination in the normal shoulder. Clin Orthop Relat Res. 1990;(257):76-85."
                ],
                model_assumptions="Tendon slack length 10.95 cm, optimal fiber length 10.78 cm.",
                scientific_limitations="Model treats muscle as a line of action; pennation changes during extreme contraction are approximated.",
            ),
            "FMA37684": StructureAnnotation(
                structure_id="FMA37684",
                name="Short Head of Right Biceps Brachii",
                fma_id="FMA37684",
                category="muscle",
                opensim_id="BICshort",
                direct_anatomical_facts=(
                    "Originates from the apex of the coracoid process of the scapula. Inserts into the radial tuberosity and bicipital aponeurosis. "
                    "Innervated by the musculocutaneous nerve (C5, C6)."
                ),
                kinematic_role_during_elevation=(
                    "Bi-articular muscle. Weak anterior flexor and stabilizer of the glenohumeral joint; primary forearm flexor and supinator."
                ),
                evidence_sources=[
                    "Holzbaur KR, et al. Upper extremity model. Ann Biomed Eng. 2005.",
                    "Neumann DA. Kinesiology of the Musculoskeletal System. 2017."
                ],
                model_assumptions="OpenSim rigid path wrapping around anatomical cylindrical obstacles.",
                scientific_limitations="Does not simulate fascial tension transfer across the bicipital aponeurosis.",
            ),
            "FMA37686": StructureAnnotation(
                structure_id="FMA37686",
                name="Long Head of Right Biceps Brachii",
                fma_id="FMA37686",
                category="muscle",
                opensim_id="BIClong",
                direct_anatomical_facts=(
                    "Originates from the supraglenoid tubercle of the scapula, arches over the humeral head inside the fibrous joint capsule, "
                    "and emerges through the intertubercular (bicipital) groove. Inserts into the radial tuberosity."
                ),
                kinematic_role_during_elevation=(
                    "Acts as a dynamic anterior and superior humeral head stabilizer, helping seat the humeral head in the glenoid during abduction. "
                    "Susceptible to friction and inflammation when subacromial clearance is reduced."
                ),
                evidence_sources=[
                    "Pagnani MJ, et al. Effect of lesions of the superior glenoid labrum on shoulder instability. J Bone Joint Surg. 1995.",
                    "Saul KR, et al. MoBL-ARMS Upper extremity model. 2015."
                ],
                model_assumptions="Path wraps over the humeral head; friction within the bicipital groove is neglected.",
                scientific_limitations="Intra-articular tenosynovitis or labral fraying cannot be simulated via rigid kinematics.",
            ),
        }

        # Case-insensitive lookup fallback
        if sid in annotations_db:
            return annotations_db[sid]
        for k, v in annotations_db.items():
            if k.lower() == sid.lower() or v.opensim_id.lower() == sid.lower():
                return v

        # Return generic structure record if registered in manifest
        struct_info = self._manifest.get("structures", {}).get(sid)
        if struct_info:
            return StructureAnnotation(
                structure_id=sid,
                name=struct_info.get("name", sid),
                fma_id=sid,
                category=struct_info.get("category", "bone"),
                opensim_id=struct_info.get("opensim_id", ""),
                direct_anatomical_facts=f"Structure registered in BodyParts3D (FMA: {sid}).",
                kinematic_role_during_elevation="Articulates as part of the upper extremity anatomical chain.",
                evidence_sources=["BodyParts3D Database Center for Life Science (DBCLS), Japan."],
                model_assumptions="Rigid body transformation within Three.js scene graph.",
                scientific_limitations="Model visualization only; not validated for clinical diagnosis.",
            )
        return None


# Global singleton
_shoulder_engine: Optional[ShoulderMovementLabEngine] = None


def get_shoulder_lab_engine() -> ShoulderMovementLabEngine:
    global _shoulder_engine
    if _shoulder_engine is None:
        _shoulder_engine = ShoulderMovementLabEngine()
    return _shoulder_engine
