# P15 Guided Learning Case Study & Interactive UI Acceptance
**MSK Research Lab OS — Milestone P15**  
**Role:** Biomedical User Experience Engineer, Independent QA  
**Date:** 2026-10-31  
**Module:** [`shoulder_lab.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/biomechanics/shoulder_lab.py) / [`workstation_ui.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/workstation_ui.py)

---

## 1. Guided Learning Interactive Architecture

The Guided Learning module provides a structured, 6-scene pedagogical journey embedded directly within the Shoulder Movement Lab (`#view-shoulder`).

### 1.1 UI Controls & State Synchronization
- **Navigation Controls:** `← Prev Scene` (`#btn-guided-prev`), `Next Scene →` (`#btn-guided-next`), and direct scene dot indicators (`#guided-scene-dots`).
- **Dynamic State Updates:** Transitioning scenes automatically adjusts:
  1. Arm elevation timeline slider (`#shoulder-timeline-slider`).
  2. Movement comparison model (`#shoulder-comparison-select`).
  3. Highlighted 3D anatomical structure (`#shoulder-structure-select`).
  4. Pedagogical narrative, biomechanical insights, and scientific limitations.
  5. Contextual explanation resolving why shoulder tension returns.

---

## 2. Six-Scene Structured Curriculum

```mermaid
journey
    title 6-Scene Guided Movement Education Curriculum
    section Scene 1: Foundations
      Resting Skeletal Alignment: 5: Scapula FMA13395, 0° Arm Elevation
    section Scene 2: Canonical Rhythm
      Inman 2:1 Scapulohumeral Coordination: 5: 90° Elevation, Subacromial Clearance
    section Scene 3: Restricted Pathology
      Hypothetical Restriction & Compensation: 4: Restricted 4:1 Rhythm, Impingement Risk
    section Scene 4: Muscle Mechanics
      OpenSim Fiber Lengths & Passive Elastic Force: 5: DELT1/DELT3, KMSI Color Chips
    section Scene 5: Sensorimotor Loops
      Proprioception, Spindles & Reflex Arcs: 5: Ia/Ib Afferents, Gamma Drive
    section Scene 6: Durable Repatterning
      Why Tension Returns & Principles of Lasting Change: 5: Viscoelasticity vs Active Neuroplasticity
```

### Scene 1: Anatomical Architecture of the Shoulder Girdle
- **Recommended Angle:** $0.0^\circ$ (Neutral Rest)
- **Comparison Mode:** Canonical 2:1 Rhythm
- **Highlighted Structure:** Right Scapula (`FMA13395`)
- **Key Pedagogical Focus:** 4-articulation system (GH, SC, AC, ST) and resting muscular fiber lengths ($l_{M,0}$).

### Scene 2: Canonical 2:1 Scapulohumeral Rhythm
- **Recommended Angle:** $90.0^\circ$ (Horizontal Abduction)
- **Comparison Mode:** Canonical 2:1 Rhythm
- **Highlighted Structure:** Right Clavicle (`FMA13322`)
- **Key Pedagogical Focus:** Setting phase ($0^\circ–30^\circ$) vs coordinated upward rotation ($30^\circ–180^\circ$) maintaining subacromial space.

### Scene 3: Hypothetical Restricted Scapular Rotation
- **Recommended Angle:** $90.0^\circ$
- **Comparison Mode:** Forward Shoulder Restricted (4:1 Rhythm)
- **Highlighted Structure:** Right Scapula (`FMA13395`)
- **Key Pedagogical Focus:** Scapular upward rotation restricted from $20^\circ$ down to $12^\circ$, forcing compensatory glenohumeral over-elevation to $78^\circ$ and subacromial space compromise.

### Scene 4: OpenSim Modeled Muscle Fiber Length & Passive Force
- **Recommended Angle:** $120.0^\circ$ (High Abduction)
- **Comparison Mode:** Canonical 2:1 Rhythm
- **Highlighted Structure:** Anterior Deltoid (`FMA34680` / `DELT1`)
- **Key Pedagogical Focus:** Forward kinematics fiber length dynamics: agonist shortening ($\tilde{l}_M < 0.85$, blue) vs antagonist stretching ($\tilde{l}_M > 1.15$, amber/red) and exponential passive force generation ($F^{pe}$).

### Scene 5: Neural Planning & Afferent Sensory Feedback
- **Recommended Angle:** $45.0^\circ$ (Early Elevation)
- **Comparison Mode:** Canonical 2:1 Rhythm
- **Highlighted Structure:** Humerus (`FMA23130`)
- **Key Pedagogical Focus:** Sensorimotor loops, spindle length tracking, GTO force sensing, and gamma-motor neuron sensitivity preservation.

### Scene 6: Why Tension Returns & Principles of Lasting Change
- **Recommended Angle:** $0.0^\circ$ (Neutral Rest)
- **Comparison Mode:** Canonical 2:1 Rhythm
- **Highlighted Structure:** Right Scapula (`FMA13395`)
- **Key Pedagogical Focus:** Viscoelastic stress-relaxation and thixotropy explain short-term manual relief; lasting postural repatterning requires deliberate active movement practice driving cortical map reorganization.
