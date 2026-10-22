# MSK Research Lab OS — v2.1 Engineering Specification

**Document status:** IMPLEMENTATION-READY DESIGN CONTRACT — **NOT IMPLEMENTED / NOT VERIFIED**  
**Version:** 2.1.0  
**Prepared:** 2026-10-22  
**System:** MSK Research Lab OS (a standalone research workbench, **not** a new operating system)  
**Primary target:** Windows 10 + Ubuntu WSL2; Intel i7-5600U, 8 GB RAM, Intel HD Graphics 5500, ~238 GB SSD  
**Intended operator:** One local research user, using a Windows browser; no real patient information  
**Related application:** MSK-Therapy-OS, a separate consumer of *reviewed, source-linked* research via an authenticated read-only API

> **Governing rule:** A feature is complete only when its real end-to-end user journey works on the target machine, its source and audit trail are reproducible, and its negative/failure paths have been demonstrated. A green unit test or a generated screenshot is not sufficient.

---

## 0. Source basis, change policy, and limits of verification

### 0.1 Documents reviewed for this specification

1. `MSK_Research_Lab_OS_MVP_v2_SPEC(1).md` (2026-10-21), SHA-256: `cd7cfdbfdb05148aea81da2eacfdb02b3324be0debf099f85802b46ca7f3bfef`.
2. `firstbrain-main.zip` (uploaded snapshot, dated 2026-09-27 within the archive), SHA-256: `b4479d08ed92bdfe8af5723c75e7d03aba2a7d82567298ee4ff9265b2da04964`.
3. Inside the FirstBrain archive, relevant inspected materials include:
   - `README.md` and `SPECIFICATION.md`: parallel source/translation, exact locators, provenance, and contribution verification.
   - `tools/scholarly_ledger.py` and `tools/test_scholarly_ledger.py`: claim, evidence, contradiction ledgers; claim revision linkage; export to graph/Parquet.
   - `tools/local_corpus_framework/corpus/ontology.py` and `ontology.json`: deterministic multilingual concept/term mapping.
   - `tools/local_corpus_framework/README.md`, `publish_mvp.py`, and `corpus/publication.py`: staging, index publication, validation and rollback practices.
   - `tools/local_corpus_ui/README.md`: offline local search workflow.

**Source-derived lessons:** Separate claims from evidence and contradiction; retain exact provenance and locators; preserve distinct originals/translations; expose unresolved source gaps; normalize ontology terms deterministically; publish validated immutable snapshots instead of mutating a live search index in place.

**MSK-specific design extensions (not claimed to exist in FirstBrain):** Clinical-evidence taxonomy, separate anatomical and traditional namespaces, geometrical-source comparison, healthcare-related safety vocabulary, API payloads, and the acceptance tests specified below. These are requirements for the new Lab, **not** verified upstream capabilities.

**Verification boundary:** This document inspects an uploaded ZIP snapshot and the supplied v2 spec. It does not claim that FirstBrain's external databases, unpublished documents, deployment environments, or every test run were independently executed. FirstBrain is an architectural reference, not a required runtime dependency, import source for Buddhist texts, or license clearance.

### 0.2 Relationship to MVP v2

This v2.1 specification is an **additive amendment** to MVP v2.0.0:

- Retain all original journeys **G1–G6**, test fixtures, thresholds and the SEC security gate unchanged.
- Add **G7: Tri-Ledger**, **G8: Provenance + Parallel Source Comparison**, **G9: Ontology + Knowledge Graph**, and **G10: Atomic Research Snapshot Publication / Rollback**.
- Preserve *standalone deployability*: Research Lab and Therapy OS remain separately runnable. They **may** be placed under a parent monorepo later, but a monorepo migration is **not** a prerequisite or a reason to change the Lab's data ownership.
- Do **not** replace the v2 spec with weaker criteria. If supporting files are missing or conflict, log **BLOCKED** and reconcile them before implementing the corresponding gate.
- v2.1 can be built in phases. **v2.1 release is not PASS until G1–G10 + SEC are all PASS.** A partial build may be reported as `v2.1-IN-PROGRESS`; do not relabel it complete.

### 0.3 Non-goals (still excluded)

Real patient records, identifiers or photographs; diagnosis and treatment recommendation; validated acupoint placement; dosage/needling/DDS settings; medical-device claims; 3D biomechanical simulation; live motion capture; public social features; automatic web scraping of copyrighted books; cloud LLMs; medical RAG; mandatory embeddings/vector databases; mandatory Parquet/Hugging Face; mandatory new agent frameworks; and mandatory execution of every candidate GitHub repository.

---

## 1. Product objective and operator journeys

**Vision:** Turn heterogeneous open-source anatomy/TCM/massage repositories and local technical/academic documents into a **traceable, comparable and safely reusable research memory**. The operator must be able to ask *what does a source say, where does it say it, who disagrees, and how certain is the conclusion?*

| ID | Journey | Acceptance outcome |
|---|---|---|
| G1 | Open Lab from Windows; health-check WSL environment | Real browser, responsive 1366x768, restartable service |
| G2 | Discover, inspect, explicitly approve, clone, launch and stop 3 different upstream apps | Real interactions, SHA-pinned versions, bounded logs, no zombie processes |
| G3 | Import 4 PDFs (2 scanned/image-bearing), 3 EPUBs, 3 DOCXs | Immutable originals, complete location accounting, visible OCR/figure gaps |
| G4 | Search and open source at exact PDF page, EPUB chapter, DOCX structural location | Resolvable locators, real source viewer, no fabricated citations |
| G5 | Create evidence-linked note/experiment; export; call read-only authenticated API | Cited content with correct repo commits and source locations |
| G6 | Back up and restore into a fresh data directory | Hashes, notes, locators, searches, and permissions survive |
| **G7** | Create a claim; attach supporting and counter-evidence; revise; review a disagreement | Auditable Claim, Evidence and Contradiction ledgers with fail-closed transitions |
| **G8** | Compare two independently identifiable sources/editions side-by-side | Exact locators, translation/edition identity, rights, source independence, uncertainty |
| **G9** | Search one term across approved aliases, inspect graph neighbors | Deterministic ontology and provenance-bearing typed graph; no inferred anatomy equivalence |
| **G10** | Stage a revised knowledge index, validate, publish and roll back | Atomic pointer switch; old readers safe; failed staging never corrupts active release |

