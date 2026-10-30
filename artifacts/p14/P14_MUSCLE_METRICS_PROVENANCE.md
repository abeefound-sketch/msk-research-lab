# P14 Muscle Metrics Scientific Provenance & Biomechanical Interpretation
**MSK Research Lab OS — Milestone P14**  
**Role:** OpenSim Integration Engineer, Biomechanical Metrology Auditor  
**Date:** 2026-10-30  
**Dataset Reference:** OpenSim 4.6 `MOBL_ARMS_41.osim` / `muscle_response_validation.csv`  

---

## 1. Executive Summary

A core requirement of P14 is ensuring absolute scientific integrity in how computational muscle outputs are presented to researchers and learners. Computational models predict structural fiber excursion and passive elastic tension based on musculoskeletal geometry; they do **not** record electromyographic (EMG) motor unit recruitment, neural firing frequency, or clinical muscle pathology.

This report documents:
1. The mathematical definition and Hill-type formulation of normalized muscle fiber length ($\tilde{l}_M$) and passive elastic tension.
2. The rigorous separation of structural muscle length from voluntary neural activation.
3. The resolution of the cross-model attribution defect (**DEF-43**): ensuring that baseline OpenSim muscle forces are never deceptively presented as if they had been recomputed for the Forward Shoulder posture scenario.

---

## 2. Hill-Type Muscle Modeling Formulation

The OpenSim `MOBL_ARMS_41` upper extremity model (Saul et al., 2015) employs the Millard2012 Equilibrium Muscle Model (Millard et al., 2012) to calculate force-length-velocity dynamics.

### 2.1 Kinematic Excursion & Fiber Length
The total musculotendon length $l_{MT}$ is determined by the 3D joint coordinate state $\vec{q}$ and the wrapping path over anatomical cylindrical and ellipsoidal obstacles:
$$l_{MT} = f(\vec{q})$$

The musculotendon unit comprises the active muscle fibers (length $l_M$ with pennation angle $\alpha$) in series with the tendon (length $l_T$):
$$l_{MT} = l_M \cos\alpha + l_T$$

### 2.2 Normalized Fiber Length ($\tilde{l}_M$)
To evaluate where a muscle operates on its active force-length curve, fiber length is normalized by its optimal fiber length $l_{M,0}$:
$$\tilde{l}_M = \frac{l_M}{l_{M,0}}$$
- **Ascending Limb ($\tilde{l}_M < 0.85$):** Myofilament overlap is excessive; active force capacity declines. Labeled as `SHORTENED` in KMSI.
- **Plateau / Resting Region ($0.85 \le \tilde{l}_M \le 1.15$):** Maximal cross-bridge formation. Labeled as `NOMINAL_RESTING` in KMSI.
- **Descending Limb ($1.15 < \tilde{l}_M \le 1.40$):** Reduced cross-bridge overlap; active force declines while passive tension begins to rise. Labeled as `MODERATE_STRETCH` in KMSI.
- **Extreme Passive Stretch ($\tilde{l}_M > 1.40$):** Passive elastic elements dominate. Labeled as `HIGH_STRETCH` in KMSI.

### 2.3 Passive Elastic Force ($F_{passive}$)
Passive force does **not** indicate voluntary contraction or neural spasm. It represents the non-linear exponential elastic recoil of structural intracellular macromolecules (primarily titin) and extracellular collagen matrix (perimysium, endomysium) when stretched beyond optimal length:
$$F_{passive} = F_0^M \cdot f_{PE}(\tilde{l}_M)$$
where $F_0^M$ is maximum isometric force and $f_{PE}(\tilde{l}_M)$ is the normalized passive force-length relationship.

---

## 3. Monitored Muscle Characteristics & Trajectory Responses

The Shoulder Movement Lab tracks 8 representative upper extremity muscle compartments across coronal arm elevation:

