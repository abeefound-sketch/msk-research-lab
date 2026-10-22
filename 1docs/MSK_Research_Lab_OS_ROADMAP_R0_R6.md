# Execution Roadmap — R0 through R6

**Binding delivery plan.** This document defines order, work packages, dependencies, proof and rollback. An agent must work on **one release at a time**. Neither this roadmap nor the accompanying config constitutes permission to run untrusted source or install arbitrary dependencies.

## Sequencing and release-gate dependency graph

```text
R0: Foundation / Doctor / Isolation feasibility                   G1-base, SEC-base
 ├── R1: Safe repository research and live demos                 G1,G2,SEC
 └── R2: Private document library + research notes              G3,G4,G5,G6
      └── R3: Tri-Ledger, comparison, ontology, graph, releases  G7,G8,G9,G10,SEC
           └── R4: One Unified Atlas renderer + geometry         ATLAS-01..04
                └── R5: Point/path and facial atlas authoring     ATLAS-05..06
                     └── R6: Therapy bridge + offline packages   BRIDGE-01..03
```

R2 can overlap limited planning of R1, but it does not excuse R1's missing execution/security evidence. A thin, clearly labeled Atlas *technical spike* may run under R1 or R2 on one reviewed model to expose GPU/asset blockers early; it **must not** be marked ATLAS PASS before R4 QA.

## State semantics and promotion

`NOT_STARTED` → `IN_PROGRESS` → `READY_FOR_VERIFICATION` → `PASS`, `FAIL`, `BLOCKED`, or `INCONCLUSIVE`. `PASS` is allowed only for a precisely scoped release gate backed by verification artifacts. `SKIPPED` and `NOT_TESTED` are separate. A failed critical gate prevents downstream release **promotion**; work on independent tests may continue as research but cannot be represented as a passed prerequisite. Mark findings `NOT_VERIFIED` if code exists without an actual on-device run.

**Release bundle:** Lab commit; approved source/asset licenses; upstream SHA manifest; environment and actual hardware fingerprints; database migration; testcase IDs/results; stderr/stdout and exit codes; real Windows browser captures + URL/viewport; negative cases; resource telemetry; evidence checksums; known gaps; rollback tested; `AGENT/MILESTONE_REPORT_TEMPLATE.md` filled; next-session handoff.

## R0 — Verified Local Foundation

**Goal:** establish a standalone, secure-by-default workspace that can truthfully diagnose the actual target machine. Do not automatically clone/install/launch candidate repos.

**Work packages (execute in dependency order):**

| ID | Work | Dependencies | Evidence/Done |
|---|---|---|---|
| R0-01 | Inspect workspace, `AGENTS.md`, 4 source specs, disk/CPU/RAM/WSL/network, Git, Python, Node, browser and FTS5; record observed versus unknown | None | `doctor.json`, commands with exit codes; no guessed properties |
| R0-02 | Initialize *new separate* Git repo, `pyproject.toml`, pinned minimal dependencies, `.gitignore`, README, settings and migration framework | R0-01 | Clean Lab-owned Git history, source/fixture separation |
| R0-03 | Implement SQLite WAL, FKs, migrations and basic API `GET /api/v1/health` | R0-02 | Migration round-trip, integrity checks |
| R0-04 | Implement `doctor`, `serve`, lifecycle logs, shutdown/restart, local-only `127.0.0.1:8091` and simple usable Dashboard | R0-03 | Real browser interaction at 1366x768; port conflict and restart tests |
| R0-05 | Threat model and sandbox readiness probe (rootless Podman or evaluated equivalent); verify mounting, write denial, network policy and resource cgroups on this WSL host | R0-01 | **Measured** isolation capability or explicit `SANDBOX_UNAVAILABLE`; no bypass |
| R0-06 | Seed untrusted repo catalog, schema linting, policies and CLI help; create synthetic fixtures skeleton | R0-03 | Automated schema and safety tests |
| R0-07 | UI/browser test harness and independent evidence verifier | R0-04 | Source-linked logs/test manifest; real browser evidence |

**Gate:** G1 foundation, SEC diagnostics; untrusted execution remains disabled. **Negative tests:** invalid workspace path, port occupied, invalid/missing tool version, failure to bind non-loopback, stale database migration, unsafe symlink. **Rollback:** restore baseline migration/snapshot; stop local service; no Therapy OS mutation.

## R1 — Repository Discovery, Secure Launch and Reproducible Evaluation

