# MSK Research Lab OS — v3.1 Discovery & Research Pipeline Roadmap Addendum

**Date:** 2026-10-23  
**Status:** Proposed amendment, **not implemented and not verified**.  
**Primary system:** Standalone MSK Research Lab OS, Windows 10 + WSL2, 8 GiB RAM, integrated Intel HD 5500.  
**Authoritative baseline:** `1docs/MSK_Research_Lab_OS_MASTER_SPEC_v3.0.md`, `1docs/MSK_Research_Lab_OS_ROADMAP_R0_R6.md`, release gates, and the audited current repository.  
**Progress correction:** `MSK_Research_Lab_OS_Progress_Rebaseline_2026-10-23.md`. Existing source has repo catalog, manually registered URL, static inspector and guarded cloner; the source snapshot does **not** establish implemented Markdown-import discovery, live GitHub search, systematic source-analysis reports or integrated REA. Prior R0–R6 PASS claims are not independently established.

## 1. Decision and roadmap placement

**Do not replace R0–R6.** Add **R1D (Repository Discovery & Research Pipeline)** as an incremental capability inside the R1 product area, plus optional **R1R (Advanced Reverse-Engineering Adapter)**. Their implementation may proceed after deterministic clean-run fixes, but neither waives the original R1 **G2 secure three-repository live-run requirement**. Atlas work and Therapy integration remain distinct.

**Human workflow:** Add/search GitHub repositories or import a local `.md` reference list → normalize/deduplicate → collect factual metadata → prioritize and compare candidates → explicitly approve a SHA-pinned clone → inspect source/dependencies/licenses → propose an experiment → explicitly approve execution only in an evaluated sandbox → capture evidence → record `ADOPT / ADAPT / REJECT / DEFER` with justification → publish reviewed, rights-cleared research *metadata* to the Lab Knowledge system. A Markdown document is a **source artifact**, never an executable instruction or an implicit approval.

### Adjusted execution order

| Order | Work package | Existing/new | Exit proof |
|---|---|---|---|
| **P0-A** | Reconcile code, specs, handoff and release statuses; retain prior evidence without claiming unverified PASS | Existing blocker | Honest gate matrix with evidence links |
| **P0-B** | Fix clean-install migrations and deterministic test fixtures/seed isolation; rerun full tests | Existing blocker | Repeatable tests with counts/exits from fresh DB |
| **P0-C** | Inspect security isolation and runnable environments on the actual WSL host; keep unreviewed execution blocked | Existing blocker | Capability matrix, negative tests and explicit `SANDBOX_UNAVAILABLE` if necessary |
| **P1 / R1D** | Markdown repo-list import; live GitHub discovery; candidate registry; static analysis; research queue; evidence reports | **New priority** | DISC-01..04 and REV-01 PASS |
| **P2 / R1R** | Optional REA MCP/CLI adapter for **authorized** opaque web/Electron/binary investigations | New optional capability | REV-02 PASS only when installed, configured and consented; `OPTIONAL_UNAVAILABLE` otherwise |
| **P2 / original R1** | Three approved upstream applications: SHA-pinned clone, isolated install/run, browser-interact, clean stop | Existing blocked gate | G2 + SEC tests, real screenshots/logs |
| **P3 / original R2–R3** | Reverify ten originals, exact citations, Tri-Ledger, published snapshots and rollback; ingest discovery findings as source records | Existing unverified gates | G3–G10 tests and negative cases |
| **P4 / original R4–R5** | Replace schematic Canvas 2D Atlas with real rights-verified 3D mesh and WebGL; complete custom studio E2E | Existing incomplete gates | ATLAS-01..06 with real browser interactions |
| **P5 / original R6** | Validate Therapy API and offline packages with proper source rights, auth and published-only rules | Existing partial gate | BRIDGE-01..03 and full regression |

**Scope of first coding-agent session:** P0-A/P0-B then DISC-01 as a verified vertical slice. Do **not** skip straight to optional REA or claim G2 PASS without a sandbox and real live runs.

## 2. R1D functional requirements

### DISC-01: Local Markdown Import

- Import explicitly selected `.md` or `.markdown` from an **allowlisted** local reference folder, e.g. `research/references/` (never recursively scan arbitrary host folders without consent). Provide both UI file picker and CLI; support one local fixture in CI.
- Parse ordinary Markdown links (`[label](https://github.com/owner/repo)`), plain repository URLs, and Markdown table cells; tolerate query strings such as `?utm_source=...` by stripping tracking components after URL validation. Do not follow arbitrary redirects, execute fenced code, or obey instructions embedded in the Markdown.
- Validate canonical GitHub repository root (`https://github.com/{owner}/{repo}`), explicitly reject `file://`, credentials in URLs, GitHub lookalike hosts, unrelated paths, embedded shell syntax, path traversal and invalid owner/repo. Extend and test `repos/inspector.py` as needed rather than implementing a separate inconsistent validator.
- Deduplicate by canonical owner/repo while **preserving source occurrences**: original file SHA-256, original local path alias, line number/Markdown position, link label, surrounding note, import timestamp. Multiple markdown files referring to the same repo yield one candidate plus multiple provenance references.
- Register only as `DISCOVERED_UNVERIFIED`; importing a list must **not** clone, install or launch anything.

