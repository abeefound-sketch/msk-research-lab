# P16 Defect Register & Resolution Log
**MSK Research Lab OS — Milestone P16**  
**Role:** Independent Release QA, Software Reliability Auditor  
**Date:** 2026-10-31  

---

## 1. Defect Summary Table

| Defect ID | Severity | Category | Description | Root Cause | Status |
|---|---|---|---|---|---|
| **DEF-16** | Medium | Visual Evidence | Consecutive full-viewport screenshots without scroll or state changes produced duplicate SHA-256 hashes for Steps 3/4, 7/8, 9/10, 11/12. | Full-page captures captured unchanged viewport areas instead of isolating the specific UI element under test. | **RESOLVED** (Implemented element-isolated locator screenshots for structure inspector, muscle metrics, caution badge, motor control cards, and scene narrative; 11/11 unique SHA-256 digests verified). |
| **DEF-17** | Medium | Scientific Terminology | Three.js action lines labeled as full OpenSim muscle paths; fiber length was not clearly differentiated from musculotendon length. | Three.js rendered straight-line connectors between origin and insertion rather than geodesic wrapping cylinders. | **RESOLVED** (Updated `path_classification` to `SIMPLIFIED_ORIGIN_INSERTION_CONNECTOR`, added `musculotendon_length_m` field and UI readout, calibrated Scene 6 / Motor Control educational narratives to eliminate dogmatic causal assertions). |
| **DEF-18** | Medium | Biomechanics Semantics | Scapulohumeral rhythm ratio labeled ambiguously as "2:1" without distinguishing incremental ratio above 30° from cumulative ratio. | Biomechanics literature frequently refers to the incremental ratio as "2:1", whereas cumulative ratio varies from $\infty$ down to 2.6:1. | **RESOLVED** (Added `incremental_rhythm_ratio` and `cumulative_rhythm_ratio` fields to `ShoulderKinematicsFrame` and dedicated UI readouts). |
| **DEF-19** | High | Test Accounting | Both P14 and P16 reported 316 tests despite 9 unit tests and 1 E2E test being added in P15 without deletions. | P14 JSON report artificially added `"windows_native_e2e_journeys": 10` on top of 125 integration tests that already contained those journeys. | **RESOLVED** (Conducted node-by-node extraction proving 306 true unique tests at P14, 316 true unique tests at P16; documented in `P16_FULL_TEST_ACCOUNTING.md`). |
| **DEF-20** | Low | E2E Harness | Step 13 post-reload screenshot captured 0° resting frame before 45° scrub completed, colliding with Step 3 hash. | Asynchronous WebGL loading post-reload required an explicit wait and kinematics update. | **RESOLVED** (Updated `test_p15_guided_learning_e2e.py` with explicit post-reload kinematics invocation and 1s wait; 11/11 distinct hashes verified). |

---

## 2. Verification Summary

All 5 defects identified during P16 adversarial verification have been fully resolved with source code updates, automated tests, and cryptographic verification. Zero open defects remain.
