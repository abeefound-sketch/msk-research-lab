# MSK Research Lab OS — Master Product & Engineering Specification v3.0

**Document ID:** MRL-MASTER-003  
**Version:** 3.0.0 | **Status:** IMPLEMENTATION CONTRACT; NOT IMPLEMENTED OR VERIFIED  
**Date:** 2026-10-23 | **Language:** English  
**Product:** An independent local-first research workbench, not a new operating system  
**Flagship product:** Unified Acupuncture & Meridian Atlas  
**Reference hardware:** Windows 10 + Ubuntu WSL2, Intel i7-5600U, 8 GiB physical RAM, Intel HD 5500, approximately 238 GiB SSD  
**Users:** One authorized local researcher initially; no real patient data  
**Downstream consumer:** MSK-Therapy-OS, independently deployable and independently owned

> **Contract of truth:** A function is DONE only when its complete user journey works on the actual target machine, source/evidence artifacts are reproducible, negative cases pass, and its release gate is independently reviewed. Passing unit tests, producing a design, cloning an upstream repository, or displaying a plausible screenshot is not equivalent to completion.

## 1. Product definition and success criteria

MSK Research Lab OS is one coherent research product with two distinct experiences:

1. **Research Workbench:** discover, register, inspect, securely clone, evaluate, launch, stop, benchmark, compare, review, and archive open-source repositories and imported user documents.
2. **Unified Atlas:** use a single interactive 3D anatomical viewer to study anatomy, source-attributed acupoints and meridians; author private research maps (including Diện Chẩn 2D diagrams); and open original textual/visual evidence from the same UI.

Research findings are not automatically published as facts. The **Knowledge Integrity System** records claims, evidence, counter-evidence, edition/provenance, ontology mappings, human reviews, and validated immutable releases. Reviewed and rights-permitted knowledge is made available to MSK-Therapy-OS through a read-only API **and** an offline signed/hashed manifest package. A functioning Therapy OS must not depend on Research Lab being online.

### Measurable product outcomes

| ID | Outcome | Proof |
|---|---|---|
| PO-01 | Operator can run Lab from a Windows browser with WSL backend | Actual Windows browser interaction + process logs |
| PO-02 | Operator can safely inspect, approve, launch, interact with and stop three different upstream applications, sequentially | SHA-pinned launches, real UI images, process cleanup, security evidence |
| PO-03 | Operator can import/search/inspect 4 PDFs (2 scans), 3 EPUBs and 3 DOCXs | Exact source locations, image-gap report, OCR uncertainty, checksums |
| PO-04 | Operator can create/review claims and contradictions and compare original sources | Auditable Tri-Ledger + source resolver + negative promotion checks |
| PO-05 | Operator can search controlled multilingual aliases and browse evidence-linked graph | Deterministic concept IDs, provenance on graph edges |
| PO-06 | Operator can publish and roll back immutable knowledge snapshots | Atomic publication and crash/recovery tests |
| PO-07 | Operator can inspect actual anatomy with meaningful deep-layer controls | True anatomy assets, structure selection, source/asset license evidence |
| PO-08 | Operator can explore points/path overlays on a designated skin mesh | Surface QA metrics, camera/occlusion regressions, unregistered cases clearly labeled |
| PO-09 | Operator can create and revise private research atlases and 2D face-map annotations | Undo/redo, version history, save/reload, export/import |
| PO-10 | Therapy OS can access only approved, permissible research without DB/process coupling | Authenticated client + offline package verification + forbidden-content tests |

### Non-goals and absolute exclusions

- Not a new OS, monolithic merger of all upstream source trees, universal repository launcher, Git host or AI framework.
- Not a medical device, a patient EHR, clinical decision-support system, automated diagnostic or treatment-recommendation service.
- No instructions for invasive needle placement/depth, electrical DDS stimulation settings, individualized medical intervention or patient-specific therapeutic protocols.
- No real patient records, facial photographs, identification, clinical case histories, or medical notes in Lab v3 releases. Use labeled synthetic educational fixtures.
- No assertion that meridians, Diện Chẩn points, Thai Sen lines or trigger points are identified physiological nerves or vessels.
- No assumption that a mesh-surface projection validates acupoint anatomy or treatment efficacy.
- No cloud-first services, mandatory LLM/API keys, mandatory vector database, heavy GPU, always-running agents or bulk copyrighted content redistribution.
- No requirement that all nine candidate repos are runnable, installed or integrated; nine are catalogued, selected candidates are investigated, and at least three independent real apps must pass the R1 demo gate.