**Goal:** non-coder can clone and actually try three different inspected real apps sequentially without endangering private research books or machine state.

| ID | Work | Dependencies | Evidence/Done |
|---|---|---|---|
| R1-01 | Repo URL normalization, dedup and metadata discovery; rights status per code/asset/data; inspect profile | R0 | `REGISTERED`, `INSPECTED`, `REVIEW_REQUIRED`; negative malformed URL |
| R1-02 | Separate `Clone`, `Install`, `Run` approvals; SHA-pinned clone; dirty-tree/branch/update guard; disk estimates | R1-01 | Checkout SHA verification; no script executed on clone |
| R1-03 | Reviewed, disabled-by-default run profiles with exact argv, paths, mounts, ports, network, limits and expected side effects | R0-05,R1-01 | Owner approvals and full audit history |
| R1-04 | Sandbox runner; process-group cleanup, timeout, bounded logs, loopback proxy for web apps, resource budget | R1-03 | File/network/privilege negative tests; measured limits |
| R1-05 | Repo start/stop/open UI; verify `STARTED`, `HEALTHY`, `RENDERED`, `VISUALLY_VERIFIED` separately | R1-04 | Three real browser workflows, click interaction, SHA/URL screenshot metadata, zero zombies |
| R1-06 | Evidence store with SHA-256 manifests; source/commands/environment/metrics/artifacts; verifier and decisions | R1-05 | Tamper test invalidates evidence; no self-certification |
| R1-07 | Initial `surface-registration-v1` comparator harness and capability inventory for 4 geometry repos; unsupported explicitly classified | R1-01,R1-06 | Reproducible synthetic mesh test, no false normalized distance |
| R1-08 | Early unified-viewer spike with one legally usable real anatomy asset, as hardware feasibility test only | R1-04 | WebGL render/performance observations; **no** R4 PASS |

**Gate:** G2: **3 different** successful real SHA-pinned inspected approved apps launched, interacted with and stopped *sequentially*; SEC enforced. Prefer candidate WaterCMY, spacejohnlf, Meridian Studio only if current source and environment actually qualify; substitute with a genuine reviewed repo if blocked. Inspect all four geometrical research sources, but do not require all to run on 8 GiB hardware. **Negative:** denial of approval, failed/dead process, unknown argv, attempted file/network escape, missing dependency, dirty repo, wrong commit, occupied port, and forced timeout. **Rollback:** all process trees dead, disposable workspace cleaned, original upstream checkout unchanged.

## R2 — Evidence-Complete Library, Notebook, Recovery

**Goal:** source-first, image-aware private book research that works before any AI service exists.

| ID | Work | Dependencies | Evidence/Done |
|---|---|---|---|
| R2-01 | Immutable SHA-256 original store, rights metadata, safe file picker, type sniffing and size/zip safety; duplicate aliases | R0 | Bytes preserved; malformed/oversized input rejected |
| R2-02 | PDF native-text extraction plus **every page** including blank/scan/errors; original page viewer and normalized region locators | R2-01 | 4 PDFs including >=2 scanned, page coverage report |
| R2-03 | Opt-in local Tesseract OCR, per-page status, optional language packs; show image/table gaps | R2-02 | OCR failed/partial states and original image visible |
| R2-04 | EPUB spine/href/chapter and safe HTML viewer; DOCX paragraph/heading/table/figure structure with source anchor | R2-01 | 3 EPUB + 3 DOCX, exact locator viewer tests |
| R2-05 | SQLite FTS5 and explicitly reviewed Unicode/aliases; search filters, snippets, open-original, copy citation | R2-02,R2-04 | Search opens correct locations for all three formats; false locator rejected |
| R2-06 | Notes/experiments linked to 2 book citations + 1 Git SHA; source comparison; JSON/MD rights-filtered export | R2-05,R1-01 | Cross-source note workflow; exported references resolvable |
| R2-07 | Preliminary authenticated **research-note-only** read API; point knowledge returns 404 if unpublished; standalone sample consumer | R2-06 | No/wrong token + cross-origin tests; no raw private book by default |
| R2-08 | Consistent SQLite backup, originals, attachments/indices + checksum manifest; restore to fresh directory | R2-06 | Original hashes, citations, search and notes preserved; corrupt backup rejected |