**Priority:** Reproduce v2 G1–G6 before adding complex v2.1 UI. First implement the **ledger + provenance** core, then graph, then publication. All are useful without AI or 3D hardware acceleration.

---

## 2. Architecture

### 2.1 Deployment boundaries

```text
Windows browser
      |
      | localhost:8091
      v
MSK Research Lab OS (WSL2, standalone)
  |-- Dashboard / Repo Manager / Launcher               [v2]
  |-- Original Document Store + PDF/EPUB/DOCX Viewer     [v2]
  |-- SQLite FTS5 Search / Source Resolver               [v2]
  |-- Notebook / Experiments                             [v2]
  |-- Scholarly Ledger Service                           [v2.1 NEW]
  |     |-- Claims
  |     |-- Evidence
  |     `-- Contradictions / Revision lineage
  |-- Provenance & Parallel Comparison                  [v2.1 NEW]
  |-- Controlled Ontology & Typed Knowledge Graph       [v2.1 NEW]
  |-- Staged Snapshot Publisher + Rollback              [v2.1 NEW]
  |-- Local, authenticated read-only Research API        [v2 + v2.1]
  `-- SQLite metadata + immutable source files + release snapshots
                ^
                | localhost HTTP (Bearer token; read-only)
                |
       MSK-Therapy-OS (separate app/process and database)
```

**Boundary invariants:** Therapy OS never directly opens Lab SQLite files or clone directories. Lab never queries Therapy OS patient records. The read-only API never serves full copyrighted documents to Therapy OS by default. No installed upstream repository can read user document storage or API secrets by design; enforcement must be tested, not assumed.

### 2.2 Technology choices and laptop constraints

| Layer | v2.1 choice | Constraints |
|---|---|---|
| App/API | Python 3.11+; pinned FastAPI/Uvicorn | Local loopback only; OpenAPI generated and tested |
| DB | SQLite WAL + migrations + FTS5 + FK checks | Single operator; no Neo4j/Postgres required |
| UI | HTML/CSS/vanilla JS; accessible server-rendered pages | No mandatory React build; no extra frontend daemon |
| Graph | SQLite `nodes`/`edges` + JSON adjacency API | Graph **listing/filtered neighborhood first**; no default whole-graph force simulation |
| Ontology | Versioned JSON/YAML definitions, validated into SQLite | Manual curation; deterministic expansion only |
| Index build | SQLite staging DB, QA reports, manifest and atomic release-pointer | Never overwrite an open active DB; explicit publish/rollback |
| Documents | v2 readers + immutable originals | PDF page-image rendering retained; opt-in local OCR |
| Export | JSON and Markdown baseline | Parquet is optional behind separately reviewed dependency |
| Security | Approved launch profiles + OS process isolation assessment | `shell=False` alone is not a sandbox; deny untrusted scripts access to private directories |

**Operational limits:** Aim for idle Lab process RSS below ~500 MB; run at most one 3D upstream app or OCR job at a time; limit graph view to bounded neighborhoods (e.g., first 100 nodes/200 edges, paginated); preserve full graph in storage without rendering it all. Use the WSL Linux filesystem for SQLite staging where practical, measure destination disk availability, and keep browser/GPU load explicitly monitored. Never claim 60 FPS, medical validation, or total memory from JavaScript heap alone.

### 2.3 Directory structure (additive)

```text
msk-research-lab-os/
  AGENTS.md
  spec.md                             # v2.1 contract (this document)
  README.md
  pyproject.toml
  config/
    repo_catalog.json                # candidate metadata; untrusted until inspected
    run_profiles.json                # explicit reviewed launch profiles only
    ontology/                         # versioned MSK-specific concept sets
      msk-core.v1.json
  msk_research_lab/
    __main__.py                       # serve, doctor, ledger, validate, build, publish, rollback, backup
    api/                              # web UI, v1 API, bearer auth
    core/                             # migrations, audit, config, jobs
    repos/                            # discovery, clone, inspect, launch/stop
    library/                          # store, parsers, visuals, source resolver, FTS5
    research/                         # notebook, experiments, citations
    ledgers/                          # claims, evidence, contradictions, review policy
    provenance/                       # source registry, locators, independence lineage
    ontology/                         # definitions, aliases, crosswalks, validation
    graph/                            # typed nodes and edges; neighborhood queries
    publication/                      # snapshot builder, manifest, QA, activate, rollback
    templates/
    static/
  docs/
    ARCHITECTURE.md
    DATA_MODEL.md
    API_CONTRACT.md
    ACCEPTANCE.md
    TEST_DATA_CONTRACT.md
    SECURITY_AND_RIGHTS.md
    UPSTREAM_FIRSTBRAIN_ADAPTATION.md
    MIGRATION_V2_TO_V2_1.md
  scripts/
  tests/{unit,integration,browser,fixtures}/
  evidence/                           # reproducible test logs/captures, no private content
  data/                               # private, gitignored
    originals/                        # immutable SHA-256 addressed files
    snapshots/.builds/
    snapshots/.releases/
    snapshots/.active/
  research/upstream/                   # gitignored reviewed upstream clones only
```

