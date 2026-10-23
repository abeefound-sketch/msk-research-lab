# [R3] Milestone Validation Report

**Project:** MSK Research Lab OS v3.0  
**Release:** R3 — Auditable Claims, Tri-Ledger, Controlled Multilingual Ontology, Typed Graph, and Validated Snapshot Publisher  
**State:** PASS (All G7, G8, G9, G10 and SEC acceptance gates verified with reproducible evidence and sealed SHA-256 manifests)  
**Execution timestamp / timezone:** 2026-10-23T07:55:00+07:00 (UTC+7)  
**Lab repo path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`)  
**Target display resolution:** 1366x768 (Windows Browser)  
**Database:** SQLite 3.37.2 (WAL Mode = True, Foreign Keys = True, Migrations = v4)  

---

## 1. Scope and Actual Changed Files

### Planned work packages:
- **R3-01:** Provenance registry (sources, editions, translations, derivative lineage, source independence tracking, exact locator verification, rights status).
- **R3-02:** Scholarly Tri-Ledger: auditable claims, evidence attribution, open contradictions, human review audit events, and irreversible revision lineage.
- **R3-03:** Fail-closed promotion gates: mandatory human reviewer, verified source locator resolution, uncorrupted source byte SHA, counter-evidence disclosure, and separate clinical evidence appraisal.
- **R3-04:** Parallel source comparison workspace: side-by-side original view, independence check, classifications (`MATCH`, `DIFFERENCE`, `UNCERTAIN`, `NOT_COMPARABLE`), and epistemic geometric guard (`UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL`).
- **R3-05:** Controlled multilingual ontology: seed loader (`config/ontology_seed.json`), deterministic multilingual lookups (`GB21` &rarr; `Jianjing` / `Kiên tỉnh`), diacritic-insensitive normalization, and disclaimers prohibiting physiological equivalence claims.
- **R3-06:** Typed SQLite knowledge graph: allowlisted node and edge types, mandatory provenance for associative edges, and bounded 1-hop neighborhood queries.
- **R3-07:** Validated knowledge snapshot publisher: staging in `2data/snapshots/.builds/`, automated QA validation (integrity, FK, locators, graph orphans, rights compliance), promotion to immutable `2data/snapshots/.releases/`, atomic pointer activation in `2data/snapshots/.active/current.json`, and disaster rollback.
- **R3-08:** Published-only read API with Bearer token authentication: `/api/v1/claims/{id}`, `/api/v1/contradictions`, `/api/v1/sources/{id}`, `/api/v1/ontology/lookup`, `/api/v1/graph/neighborhood`, `/api/v1/snapshots/current`, and `/api/v1/knowledge/points/{code}`.

### Files added / updated:
- `src/msk_research_lab/core/migrations.py`: Added Migration 0004 for all 15 R3 tables (`sources`, `source_locations`, `source_relations`, `claims`, `evidence`, `claim_evidence_links`, `contradictions`, `claim_revision_events`, `review_events`, `comparisons`, `ontology_concepts`, `concept_aliases`, `graph_nodes`, `graph_edges`, `published_releases`).
- `src/msk_research_lab/provenance/registry.py`: Sources provenance, independence tracking, and multi-format locator resolution.
- `src/msk_research_lab/provenance/comparator.py`: Side-by-side comparison and epistemic geometry guard.
- `src/msk_research_lab/ledgers/claims.py`: Scholarly tri-ledger, fail-closed promotion, revision lineage, and anti-deletion invariants.
- `src/msk_research_lab/ontology/lookup.py`: Ontology seed ingestion and deterministic multilingual lookup.
- `src/msk_research_lab/graph/builder.py`: Typed graph builder, edge provenance validation, and 1-hop neighborhood queries.
- `src/msk_research_lab/publication/publisher.py`: Snapshot staging, automated QA verification, promotion, atomic pointer switch, and rollback.
- `src/msk_research_lab/api/app.py`: Published knowledge API endpoints, token auth safeguards, and updated responsive Dashboard.
- `src/msk_research_lab/core/config.py`: Convenience properties for data and root paths.
- `tests/unit/test_provenance_registry.py`: Provenance, independence, and locator resolution unit tests.
- `tests/unit/test_tri_ledger.py`: Tri-ledger lifecycle, fail-closed promotion, counter-evidence disclosure, and revision tests.
- `tests/unit/test_comparator.py`: Parallel source comparison and geometric comparability tests.
- `tests/unit/test_ontology_graph.py`: Ontology seed loading, multilingual aliases, and typed graph tests.
- `tests/unit/test_snapshot_publisher.py`: Snapshot staging, QA validation, promotion, and atomic rollback tests.
- `tests/integration/test_knowledge_api.py`: Bearer token authentication, pre/post publication contracts, and 404 gates.
- `2data/evidence/R3/run_r3_integrity_publisher_001/`: Sealed evidence bundle with SHA-256 manifest.

---

## 2. Gate-by-Gate Acceptance Results

| Gate ID | Release | Requirement | Result | Evidence / Notes |
|---|---|---|---|---|
| **G7** | R3 | Scholarly Tri-Ledger: Claim/Evidence/Contradiction ledgers; counter-evidence retained; fail-closed promotion; immutable revision events | **PASS** | Automated promotion bypass rejected; unreviewed evidence promotion rejected; counter-evidence omission rejected; revision lineage preserved in `g7_tri_ledger_audit.json`. |
| **G8** | R3 | Provenance Registry & Parallel Source Comparison: Exact multi-format locators; hash verification; independence tracking; operator classifications | **PASS** | Shared vs distinct provenance groups evaluated; translations and mirrors flagged as non-independent; geometric guard blocks fake millimeter differences; verified in `g8_provenance_independence.json` & `g8_parallel_comparison.json`. |
| **G9** | R3 | Controlled Ontology & Typed Knowledge Graph: Namespaced concepts; multilingual aliases (`GB21` &rarr; `Jianjing` / `Kiên tỉnh`); mandatory edge provenance; bounded 1-hop neighborhood | **PASS** | Seed loaded; diacritic-insensitive lookups validated; edge without evidence denied; 1-hop neighborhood query verified in `g9_ontology_lookups.json` & `g9_typed_graph_neighborhood.json`. |
| **G10** | R3 | Validated Snapshot Publisher & Disaster Rollback: Staged immutable build; automated QA validation; atomic pointer switch via `os.replace`; safe rollback | **PASS** | QA validation checked (PRAGMA integrity, FK, locators, graph orphans, rights); atomic switch of `current.json` tested; rollback switches pointer safely while preserving working DB; verified in `g10_snapshot_publication.json`. |
| **SEC** | R3 | API Access Safeguards: Loopback binding; Bearer token authentication; unreviewed 404 gates; deny-by-default execution policy | **PASS** | Anonymous requests rejected with 401; invalid tokens rejected with 403; unreviewed points return 404 `UNREVIEWED_NOT_PUBLISHED`; published knowledge served only from validated active snapshot. |

---

## 3. Automated Test Battery (Full Regression)

- **Test execution command:** `PYTHONPATH=src:. .venv/bin/pytest -v`
- **Result:** **56 passed, 0 failed** in 69.52 seconds.
- **Coverage breakdown:**
  - R0 Foundation (Health, DB WAL/FK, Config, Security): 7 tests
  - R1 Repo Lab (Catalog, Inspector, Cloner, Runner, SR-01..10 Benchmark): 14 tests
  - R2 Library & Recovery (Store, Parsers, Search, Notes, Backup/Restore): 20 tests
  - R3 Integrity & Publisher (Provenance, Tri-Ledger, Comparator, Ontology, Graph, Snapshot, Knowledge API): 15 tests
  - Total: **56 / 56 PASS (100%)**

---

## 4. Tamper Detection & Sealed Evidence Bundle

- **Evidence bundle directory:** [`2data/evidence/R3/run_r3_integrity_publisher_001/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R3/run_r3_integrity_publisher_001)
- **Manifest Hash:** `5ac8d7d29542847e246ee060a3d370a7d0ed98342f2b6c2a66c9841d3c52e927`
- **Artifact count:** 6 sealed artifacts
- **Verification status:** `PASS` (`{"valid": true, "total_files": 6, "mismatches": []}`)