**Gate:** G3, G4, G5 and G6. **Critical reconciliation:** G5's prepublication read-only API supplies reviewed *research records/notes*, not unvalidated medical point claims. `/knowledge/points/{code}` is 404 until R3 publishes a validated snapshot. **Negative:** scan with no OCR, bogus EPUB page, invalid DOCX index, missing illustration, unsafe EPUB HTML, revoked rights, corrupt backup, anonymous client. **Rollback:** prior database and originals intact on failed import/restore.

## R3 — Auditable Claims, Ontology, Graph and Knowledge Publication

**Goal:** know exactly who says what, in which source, which other sources disagree and which approved revision Therapy clients may eventually query.

| ID | Work | Dependencies | Evidence/Done |
|---|---|---|---|
| R3-01 | Provenance registry (edition, translation, derivative lineage, source independence, locator verification, rights) | R2 | Exact original PDF/EPUB/DOCX/Git locators; hash-mismatch refusal |
| R3-02 | Tri-Ledger: claims/evidence/contradictions, review events and irreversible revision lineage | R3-01 | Evidence-linked record, counter-record, reviewer gate; audit log |
| R3-03 | Fail-closed promotion: original resolver, human content review, counter-evidence disclosure, separate clinical assessment | R3-02 | Negative unsupported/OCR-only/deleted-counter promotion refused |
| R3-04 | Side-by-side original source/edition comparison, independence tracking, `MATCH`, `DIFFERENCE`, `UNCERTAIN`, `NOT_COMPARABLE` | R3-01 | Two originals independently traceable; misleading geometry distance prohibited |
| R3-05 | Namespaced multilingual ontology, TARA adapter behind rights gate; aliases never imply physiology | R3-01 | Deterministic GB21 example from **synthetic educational** fixture; unknown alias remains unknown |
| R3-06 | Typed SQLite graph with reviewed edge evidence and bounded one-hop UI/API; no mandatory Neo4j | R3-02,R3-05 | Source-openable graph edges; orphan/non-provenance and unreviewed promotions refused |
| R3-07 | Staged immutable SQLite knowledge snapshots, manifest/QA rights checks, explicit activation and rollback | R3-03,R3-06 | Crash before/during/after activation; last known good preserved |
| R3-08 | Published-only read-only API and snapshot awareness | R3-07 | Authenticated client, `snapshot_id`, counter-evidence, unreviewed 404 |

**Gate:** G7, G8, G9, G10 and SEC regression, plus rerun G1–G6 after migrations. **Negative:** mismatched source hash, non-independent duplicate, absent source, malicious query, reviewer bypass, broken graph edge, corrupt snapshot, publisher collision, WSL filesystem atomicity failure. **Rollback:** pointer to prior validated immutable release, working DB untouched.

## R4 — Unified Anatomy & Meridian Atlas

**Goal:** one true anatomical viewer, not a collection of iframes, plus explainable on-skin geometry derived from reviewed models.

| ID | Work | Dependencies | Evidence/Done |
|---|---|---|---|
| R4-01 | Renderer+asset ADR comparing Open Anatomy Atlas and alternatives for deep tissues, rights, FPS/RSS, 1366x768 | R1-08,R3 | Written choice and real-model evidence; no mock human silhouette |
| R4-02 | Single canvas anatomy layers, region tree, isolate/focus, X-ray, clipping if available, synced camera/inspector | R4-01 | Select neck/shoulder vs other regions; true deep muscle assets where present |
| R4-03 | Model registry: hash, pose, units, transforms, handedness, landmarks, skin mesh, source/rights | R4-01 | Reject missing/ambiguous frame; round-trip transforms |
| R4-04 | BVH/nearest-triangle + constrained raycast surface anchors, barycentric persistence and mesh-change invalidation | R4-03 | SR-01..03; actual measured errors, bad mirror/scale failures |
| R4-05 | Meridian path baking with topology/region checks, gaps/warnings, occlusion correctness, multi-camera reviews | R4-04 | SR-04..08; no hidden invented continuity through body |
| R4-06 | Comparison adapters for at least two meaningful source placements; `NOT_COMPARABLE` where frame registration absent | R4-03,R4-05 | SR-09..10 and cross-source diff; evidence hash |
| R4-07 | Point inspector linking claims/ontology/book provenance, uncertainty and alternate placements without blending conflicts | R4-05,R3 | Click anatomy → point → source original (when rights allow) |
| R4-08 | Target-device performance optimization (LOD, progressive region loading, baked caches) | R4-02,R4-05 | Real CPU/browser/WSL/GPU-visible measurements; no invented FPS |

