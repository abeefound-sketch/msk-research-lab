# Coding Session Handoff & Completion Record — Candidate 2 Verified (2/3 Demos), Candidate 3 Approval Plan

**Project:** MSK Research Lab OS v3.1  
**Status:** **R0, R1 (Static), R1D, R2, R3, R4 (Authentic Models Ingested + Procedural Demo), R5, R6 VERIFIED (155 TESTS PASSING); G2 IN PROGRESS (2/3 DEMOS VERIFIED — CANDIDATE 1 & 2 VERIFIED; AWAITING CANDIDATE 3 APPROVAL)**  
**Target Platform:** Windows 10 / Ubuntu WSL2 (Intel HD 5500, 8 GiB RAM, 1366x768 Display)  
**Lab Repository Path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`) strictly on C: drive  
**MSK-Therapy-OS Status:** Untouched / Immutable at `/mnt/d/5Projects/msk-therapy-os` (Zero changes made to Therapy OS)  
**Total Automated Tests:** **155 passed, 0 failed** in 96.48 seconds  
**Database Schema Version:** v7 (Migrations 0001 through 0007 applied transactionally with WAL and Foreign Keys ON)  

---

## 1. Executive Summary & Release Gates State

| Release | Focus Area | Acceptance Gates | Verified Result | Evidence Manifest & Caveats |
|---|---|---|---|---|
| **R0** | Local Foundation & Diagnostics | **G1** | **PASS (VERIFIED)** | SQLite WAL, loopback port 8091 guard, doctor diagnostics. `2data/evidence/R0_report.md` |
| **R1 (Static)** | Repo Lab Static & Surface Benchmark | **G3, G4, SEC, SR-01..10** | **PASS (VERIFIED)** | Static AST analysis, license auditor, SR-01..10 registration benchmark 100% pass. `2data/evidence/R1_report.md` |
| **R1 (G2)** | Live Upstream Sandbox Run | **G2, SEC** | **IN PROGRESS (2/3 DEMOS VERIFIED)** | Bubblewrap rootless container sandbox with Unix domain stream socket bridge verified. Candidate 1 (`WaterCMY/anatomy-3d`) and Candidate 2 (`spacejohnlf/tcm-acupoints`) both executed under strict `--unshare-net`, HTTP 200 on all assets, WebGL rendered, low RSS (< 2 MB), screenshots captured at 1366x768, cleanly stopped. Candidate 3 awaiting operator execution approval. |
| **R1D** | Discovery & Research Pipeline | **DISC-01..04, REV-01..02** | **PASS (VERIFIED)** | Local MD import, live GitHub discovery, candidate queue, AST static analysis, reports. REA adapter is OPTIONAL_UNAVAILABLE. Real browser screenshots: `2data/evidence/R1D/run_r1d_discovery_001/dashboard_r1d_1366x768.png` |
| **R2** | Research Library & Disaster Recovery | **G5, G6** | **PASS (VERIFIED)** | Content-addressed originals (`2data/originals/`), FTS5 BM25 search, VACUUM INTO backup/restore. `2data/evidence/R2_report.md` |
| **R3** | Scholarly Tri-Ledger & Publisher | **G7, G8, G9, G10, SEC** | **PASS (VERIFIED)** | Tri-ledger (Claims, Evidence, Contradictions), ontology lookup, typed graph, snapshot publisher. `2data/evidence/R3_report.md` |
| **R4** | Unified Anatomy & Meridian Atlas | **ATLAS-01..06, SR-01..10** | **AUTHENTIC ASSETS INGESTED + PROCEDURAL DEMO** | Registered authentic BodyParts3D GLB model (`watercmy_bp3d_z_anatomy`, 9.29 MB) and Z-Anatomy mannequin (`spacejohnlf_z_anatomy`, 8.25 MB) with direct streaming endpoints. Retains calibrated 5-layer procedural benchmark demonstration with explicit epistemic disclaimers. 155 automated tests passing. |
| **R5** | Private Studio & 2D Diện Chẩn | **ATLAS-05, ATLAS-06** | **PASS (VERIFIED)** | Multi-tradition studio editor, transactional undo/redo, 2D Diện Chẩn maps, epistemic 2D->3D rejection. `2data/evidence/R5_report.md` |
| **R6** | Therapy Bridge & Offline Packages | **BRIDGE-01..03, SEC** | **PASS (VERIFIED)** | Scoped Bearer authentication, offline hashed research packages, mock consumer client, zero patient data boundary. `2data/evidence/R6_report.md` |

---

## 2. Candidate 1 Execution Record: `WaterCMY/anatomy-3d` (Demo 1 of 3)

- **Status:** **PASS (VERIFIED)**
- **Pinned Commit:** `e8d40dca7b1f63f54567395df21d8b1b38a7e840` | **Licenses:** MIT (code), CC BY-SA 2.1 Japan (model)
- **Execution Architecture:** Bubblewrap rootless container (`bwrap`) with `--unshare-all`, `--unshare-net`, `--unshare-pid`, `--tmpfs /tmp`, read-only rootfs binds, read-only `/app`.
- **Bridge Mechanism:** Unix stream socket `/bridge/app.sock` &rarr; host loopback `127.0.0.1:8092`.
- **Process Metrics:** Peak RSS = 1.89 MB, Peak VMS = 3.57 MB.
- **Screenshot (1366x768):** `2data/evidence/R1_G2/run_g2_candidate1_watercmy/candidate1_watercmy_default_1366x768.png` (SHA-256: `abd3d7fd109a3e7c6c75277378d5afddd22c6f4df3efd7c2fbde9645f28ab947`).
- **Sealed Report:** `2data/evidence/R1_G2/run_g2_candidate1_watercmy/evidence_report_candidate1.json`.
- **Sequential Invariant:** Cleanly stopped prior to Candidate 2 live run.

---

## 3. Candidate 2 Execution Record: `spacejohnlf/tcm-acupoints` (Demo 2 of 3)

- **Status:** **PASS (VERIFIED)**
- **Pinned Commit:** `04e35abb66585eb29c7250ea8ab5243c8c744f64`
- **Licenses:** `MIT` (code in `LICENSE`), `CC BY-SA 4.0` (Z-Anatomy derived model in `ATTRIBUTION.md`).
- **Asset Integrity:** `public/models/body.glb` (8,249,484 bytes, SHA-256: `0886b6a068e655b284903664e2178d7964f80b1c0ce798461909ac806bcef2e3`, 1,872 nodes, 826 meshes).
- **Scoped Pre-fetch Compliance:**
  - Downloaded only the 79 lockfile-declared packages from `https://registry.npmjs.org/`.
  - Verified each package's SHA-512 against `package-lock.json` integrity digests.
  - Zero unapproved URLs, zero redirects, zero script execution outside sandbox.
  - Populated dedicated disposable npm cache at `/tmp/msk-candidate2-cache`.