### DISC-02: GitHub Intelligent Discovery

- Search by keyword, topic and language using documented public GitHub APIs or a provider adapter, after explicit operator action. Display repo URL, description, primary language, last update, license signals, approximate size and archived status with source/fetched-at timestamps; distinguish `UNKNOWN` from `NONE`.
- Support optional GitHub token through an environment/config secret outside Git; handle no token, offline, HTTP 403/429, provider outages, pagination, user cancellation and limited 8 GiB resources. Cache metadata with TTL and stale flags, without inventing results.
- Combine manual Markdown candidates and API results in a searchable dashboard; **never** rank popularity as correctness or medical validity. Scores, if shown, are transparent heuristics with input fields and unknown-value penalties.

### DISC-03: Research Queue and Lifecycle

- Allow multi-select candidates, tags, priority, research questions and per-item assignments. Persist queue and job state across restart. Limit heavyweight jobs to one at a time.
- Proposed transitions: `DISCOVERED_UNVERIFIED` → `METADATA_INSPECTED` → `RESEARCH_QUEUED` → `STATIC_ANALYZED` → `CLONE_APPROVAL_PENDING` → `CLONED_PINNED` → `RUN_APPROVAL_PENDING` → `SANDBOX_VERIFIED_RUN` → `EVALUATED` → human `ADOPT/ADAPT/REJECT/DEFER`. A repo may stay `BLOCKED`, `UNSUPPORTED`, `INCONCLUSIVE` or `REVIEW_REQUIRED` at any gate.
- Keep **clone approval distinct from install and run approval**. Pin full commit; check dirty state, submodules/LFS/install scripts and code/asset/data license separately. If sandbox is unavailable, still allow *static inspection* (within safe read-only limits), but block untrusted execution; G2 remains BLOCKED.

### DISC-04: Search, Compare and Publish Research Findings

- Compare two or more candidate repo records by capabilities, stack, dependencies, source code paths, license uncertainties, estimated size, actual observed hardware costs and tested behaviors. Unknown or untested is never reported as PASS.
- Generate a source-anchored Markdown research report and machine-readable JSON with candidate ID, URL, pinned SHA (or `NOT_CLONED`), exact file and line locator when source inspected, dependency findings, evidence IDs/hashes, limitations, reusable ideas, integration decision state and reviewer identity/status.
- Save outputs under a dedicated reviewed reports directory, e.g. `research/reports/<repo-id>/<revision>/` with manifest/checksums. Submit eligible findings to the existing provenance/Tri-Ledger system as **unreviewed** source claims pending human review; never publish restricted content, GPL/AGPL source code, book pages or unlicensed 3D meshes merely because indexed.

## 3. Reverse Engineering workbench

### REV-01: Static Source Investigation (required)

- For an approved, pinned checkout, provide deterministic code map: languages, project entrypoints, `package.json`/`pyproject.toml`/requirements, imported modules, declared scripts, likely UI framework, 3D model formats, data sources, relevant test files and high-risk install hooks.
- An agent may write source-backed explanations of algorithms, but must cite the actual commit, source path and lines; speculation is labeled `HYPOTHESIS`. No automatic copying of external code into Lab core, and no reverse engineering is required when normal source inspection answers the question.
- Support operator notes and comparisons. Analysis of source files must not execute them.

### REV-02: Optional REA Adapter (conditional)

- REA (`morluto/rea`) is a **separate, optional tool**, not a mandatory runtime dependency. Only use it for authorized applications and techniques allowed by the operator's access rights and applicable law.
- Adapter should detect local installation, capability/provider and environment; show target, requested analysis, commands, data exposure and expected side effects; require explicit approval; run in controlled environment, redact secrets and bound resources/time.
- Preserve output hash, tool/provider versions and limitations; reject binary analysis when dependencies or rights are uncertain. Do not make `rea-agents setup` or arbitrary installs automatic, and do not require REA for DISC-01..04 or REV-01.

## 4. Data and API design (agent to formalize/migrate)

**Minimum persisted entities:** `repository_candidates`, `reference_documents`, `reference_occurrences`, `github_discovery_queries`, `candidate_snapshots`, `research_jobs`, `static_analysis_artifacts`, `research_decisions`, `research_report_manifests`. Reuse existing repository IDs/tables where possible; prefer additive migrations with foreign keys and unique indexes; document alternatives and avoid data loss.

**Suggested UI:** `Discover`, `Import Markdown`, `Candidate Registry`, `Research Queue`, `Static Analysis`, `Compare`, `Research Reports`, `Optional REA`. Never expose privileged launch/install controls to the read-only Therapy API.