**Migration compatibility:** Preserve existing v2 table names and APIs; add new tables/migrations rather than rewrite all v2 modules. Never put uploaded original books or FirstBrain corpus text in Git.

---

## 3. The Scholarly Tri-Ledger (G7)

### 3.1 Epistemic model

**Evidence** means a traceable observation or excerpt. **Claim** means a human-authored proposition. **Contradiction** means a recorded conflict or counterexample deserving review. Their existence does **not** prove clinical effect. A source accurately saying something is different from that statement being scientifically established.

Supported classification dimensions:

- `knowledge_namespace`: `SOMATIC_ANATOMY`, `TRADITIONAL_ACUPUNCTURE`, `TRADITIONAL_DIEN_CHAN`, `TRADITIONAL_THAI_SEN`, `MANUAL_THERAPY`, `BIOMECHANICS`, `DEVICE_TECHNOLOGY`, `SOFTWARE_ENGINEERING`.
- `claim_kind`: `SOURCE_DESCRIPTION`, `ANATOMICAL_FACT`, `TRADITIONAL_THEORY`, `HYPOTHESIS`, `GEOMETRIC_ASSERTION`, `INTERVENTION_EFFECT`, `TECHNICAL_FINDING`.
- `source_kind`: `PEER_REVIEWED_STUDY`, `SYSTEMATIC_REVIEW`, `CLINICAL_GUIDELINE`, `TEXTBOOK`, `TRADITIONAL_PRIMARY_TEXT`, `REPO_SOURCE_CODE`, `REPO_DOCUMENTATION`, `IMAGE`, `OPERATOR_OBSERVATION`, `OTHER`.
- `review_state`: `UNREVIEWED`, `LOCATOR_VERIFIED`, `CONTENT_REVIEWED`, `DOMAIN_REVIEWED`, `REJECTED`.
- `claim_status`: `DRAFT`, `PROVISIONAL`, `SOURCE_SUPPORTED`, `DISPUTED`, `REVISED`, `REJECTED`.

**Important naming choice:** `SOURCE_SUPPORTED` means a reviewed source supports the *accurate attribution of a statement*. It is **not** a synonym for clinically proven. The optional clinical evidence assessment is independent and must be supplied by qualified review with documented methods. Never translate FirstBrain's generic `SUPPORTED` status into `CLINICALLY_VALIDATED`.

### 3.2 Minimum ledger schema

```text
claims(
  claim_id PK, statement, knowledge_namespace, claim_kind,
  status, author_kind, review_state, clinical_evidence_assessment NULL,
  supersedes_claim_id FK NULL, created_at, revised_at, reviewer_id NULL,
  review_rationale NULL, uncertainty_text NULL
)
evidence(
  evidence_id PK, source_id FK, locator_id FK, source_kind,
  excerpt_or_observation, extraction_method, review_state,
  provenance_hash, original_language NULL, edition_id NULL,
  author_kind, independence_group_id NULL, created_at
)
claim_evidence_links(
  claim_id FK, evidence_id FK, relation enum(SUPPORTS, CONTRADICTS, CONTEXT),
  reviewer_rationale, PRIMARY KEY(claim_id,evidence_id,relation)
)
contradictions(
  contradiction_id PK, claim_a_id FK, claim_b_id FK NULL,
  counter_evidence_id FK NULL, conflict_kind, state enum(OPEN, UNDER_REVIEW,
  RESOLVED_WITH_RATIONALE, INCONCLUSIVE), rationale, created_at, updated_at
)
claim_revision_events(
  event_id PK, prior_claim_id FK, next_claim_id FK,
  reason, author_kind, created_at, content_hash
)
review_events(
  review_id PK, record_type, record_id, previous_state, next_state,
  reviewer_id, justification, timestamp, evidence_snapshot_hash
)
```

**Database rules:** Foreign keys enabled on every connection; enforce unique IDs, enum constraints, source locator resolution and reviewer actions transactionally; restrict hard deletion of cited evidence or contradiction records; use soft retirement/tombstones plus an append-only event log and immutable snapshots. Backups must include event history and source files. Deleting a source alias never deletes the canonical original bytes while referenced.

### 3.3 Fail-closed promotion gate

A claim cannot transition to `SOURCE_SUPPORTED` unless **all** conditions hold:

1. At least one linked evidence entry has a resolvable original source, exact locator and consistent source fingerprint (document SHA-256 or full Git commit + file locator).
2. The relevant original location can be opened and reviewed; metadata-only hits and OCR snippets not checked against the original cannot pass.
3. Evidence is `CONTENT_REVIEWED` or `DOMAIN_REVIEWED`; not merely imported or automatically generated.
4. The claim's precise statement, scope and type agree with what the source actually says; the recorded rationale identifies that scope.
5. Existing linked counter-evidence and open contradictions appear in the reviewer UI and export. The reviewer cannot silently delete them to promote a claim.
6. A human explicitly promotes the claim; no extractor, AI tool, ontology matcher, GitHub README or batch migration may self-promote.

For `INTERVENTION_EFFECT`, further review of study design, population, outcomes, risks and confidence is required before any non-null `clinical_evidence_assessment` value. **Even then, this Lab does not recommend treatment.**

If a source is missing, stale, unlicensed for an intended export, hash-mismatched or unreviewed, return `INSUFFICIENT_VERIFIED_EVIDENCE` / `SOURCE_UNAVAILABLE` with scope and resolution steps, never a fabricated supported verdict.

### 3.4 Contradiction semantics

