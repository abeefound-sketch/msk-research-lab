# Future Release Session Prompts — R1 through R6

**Not automatically authorized.** This file is a planning aid for subsequent coding sessions. Each release needs an explicit new user instruction after its prerequisites are verified. Proposed code or a saved prompt cannot approve installing/executing third-party repositories, changing OS security configuration, publishing knowledge, or modifying MSK-Therapy-OS.

## R1 Session — Safe Repository Lab and Live Comparison

> Implement **R1 only** according to `SPEC/ROADMAP_R0_R6.md`, `SPEC/SECURITY_AND_RIGHTS.md`, `SPEC/ACCEPTANCE_MATRIX.md` G2/SEC and `CONFIG/task_backlog.json`. First verify R0 artifacts and sandbox containment *on the actual host*. Import the untrusted nine-repo catalog without auto-cloning/installing. Implement inspected SHA-pinned clones, separate approval gates, disabled-until-reviewed argv profiles, verified sandbox execution, start/stop/logs/browser tests. Run three distinct real approved apps **sequentially** only after explicit operator permissions for each materially different install/run profile. Create the `surface-registration-v1` harness and an early single-model Atlas technical spike without claiming R4 PASS. Save complete evidence, negative isolation tests and resource measures. Stop at R1, report any blocked prerequisite honestly, hand off R2.

## R2 Session — Research Library and Recovery

> Implement **R2 only**. Verify R0/R1 regression. Build SHA-immutable PDF/EPUB/DOCX originals store with exact locations and original viewer, opt-in local per-page OCR, visual gap accounting, FTS5, source-linked notes/experiments and a narrowly scoped authenticated research-note read API. Create/test 4 PDFs including two scans, three EPUB, three DOCX **synthetic fixtures**. Confirm G3–G6 and negative malformed/rights/restore cases. Point knowledge endpoint must still return 404 while unpublished; do not expose private full books to Therapy. Back up/restore to a fresh directory, document actual evidence and stop after R2.

## R3 Session — Provenance, Tri-Ledger, Ontology, Snapshot Publisher

> Implement **R3 only**. Verify R0–R2. Add exact source provenance/edition/relation registry, Claim/Evidence/Contradiction with immutable revision events and human review gates, side-by-side original comparisons, controlled multilingual namespaced ontology, evidence-linked bounded typed graph, staged immutable SQLite release publisher with atomic pointer/rollback and rights QA. Keep draft data separate from the published-only API. Test G7–G10, failure cases (source hash changed, false claim promotion, non-independent mirrors, corrupt graph/snapshot, concurrent publication, crash rollback), and SEC. No agent self-promotion of clinical or content reviews. Produce real source-linked evidence and handoff.

## R4 Session — Unified Anatomy & Meridian Atlas

> Implement **R4 only** after R3 PASS. Choose one real rights-cleared anatomical viewer and mesh with evidence on the actual 8 GiB/Intel HD 5500 host; preserve an ADR. Implement one production WebGL canvas with truthful anatomical layers, region selection/isolate, occlusion-correct overlays; source model/pose/units/mesh SHA, frame-registration adapters, constrained BVH skin anchors and path baking. Run SR-01..SR-10, two-source comparison with `NOT_COMPARABLE` when unregistered, multiple-angle browser and resource evidence. Test ATLAS-01..04; no fabricated medical coordinate accuracy or alternate dummy anatomy. Stop after R4.

## R5 Session — Custom Atlas Studio and Diện Chẩn 2D

> Implement **R5 only**. Add private versioned point/meridian editors (move/add/delete, undo/redo, save/reload, import/export) and source-linked 2D front/profile face-map annotation with image SHA/pixel anchors. Preserve independent TCM, Diện Chẩn, Thai Sen and manual therapy namespaces; separate fixed educational atlas point from synthetic reactive/session observation. Keep original upstream checkouts immutable and unpublished drafts private. Validate ATLAS-05..06, negative corrupt topology/invalid image/rights and recovery tests, and produce real UI evidence. Stop after R5.

## R6 Session — Therapy Research Bridge and Whole-System Verification

> Implement **R6 only** after prior release gates actually PASS. Lock OpenAPI `/api/v1`, scope bearer-only read-only Therapy client to active immutable source-reviewed/right-approved knowledge, and implement hashed offline research packages with strict integrity/rights validation. First prove a **separate mock consumer** on Windows/WSL; verify Lab-offline fallback, token/CORS, revoked rights and tamper negatives. Only modify MSK-Therapy-OS after a **separate explicit owner approval** authorizing exact Therapy-side changes. Run whole-product regression G1–G10 + SEC + ATLAS-01..06 + BRIDGE-01..03 on the target host, include independent evidence and owner signoff. If any gate unverified/blocked, report partial product rather than full completion.

## Continuation rules

At the start of each session read prior `evidence/R*_report.md`, latest Git commit, source manifest and blockers; at end fill `AGENT/MILESTONE_REPORT_TEMPLATE.md` and `AGENT/SESSION_HANDOFF_TEMPLATE.md`. Never assume a past chat's summary substitutes for actual repository state. Don't run all release prompts in parallel or represent the current task as authorization for future work.
