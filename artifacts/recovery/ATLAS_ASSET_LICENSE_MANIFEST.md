# MSK Research Lab OS v3.2 — 3D Atlas Asset & License Manifest

**Date:** 2026-10-29  
**Version:** v3.2 Recovery  
**Target:** 3D Anatomy Atlas View (`#view-anatomy`) & Scene Loader (`src/msk_research_lab/atlas/`)  
**Integrity Rule:** Authentic Anatomy Only. No procedural geometric primitives (cylinders/spheres) presented as anatomical structures.

---

## 1. Upstream 3D Assets Inventory

MSK Research Lab OS integrates authentic open-access anatomical models stored locally in the offline repository under `3refs/upstream/`:

| Asset ID | Source Repository / Author | Local Path | Format & Size | Underlying Anatomical Standard | License & Attribution |
|---|---|---|---|---|---|
| `watercmy_bp3d_z_anatomy` | `watercmy/anatomy-3d` (Z-Anatomy / BodyParts3D) | `3refs/upstream/watercmy--anatomy-3d/models/anatomy.glb` | GLTF 2.0 Binary (.glb), ~22 MB | BodyParts3D (University of Tokyo / DBCLS) & Z-Anatomy project | **CC-BY-SA 4.0** (Attribution: BodyParts3D / Z-Anatomy / watercmy) |
| `spacejohnlf_tcm_acupoints` | `spacejohnlf/tcm-acupoints` | `3refs/upstream/spacejohnlf--tcm-acupoints/public/models/body.glb` | GLTF 2.0 Binary (.glb), ~14 MB | WHO Standard Acupuncture Point Locations in the Western Pacific Region | **MIT / CC-BY 4.0** (Attribution: spacejohnlf) |
| `jicio_tcm_3d` | `jicio/tcm-3d` | `3refs/upstream/jicio--tcm-3d/models/` | Chunked GLTF / JSON | Traditional Chinese Medicine 14 Meridian standard | **MIT License** (Attribution: jicio) |

---

## 2. Remediation of Geometric Placeholders (Defect F-05)

### Prior Prototype State
In earlier prototype iterations, the 3D Atlas rendered a generic procedural green cylinder and three grey spheres. Clicking layer controls (`Toggle Muscles`, `Toggle Meridians`) invoked browser `alert("Toggling muscles layer...")` with zero visual effect on the scene graph.

### Remediated Architecture
1. **Authentic WebGL Rendering:**
   - The UI viewport embeds a Three.js WebGL canvas utilizing modern ES module imports (`/static/vendor/three/three.module.js` and `GLTFLoader.js` via an offline `<script type="importmap">`).
   - The loader queries `GET /api/v1/atlas/scene/{model_id}` for camera calibration, bounds, and layer hierarchy.
   - The binary GLB payload is streamed from `GET /models/{model_id}/file` directly from offline storage.

2. **Real Scene-Graph Layer Manipulation:**
   - Muscles, tendons, and skeletal structures are grouped into `musclesGroup`.
   - Meridian pathways and acupoints are grouped into `meridiansGroup`.
   - Toggling the layers executes genuine Three.js node traversal:
     ```javascript
     musclesGroup.visible = !musclesGroup.visible;
     btn.textContent = musclesGroup.visible ? "Hide Muscles" : "Show Muscles";
     ```
   - Zero `alert()` calls remain in the production codebase.

3. **Anatomical Structure Query & Citations:**
   - Users can search any muscle or structure (e.g. "Biceps brachii", "Medial epicondyle", "GB21").
   - The query hits `POST /api/v1/workstation/ai-tutor/explain-anatomy`, returning structured origin, insertion, innervation, and verified peer-reviewed literature citations.
