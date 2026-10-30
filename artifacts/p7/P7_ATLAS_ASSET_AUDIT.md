# MSK Research Lab OS — P7 3D Atlas & Knowledge Integrity Audit

**Audit Role:** Biomedical Software Safety Engineer & 3D Anatomical Asset Inspector  
**Date:** 2026-10-30  
**Standards:** Open Anatomy License Compliance, Epistemic Boundary Verification, DBCLS BodyParts3D & Z-Anatomy Provenance  

---

## 1. Executive Summary & Epistemic Boundaries

In medical and anatomical software, substituting simplified geometric shapes (such as cylinders or spheres) for actual anatomical structures while presenting the result as authentic anatomy constitutes an epistemic safety violation.

During the P7 audit, **DEF-05** was discovered: when GLTFLoader errored or a model was missing, [`workstation_ui.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/workstation_ui.py) fell back to `renderCalibratedReferenceTorso()`, which rendered a `THREE.CylinderGeometry(0.5, 0.4, 1.4, 16)` and spine line.

**DEF-05 was completely remediated:**
- All primitive cylinder geometry fallbacks were permanently deleted.
- If an anatomical asset fails to load, the UI displays an explicit fail-closed alert:  
  `3D ANATOMICAL ASSET ERROR: Failed to load authentic 3D mesh. Mock primitive substitution is prohibited by biomedical safety invariants.`

---

## 2. Comprehensive 3D and Neural Model Asset Inventory

Every model asset present in the offline workstation was forensically verified with file size, SHA-256 checksum, upstream origin, license terms, and runtime load status:

| Asset Identifier | File Path | File Size | SHA-256 Checksum | Upstream Provenance | License | Load Status |
|---|---|---|---|---|---|---|
| **`watercmy_bp3d_z_anatomy`** | `3refs/upstream/watercmy--anatomy-3d/models/anatomy.glb` | 27,272,392 B (26.0 MB) | `318347f91e4989da0c271e9662df536943df1149b413fef01cf21586073ea73e` | DBCLS BodyParts3D / Z-Anatomy (watercmy repository) | **CC-BY-SA 2.1 Japan** | **VERIFIED (Active Default)** |
| **`spacejohnlf_z_anatomy`** | `3refs/upstream/spacejohnlf--tcm-acupoints/dist/models/body.glb` | 1,843,440 B (1.76 MB) | `0886b6a068e655b284903664e2178d7964f80b1c0ce798461909ac806bcef2e3` | spacejohnlf TCM Acupoints Mannequin Mesh | **MIT (Upstream Package)** | **VERIFIED (Alternative Model)** |
| **`spacejohnlf_body_public`** | `3refs/upstream/spacejohnlf--tcm-acupoints/public/models/body.glb` | 1,843,440 B (1.76 MB) | `0886b6a068e655b284903664e2178d7964f80b1c0ce798461909ac806bcef2e3` | Identical source copy in public asset tree | **MIT** | **VERIFIED (Identical Mirror)** |
| **`pose_landmarker_lite`** | `2data/models/pose_landmarker_lite.task` | 5,777,746 B (5.51 MB) | `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a` | Google MediaPipe Tasks Vision Model Bundle | **Apache 2.0** | **VERIFIED (Offline Pose Tracker)** |

---

## 3. WebGL Scene Graph & Anatomical Layer Controls

The Three.js viewer ([`src/msk_research_lab/api/workstation_ui.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/workstation_ui.py#L1550-L1680)) implements genuine scene graph hierarchy management:

```
[threeScene]
  ├── [AmbientLight + DirectionalLights (3x)]
  ├── [musclesGroup]  --> Contains authentic GLTF Mesh nodes parsed from anatomy.glb
  └── [meridiansGroup] --> Contains authenticated acupoints & meridian trajectory lines
```

### Verified Layer Interactions
1. **Muscles Toggle (`btn-toggle-muscles`):**  
   Directly toggles `musclesGroup.visible = !musclesGroup.visible`. When OFF, all superficial and deep muscle meshes are hidden from the WebGL rasterizer.
2. **Meridians Toggle (`btn-toggle-meridians`):**  
   Directly toggles `meridiansGroup.visible = !meridiansGroup.visible`. When OFF, all acupoint spheres and connecting polyline trajectories are hidden.
3. **Reset View (`btn-reset-atlas`):**  
   Resets camera position to $(0, 0, 4)$ and targets the coordinate origin $(0, 0, 0)$ via `OrbitControls.target.set(0, 0, 0)`.

---

## 4. Epistemic Guard: 2D Diện Chẩn to 3D Projection Invariant

Traditional Vietnamese Diện Chẩn facial acupuncture points are cataloged as **2D pixel coordinates on calibrated reference facial charts** (e.g., [`DC_19`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_dien_chan_2d.py#L24-L30) at $x=250.0, y=310.0$ on front view).

### Strict Enforcements Verified in Code:
1. **Forbidden Implicit 3D Conversion:**  
   In [`src/msk_research_lab/studio/dien_chan.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/studio/dien_chan.py), calling [`attempt_project_2d_to_3d()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/studio/dien_chan.py#L120) strictly raises:
   ```python
   raise DienChanError("CANNOT_IMPLICITLY_PROJECT_2D_TO_3D: 2D facial reflexology points cannot be projected into 3D mesh without calibrated bi-planar photogrammetry.")
   ```
2. **Session-Specific Reactive Observation Boundary:**  
   Hyper-sensitive reactive points observed during a live therapy simulation (`REACTIVE_OBSERVATION`) are strictly barred from being promoted to permanent global canonical standards ([`attempt_promote_reactive_to_global()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/studio/dien_chan.py#L145)).
3. **Automated Unit Verification:**  
   Confirmed by [`tests/unit/test_dien_chan_2d.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/unit/test_dien_chan_2d.py):
   - `test_epistemic_guard_rejects_implicit_2d_to_3d`: **PASS**
   - `test_epistemic_guard_rejects_reactive_to_global_promotion`: **PASS**
   - `test_privacy_guard_rejects_patient_pii`: **PASS**

---

## 5. Knowledge Library & FTS5 Citation Truthfulness

### Attributable Search Verification (Remediated DEF-06):
- **Database Index:** SQLite FTS5 virtual table `fts_document_locations` (1,123 literature passages) joined with `documents` (356 records) and `document_locations`.
- **Query Sanitization:** [`search_evidence_library()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/ai_tutor/tutor.py#L228) cleans input queries using regex tokenization (`\b[\w\-]+\b`) and wraps terms in safe prefix strings.
- **Truthful Empty Results:** Punctuation-only queries (`***???`) or non-matching terms return `[]`. The system never fabricates placeholder rows or dummy citation notes.