| Muscle Identifier | Anatomical Name | Compartment Role | Optimal Length $l_{M,0}$ | Tendon Slack $l_T^s$ | State at 0° | State at 90° | State at 180° |
|---|---|---|---|---|---|---|---|
| **DELT1** | Anterior Deltoid | Clavicular head; flexion/abduction | 9.76 cm | 9.30 cm | $\tilde{l}_M = 1.082$ (Nominal) | $\tilde{l}_M = 0.932$ (Shortening) | $\tilde{l}_M = 0.741$ (Shortened) |
| **DELT2** | Middle Deltoid | Acromial head; primary abductor | 10.78 cm | 10.95 cm | $\tilde{l}_M = 1.054$ (Nominal) | $\tilde{l}_M = 1.018$ (Nominal) | $\tilde{l}_M = 0.985$ (Nominal) |
| **DELT3** | Posterior Deltoid | Scapular spine; extension/retraction | 13.72 cm | 3.00 cm | $\tilde{l}_M = 0.950$ (Nominal) | $\tilde{l}_M = 1.180$ (Stretch) | $\tilde{l}_M = 1.345$ (High Stretch) |
| **PECM1** | Pectoralis Major (Clavicular) | Horizontal adduction / flexion | 14.50 cm | 10.00 cm | $\tilde{l}_M = 0.880$ (Nominal) | $\tilde{l}_M = 1.150$ (Moderate Stretch) | $\tilde{l}_M = 1.280$ (Stretch) |
| **PECM2** | Pectoralis Major (Sternal) | Powerful adduction / internal rot | 15.20 cm | 12.00 cm | $\tilde{l}_M = 0.920$ (Nominal) | $\tilde{l}_M = 1.350$ (High Stretch) | $\tilde{l}_M = 1.480$ (Extreme Stretch) |
| **BICshort** | Biceps Brachii (Short Head) | Coracoid origin; GH flexion/stab | 13.08 cm | 27.24 cm | $\tilde{l}_M = 1.012$ (Nominal) | $\tilde{l}_M = 0.915$ (Shortening) | $\tilde{l}_M = 0.840$ (Shortened) |
| **BIClong** | Biceps Brachii (Long Head) | Supraglenoid origin; humeral head stab | 11.57 cm | 27.24 cm | $\tilde{l}_M = 1.045$ (Nominal) | $\tilde{l}_M = 0.940$ (Shortening) | $\tilde{l}_M = 0.865$ (Shortened) |
| **TRIlong** | Triceps Brachii (Long Head) | Infraglenoid origin; bi-articular ext | 13.40 cm | 19.00 cm | $\tilde{l}_M = 0.980$ (Nominal) | $\tilde{l}_M = 1.210$ (Moderate Stretch) | $\tilde{l}_M = 1.420$ (High Stretch) |

---

## 4. Remediation of Cross-Model Attribution (DEF-43)

### 4.1 The Defect
In P13, the REST endpoint `/api/v1/biomechanics/shoulder/muscles/response` returned muscle metrics derived exclusively from baseline `MOBL_ARMS_41` coordinates regardless of whether the user had selected Model A (Normal) or Model B (Forward Shoulder). This could mislead researchers into believing that passive forces and fiber stretch had been recalculated for the altered scapulothoracic kinematics of Model B.

### 4.2 The Solution
In Milestone P14:
1. The route now takes `comparison_mode`:
   `/api/v1/biomechanics/shoulder/muscles/response?arm_elevation_deg=90.0&comparison_mode=forward_shoulder_restricted`
2. When `comparison_mode == "forward_shoulder_restricted"`:
   - `data_provenance = "BASELINE_MOBL_ARMS_MODEL_ESTIMATE; UNADJUSTED_FOR_RESTRICTED_POSTURE"`
   - `validation_status = "NOT_VERIFIED_FOR_MODIFIED_POSTURE"`
   - `scenario_adjusted = False`
   - `scenario_note = "CAUTION: OpenSim muscle metrics reflect baseline anatomical kinematics (MOBL_ARMS_41). Scenario-specific re-simulation for restricted scapular geometry has not been performed."`
3. The UI renders an unmistakable amber/red warning badge on every muscle row: `[BASELINE (UNADJUSTED)]` with the caveat note visible in tooltips and headers.
4. When `comparison_mode == "normal_2to1"`:
   - `validation_status = "VERIFIED_BASELINE_BENCHMARK"`
   - `scenario_adjusted = True`
   - UI renders: `[BENCHMARK]`.

---

## 5. Separation of Structural Length from Neural Activation

To ensure researchers and students do not conflate geometric fiber length with voluntary neurological recruitment or pathological muscle tone:
1. All muscle records include `activation_estimate: 0.02` (fixed nominal baseline passive tone).
2. The schema includes `neural_activation_note`:
   *"Unmodeled: activation is fixed at nominal passive tone (0.02). Does not represent EMG recruitment or voluntary contraction."*
3. The UI presents a dedicated footer note clarifying that muscle force metrics reflect passive Hill-type elasticity under geometric deformation, **not** active electromyography.