**Gate:** ATLAS-01..04. **Negative:** uncalibrated mm input, topology change, left/right swap, missing skin, occlusion, wrong region selection, corrupt GLB, license-blocked mesh, out-of-RAM cancellation. **Rollback:** feature flags and last known valid model/anchor cache.

## R5 — Private Acupoint, Meridian and Diện Chẩn Studio

**Goal:** researchers can author, inspect, compare and export their own point systems while preserving original evidence.

| ID | Work | Dependencies | Evidence/Done |
|---|---|---|---|
| R5-01 | Versioned canonical concept + source placement + private atlas records, per-tradition namespaces | R4-03,R3 | No collision between FMA/anatomy/TCM/Diện Chẩn/Thai Sen IDs |
| R5-02 | Point/curve create/move/delete, constraints and notes, undo/redo, draft autosave with recovery | R5-01,R4-05 | Reload exact anchors and full edit lineage; upstream unchanged |
| R5-03 | Two-dimensional front/profile image atlas editing, pixel coordinates and image SHA; 2D→3D not implicit | R5-01 | Synthetic Diện Chẩn example export/reimport, correct image anchors |
| R5-04 | Separate fixed educational references from session-specific reactive/observed points (synthetic only) | R5-01 | No promotion of one observed point to universal standard |
| R5-05 | Versioned JSON schema, import/export, diff, review and unsupported-license block | R5-02,R5-03 | Round-trip, invalid point/mesh/source rejected |

**Gate:** ATLAS-05..06. **Negative:** bad barycentric weights, unknown base mesh, editing upstream checkout, 2D mislabeled 3D, leaking private atlas to published API. **Rollback:** versioned revision log, source files untouched.

## R6 — Therapy Delivery, Interoperability and Full-System Review

**Goal:** Therapy OS can consume reviewed Lab research safely without owning Lab internals or needing Lab online.

| ID | Work | Dependencies | Evidence/Done |
|---|---|---|---|
| R6-01 | Lock `/api/v1` schema, allowlisted published-only source/point/meridian/claim endpoints, explicit field-level privacy and rights filters | R3,R5 | Contract tests; no raw book or repo-process API exposure |
| R6-02 | Build immutable, rights-filtered offline packages with hash manifest, snapshot/source IDs, version and import validator | R3 | Corrupt hash and unapproved content rejected |
| R6-03 | Build standalone consumer proof (Python/curl), Lab online/offline fallback; Therapy repository untouched during first validation | R6-01,R6-02 | Auth/404/revocation/cached package tests; exact IDs verified |
| R6-04 | With explicit separate approval only, integrate read-only click-to-research in Therapy UI; never share DB or patient records | R6-03 | Source-linked point opens; Lab-offline safe state |
| R6-05 | Full regression G1–G10 + SEC + ATLAS-01..06 + BRIDGE-01..03; backup/restore & incident drills | R6-01..04 | Final validation report; blocker disclosure; owner signoff |

**Gate:** BRIDGE-01..03 plus all earlier gates on actual target device. **Negative:** missing token, permission revocation, copyright-restricted excerpt, wrong API version, corrupted offline package, Lab process dead, contradictory/unreviewed claim hidden, Therapy patient-data crossover.

## Required cross-cutting threads

- **Licensing:** each candidate has separate source-code, model/data and imported-document rights. AGPL and missing upstream license approvals are release blockers for source reuse, not for inert private study of metadata.
- **Geometry epistemics:** no `faceIndex` reused on a different mesh; no fake millimeter differences across unaligned frames; geometric PASS != clinical validation.
- **Agent operations:** optional five *logical* roles (Scout, Security, Runner, Comparator, Auditor), run sequentially by one coding agent if needed. Independent verification requires distinct evidence/checks, not merely an agent saying it audited itself.
- **UI usability:** actual screenshot with interactions; `localhost:8091` UI must be usable on real Windows browser, 1366x768.
- **Source preservation:** all four original specs remain retained, hash-pinned and compared through `TRACEABILITY/SOURCE_RECONCILIATION.md`.
- **Failure recovery:** every mutating workflow has idempotency or journal/recovery and its own negative test.

## Completion reporting rules

Every release report must include gate-by-gate `PASS`, `FAIL`, `BLOCKED`, `INCONCLUSIVE`, `NOT_TESTED`, original evidence paths, actual test command exits and a next-step plan. **Do not** report 100% unless the complete known test denominator is displayed and all required cases actually ran. Do not promise unattended/background progress after the current agent execution stops.