- A difference in terminology, translation or anatomical ID is **not automatically** a contradiction. It may be `ALIAS_VARIANT`, `TRANSLATION_DIFFERENCE`, `SOURCE_DISAGREEMENT`, `MEASUREMENT_DIFFERENCE`, `METHODOLOGICAL_LIMITATION`, or `CLINICAL_EVIDENCE_CONFLICT`.
- Retain all sides, original source anchors, reviewers, dates and resolution rationale.
- Never resolve conflict by popularity, number of derivative sites, or the majority of repos repeating the same inherited geometry.
- Display both *independence group* and individual source count: copies/translations/ports of a common source are not independent confirmations.

### 3.5 Required example (synthetic educational fixture)

- Claim A: “Repository X draws GB21 at coordinate `(x,y,z)` on its reference mesh.” Kind `GEOMETRIC_ASSERTION`, source-linked to pinned Git SHA and file/line.
- Evidence A: Original JSON coordinate with exact locator and SHA.
- Claim B: “Repository Y places the analogous label at a different position.” Same namespace but separate model/version.
- Contradiction: Record geometric disagreement **without** asserting which position is clinically correct.
- Revision: Retire a broad claim, create a narrower successor, preserve original and counter-evidence.
- No synthetic test entry may be mistaken for a real patient or a clinical outcome.

---

## 4. Source Provenance and Parallel Comparison (G8)

### 4.1 Provenance registry

Every item used as evidence must identify a *specific source artifact*, not just a repository home page or a human-readable title.

```text
sources(
  source_id PK, kind, canonical_uri, title, author NULL, translator NULL,
  publisher NULL, language NULL, edition_id NULL, acquisition_time,
  source_version NULL, git_commit_sha NULL, sha256 NULL,
  rights_status enum(ALLOWED, RESTRICTED, UNKNOWN, REVIEW_REQUIRED),
  declared_license NULL, asset_license NULL, origin_id NULL,
  independence_group_id NULL, authenticity_state, notes NULL
)
source_locations(
  locator_id PK, source_id FK, locator_type,
  locator_json, preview_text_hash NULL, extract_method,
  visibility_status, source_resolver_version
)
source_relations(
  relation_id PK, source_a_id FK, source_b_id FK,
  kind enum(TRANSLATION_OF, DERIVED_FROM, MIRRORS, SAME_EDITION,
  INDEPENDENT_WORK, ALIAS_OF, REFERENCES), rationale, review_state
)
```

**Concrete locators:**

| Format | Stable locator example | Rule |
|---|---|---|
| PDF | `{ "page": 14, "region": [0.1,0.2,0.6,0.4] }` | UI/API pages 1-based; region normalized; original page viewer required |
| EPUB | `{ "spine_index": 3, "href": "ch2.xhtml", "fragment": "s2" }` | Never invent physical page numbers |
| DOCX | `{ "block_type": "paragraph", "block_index": 27, "heading_path": ["Chapter 2"] }` | Preserve original structural order and tables |
| JSON | `{ "pointer": "/points/GB21/position" }` | RFC 6901; verify extracted value round-trip |
| Source code | `{ "commit": "<40-hex>", "path": "src/points.json", "start_line": 3, "end_line": 7 }` | Pin full SHA; detect subsequent repo updates |
| Image | `{ "asset_sha256": "<64-hex>", "annotation_id": "a001" }` | Store original image plus human review provenance |

Do **not** treat filename, Git tag, snippet, graph label, UI route or automatically derived coordinate as a valid original locator by itself.

### 4.2 Rights / independence requirements

- Default imported asset rights to `UNKNOWN`, not `ALLOWED`. GitHub code license and anatomical 3D model/data license may differ; store both.
- Preserve author, translator, edition, license notices, original bytes, hash and acquisition date.
- Never bulk export source content to Therapy OS without a separate rights decision. By default export **metadata, permissible snippets and resolvable local links only**.
- Store `DERIVED_FROM` chains and `independence_group_id`, especially for multiple implementations backed by BodyParts3D or WHO source documents.
- Changes in upstream Git or a replacement book must create a new versioned source artifact; no silent in-place mutation.

### 4.3 Parallel Comparison workspace

From the Dashboard, select two or more items to compare (minimum two mandatory for acceptance):

- Left/right original source views (exact page, heading, JSON pointer or repo commit/file).
- Claim text **versus** source quotation clearly distinguished.
- Edition, language, translation, source ancestry, hash, license and review status displayed.
- Supports `MATCH`, `DIFFERENCE`, `UNCERTAIN`, `NOT_COMPARABLE`; these are operator classifications, not automatic claims of equivalent anatomy.
- Side-by-side note saving with stable citations and optional screenshots.
- A comparison card may represent `ACU-GB21`, but coordinates must carry `model_id`, `mesh_id`, `coordinate_frame`, `units`, `reference_body`, `point_definition_source`, `registration_method`, and `geometry_review_status` if displayed.
- Without common frame/scale and landmark-registration evidence, show `UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL`, **not** a misleading millimeter difference.
- If a source is unavailable at review time, allow metadata view but disable `verified comparison` completion.

---

## 5. Controlled MSK Ontology and Knowledge Graph (G9)

### 5.1 Why the ontology is needed

A search for `GB21`, `Jianjing` or `Kiên tỉnh` should find relevant *source records* across languages without declaring equivalence to nearby muscle fibers or a nerve. FirstBrain demonstrates deterministic cross-language term expansion. MSK must build a **new domain ontology**; never import Buddhist conceptual terms as MSK vocabulary.

### 5.2 Ontology entry contract

```json
{
  "schema_version": "1.0",
  "concept_id": "tcm:acupoint:GB21",
  "namespace": "TRADITIONAL_ACUPUNCTURE",
  "canonical_label": "GB21",
  "aliases": [
    { "value": "Jianjing", "language": "zh-Latn", "kind": "TRANSLITERATION" },
    { "value": "Kiên tỉnh", "language": "vi", "kind": "TRADITIONAL_NAME" }
  ],
  "definition_source_ids": ["SOURCE_ID_TO_BE_REVIEWED"],
  "review_state": "UNREVIEWED",
  "source_conflict_notes": null
}
```

