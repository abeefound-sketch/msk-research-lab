# Unified Atlas: Anatomical Rendering, Coordinates and Editor Contracts

## Viewer acceptance, not a demo iframe

One Lab-owned production renderer and canvas; upstream standalone apps are research specimens, not embedded permanent UI. First investigate Open Anatomy Atlas as source for true layered anatomy, structure tree, clipping, region filtering, visibility and FMA linking. Only integrate/port code after pinned revision and code/asset/data rights audit. Support only layers actually present in the approved model (skin, bone, muscles including deep when available, cartilage/joint, fascia, nerve, vessel). Missing tissue = explicitly unavailable, never generated from labels.

Minimum viewer controls: orbit/pan/zoom/reset; selectable front/back/left/right and oblique camera presets; region and system picker; hide/show, opacity, X-ray, isolate, focus, clipping when source supports it; structure inspector synchronized with selection; points/paths visible only for selected region/tradition by default. 1366x768 Windows display without clipped controls; keyboard accessibility on major operations. Occluded points hidden by default; opt-in X-ray labeled clearly. A selected neck region must never leave a thigh structure inspector.

## Separate concept, source placement, mesh anchor

```text
Tradition namespace + canonical point concept [GB21 / own-school-ID]
  -> reviewed crosswalk to each source-specific point identifier
    -> source-specific placement at source model / pose / original units
      -> transform/landmark registration to *target* model
        -> exterior skin mesh candidate + ambiguity assessment
          -> mesh-hash-specific triangle + barycentric weights + normal
            -> on-skin display geometry only, clinical validation UNASSESSED
```

Do not share barycentric face indices across unrelated topology. A source showing points on a smooth enclosing hull is not equivalent to a verified point on a detailed body skin mesh. Registered coordinates are not inherently clinically correct.

## Canonical coordinate requirements

- Always retain **source** frame and units; choose versioned target model-local frame and documented transform.
- Declare world and mesh local matrices, units in meters/mm or source-specific scale, handedness, axes (+X/+Y/+Z interpretations), origin and reference pose.
- Preserve side semantics and mirror behavior, known body landmarks, mesh topology/version and source author/date.
- Apply transform only after units/landmarks/pose validation. Fail `UNREGISTERED` on missing landmarks or unknown scale; never quietly guess frame from coordinate magnitudes.
- For explicitly registered same-frame compatible points, report measured distance in calibrated units and transform error/landmark residual; otherwise report `NOT_COMPARABLE` instead of a fake mm number.
- Anchors persist as `(model_sha, skin_mesh_sha, face_index, barycentric_weights, original_source, algorithm_version)` plus recorded local normal/position and QA metrics; invalidated on mesh/LOD topology change.
- Raycast/nearest surface may use pinned `three-mesh-bvh` and region masks. Record ray origin/direction, candidate distances, normals, backface decisions, side and anatomical region constraints.
- Path bakes sample constrained exterior skin. A disconnected region, sudden topology jump, poorly registered crossing or candidate ambiguity must yield a **visible break/warning**, not a line through the body.

## Engineering metrics and testcases

Canonical fixture `surface-registration-v1` records model SHA and license, mesh units/pose/topology, camera presets and actual hardware; tests SR-01 through SR-10 as defined in `ACCEPTANCE_MATRIX.md` and `TESTS/BENCHMARK_SURFACE_REGISTRATION.md`.

Report point success rate, signed/unsigned surface distance, median/p95/max projection displacement when units calibrated, displacements from original source, laterality and region failures, path continuity failures, occlusion/depth failures, selection sync anomalies, FPS percentile if measurable, time-to-first-render and peak backend/WSL/browser memory. **Geometry tolerance must be fixture/config-defined**, not a universal 2 mm or 5 mm clinical threshold. If a specific engineering fixture adopts a 5 mm surface-contact tolerance, label it `GEOMETRIC_CONTACT_ONLY`, justify scale/mesh error and never present it as acupoint location accuracy. Numerical score comparisons require compatible inputs and normalization manifest; unsupported testcases are distinct from PASS.

## Source-to-capability evaluation matrix

| Source | Candidate behavior to inspect, not assumed correct | Must review before reuse |
|---|---|---|
| `CognitionLabSNUC/open-anatomy-atlas` | Anatomy layers, labels, clip/cut, reference model support | Actual runtime, 8 GiB performance, code MIT vs separate model rights |
| `JICio/tcm-3d` | Baked surface triangle anchors and path projection | Point precision admissions, body mesh hashes, source data licenses |
| `eb-barry/acupuncture-3d-authoring` | Surface editor, drag/undo/redo and JSON transfer | Root code license **not established** in baseline; male/female GLB separate rights |
| `WaterCMY/anatomy-3d` | Lightweight deep-muscle display and path heuristics | Hull ≠ external skin, possible share-alike asset obligations |
| `spacejohnlf/tcm-acupoints` | Direction-constrained point snap; normal behavior | Source GLB ancestry and right to use assets |
| `SciCrunch/TARA-Ontology-Repository` | Point identity and relationship terms | Curated data/ontology rights not established by root LICENSE alone |
| `galaxy-hzy/meridian-atlas` | Classical descriptions, historical labels and source references | AGPL-3.0 code; attribution/rights of underlying texts |

## Research Atlas Studio

Private versioned point/curve/map editor with edit modes, local undo/redo and persisted revisions. User may create nonstandard educational atlas namespaces (Diện Chẩn, Thai Sen, trigger-point research, user-generated maps) while keeping source types distinct from each other and from FMA anatomy. For frontal/profile facial diagrams, preserve **source image SHA and pixel anchors**; manual chart-to-3D experiments require distinct unreviewed annotation plus landmark registration, never automatic truth claims. `reactive_observation` has contextual synthetic session ID and timestamp; cannot be published as general fixed-point geometry. Export JSON includes schema version, rights, sources, base model/image hashes, authorship and validation state.

## Resource strategy

Single WebGL renderer, region-first lazy model loading, material/LOD throttling, cached pre-baked meshes, bounded label count, lower pixel ratio when device measurements justify, worker-based offline BVH computation under time/memory limits. Monitor peak browser working set and WSL aggregate as possible; JS heap is not whole-machine memory. If an asset exceeds budget, provide lower-detail approved alternative or report `BLOCKED`.