- **Offline Sandboxed Build in Bubblewrap:**
  - Ran `npm ci --ignore-scripts --offline --cache /cache` inside Bubblewrap with `--unshare-net` (completed in 6s, 0 vulnerabilities).
  - Ran `npm run build` (`tsc -b && vite build`) inside Bubblewrap (completed in 1.15s, generating `dist/`).
- **Restricted Unix Socket Bridge Execution:**
  - Launched Bubblewrap container serving `dist/` over Unix socket `/tmp/msk-bridge-8093/app.sock` with `--unshare-net` and 500 MB `RLIMIT_AS`.
  - Host loopback proxy on `127.0.0.1:8093`.
- **HTTP Endpoint Latency & Delivery:**
  - `GET /index.html` (896 B) &rarr; HTTP 200 (10.15 ms)
  - `GET /models/body.glb` (8.25 MB) &rarr; HTTP 200 (9.29 ms streaming)
  - `GET /assets/index-BsmLTZnE.css` (9.5 KB) &rarr; HTTP 200 (11.13 ms)
  - `GET /assets/index--6mdkOlg.js` (369.6 KB) &rarr; HTTP 200 (8.62 ms)
  - `GET /assets/viewer-594QV7r1.js` (661.1 KB) &rarr; HTTP 200 (8.57 ms)
  - `GET /assets/draco_decoder-Z1_iN-Ht.wasm` (192.4 KB) &rarr; HTTP 200 (7.65 ms)
- **Process Resource Usage:**
  - Observed Peak RSS: **1.88 MB** | Peak VMS: **3.57 MB** (Budget: 500 MB).
- **Interactive Browser Verification:**
  - Real Windows Chrome capture at 1366x768:  
    `2data/evidence/R1_G2/run_g2_candidate2_spacejohnlf/candidate2_spacejohnlf_default_1366x768.png`  
    *(Size: 281.31 KB, SHA-256: `895b7d6655befd57ce655d49b4bab7c4ab6816f821e92f339495233bc3a083fd`)*.
- **Clean Process Termination:** Process group and temporary workspace cleanly terminated without orphaned children.
- **Sealed Report:** `2data/evidence/R1_G2/run_g2_candidate2_spacejohnlf/evidence_report_candidate2.json`.