This is a **schema example**, not a verified authoritative GB21 record or proof of point placement.

Rules:

- Namespace-qualified IDs are stable; avoid collision between anatomical structures, trigger points, reflexology points and acupuncture points.
- An alias must not automatically create a `SAME_AS` edge across conceptual frameworks.
- Normalize Unicode carefully; exact-match first, then optional accent-insensitive search with visible `EXPANDED_QUERY` labels.
- Query expansion has hard limits, source review flags and logged matched terms; no opaque clinical synonym inference.
- Do not claim complete Chinese segmentation or precise Vietnamese transliteration without tests.
- Allow conflicting traditions to have distinct concept IDs connected by `RELATED_TO` rather than merged.

### 5.3 Typed graph schema

```text
graph_nodes(node_id PK, node_type, namespace, label, stable_ref,
            review_state, source_id NULL, properties_json, version)
graph_edges(edge_id PK, source_node_id FK, target_node_id FK,
            relation_type, assertion_kind, provenance_evidence_id FK NULL,
            review_state, confidence_text NULL, valid_from, supersedes_edge_id NULL)
```

Allowlisted `node_type`: `ANATOMICAL_STRUCTURE`, `JOINT`, `MUSCLE`, `ACUPOINT`, `MERIDIAN`, `DIEN_CHAN_POINT`, `THAI_SEN_LINE`, `SYMPTOM_TERM`, `TECHNIQUE`, `SOURCE`, `CLAIM`, `EVIDENCE`, `CONTRADICTION`, `REPOSITORY_VERSION`, `ONTOLOGY_CONCEPT`.

Allowlisted `relation_type`: `CITES`, `SUPPORTS`, `CONTRADICTS`, `DERIVED_FROM`, `TRANSLATION_OF`, `ALIAS_OF`, `PART_OF`, `CONCEPTUALLY_ASSOCIATED_WITH`, `LOCATED_ON_REFERENCE_MESH`, `REPORTED_IN_SOURCE`, `COMPARES_WITH`, `SUPERSEDES`.

**No automatic anatomical equivalence:** `CONCEPTUALLY_ASSOCIATED_WITH` does not mean `IS_A_NERVE`, `HAS_KNOWN_PHYSIOLOGICAL_CHANNEL`, clinical benefit or safe treatment site. Graph edges derived from imported prose must remain **unreviewed candidates** until a human checks the original.

### 5.4 Graph UI and retrieval

- From a source, point, muscle or claim, select **Explore connections**.
- Default to a paginated **1-hop neighborhood** filtered to reviewed relationships; user can request another hop deliberately.
- Inspect any edge to see its relation type, source evidence, locator, human review status and timestamp.
- Toggle `Show unreviewed`, clearly differentiated from reviewed edges.
- Graph search resolves back to the original library item or the exact Git source commit.
- **No graph hairball requirement**: a simple inspectable list/tree of nodes and edges counts as full MVP functionality; attractive force-layout rendering is optional and must not freeze Intel HD 5500.

---

## 6. Validated Research Snapshots, Atomic Publication and Rollback (G10)

### 6.1 Publication model

The **working metadata database** receives new notes and research edits. Published **read-only knowledge snapshots** are separate artifacts consumed through the read-only Research API. This prevents ongoing edits, incomplete OCR or unreviewed graph edges from leaking into a supposedly vetted knowledge release.

```text
Working Lab SQLite DB + Immutable originals
       |
       | build --staging-only (explicit user action)
       v
snapshots/.builds/<build-id>/
  knowledge.sqlite
  manifest.json
  qa.json
       |
       | validate source references + rights + schema + index
       v
snapshots/.releases/<release-id>/
  knowledge.sqlite  (immutable)
  manifest.json
  qa.json
       |
       | atomic change of .active/current.json
       v
GET /api/v1/... resolves the active read-only snapshot
       |
       `-- rollback -> previous validated release pointer