## 2. Authoritative document hierarchy and conflict policy

1. This **MASTER_SPEC_v3.0.md** is the normative product boundary and milestone allocation.
2. `ROADMAP_R0_R6.md`, `ACCEPTANCE_MATRIX.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`, `ATLAS_GEOMETRY.md`, `KNOWLEDGE_LIBRARY.md`, `KNOWLEDGE_INTEGRITY.md`, `API_CONTRACT.md`, `SECURITY_AND_RIGHTS.md`, and `RESOURCE_BUDGET.md` provide binding technical detail within their specific topics.
3. `CONFIG/` and `SCHEMAS/` are **proposed contracts and seed metadata**, not verified deployed settings or granted permissions.
4. `AGENT/AGENTS.md` controls agent execution/reporting. `AGENT/SESSION_00_PROMPT.md` authorizes **R0 only**, not every future milestone.
5. Original four specs under `REFERENCES/` are preserved unmodified as decision sources; conflicts are recorded in `TRACEABILITY/SOURCE_RECONCILIATION.md`. They do not silently override this v3 contract.

All changes to release gates require an explicit versioned amendment and recorded human approval. A coding agent may not weaken a gate, hide unsupported cases, or replace missing evidence with generated text.

## 3. Baseline hardware and design constraints

- Backend Python 3.11+ under WSL; Windows browser UI; loopback-only by default.
- SQLite WAL, FK enforcement, schema migrations, FTS5; exact local original-document storage.
- Minimal served HTML/CSS/vanilla JS for Lab controls. The **Unified Atlas** may use a single pinned Three.js/WebGL canvas; do not mount multiple upstream 3D UIs as a permanent product.
- Use one heavyweight job at a time (upstream 3D, OCR, asset conversion, BVH bake). Queue and cancel jobs. Avoid background daemons for optional workers.
- Target Lab backend idle RSS < ~500 MiB; measure rather than promise. No blanket 60 FPS target without device evidence. Budget, timeouts and monitoring are specified in `RESOURCE_BUDGET.md`.
- Rootless Podman or equivalently verified sandbox is preferred for untrusted execution. WSL and `subprocess(shell=False)` are **not** security sandboxes. If enforceable isolation is absent, inspect only and report R1 `BLOCKED`, not a synthetic PASS.
- Never assume that model meshes share unit, pose, topology, coordinate frame, handedness, landmark conventions, or rights status.

## 4. Product subsystem contracts

### P-REPO: Repository Lab

**Functions:** arbitrary GitHub URL registration; duplicate detection; source registry by full SHA; metadata/size/dependency/rights inspection; clone/update preview; explicit approval of install/run profiles; actual process lifecycle; bounded stdout/stderr; actual browser interaction; snapshot and evidence capture; reproducible benchmark; auditable KEEP/ADAPT/DEFER/REJECT decisions.

**Invariants:** registration != clone != install != execution != approval; no arbitrary README commands executed; clones gitignored and separate; no uncontrolled auto-update; dirty checkouts preserved; child processes and ports cleaned; execution denied without validated containment and reviewed argv/writable paths/network plan. Exact rules in `SECURITY_AND_RIGHTS.md`.

**Research inventory:** nine candidate repos from the source design, plus `three-mesh-bvh` as a package and REA as optional tooling. See `CONFIG/repo_catalog.json`, not hard-coded claims about live compatibility. Three real apps demonstrated by R1 and a four-source `surface-registration-v1` benchmark later when supported.

### P-LIB: Private document research library

**Inputs:** PDF, EPUB, DOCX from authorized local files; preserve original bytes and SHA-256. Text, tables and figures are distinct evidence types; do not equate OCR coverage with understanding diagrams.

