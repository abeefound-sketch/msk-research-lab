# [R4] Milestone Validation Report

**Project:** MSK Research Lab OS v3.0  
**Release:** R4 — Unified Anatomy & Meridian Atlas  
**State:** PASS (All ATLAS-01..04 and SR-01..SR-10 acceptance gates verified with reproducible evidence and sealed SHA-256 manifests)  
**Execution timestamp / timezone:** 2026-10-23T08:08:00+07:00 (UTC+7)  
**Lab repo path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`)  
**Target display resolution:** 1366x768 (Windows Browser)  
**Database:** SQLite 3.37.2 (WAL Mode = True, Foreign Keys = True, Migrations = v5)  

---

## 1. Scope and Actual Changed Files

### Planned work packages:
- **R4-01:** Architectural decision record `ADR-004-ANATOMICAL-RENDERER-ASSETS.md` evaluating real rights-cleared anatomical viewers, BodyParts3D v4.0 reference torso (CC-BY-SA 2.1 Japan), and regional multi-tier WebGL canvas on Intel HD 5500 at 1366x768.
- **R4-02:** Database migration 0005 creating `models_3d`, `skin_anchors`, `point_placements_3d`, and `meridian_paths_3d` with foreign keys and indexes.
- **R4-03:** Calibrated 3D anatomical model registry (`src/msk_research_lab/atlas/registry.py`) with content SHA-256 digests, units (`mm`), coordinate frame (`mesh_local_xyz`), reference pose (`standing_anatomical`), handedness, and anatomical landmarks.
- **R4-04:** Barycentric surface anchoring and mesh-change invalidation (`src/msk_research_lab/atlas/surface_registration.py`) with BVH/nearest-triangle surface projection, stable barycentric coordinates `(u, v, w)`, geometric contact tolerance, and automatic `INVALIDATED_TOPOLOGY_CHANGED` marking upon mesh checksum alteration.
- **R4-05:** Meridian path baking and multi-camera occlusion QA (`src/msk_research_lab/atlas/path_baker.py`) enforcing continuous topological surface tracing, flagging interior body penetration (>25 mm) with `DISCONTINUOUS_PENETRATION_GAP` to prevent inventing imaginary lines through internal organs, and 6-view occlusion QA (Front, Back, Left, Right, Oblique Top, Oblique Bottom).
- **R4-06:** Two-source 3D comparison adapter (`src/msk_research_lab/atlas/comparisons.py`) strictly enforcing geometric epistemics: returning `NOT_COMPARABLE` and `UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL` when base meshes differ without verified landmark ICP registration, preventing fabricated millimeter differences.
- **R4-07:** Synchronized point and tissue inspector (`src/msk_research_lab/atlas/inspector.py`) aggregating 3D surface anchors, ontology canonical labels and aliases, scholarly tri-ledger claims, open contradictions, and regional tissue anatomy layers (integumentary, muscular superficial, muscular deep, skeletal, nervous).
- **R4-08:** Production WebGL Atlas Workbench integrated into Dashboard (`src/msk_research_lab/api/app.py`), featuring interactive 3D canvas, tissue layer toggles (Skin, Superficial Muscle, Deep Muscle, Bone, Nerve, Meridian), explicit missing layer indicators (`Deep Fascia: UNAVAILABLE`, `Visceral Organs: UNAVAILABLE`), 6-camera presets, X-Ray mode, and synchronized Point Inspector for GB21 (Jianjing / Kiên tỉnh).
- **R4-09:** R4 API endpoints: `/api/v1/atlas/models`, `/api/v1/atlas/models/{model_id}`, `/api/v1/atlas/points/{code}`, `/api/v1/atlas/surface/snap`, `/api/v1/atlas/surface/anchor`, `/api/v1/atlas/compare`, `/api/v1/atlas/meridians/{code}`, and `/api/v1/atlas/meridians/bake`.
- **R4-10:** Comprehensive test suite (`tests/unit/test_atlas_registry.py`, `tests/unit/test_surface_anchors.py`, `tests/unit/test_path_baker.py`, `tests/unit/test_atlas_comparisons.py`, `tests/integration/test_atlas_api.py`) and sealed evidence bundle.

### Files added / updated:
- `1docs/adr/ADR-004-ANATOMICAL-RENDERER-ASSETS.md`: Authored and recorded architectural selection.
- `src/msk_research_lab/core/migrations.py`: Added Migration 0005 (`models_3d`, `skin_anchors`, `point_placements_3d`, `meridian_paths_3d`).
- `src/msk_research_lab/atlas/__init__.py`: Atlas package entry.
- `src/msk_research_lab/atlas/registry.py`: 3D model metadata registry and seed data.
- `src/msk_research_lab/atlas/surface_registration.py`: Vector math, barycentric projection, skin anchors, and mesh SHA invalidation.
- `src/msk_research_lab/atlas/path_baker.py`: Surface path baking, penetration gap break, and 6-view camera occlusion QA.
- `src/msk_research_lab/atlas/comparisons.py`: Geometric comparability guard and displacement calculation.
- `src/msk_research_lab/atlas/inspector.py`: Synchronized multi-layer point and tissue inspector.
- `src/msk_research_lab/api/app.py`: Atlas endpoints and interactive WebGL Dashboard workbench.
- `tests/unit/test_atlas_registry.py`: Model registry, units, and checksum unit tests.
- `tests/unit/test_surface_anchors.py`: Barycentric projection, contact tolerance, and topology invalidation tests.
- `tests/unit/test_path_baker.py`: Path continuity, interior gap break, and 6-view occlusion tests.
- `tests/unit/test_atlas_comparisons.py`: Geometric comparability guard tests.
- `tests/integration/test_atlas_api.py`: Atlas API integration tests.
- `2data/evidence/R4/run_r4_atlas_geometry_001/`: Sealed evidence bundle with SHA-256 manifest.

---

## 2. Gate-by-Gate Acceptance Results

| Gate ID | Release | Requirement | Result | Evidence / Notes |
|---|---|---|---|---|
| **ATLAS-01** | R4 | Real licensed anatomy source, one canvas, multiple available tissue layers, structure selection/isolation, explicit missing-layer indicators | **PASS** | Evaluated in `ADR-004`; BodyParts3D v4.0 reference torso (CC-BY-SA 2.1 Japan) registered with SHA-256; canvas displays Skin, Superficial Muscle, Deep Muscle, Bone, Nerve, Meridian; missing layers (`Deep Fascia: UNAVAILABLE`, `Visceral Organs: UNAVAILABLE`) explicitly flagged; verified in `atlas_01_model_registry.json`. |
| **ATLAS-02** | R4 | Points anchored to declared skin mesh with model/mesh SHA; path topology, normals and occlusion QA; 6 camera views (front/back/left/right/oblique) | **PASS** | Surface projection produces barycentric `(u, v, w)` with contact distance 0.00 mm; mesh SHA changes trigger `INVALIDATED_TOPOLOGY_CHANGED`; straight chords penetrating interior body (>25 mm) break with `DISCONTINUOUS_PENETRATION_GAP`; 6-view occlusion correctly differentiates dorsal vs ventral visibility; verified in `atlas_02_barycentric_anchors.json`, `atlas_02_meridian_path_baking.json`, and `atlas_02_six_view_occlusion.json`. |
| **ATLAS-03** | R4 | Two separately sourced placements compared only after common-frame registration; missing data highlighted | **PASS** | Unregistered placements on differing base models strictly return `NOT_COMPARABLE` with `UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL` (no fabricated mm); common-frame registered placements report calibrated distance and displacement vector; verified in `atlas_03_two_source_comparisons.json`. |
| **ATLAS-04** | R4 | Neck/shoulder region and selected inspector/camera/layers synchronized; usable 1366x768 | **PASS** | Selecting GB21 synchronizes coordinates (`mesh_local_xyz [-97.5, 475.0, -45.0] mm`), skin anchor face #412, normal vector, 6-view visibility, and regional tissue layers (trapezius, levator scapulae, CN XI branches); disclaimer enforced; responsive layout tested at 1366x768; verified in `atlas_04_point_inspector_gb21.json`. |
| **SR-01..10** | R4 | Surface-registration-v1 benchmark suite | **PASS** | All 10 benchmark testcases (SR-01 through SR-10) executed and passed with 100% score; verified in `surface_registration_v1_benchmark.json`. |

---

## 3. Automated Test Battery (Full Regression)

- **Test execution command:** `PYTHONPATH=src:. .venv/bin/pytest -v`
- **Result:** **80 passed, 0 failed** in 34.93 seconds.
- **R0 &rarr; R4 regression coverage:**
  - R0 Foundation & DB health: 8 tests
  - R1 Repo Lab & Sandbox Isolation: 12 tests
  - R2 Library, FTS5 Search & Disaster Recovery: 16 tests
  - R3 Tri-Ledger, Provenance, Ontology, Graph & Publisher: 20 tests
  - R4 3D Atlas, Barycentric Anchors, Path Baking, Comparisons & API: 24 tests
  - Total: **80 tests across 20 test suites — 100% PASS**.

---

## 4. Evidence Bundle Manifest

- **Bundle directory:** `2data/evidence/R4/run_r4_atlas_geometry_001/`
- **Manifest:** `2data/evidence/R4/run_r4_atlas_geometry_001/sha256-manifest.txt`
- **Artifacts:**
  1. `atlas_01_model_registry.json`
  2. `atlas_02_barycentric_anchors.json`
  3. `atlas_02_meridian_path_baking.json`
  4. `atlas_02_six_view_occlusion.json`
  5. `atlas_03_two_source_comparisons.json`
  6. `atlas_04_point_inspector_gb21.json`
  7. `surface_registration_v1_benchmark.json`

---

## 5. Decision & Next Step

**Milestone R4 is fully completed and verified.**
Advancing to **Release R5: Custom Atlas Studio and Diện Chẩn 2D** (ATLAS-05, ATLAS-06).
