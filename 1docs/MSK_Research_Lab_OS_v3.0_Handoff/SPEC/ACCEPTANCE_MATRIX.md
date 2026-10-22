# Binding Acceptance Matrix and Evidence Contract

**Status:** All gates `NOT_TESTED` on delivery of these design files. No implementation has been performed by this handoff.

## Gate-state vocabulary

`NOT_TESTED` (no executed test); `IN_PROGRESS` (not a verdict); `PASS` (real evidence for all positives and negatives); `FAIL` (observed violation); `BLOCKED` (unmet external prerequisite, e.g. sandbox or operator permission); `INCONCLUSIVE` (ambiguous measurement; do not treat as PASS). `SKIPPED` is separately counted, not PASS. A feature's existence, README claim or screenshot alone cannot establish PASS.

## Legacy baseline: preserve G1–G10 and SEC

| Gate | Release | Mandatory positive proof | Mandatory negative/failure proof | Minimum artifacts |
|---|---|---|---|---|
| G1 | R0 | Real Windows browser accesses WSL backend; health/doctor, restart, usable at 1366x768 | Port clash, bad/missing runtime, responsive overflow, non-loopback binding refused | Environment fingerprint, browser screenshot, port logs |
| G2 | R1 | **3 distinct** real approved repos cloned, clicked/interacted with, stopped sequentially, exact full SHA | Approval denied, invalid profile, dirty repo, bad SHA, runaway child, timeout, socket cleanup | Per-repo clone/command logs, live screenshots, PID/port cleanup, approvals |
| G3 | R2 | **10 originals:** 4 PDFs (2 scanned/image-bearing), 3 EPUBs, 3 DOCXs, exact hashes and page/section accounting | Corrupt/malicious/oversized input, failed OCR, missing/blank page flagged | Content manifest, DB counts, original hashes, coverage reports |
| G4 | R2 | Exact source search opens correct original PDF page / EPUB spine-href / DOCX paragraph-table | Missing locator, invented EPUB pages, false OCR certainty or lost figure surfaces as warning | Real original viewer captures, search records, locator resolver tests |
| G5 | R2 | Source-linked note/experiment with ≥2 book refs + Git SHA; rights-aware export; token-protected standalone read-only **research-note** API | Anonymous/wrong token, forged citation, arbitrary private book extraction, unpublished point access | Export JSON/MD, API responses, independent client logs |
| G6 | R2 | Backup all relevant private originals, notes, indexes, refs; restore to new directory | Tampered/corrupt/incomplete backup rejected; interrupted restore leaves old state intact | Before/after hashes, restore logs, identical search/citation |
| G7 | R3 | Claim/Evidence/Contradiction ledgers; counter-evidence retained; revision and reviewed state transitions | Unreviewed evidence auto-promoted; missing source; counter-evidence deleted | Ledger audit, reviewer trail, rejected transitions |
| G8 | R3 | Two original sources/editions compared side by side with rights, ancestry and precise locators | Mismatched hash, fake JSON pointer, non-independent duplicate, unregistered geometry distance | Original viewer, comparison manifest, source SHA |
| G9 | R3 | Approved multilingual aliases and typed one-hop graph with source-backed edges | Unknown alias, invented anatomy equivalence, orphan edge, oversized graph request | Ontology version, graph audit, original source links |
| G10 | R3 | Stage→validate→publish→query→rollback immutable snapshots; old readers safe | Crash/corrupt index, missing rights, stale pointer, concurrent publisher | Release manifest, QA logs, old/new snapshot IDs, crash tests |
| SEC | R0–R6 | Loopback/auth/CSRF/CORS tests; proven isolation and resource policy; no real patient data | Shell/path traversal, unauthorized install/launch, forbidden mount, network escape, secret leakage | Actual sandbox config/negative logs, security checklist |

**Important v2/v2.1 reconciliation:** G5 is satisfied initially with a source-linked *research note* from the Lab's protected work area. Prepublication `/api/v1/knowledge/points/{code}` returns 404/`UNREVIEWED_NOT_PUBLISHED`; R3 G10 adds snapshots consumed by published-only knowledge endpoints. No clinical point record is automatically exposed to satisfy G5.

## New Unified Atlas + Bridge gates