**Source location rules:** PDF 1-based page + optional normalized region; EPUB spine index + href/fragment; DOCX paragraph/table index + structural heading path; repo file locator requires full SHA/path/line or JSON pointer. Every source citation must open the actual original location, with explicit `UNRESOLVED` on failure. Imported files never become LLM instructions.

**MVP:** 10-document acceptance fixture (4 PDFs including >=2 scanned/image-bearing, 3 EPUB, 3 DOCX); per-page coverage/visual flags; local opt-in Tesseract OCR; SQLite FTS5 + reviewed aliases; source viewer, bookmark, copy citation, notebook. Embeddings/RAG may be proposed after offline deterministic search proves useful; not a release dependency.

### P-EVIDENCE: Research integrity and audit

Three independent records: **Claim**, **Evidence**, **Contradiction**; revision lineage, reviewer attribution and exact provenance. `SOURCE_SUPPORTED` means accurate sourced attribution, **not clinically proven**. No automated promotion to supported status; negative evidence stays visible. Separate independent sources from copied translations or derived repositories. All graph edges must be typed and source-backed or clearly marked candidate. Details in `KNOWLEDGE_INTEGRITY.md`.

### P-ATLAS: Unified anatomy/meridian canvas

**User experience:** select body region/system and anatomy structures, isolate superficial/deep tissues, inspect source identity, select one meridian or point group, see occlusion-correct overlays, open source-linked descriptions beside geometry. Avoid showing every meridian and label by default. Support front/back/left/right/oblique views, correct selection and responsive 1366x768 controls.

**Geometry:** explicit model/pose/frame/mesh+asset SHA, canonical point identity separate from source placements, versioned surface anchors `(mesh_sha, face_index, barycentric)`, constrained projection, no line penetration/false continuity, ability to say `NOT_COMPARABLE`. A shared code like GB21 is never proof that two XYZ values are comparable. Geometry thresholds are fixture-specific and non-clinical; see `ATLAS_GEOMETRY.md`.

**Sources:** first evaluate Open Anatomy Atlas as candidate renderer; JICio for skin path/point baking; Meridian Studio for editor behavior; WaterCMY and tcm-acupoints for comparative algorithms; TARA for proposed ontology; Meridian Atlas and chino-meds for sourced learning content. Reuse code only after rights and technical review; no forced integration of AGPL or unlicensed assets.

### P-EDITOR: Private atlas authoring

Support custom named point sets and line paths, source-specific placement, model/mesh or image anchors, undo/redo, revision history, import/export JSON, independent namespaces for traditional acupuncture, Diện Chẩn, Thai Sen and manual therapy. Provide two-dimensional facial chart annotations with **image-pixel coordinates** (front/profile). Never silently project 2D diagrams onto 3D bodies as clinically established coordinates. Distinguish reference points from time-specific observed/reactive points (synthetic only in v3).

### P-PUBLISH: Knowledge snapshot publisher

Working Lab SQLite and immutable originals are separate from published read-only research snapshots. Build staging snapshot → integrity/rights/evidence QA → human review → atomic activation of immutable release pointer → rollback to prior validated release; no implicit auto-publication after book import or ontology edit. Therapy consumers may see only the active, reviewed, rights-allowed content. R3 delivers verified snapshots. See `KNOWLEDGE_INTEGRITY.md` and `API_CONTRACT.md`.

### P-BRIDGE: MSK-Therapy-OS interoperability

Research Lab and Therapy OS keep separate repositories, databases, runtime and legal/privacy responsibility. An authenticated read-only HTTP interface offers **approved data only**. Offline package exports include schema version, exact source/revision, evidence IDs, rights, source locators, snapshot ID, hashes and export review. No full copyrighted book by default, no private files/directories, no patient records. R6 verifies a separate consumer and safe behavior if Lab is offline. Do not modify Therapy OS prior to separately approved R6 integration work.

## 5. Research and clinical epistemic boundaries

