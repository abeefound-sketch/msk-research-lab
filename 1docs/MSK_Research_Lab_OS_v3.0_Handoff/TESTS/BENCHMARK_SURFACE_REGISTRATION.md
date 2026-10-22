# `surface-registration-v1` — Comparable Geometry Research Benchmark

## Purpose

Test geometry consistency of surface point/path projection across source algorithms, not correctness of acupoint medical location. Target the four candidate methods: JICio/tcm-3d, Meridian Studio, WaterCMY/anatomy-3d and spacejohnlf/tcm-acupoints; Open Anatomy Atlas is a possible reference model. A source that cannot accept the same fixture gets `UNSUPPORTED` or `ADAPTED` (with disclosed transform), not a false low score or bogus PASS.

## Fixture and manifest

`mesh_reference.glb` or `.obj`, `mesh_sha256`, code/model license; exact units, axes, handedness, triangles and exterior skin identity; known anatomical-like synthetic landmarks, camera poses, bounding box and height. `points_reference.json`: named synthetic point IDs, left/right, source placement, expected projection region and true reference geometry. `scenarios.yaml`: versioned tolerance expressed relative to calibrated units/error budget, negative cases; `hardware.json`: real device, WSL/browser/WebGL features; full source Git SHAs.

## Tests

| ID | Test and instrumentation | Expected behavior |
|---|---|---|
| SR-01 | Import fixtures and transform from source to target frame | Units/axes/scale and matrix logged; reject silent mirror or rescale |
| SR-02 | Snap/project synthetic test points to declared external skin | Distance, candidate ambiguity and calibration reported |
| SR-03 | Barycentric anchor persistence after valid camera/view transform | Face index+barycentric stable for same mesh SHA; topology change invalidates |
| SR-04 | Constrain line samples to same skin topology | No silently connected path across disjoint islands or body interior |
| SR-05 | Laterality/mirroring | Intentional left/right reversal flagged |
| SR-06 | Region selection | Neck selection hides unrelated overlay; structure inspector consistent |
| SR-07 | Occlusion/viewports | Real screenshots from front/back/left/right/two obliques; no unexplained floating overlay |
| SR-08 | Negative inputs | NaN, invalid units, rotated/mirrored frame, wrong mesh, bounds/normal error safely rejected |
| SR-09 | Resource and performance | Backend/sandbox/browser memory and time-to-render measured; GPU caveats recorded |
| SR-10 | Determinism | Three clean input-matched runs; variation and instrumentation declared |

## Scoring / comparison

Each repo per case: `SUPPORTED`, `ADAPTED`, `UNSUPPORTED`; actual `PASS`, `FAIL`, `BLOCKED`, `INCONCLUSIVE`; source SHA; fixture SHA; transform/effective thresholds; raw measurements and sample count; screenshot inspection; provenance. Compute RMS/median/p95/max **only for valid comparable quantities**; preserve distributions and missing denominator. If source meshes/poses/units differ without a validated registration, state `UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL`. Never average contested placements into purported authoritative clinical centroids.

## Evidence review

Separate deterministic geometric checks, real browser QA and future qualified domain review. Geometric contact/scene occlusion can PASS while medical localization remains `NOT_ASSESSED`. The benchmark suite, code, fixtures and scoring logic must have their own versioned hashes and execution logs; immutable evidence tampering invalidates downstream decisions.