```

**No automatic publication.** The UI shows a diff of source versions, approved claims, graph changes, unresolved contradictions, rights flags and index coverage, then requests explicit operator confirmation.

### 6.2 QA gate before activation

Publication is **blocked** if any required invariant fails:

1. SQLite `PRAGMA integrity_check`, FK validation, schema version, and FTS consistency.
2. Complete snapshot manifest with count, build configuration fingerprint, source IDs, source hashes or Git SHAs, original locator resolution and licensing flags.
3. **Every published claim** meets the promotion gate; its reviewed evidence exists and the source can still resolve. Check all published locators, not merely a sampled subset in this small v2.1 scope.
4. Contradictions, reviewer annotations and revision history remain accessible; disputed claims are displayed with their dispute status, not silently filtered into a supported-only response.
5. Orphan/duplicate IDs and missing graph-edge provenance are zero for published asserted relationships.
6. Query regression fixtures return expected normalized results; stored documents/extraction coverage is unchanged.
7. Rights checks pass for every exposed excerpt or asset; `UNKNOWN` / `RESTRICTED` full text is not exported to cross-app API.
8. The release directory has sufficient disk space, new files match manifest hashes, and the target active pointer is unchanged since build began (optimistic concurrency check).

A failed build stays in `.builds/` with a report, never becomes active.

### 6.3 Crash-safety and rollback

- Publish using a versioned immutable directory, temporary pointer file, fsync where supported and atomic `os.replace` **on the same filesystem**; verify actual target environment semantics, especially WSL `/mnt/c` versus ext4.
- Never replace/delete an active SQLite database, or its WAL/SHM, in place. Existing reader requests finish using the old snapshot; new requests use the new pointer.
- Use publisher lock and expected previous release ID; refuse concurrent conflicting publish.
- Rollback changes only the active pointer to a **previously validated retained release**; it does not discard source artifacts or ledger audit history.
- Backup/restore (G6) must include current working state, immutable originals, snapshots/manifest and active release pointer. Tokens/secrets remain excluded.
- Test kill/crash simulation before pointer switch, during staging and after activation. Confirm the last known good release always remains searchable.

---

## 7. Read-only API and Therapy OS interoperability

### 7.1 Versioning and authentication

Retain existing v2 `GET /api/v1/health`, `/repos`, `/library/documents`, `/library/search`, `/documents/{id}/locations/{location_id}`, `/research/notes/{id}`, and `/knowledge/points/{code}`. Add, without breaking v1 clients:

| Method | Endpoint | Outcome |
|---|---|---|
| GET | `/api/v1/claims/{id}` | Claim, kind/status, reviewer state, source and counter-evidence links |
| GET | `/api/v1/claims/{id}/evidence` | Paginated exact source references and confidence/uncertainty |
| GET | `/api/v1/contradictions?claim_id=...` | Open or resolved disagreements and rationales |
| GET | `/api/v1/sources/{id}` | Provenance metadata, rights and available locators |
| GET | `/api/v1/comparisons/{id}` | Frozen comparison report with both source IDs |
| GET | `/api/v1/ontology/lookup?term=...` | Reviewed concept matches with expansion provenance |
| GET | `/api/v1/graph/neighborhood?node_id=...&depth=1` | Bounded, typed, evidence-anchored node/edge set |
| GET | `/api/v1/snapshots/current` | Immutable active snapshot ID, build hash, timestamp, coverage |

Example **illustrative response shape** (not real researched medical evidence):

```json
{
  "claim_id": "claim:example:001",
  "text": "Source X describes an educational landmark for GB21.",
  "claim_kind": "SOURCE_DESCRIPTION",
  "knowledge_namespace": "TRADITIONAL_ACUPUNCTURE",
  "status": "SOURCE_SUPPORTED",
  "clinical_validity": "NOT_ASSESSED",
  "source_evidence": [
    {"source_id": "source:example:X", "locator_id": "loc:example:7",
     "source_version": "REPLACE_WITH_VERIFIED_VERSION",
     "review_state": "CONTENT_REVIEWED"}
  ],
  "counter_evidence": [],
  "open_contradiction_count": 0,
  "snapshot_id": "release:example",
  "disclaimer": "Educational research record; not medical advice."
}
```

**Access safeguards:** Random local bearer token stored outside Git, same-origin protections/CSRF for UI writes, allowlisted origins (no `*` CORS), bound only to loopback, strict field-level filtering, paginated responses and 401/403 on unauthorized requests. Never put auth tokens in screenshots/logs or Git. Treat API text as untrusted data in Therapy OS.

### 7.2 Publication visibility rule

The **public-to-local-client API** reads only the active validated knowledge snapshot for reviewed claims/graph edges, while the local Dashboard can examine drafts/unpublished state behind its own authenticated session. A query for an unreviewed term or a missing source-linked point must yield **404 or explicit `UNREVIEWED_NOT_PUBLISHED`**, never fabricate a clinical interpretation. API consumers must see snapshot freshness and unresolved uncertainty.

### 7.3 Integration acceptance without modifying Therapy OS

A standalone Python or curl client on Windows/WSL must:

1. Reject no/wrong token.
2. Return a published example source-backed record with a resolvable local locator and release ID.
3. Return an unresolved contradiction when one exists.
4. Reject unreviewed point claims.
5. Continue working after snapshot publish and rollback, with the release ID changing appropriately.

Do not edit the Therapy OS repository as part of v2.1 implementation. A separate future change may add a click-to-research integration in the Therapy UI.

---

## 8. UI design and exact interaction flows

Minimum new navigation: **Research Notebook**, **Claims & Evidence**, **Compare Sources**, **Concept Explorer**, **Knowledge Releases**. Preserve the v2 Repo Manager, Library, Search and Health pages.

**Flow A — From page to claim:** Search `GB21` → open a source result at its exact page/section → create evidence excerpt → attach to a new claim → record review state → preview the claim alongside original. Imported OCR starts as unreviewed.

**Flow B — Register disagreement:** Open claim → add counter-evidence from another source → classify source independence and contradiction type → compare both original views → save unresolved contradiction. The UI must not suppress a disagreement behind a “verified” badge.

**Flow C — Compare research repos:** Choose two SHA-pinned upstream repos → inspect corresponding point coordinates/claims → see model/coordinate-frame metadata → classify comparability → save a side-by-side experiment with screenshots and file locators. Show `NOT_COMPARABLE` rather than invalid geometric math.

**Flow D — Publish and roll back:** Change reviewed ontology alias or claim → build staging index → inspect QA and diff → publish → query API and capture snapshot ID → roll back → confirm old answer and ID. Must work after process restart.

**Flow E — Explore graph:** Search an approved concept alias → open one-hop associations → click an edge → jump to the original source and human rationale. No clinical claims inferred from spatial proximity.

**Usability contract:** 1366x768 Windows browser, keyboard navigation to core actions, clear status banners, no horizontal page scrolling, progress/cancel for long operations, bounded logs and visible `READY`, `PARTIAL`, `BLOCKED`, `FAILED` states. Do not build a mock graph or dummy “PASS” interface.

---

## 9. Security, rights, scientific and clinical guardrails

1. **No real patient data:** No real patient images, names, notes or medical histories in the Lab. Synthetic fixture data only. Therapy OS keeps its own separate patient/data controls.
2. **Never equate theories with anatomy:** Meridians, Thai Sen Sib and Dien Chan mappings are historically and pedagogically distinct from anatomical nerves, vessels, fascia and validated clinical interventions.
3. **No automated therapy recommendations:** Source claims about indications are described as *what the cited source says*, paired with evidence quality and relevant uncertainty. No treatment personalization.
4. **Source trust:** Repository code, cloned READMEs, PDF text, EPUB HTML, ontology files and extracted snippets are untrusted. Sanitize display, cap payloads, reject path traversal/zip bombs, validate file types and do not execute text as commands or instructions.
5. **Repo execution:** Use explicit approval for Clone/Install/Run/Update; reviewed argv profiles; no `curl | bash`; launch in controlled user-level environments with minimal permissions, bounded CPU/memory/child processes, loopback ports and private library path isolation. If practical isolation cannot be enforced on WSL, label execution risk and do not mark SEC PASS.
6. **Rights:** Maintain per-file and per-asset provenance; do not assume repo license applies to embedded 3D meshes, diagrams, translations, textbooks or scanned pages. Do not redistribute FirstBrain's Buddhist source corpus or any copyrighted medical textbooks by default.
7. **No false certainty:** Always distinguish `SOURCE_SUPPORTED`, `CLINICAL_EVIDENCE_ASSESSED`, `HYPOTHESIS`, and `NOT_ASSESSED`. A correct on-surface snap or matching coordinate is geometric consistency, not clinical accuracy.
8. **No LLM dependency:** Deterministic search, typed relations and manual review must work offline. Any future optional RAG must cite exact immutable sources and fail closed, but is not included in v2.1.

---

## 10. Implementation plan, milestones and deliverables

### M0–M3 — Preserve and complete v2 foundation

- **M0:** Working Windows/WSL dashboard, `doctor`, SQLite/FTS5, safety defaults → **G1**.
- **M1:** Audited Repo Catalog and real sequential launch/stop of 3 different repos → **G2**.
- **M2:** 10 mixed-document import, original viewers, optional OCR, precise search → **G3–G4**.
- **M3:** Source-linked notebook, read-only API and backup/restore → **G5–G6**.

**Do not claim v2 was already built merely because its spec was written.** Verify each installed component and preserve evidence.

### M4 — Provenance + Tri-Ledger (v2.1 first priority)

- Add versioned provenance/migration tables, resolvable locators, source independence and rights status.
- Add claim/evidence/contradiction tables, revision lineage, review events and fail-closed policy.
- Build source-to-claim and claim-to-source UI and tests.
- Provide two-source side-by-side comparison with uncertainty.
- **Gate:** G7 + G8, including negative cases.

### M5 — Curated Ontology + Knowledge Graph

- Add schema-validated MSK vocabulary, alias registry, controlled expansion.
- Build deterministic graph nodes/edges and bounded neighborhood UI/API.
- Link every reviewed assertion to source and reviewer; preserve unreviewed candidates separately.
- **Gate:** G9.

### M6 — Staged Publication and Safe Read-only Delivery

- Build immutable SQLite snapshots from reviewed records; source and index validation.
- Implement pointer-based activation and rollback; crash tests and readers holding old snapshots.
- Add v2.1 API views and test standalone client.
- **Gate:** G10 + read-only API integration tests; rerun G1–G9 and SEC.

### Required artifacts after each milestone

- Git commit for **Lab-owned** code, source tree diff and pinned dependency manifests.
- Exact commands, versions, exit codes and environment/hardware observations.
- Unit/integration/Playwright output, **actual Windows browser** screenshots, negative-path results.
- `evidence/Mx_report.md`: gate IDs and statuses (`PASS`, `FAIL`, `BLOCKED`) with steps to reproduce.
- SQLite migration report, example data / test fixture manifest, original-source checksum demonstration.
- At M6: `docs/API_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/MIGRATION_V2_TO_V2_1.md`, `docs/ACCEPTANCE.md`, `MVP_V2_1_VALIDATION.md` with references to live evidence.

---

## 11. Test matrix and objective release criteria

| Gate | Mandatory positive demonstration | Mandatory negative/failure demonstration |
|---|---|---|
| G1 | Windows browser reaches real WSL Dashboard | Port clash/restart, layout at 1366x768 |
| G2 | 3 reviewed upstream apps cloned, run, interacted with and stopped sequentially | Denied approval, bad profile, timeout, dirty repo, zombie process |
| G3 | 4 PDFs incl 2 scanned, 3 EPUBs, 3 DOCXs imported with stable hashes | Corrupt/oversized/unsafe file, failed OCR, missed PDF page flagged |
| G4 | FTS5 hit opens exact original page/chapter/structural location | Missing locator and false OCR confidence fail visibly |
| G5 | Export source-linked note/experiment; token-protected v1 API | Anonymous/wrong-token and forged citation rejected |
| G6 | Restore to new directory; compare originals, indexes and citations | Corrupted/incomplete backup rejected; old data intact |
| **G7** | Create claims, verified sources, counters, contradiction and preserved claim revision | Unsupported claim promotion, deleting counter-evidence, unresolved source rejected |
| **G8** | Compare two original source locations; display editions, ancestry, reviewer/rights, source SHA | Mismatched hash, nonexistent JSON pointer, non-independent duplicate, unregistered 3D frames flagged |
| **G9** | Deterministic multilingual aliases yield cited nodes/edges; click opens source | Unknown alias, self-invented anatomy equivalence, orphan edge and oversized graph refused |
| **G10** | Stage, validate, publish, read, roll back; old/new snapshot IDs verifiable | Kill during build, corrupt DB, source hash change, stale publish lock, concurrent activation |
| **SEC** | Loopback only, inspected execution, auth+CSRF+CORS checks, private file isolation, no patient data | Shell/path injection, secrets leakage, forbidden file access, unauthorized app launch |

**Release rule:** Every G1–G10 and SEC must be marked **PASS with reproducible evidence**. Environment-limited steps are **BLOCKED**, never silently waived. Record actual resource peaks (Lab RSS, WSL aggregate RSS if available, disk footprint, OCR time, viewer responsiveness). Reports must not attribute the laptop's resource limits to missing medical accuracy without testing the dataset/renderer separately.

### Minimum fixture set for v2.1

Create synthetic, clearly labeled artifacts with predictable exact ground truth:

1. Two short source documents describing **different traditional educational descriptions** of a fictional point, containing divergent wording and explicit edition information.
2. A scanned PDF page requiring opt-in OCR; original must remain visually inspectable.
3. Two repo snapshots or synthetic Git fixtures with different coordinates and **different coordinate frames**, where geometry comparison **must** return `NOT_COMPARABLE` until alignment information exists.
4. A multilingual alias fixture (Vietnamese + English + transliteration), including ambiguous mappings that must remain separate.
5. An unreviewed contradictory claim and a revised successor; reviewer progression includes a rejected promotion attempt.
6. A valid and deliberately corrupt knowledge release; automated crash/corruption rollback checks.

Fixtures must not be quietly inserted into the production knowledge base and must never be presented as real clinical data.

---

## 12. Command-line contract (proposed; implement and test before marking PASS)

```bash
# Basic Lab; commands from v2 remain supported
python -m msk_research_lab doctor
python -m msk_research_lab serve --host 127.0.0.1 --port 8091