---

## 4. Proposal for Candidate 3 Execution: `JICio/tcm-3d` (Awaiting Operator Approval)

In strict compliance with Directive 5, Candidate 3 has **not** been executed automatically. I hereby present the exact proposed parameters and run command for operator approval:

- **Target Repository:** `JICio/tcm-3d` at `3refs/upstream/jicio--tcm-3d`
- **Pinned Commit SHA:** `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a`
- **Licenses:** Code `MIT` (`LICENSE` and `public/CODE-LICENSE.txt`), Assets `CC BY 4.0` (`NOTICE` and `public/ATTRIBUTION.md`).
- **Asset Scope:** Authentic BodyParts3D 4.0 chunked meshes in `public/models/`:
  - `atlas.json` (1.3 MB JSON index)
  - 15 binary mesh chunks (`body-0.bin` through `body-14.bin`, ~60 MB total).
- **Dependencies:** 38 npm packages declared in `package-lock.json`. Zero lifecycle hooks (`preinstall`, `postinstall`, `install`).
- **Proposed Port & Bridge:** `http://127.0.0.1:8094/` via `/tmp/msk-bridge-8094/app.sock`.
- **Proposed Safe Build & Execution Procedure:**
  1. Re-verify pinned Git commit `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a` and verify all URLs point strictly to `https://registry.npmjs.org/`.
  2. Scoped dependency pre-fetch of the 38 lockfile-declared packages into disposable cache `/tmp/msk-candidate3-cache`, verifying SHA-512 hashes.
  3. Inside Bubblewrap with `--unshare-net`, perform offline `npm ci --ignore-scripts --offline` and `npm run build:tcm` (or `npm run build`).
  4. Serve built static distribution via Bubblewrap Unix socket bridge on port `8094`.
  5. Capture 1366x768 Chrome screenshot, measure RSS/VMS, and cleanly stop.

> [!IMPORTANT]
> **Operator Approval Required:** Candidate 3 will NOT be executed until the operator grants explicit approval for `JICio/tcm-3d`.

---

## 5. Verification Evidence & Artifact Manifest

| Artifact | Path | SHA-256 Hash |
|---|---|---|
| **Candidate 1 Chrome Screenshot (1366x768)** | `2data/evidence/R1_G2/run_g2_candidate1_watercmy/candidate1_watercmy_default_1366x768.png` | `abd3d7fd109a3e7c6c75277378d5afddd22c6f4df3efd7c2fbde9645f28ab947` |
| **Candidate 1 Evidence Report** | `2data/evidence/R1_G2/run_g2_candidate1_watercmy/evidence_report_candidate1.json` | Sealed JSON manifest |
| **Candidate 2 Chrome Screenshot (1366x768)** | `2data/evidence/R1_G2/run_g2_candidate2_spacejohnlf/candidate2_spacejohnlf_default_1366x768.png` | `895b7d6655befd57ce655d49b4bab7c4ab6816f821e92f339495233bc3a083fd` |
| **Candidate 2 Evidence Report** | `2data/evidence/R1_G2/run_g2_candidate2_spacejohnlf/evidence_report_candidate2.json` | Sealed JSON manifest |
| **G2 Master Evidence Report** | `2data/evidence/R1_G2/run_g2_bubblewrap_001/evidence_report_g2.json` | Updated: 2/3 Verified |
| **Full Security Test Suite** | `tests/security/` | 12/12 passed |
| **Full Integration & Unit Test Suite** | `tests/` | 155/155 passed |

---

## 6. How to Verify the System

### Run All 155 Automated Tests
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
/home/tuan/.venvs/msk-lab/bin/pytest tests -v
```

### Verify Candidate 2 Live on Port 8093
```bash
/home/tuan/.venvs/msk-lab/bin/python3 scripts/serve_candidate_2_bridge.py &
curl -I http://127.0.0.1:8093/
curl -I http://127.0.0.1:8093/models/body.glb
```

### Verify Lab OS Server on Port 8091 & Model Streaming
```bash
curl -s http://127.0.0.1:8091/api/v1/health
curl -s http://127.0.0.1:8091/api/v1/atlas/models
curl -s -D - http://127.0.0.1:8091/api/v1/atlas/models/watercmy_bp3d_z_anatomy/file -o /dev/null
curl -s -D - http://127.0.0.1:8091/api/v1/atlas/models/spacejohnlf_z_anatomy/file -o /dev/null
```
Visit `http://127.0.0.1:8091/dashboard` in a Windows web browser to view the interactive dashboard showing G2 at `IN PROGRESS (2/3 DEMOS)`.
