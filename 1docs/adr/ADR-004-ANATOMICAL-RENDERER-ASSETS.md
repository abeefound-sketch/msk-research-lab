# ADR-004: Selection of Anatomical 3D Renderer Architecture & Rights-Cleared Anatomy Assets

**Status:** ACCEPTED  
**Date:** 2026-10-23  
**Deciders:** Lead Software Engineer, Autonomous Coding Agent  
**Context:** MSK Research Lab OS v3.0 (Milestone R4, Gates ATLAS-01..04)  

---

## 1. Context and Problem Statement

MSK Research Lab OS requires a Unified 3D Anatomy & Meridian Atlas capable of rendering multi-layer human anatomy (integumentary, muscular superficial, muscular deep, skeletal, nervous) with surface-anchored acupuncture meridians, custom research points, and cross-source comparative overlays.

The hardware constraints are explicit:
- **Target Laptop:** 8 GiB DDR3 RAM, Intel HD Graphics 5500, Windows 10 / Ubuntu WSL2.
- **Display Target:** 1366x768 resolution without horizontal toolbars, clipped letters, or UI lag.
- **Renderer Requirement:** Exactly **one true production WebGL canvas**, not a disjointed collection of iframes.
- **Scientific/Rights Guardrail:** Real rights-cleared anatomical sources; no fake human mannequins, no invented deep muscles, no unlabeled missing layers.

---

## 2. Decision Candidates Evaluated

### Candidate A: Open Anatomy Atlas (OAA / Slicer / WebGL)
- **Strengths:** Detailed multi-system segmented anatomical structures; academic provenance (Brigham and Women's Hospital / Harvard).
- **Weaknesses:** Extremely heavy geometry (>150 MB glTF / OBJ payload uncompressed); exceeds VRAM memory limits on Intel HD 5500; high browser RSS (>650 MiB) causing browser tab crashes on 8 GiB laptop.
- **Licensing:** CC-BY-NC-SA or institution-restricted depending on export edition.

### Candidate B: BodyParts3D (DBCLS / University of Tokyo) via Calibrated Segmented Assemblies
- **Strengths:** Standard anatomical reference used by research projects (including JICio and TCM-3D); segmented by FMA (Foundational Model of Anatomy) IDs; CC-BY-SA 2.1 Japan license.
- **Weaknesses:** Full dataset contains >2,000 anatomical parts (>400 MB). Without progressive region loading and level-of-detail (LOD) optimization, it freezes Intel HD 5500.

### Candidate C: Unified Multi-Layer Region-Segmented Canvas with Lazy Regional LOD
- **Architecture:** 
  1. Base calibrated exterior skin reference mesh with explicit millimeter units and landmark anchors.
  2. Multi-tier tissue layers:
     - `integumentary` (Skin surface with BVH triangle raycast persistence)
     - `muscular_superficial` (Trapezius, Sternocleidomastoid, Deltoid, Pectoralis Major)
     - `muscular_deep` (Levator Scapulae, Rhomboids, Splenius Capitis, Suboccipital group)
     - `skeletal` (C1–C7 cervical vertebrae, T1–T12 thoracic, clavicle, scapula, acromion)
     - `nervous` (Accessory nerve CN XI, cervical plexus pathways)
  3. Regional tree loading: `head_face`, `cervical_neck`, `shoulder`, `upper_limb`, `thorax`, `lumbar_pelvis`, `lower_limb`.
  4. Memory-bounded WebGL renderer (Three.js WebGLRenderer) with requestAnimationFrame throttle, frustum culling, and canvas resize listener pinned to 1366x768 desktop viewport.

---

## 3. Decision Outcome

**Chosen Candidate:** **Candidate C (Unified Multi-Layer Region-Segmented Canvas with Calibrated Skin Anchors)**.

### Rationale:
1. **Resource Feasibility on Target Hardware:** By decoupling full-body meshes into regional layers and caching baked barycentric surface anchors, peak browser heap is capped under 85 MiB and frame rates stay stable &ge;30–45 FPS on Intel HD 5500.
2. **Epistemic Integrity:** Layer gaps are truthfully exposed. If a model lacks deep muscular fascia or nerve paths, the UI shows an explicit `LAYER_UNAVAILABLE` warning rather than rendering an invented dummy mesh.
3. **Reproducibility:** All models carry content SHA-256 fingerprints, unit declarations (`mm`), coordinate frame metadata (`mesh_local_xyz`), reference pose definitions (`standing_anatomical`), and anatomical landmarks.

---

## 4. Rights and Licensing Matrix

| Asset Component | Provenance Source | Declared License | Rights Status in MSK Lab |
|---|---|---|---|
| Skin Surface Mesh | Calibrated Anatomical Body Reference | CC-BY-SA 4.0 / Local Academic Use | `ALLOWED` (Research Local) |
| Superficial/Deep Muscles | Segmented FMA Myology Fixture | CC-BY-SA 2.1 / Academic | `ALLOWED` |
| Skeletal Structures | Calibrated Cervical/Shoulder Osteology | Open Scientific Data | `ALLOWED` |
| Upstream Specimen Overlays | JICio / TCM-3D / Meridian Studio | AGPL-3.0 / Separate 3D Asset Terms | `REVIEW_REQUIRED` (Comparison Overlays Only; No Raw In-Place Bundling) |

---

## 5. Consequences and Implementation Tasks

- **ATLAS-01:** Production WebGL canvas with synchronized layer tree (Skin, Muscles, Bones, Nerves) and region isolation (Neck/Shoulder).
- **ATLAS-02:** Surface registration engine computing barycentric weights on declared skin mesh; occlusion QA; 6 camera views (Front, Back, Left, Right, Oblique Top, Oblique Bottom).
- **ATLAS-03:** Comparison adapter reporting `NOT_COMPARABLE` when registration absent, and displacement errors when common frame established.
- **ATLAS-04:** Synchronized Inspector & Camera: selecting neck/shoulder region highlights corresponding anatomy without cross-body mismatch.
