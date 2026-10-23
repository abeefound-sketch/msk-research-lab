# Next Coding Session Handoff — R3 &rarr; R4

**From session/release:** R3 — Auditable Claims, Tri-Ledger, Controlled Multilingual Ontology, Typed Graph, and Knowledge Publisher  
**To proposed session/release:** R4 — Unified Anatomy & Meridian Atlas (ATLAS-01..04)  
**Current State:** R0 PASS, R1 PASS (with G2 bare-metal execution safely BLOCKED under Option B), R2 PASS, R3 PASS (Gates G1–G10 and SEC verified with real sealed evidence)  
**Lab repository path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`)  
**Lab Git branch:** `main`  
**Read first:** `1docs/MSK_Research_Lab_OS_MASTER_SPEC_v3.0.md`, `1docs/MSK_Research_Lab_OS_ROADMAP_R0_R6.md`, `2data/evidence/R3_report.md`.

---

## 1. Completed Actual Features with Runnable Reproduction

1. **Source Provenance & Independence Registry (G8 / R3-01):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest tests/unit/test_provenance_registry.py`
   - Tracks editions, translations, derivatives, and evaluates true independence (shared groups and declared mirrors/forks flagged as non-independent).
   - Resolves exact multi-format locators with disk hash verification.
2. **Scholarly Tri-Ledger & Fail-Closed Promotion (G7 / R3-02, R3-03):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest tests/unit/test_tri_ledger.py`
   - Auditable claims, evidence records, counter-evidence retention, and open contradictions.
   - Fail-closed promotion: AI/automated self-promotion blocked; unreviewed evidence blocked; hash-mismatch blocked; counter-evidence omission blocked.
   - Irreversible revision lineage (`supersedes_claim_id`, `claim_revision_events`); hard deletion forbidden.
3. **Parallel Source Comparator & Epistemic Geometry Guard (G8 / R3-04):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest tests/unit/test_comparator.py`
   - Side-by-side comparison with operator classifications (`MATCH`, `DIFFERENCE`, `UNCERTAIN`, `NOT_COMPARABLE`).
   - Epistemic guard: Unregistered 3D frames output `UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL` and forbid fake millimeter subtraction.
4. **Controlled Multilingual Ontology & Typed Knowledge Graph (G9 / R3-05, R3-06):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest tests/unit/test_ontology_graph.py`
   - Ingests `config/ontology_seed.json`; deterministic term lookups (`GB21` &rarr; `Jianjing` / `Kiên tỉnh`).
   - Disclaimers attached to all lookups; term aliases never imply physiological channels.
   - Typed SQLite graph with mandatory edge provenance and bounded 1-hop neighborhood queries.
5. **Validated Snapshot Publisher & Disaster Rollback (G10 / R3-07):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest tests/unit/test_snapshot_publisher.py`
   - Staged builds in `2data/snapshots/.builds/<build-id>/`; automated QA gates (PRAGMA integrity, FK, locators, graph orphans, rights).
   - Atomic pointer switch via `os.replace` on same filesystem into `2data/snapshots/.active/current.json`.
   - Atomic rollback to prior validated releases without altering working DB.
6. **Published Read-Only API & Interoperability (G10, SEC / R3-08):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest tests/integration/test_knowledge_api.py`
   - Bearer token authentication enforced (401/403).
   - Published endpoints query active snapshot exclusively; unreviewed points return 404 `UNREVIEWED_NOT_PUBLISHED`.
7. **Full Regression Battery (56 Tests):**
   - Command: `PYTHONPATH=src:. .venv/bin/pytest -v`
   - Result: **56 passed, 0 failed** in 69.52 seconds.

---

## 2. Next Authorized Bounded Task (R4)

**Goal:** Build the Unified 3D Anatomy & Meridian Atlas with BVH surface projections, baked meridian topology, registered landmark comparative adapters, and point inspection (Gates ATLAS-01..04).

**Work packages (R4-01 &rarr; R4-08):**
1. **R4-01:** Renderer + asset ADR comparing Open Anatomy Atlas and alternatives for deep tissues, rights, FPS/RSS, 1366x768.
2. **R4-02:** Single canvas anatomy layers, region tree, isolate/focus, X-ray, synced camera/inspector.
3. **R4-03:** 3D Model registry: hash, pose, units, transforms, handedness, landmarks, skin mesh, source/rights.
4. **R4-04:** BVH/nearest-triangle + constrained raycast surface anchors, barycentric persistence and mesh-change invalidation (SR-01..03).
5. **R4-05:** Meridian path baking with topology/region checks, gaps/warnings, occlusion correctness, multi-camera reviews (SR-04..08).
6. **R4-06:** Comparison adapters for at least two meaningful source placements; `NOT_COMPARABLE` where frame registration absent (SR-09..10).
7. **R4-07:** Point inspector linking claims/ontology/book provenance, uncertainty and alternate placements without blending conflicts.
8. **R4-08:** Target-device performance optimization (LOD, progressive region loading, baked caches).