**Proposed local-only API** (not yet implemented; agent must update OpenAPI and auth):

```
POST /api/v1/discovery/import-markdown  # local operator mutation; CSRF/auth, safe upload/path
GET  /api/v1/discovery/candidates
POST /api/v1/discovery/github-search    # explicitly requested online discovery
POST /api/v1/research/jobs              # create bounded job
GET  /api/v1/research/jobs/{id}
GET  /api/v1/research/reports/{id}
POST /api/v1/research/decisions         # requires explicit operator review
```

**CLI sketch:** `mskrl discovery import-md <file>`, `mskrl discovery search-github <query>`, `mskrl research queue <repo-id>`, `mskrl research inspect-static <repo-id>`, `mskrl research report <repo-id>`. Agent must preserve existing CLI compatibility or supply an explicit migration.

## 5. New measurable release gates

| Gate | Positive proof | Required negative proof |
|---|---|---|
| **DISC-01** | Import a fixture MD with table, inline links and plain URLs; preserve 1 canonical repo with multiple original-line references; restart persistence; no auto clone | Malicious URL, deceptive hostname, invalid path/symlink and oversized file rejected; no script executed |
| **DISC-02** | Keyword/topic/language search returns current, attributed API responses (or explicitly cached stale results); save candidate | Offline, 403/429, bad token, pagination and empty query handled without fabricated repos |
| **DISC-03** | Select and queue candidates, approve one pinned clone, inspect static content; report persistence on restart | Duplicate queue, dirty checkout, unknown license, denied approval, sandbox unavailable and failed clone have correct statuses |
| **DISC-04** | Compare 2 candidates and write 1 SHA-manifested MD + JSON report with actual locator and review state; transfer unreviewed finding to evidence registry | Tampered report and missing source locator cause verification failure; cannot publish as reviewed |
| **REV-01** | Actual pinned source-tree analysis cites commit, file and lines with reproducible findings | Source path traversal, absent file, unpinned commit and unexecuted claim rejected |
| **REV-02** | Optional REA analysis on approved demo, or marked `OPTIONAL_UNAVAILABLE` / `NOT_TESTED` | Unapproved target, arbitrary command, secret leakage, absent provider blocked |

**Release promotion:** R1D may be declared `PASS` only after DISC-01..04 + REV-01 pass in the target environment with real evidence. REV-02 is optional. Original **G2** and **SEC** remain independent and cannot be waived by R1D PASS.

## 6. Engineering safeguards and tests

- Trust boundary: imported Markdown, GitHub READMEs, cloned source, model files and REA outputs are **untrusted data**. Prevent prompt injection into coding-agent instructions. Never execute document text as a command.
- Local first: document archives, GitHub token and research notes stay private; no cloud upload by default. Querying GitHub uses the network only for the explicitly requested search/metadata and records that action.
- Rights: preserve per-code, per-asset and per-dataset license uncertainty; do not conflate repository's MIT license with included GLB/model rights.
- Memory: idle service target <500 MiB RSS; network reads bounded/paginated; only one heavy repo/3D job active. Show real host/WSL/browser measurements and actual hardware identifiers, not assumptions.
- Validation: pytest unit/integration, clean DB fixtures, Playwright/browser E2E including actual Windows browser evidence, security negative tests, hash manifest, git commit and complete command/exit logs. Missing Windows access is `BLOCKED`, not PASS.
- Preserve R0–R6 already implemented code; do not reset production DB, clobber upstream repos or modify MSK-Therapy-OS. Handle fixes with targeted migrations, versioned ADRs and rollback.

## 7. Exact first implementation slice

1. Read current source and report gaps, contradictions, tests and existing DB state. Update `NEXT_SESSION_HANDOFF.md` and the gate registry to reflect only reproducible evidence.
2. Make clean tests independent of a previously migrated/seeded production database; add deterministic fixture seed and re-run full suite with exact results.
3. Add the v3.1 addendum to `1docs/`, amend the authoritative v3.0 Master Spec, R0–R6 roadmap, machine-readable task backlog and release-gates configuration without weakening existing requirements.
4. Implement **DISC-01 end to end**: parser/importer + storage/provenance + CLI/UI + security negative tests + persistence + original MD line-link resolution. Demonstrate using a small synthetic Markdown file in a real browser and CLI.
5. Implement DISC-02, DISC-03, DISC-04 and REV-01 sequentially. Each must have test artifacts and explicit lifecycle states. Defer REV-02 if prerequisites missing.
6. Reattempt original G2 only after sandbox capability is verified. Then continue current R2–R6 revalidation and real R4 WebGL/mesh remediation from the rebaseline report.

**Definition of done for this amendment:** Operator can hand the Lab a Markdown GitHub-repo shortlist, search for more candidates, safely evaluate and compare them, persist exactly sourced findings, and decide what to adapt; source code execution remains separately gated. All outputs and claims must be independently verifiable.