# v2.1 inspection and validation
python -m msk_research_lab ledger audit --json
python -m msk_research_lab provenance verify --all --json
python -m msk_research_lab ontology validate config/ontology/msk-core.v1.json
python -m msk_research_lab graph audit --json

# Safe release operations; never automatically publish after import
python -m msk_research_lab snapshot build --staging-only
python -m msk_research_lab snapshot inspect --latest
python -m msk_research_lab snapshot validate --latest
python -m msk_research_lab snapshot publish --release-id <validated-id>
python -m msk_research_lab snapshot rollback --release-id <prior-validated-id>

# Full automated checks
python -m pytest tests/unit tests/integration -q
# Playwright test launcher documented in README and tested against the live app
```

CLI is a **target implementation contract**, not a claim these commands exist today. Commands that mutate production must require an explicit operator action and be safe against accidental repeated invocation. The publishing CLI must refuse any unvalidated or missing release ID.

---

## 13. Coding Agent handoff instructions

**Mission:** Implement MSK Research Lab OS v2.1 faithfully, using the v2 spec as the unchanged baseline and the uploaded FirstBrain archive only as an inspectable design reference.

1. Inspect current Lab repository/workspace first. Do not assume any v2 feature is implemented; produce a gap and conflict report against G1–G6.
2. Inventory existing supporting documents and candidate catalog; do not invent missing files or preapprove clone/install/run actions.
3. Compare the FirstBrain concepts with this spec. Document which were **reused conceptually**, which algorithms were **ported after license audit**, and which were **rejected**. Do not import unrelated Buddhist corpus data.
4. Implement minimally and sequentially: **v2 gates → G7/G8 → G9 → G10**. Keep each phase runnable and independently testable.
5. Retain the Lab as a standalone application; no mandatory modifications to MSK-Therapy-OS, no monolith fusion, no new heavyweight services on 8 GB RAM.
6. Review license and provenance for every upstream code/assets reuse. No unreviewed dependency postinstall, unsolicited `git pull` or automated running of cloned code.
7. Maintain exact source locators, immutable originals and explicit human-reviewed claim status. Never substitute plausibly worded generated content for evidence.
8. For every gate, provide actual on-machine screenshots, command logs, tests and failure evidence. If blocked, say **BLOCKED** and explain exactly why.
9. Do not declare completion or change a status flag until **all** G1–G10 + SEC have passed.

### Final output checklist

- [ ] Working standalone Lab Dashboard on Windows/WSL2.
- [ ] Three real, approved upstream repo launches/stops captured.
- [ ] 10 source-file ingestion/view/search journeys complete.
- [ ] Tri-Ledger persisted, reviewable, source anchored, fail-closed.
- [ ] Parallel Comparison shows original sources and uncertainty.
- [ ] Deterministic ontology/typed graph works without AI/network.
- [ ] Atomic staging/publish/rollback proves fault recovery.
- [ ] Authenticated read-only v1 API serves reviewed snapshot records.
- [ ] Backup/restore preserves originals, citations, ledgers, graph and active snapshot.
- [ ] All tests, exact command logs and reviewer-facing evidence included in `MVP_V2_1_VALIDATION.md`.

---

## 14. Decision summary

**Adopt from FirstBrain:** the *principles and patterns* of Claim/Evidence/Contradiction ledgers, exact source locators, original/translation separation, multilingual controlled vocabulary, immutable data snapshots, validation and rollback.

**Adapt for MSK:** anatomical/traditional namespace separation, explicit clinical-evidence uncertainty, tissue/point/model coordinate metadata, source-independence grouping, user-verifiable side-by-side comparisons and a private Research Knowledge API.

**Do not adopt for this MVP:** FirstBrain's Buddhist corpora, cloud data lakehouse, large multi-index builds, mandatory Parquet, unreviewed `VERIFIED` defaults, any implication that multiple documentary descriptions prove a treatment's effectiveness, or any requirement to merge research code with the Therapy application.

**Definition of success:** MSK Research Lab OS is an *independent, lightweight and auditable research workbench* that can explore open-source repositories, organize exact source evidence, preserve disagreement, publish reliable snapshots and serve transparently reviewed research to MSK-Therapy-OS **without making clinical decisions**.