Use qualified namespaces: `SOMATIC_ANATOMY`, `TRADITIONAL_ACUPUNCTURE`, `TRADITIONAL_DIEN_CHAN`, `TRADITIONAL_THAI_SEN`, `MANUAL_THERAPY`, `BIOMECHANICS`, `DEVICE_TECHNOLOGY`, `SOFTWARE_ENGINEERING`. Extend by migration, not by mixing meaning.

Use claim kinds: `SOURCE_DESCRIPTION`, `ANATOMICAL_FACT`, `TRADITIONAL_THEORY`, `HYPOTHESIS`, `GEOMETRIC_ASSERTION`, `INTERVENTION_EFFECT`, `TECHNICAL_FINDING`. Distinguish peer-reviewed evidence, guidelines, traditional primary texts, software claims, translations, and personal research notes. Classification is metadata, not an effectiveness rating.

Never infer treatment benefit from a scanned traditional text, from number of sources or repo stars, or from point-on-surface placement. The platform supports transparent research/education, not unsupervised clinical decisions. Any future clinical review has a **separate professionally governed release gate** outside v3.

## 6. Release model and no-fake-PASS rule

**R0** Foundation → **R1** Repo Research Lab → **R2** Document Library and notebook → **R3** Research Integrity/Publication → **R4** Unified 3D Atlas → **R5** Atlas Studio → **R6** Delivery Bridge. Each is shippable separately. R4 should be prototyped as a *vertical slice* during R1/R2, without prematurely claiming R4 PASS.

Existing v2 and v2.1 gates are **preserved in full**: G1–G6, G7–G10 and SEC. Additional: ATLAS-01..06, BRIDGE-01..03. Every gate requires observed positive+negative tests; environmental limitations yield `BLOCKED`; code present but no demonstration yields `NOT_VERIFIED`. R3 may PASS with Atlas incomplete; the **whole v3 product** may PASS only after R0–R6 gates are PASS on the target machine.

See binding `ROADMAP_R0_R6.md`, `ACCEPTANCE_MATRIX.md`, `TESTS/TEST_DATA_CONTRACT.md` and `AGENT/MILESTONE_REPORT_TEMPLATE.md`.

## 7. Key decisions and intentionally unresolved research

- **One UI, not one upstream source tree.** Upstream checkouts stay isolated; Lab-owned adapters normalize only reviewed functions and data.
- **No automatic repo deployment.** Any proposed command or third-party script is untrusted until reviewed and executed under enforceable restrictions.
- **No absolute acupoint XYZ truth.** Concept ID, placement, geometry and clinical status are separate records.
- **No default source-content exfiltration.** Local books are private; API defaults to authorized bibliographic metadata and permissible reviewed snippets.
- **No forced cloud AI or REA integration.** Both optional after objective need is shown.
- **No unconditional adoption of a primary viewer.** Open Anatomy Atlas is first candidate, acceptance is based on actual model, licensing, selection/layer fidelity, frame-rate and memory measurements.
- **No unidentified future workflow.** Real patients, personalized intervention, shared accounts and public hosted service require new spec, legal controls and qualified review.

## 8. Mandatory handoff and delivery evidence

At every release the coding agent must provide Lab commit SHA, unmodified upstream SHAs, exact executed commands/exit codes, dependency versions, SQLite migration evidence, automated tests, real Windows browser interactions/screenshots, positive and negative cases, memory/disk observations, security+rights status, limits/blocked cases, rollback procedure and the next-session handoff. A screenshot is evidence of visible behavior only, never clinical accuracy or sandbox enforcement by itself.

**Final full-product DoD:** G1–G10 + SEC + ATLAS-01..06 + BRIDGE-01..03 **all PASS**, and recorded owner acceptance. If anything remains `BLOCKED`, `FAIL`, `INCONCLUSIVE` or `NOT_VERIFIED`, do not declare the full project complete.

## 9. Reading order for the implementing agent

`00_START_HERE.md` → `AGENT/AGENTS.md` → this Master Spec → `SPEC/ROADMAP_R0_R6.md` → the specific release technical docs → `SPEC/ACCEPTANCE_MATRIX.md` → `AGENT/SESSION_00_PROMPT.md`. Source specs are evidence and history, not substitute for this unified contract.
