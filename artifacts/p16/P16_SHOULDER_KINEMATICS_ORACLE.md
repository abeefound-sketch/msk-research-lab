# P16 Independent Shoulder Kinematics & Analytical Oracle Report
**MSK Research Lab OS — Milestone P16**  
**Role:** Principal Biomedical Simulation Engineer, Kinematics Auditor  
**Date:** 2026-10-31  
**Target Milestone:** P16 Qualification  
**Oracle Script:** [`tests/unit/test_p16_kinematics_and_opensim_oracle.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_p16_kinematics_and_opensim_oracle.py)  

---

## 1. Executive Summary

Milestone P16 verified the shoulder elevation kinematic models through independent analytical forward kinematics oracles. The mathematical equations governing joint rotations were validated across 8 standard benchmark angles: **0°, 30°, 45°, 60°, 90°, 120°, 150°, and 180°**.

Crucially, this audit resolves the common ambiguity in biomechanics literature between **incremental scapulohumeral rhythm** (the 2:1 ratio of elevation above the setting phase) and **cumulative scapulohumeral ratio** (the instantaneous quotient of total glenohumeral elevation to total scapulothoracic upward rotation).

---

## 2. Theoretical Kinematic Architecture & Hierarchy

### 2.1 Coordinate Reference Frames and Joint Axes
The kinematic chain is organized in a fail-closed parent-child transformation tree:
$$\text{Thorax (World Root)} \xrightarrow{\mathcal{T}_{SC}} \text{Clavicle Group} \xrightarrow{\mathcal{T}_{AC}} \text{Scapula Group} \xrightarrow{\mathcal{T}_{GH}} \text{Humerus Group} \xrightarrow{\mathcal{T}_{Elbow}} \text{Forearm Group}$$

- **Sternoclavicular (SC) Joint:** Elevation axis around local Y-axis ($\mathbf{e}_y$).
- **Acromioclavicular (AC) Joint:** Relative upward rotation around local Y-axis ($\mathbf{e}_y$) and anterior/posterior tilt around local X-axis ($\mathbf{e}_x$).
- **Glenohumeral (GH) Joint:** Elevation axis around local Y-axis ($\mathbf{e}_y$).

### 2.2 Mathematical Transformation Conservation
By construction in the local group hierarchy:
1. **Total Scapulothoracic (ST) Upward Rotation:**
   $$\theta_{ST} = \theta_{SC} + \theta_{AC,rel}$$
2. **Total Humeral Elevation:**
   $$\theta_{Arm} = \theta_{SC} + \theta_{AC,rel} + \theta_{GH} = \theta_{ST} + \theta_{GH}$$

---

## 3. Incremental vs. Cumulative Scapulohumeral Ratios

### 3.1 Model A: Canonical Inman Baseline
- **Setting Phase ($0^\circ \le \theta_{Arm} \le 30^\circ$):**
  - Arm elevation is primarily glenohumeral: $\theta_{ST} = 0^\circ, \theta_{GH} = \theta_{Arm}$.
  - Incremental rhythm: Pure GH ($1:0$).
  - Cumulative ratio: Undefined at $0^\circ$; $\infty$ at $30^\circ$.
- **Active Phase ($30^\circ < \theta_{Arm} \le 180^\circ$):**
  - $\theta_{ST} = \frac{\theta_{Arm} - 30^\circ}{3}$
  - $\theta_{GH} = \theta_{Arm} - \theta_{ST} = 30^\circ + \frac{2}{3}(\theta_{Arm} - 30^\circ)$
  - **Incremental Ratio:** $\frac{\Delta\theta_{GH}}{\Delta\theta_{ST}} = \frac{2/3}{1/3} = \mathbf{2.0:1}$ (constant above 30°).
  - **Cumulative Ratio:** $\mathcal{R}_{cum}(\theta_{Arm}) = \frac{\theta_{GH}}{\theta_{ST}} = \frac{2\theta_{Arm} + 30^\circ}{\theta_{Arm} - 30^\circ}$.

### 3.2 Model B: Restricted Scapulohumeral Rhythm (Ludewig & Cook 2000)
- **Setting Phase ($0^\circ \le \theta_{Arm} \le 30^\circ$):** $\theta_{ST} = 0^\circ, \theta_{GH} = \theta_{Arm}$.
- **Active Phase ($30^\circ < \theta_{Arm} \le 180^\circ$):**
  - Scapular upward rotation restricted by 40%: $\theta_{ST} = 0.20 \times (\theta_{Arm} - 30^\circ)$.
  - **Incremental Ratio:** $\frac{\Delta\theta_{GH}}{\Delta\theta_{ST}} = \frac{0.80}{0.20} = \mathbf{4.0:1}$ (constant above 30°).
  - **Cumulative Ratio:** $\mathcal{R}_{cum}(\theta_{Arm}) = \frac{\theta_{GH}}{\theta_{ST}} = \frac{0.80\theta_{Arm} + 6.0^\circ}{0.20(\theta_{Arm} - 30^\circ)}$.

---

## 4. 8-Angle Numerical Oracle Verification Results

### 4.1 Model A: Canonical 2:1 Inman Elevation

| Arm Angle | GH Elevation ($\theta_{GH}$) | ST Upward Rot ($\theta_{ST}$) | SC Elevation ($\theta_{SC}$) | AC Rel Rot ($\theta_{AC}$) | Incremental Ratio | Cumulative Ratio | Subacromial Status |
|---|---|---|---|---|---|---|---|
| **0.0°** | 0.00° | 0.00° | 0.00° | 0.00° | Setting Phase (ST=0°) | Neutral (0°) | Adequate Clearance |
| **30.0°**| 30.00° | 0.00° | 5.40° | -5.40° | Setting Phase (ST=0°) | Pure GH (30:0) | Adequate Clearance |
| **45.0°**| 40.00° | 5.00° | 8.10° | -3.10° | **2.0:1** | **8.00:1** | Adequate Clearance |
| **60.0°**| 50.00° | 10.00° | 10.80° | -0.80° | **2.0:1** | **5.00:1** | Adequate Clearance |
| **90.0°**| 70.00° | 20.00° | 16.20° | +3.80° | **2.0:1** | **3.50:1** | Adequate Clearance |
| **120.0°**| 90.00° | 30.00° | 21.60° | +8.40° | **2.0:1** | **3.00:1** | Adequate Clearance |
| **150.0°**| 110.00° | 40.00° | 27.00° | +13.00° | **2.0:1** | **2.75:1** | Adequate Clearance |
| **180.0°**| 130.00° | 50.00° | 32.40° | +17.60° | **2.0:1** | **2.60:1** | Adequate Clearance |

### 4.2 Model B: Restricted 4:1 Elevation

| Arm Angle | GH Elevation ($\theta_{GH}$) | ST Upward Rot ($\theta_{ST}$) | SC Elevation ($\theta_{SC}$) | AC Rel Rot ($\theta_{AC}$) | Incremental Ratio | Cumulative Ratio | Subacromial Status |
|---|---|---|---|---|---|---|---|
| **0.0°** | 0.00° | 0.00° | 0.00° | 0.00° | Setting Phase (ST=0°) | Neutral (0°) | Reduced Clearance |
| **30.0°**| 30.00° | 0.00° | 3.60° | -3.60° | Setting Phase (ST=0°) | Pure GH (30:0) | Reduced Clearance |
| **45.0°**| 42.00° | 3.00° | 5.40° | -2.40° | **4.0:1** | **14.00:1** | Reduced Clearance |
| **60.0°**| 54.00° | 6.00° | 7.20° | -1.20° | **4.0:1** | **9.00:1** | **Compromised (Risk)** |
| **90.0°**| 78.00° | 12.00° | 10.80° | +1.20° | **4.0:1** | **6.50:1** | **Compromised (Risk)** |
| **120.0°**| 102.00° | 18.00° | 14.40° | +3.60° | **4.0:1** | **5.67:1** | **Compromised (Risk)** |
| **150.0°**| 126.00° | 24.00° | 18.00° | +6.00° | **4.0:1** | **5.25:1** | Reduced Clearance |
| **180.0°**| 150.00° | 30.00° | 21.60° | +8.40° | **4.0:1** | **5.00:1** | Reduced Clearance |

---

## 5. Scientific Limitations & Epistemic Guardrails

1. **Non-Universality of 2:1:** The classic 2:1 Inman ratio is an educational benchmark. Modern dynamic 3D biplane fluoroscopy reveals substantial healthy variation ranging from **1.5:1 to 3:1** across individuals and planes of elevation (sagittal, scapular, frontal).
2. **Subacromial Clearance Framing:** Narrows between 60° and 120° in Model B represent a **geometric proximity educational hypothesis**, not a personalized clinical diagnosis of subacromial impingement syndrome (SIS).
3. **Fail-Closed Verification:** All 16 oracle parameter test instances passed with zero floating-point discrepancies ($\epsilon < 10^{-4}$).