| Gate | Release | Mandatory positive proof | Mandatory negative proof | Minimum artifacts |
|---|---|---|---|---|
| ATLAS-01 | R4 | Real licensed anatomy source, one canvas, multiple available tissue layers, structure selection/isolation, explicit missing-layer indicators | Fake silhouette/mock, unavailable layer silently invented, unlicensed asset | Model SHA/license, true browser images, inspector logs |
| ATLAS-02 | R4 | Points anchored to declared skin mesh with model/mesh SHA; path topology, normals and occlusion QA; front/back/left/right/oblique | Wrong units, mirror, topology, behind-skin markers, segment through body, absent skin | SR-01..08 results and numeric metrics, 6+ views |
| ATLAS-03 | R4 | Two separately sourced placements compared only after common-frame registration; missing data highlighted | Unregistered sources yield `NOT_COMPARABLE`, no fabricated mm | Transform + landmarks evidence or rejection |
| ATLAS-04 | R4 | Neck/shoulder region and selected inspector/camera/layers synchronized; usable 1366x768 | Hidden controls, stale selection, unexpected cross-body highlights, resource failure | Real UI interaction recording/screens and metrics |
| ATLAS-05 | R5 | Private custom points/path editor; undo/redo, save/reload, version, JSON import/export, original source never edited | Invalid placement, changed model SHA, editing upstream, unpublished private atlas leak | Synthetic atlas roundtrip + diff + logs |
| ATLAS-06 | R5 | Front/profile image-based Diện Chẩn annotation with pixel locators and fixed vs reactive distinction | Automatic 2D→3D validation, patient data, reactive point promoted globally | Image hashes, saved annotated fixture, review assertions |
| BRIDGE-01 | R6 | Separate consumer reads reviewed, rights-allowed point/meridian with citations, contradiction and snapshot ID, proper bearer auth | Unauthorized/wrong-version/unreviewed source blocked | Consumer/API contract tests, responses, snapshot hash |
| BRIDGE-02 | R6 | Lab off; Therapy client retrieves approved previously exported package, validates integrity | Tampered package, stale or unapproved version blocked/marked | Offline demo, package sha manifest |
| BRIDGE-03 | R6 | Forbidden records and assets excluded, patient boundary preserved, no private DB access or process APIs | API attempt for copyrighted full book, launch command, original file, patient data rejected | Field-level security and rights redaction tests |

## Surface-registration-v1 test IDs (R1 harness, R4 true integration)

`SR-01`: units, axes and frame registration. `SR-02`: snap/project to declared exterior skin. `SR-03`: stable barycentric anchoring. `SR-04`: surface path gaps and self-crossing/penetration checks. `SR-05`: laterality and mirroring. `SR-06`: region filtering and correct selection. `SR-07`: occlusion and six-view QA. `SR-08`: NaN, bad units/rotation/out-of-bounds. `SR-09`: peak WSL/backend/browser/GPU-observable resource measurement. `SR-10`: repeatability on three clean fixture runs (when comparable). Thresholds set by versioned fixture, not clinical rules. A repo may report `UNSUPPORTED`, and unsupported cases are never silently scored as passed.

## Evidence bundle structure

```text
evidence/<release-id>/<run-id>/
  source.json                 # full upstream revision, data/model rights
  environment.json            # actual device, WSL/kernel, browser/WebGL details
  commands.json               # redacted argv, cwd, exit codes, timestamps
  stdout.log
  stderr.log
  test-results.json           # every test ID/state; skipped counted
  metrics.json                # units, methods, gaps, comparability
  captures/                   # actual running app, URL and viewport metadata
  artifacts/                  # source-anchored excerpts or synthetic fixtures
  approval-events.json
  audit-report.json           # distinct validation method/reviewer
  sha256-manifest.json        # all finalized artifacts, deterministic verification
```

**Evidence validation:** no generated placeholder logs or images; hash tampering must invalidate an earlier verdict; raw evidence retained with immutable run ID. Clinical reviewers, where later required, are humans and cannot be simulated by role-playing an AI.

## Whole-project acceptance

R0–R6 and all G1–G10 + SEC + ATLAS-01..06 + BRIDGE-01..03 must PASS with original source evidence and release-owner acknowledgment. A milestone can PASS while later milestones remain `NOT_STARTED`; no global `COMPLETE` until the full matrix passes.
