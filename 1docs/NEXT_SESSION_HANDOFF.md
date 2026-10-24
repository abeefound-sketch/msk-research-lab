# Coding Session Handoff & Completion Record — G2 Fully Verified (3/3 Upstream Demos), R4 Authentic Models Integrated

**Project:** MSK Research Lab OS v3.1  
**Status:** **R0, R1 (Static), G2 (3/3 UPSTREAM DEMOS VERIFIED), R1D, R2, R3, R4 (AUTHENTIC BP3D MODELS INGESTED + PROCEDURAL DEMO), R5, R6 VERIFIED (155 TESTS PASSING)**  
**Target Platform:** Windows 10 / Ubuntu WSL2 (Intel HD 5500, 8 GiB RAM, 1366x768 Display)  
**Lab Repository Path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`) strictly on C: drive  
**MSK-Therapy-OS Status:** Untouched / Immutable at `/mnt/d/5Projects/msk-therapy-os` (Zero changes made to Therapy OS)  
**Total Automated Tests:** **155 passed, 0 failed** in 94.62 seconds  
**Database Schema Version:** v7 (Migrations 0001 through 0007 applied transactionally with WAL and Foreign Keys ON)  

---

## 1. Executive Summary & Release Gates State

| Release | Focus Area | Acceptance Gates | Verified Result | Evidence Manifest & Caveats |
|---|---|---|---|---|
| **R0** | Local Foundation & Diagnostics | **G1** | **PASS (VERIFIED)** | SQLite WAL, loopback port 8091 guard, doctor diagnostics. [evidence](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R0_report.md) |
| **R1 (Static)** | Repo Lab Static & Surface Benchmark | **G3, G4, SEC, SR-01..10** | **PASS (VERIFIED)** | Static AST analysis, license auditor, SR-01..10 registration benchmark 100% pass. [evidence](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R1_report.md) |
| **R1 (G2)** | Live Upstream Sandbox Run | **G2, SEC** | **PASS (VERIFIED - 3/3 DEMOS)** | Bubblewrap rootless container sandbox with Unix domain stream socket bridge fully verified. Three distinct upstream repositories executed under strict `--unshare-net`, HTTP 200 on all assets, WebGL rendered, low RSS (< 2 MB), screenshots captured at 1366x768, cleanly stopped. [master evidence](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R1_G2/run_g2_bubblewrap_001/evidence_report_g2.json) |
| **R1D** | Discovery & Research Pipeline | **DISC-01..04, REV-01..02** | **PASS (VERIFIED)** | Local MD import, live GitHub discovery, candidate queue, AST static analysis, reports. REA adapter is OPTIONAL_UNAVAILABLE. Real browser screenshot: [dashboard_r1d_1366x768.png](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R1D/run_r1d_discovery_001/dashboard_r1d_1366x768.png) |
| **R2** | Research Library & Disaster Recovery | **G5, G6** | **PASS (VERIFIED)** | Content-addressed originals (`2data/originals/`), FTS5 BM25 search, VACUUM INTO backup/restore. [evidence](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R2_report.md) |
| **R3** | Scholarly Tri-Ledger & Publisher | **G7, G8, G9, G10, SEC** | **PASS (VERIFIED)** | Tri-ledger (Claims, Evidence, Contradictions), ontology lookup, typed graph, snapshot publisher. [evidence](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R3_report.md) |
| **R4** | Unified Anatomy & Meridian Atlas | **ATLAS-01..06, SR-01..10** | **AUTHENTIC ASSETS INGESTED + PROCEDURAL DEMO** | Registered 3 authentic 3D models: BodyParts3D GLB (`watercmy_bp3d_z_anatomy`, 9.29 MB), Z-Anatomy mannequin (`spacejohnlf_z_anatomy`, 8.25 MB), and BodyParts3D 4.0 Chunked Atlas (`jicio_bp3d_chunked_atlas`, FMA-mapped). Streaming endpoints active. Retains calibrated 5-layer procedural benchmark demonstration with explicit epistemic disclaimers. 155 automated tests passing. |
| **R5** | Private Studio & 2D Diện Chẩn | **ATLAS-05, ATLAS-06** | **PASS (VERIFIED)** | Multi-tradition studio editor, transactional undo/redo, 2D Diện Chẩn maps, epistemic 2D->3D rejection. [evidence](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R5_report.md) |
| **R6** | Therapy Bridge & Offline Packages | **BRIDGE-01..03, SEC** | **PASS (VERIFIED)** | Scoped Bearer authentication, offline hashed research packages, mock consumer client, zero patient data boundary. [evidence](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R6_report.md) |

---

## 2. Candidate 1 Execution Record: `WaterCMY/anatomy-3d` (Demo 1 of 3)

- **Status:** **PASS (VERIFIED)**
- **Pinned Commit:** `e8d40dca7b1f63f54567395df21d8b1b38a7e840` | **Licenses:** MIT (code), CC BY-SA 2.1 Japan (model)
- **Execution Architecture:** Bubblewrap rootless container (`bwrap`) with `--unshare-all`, `--unshare-net`, `--unshare-pid`, `--tmpfs /tmp`, read-only rootfs binds, read-only `/app`.
- **Bridge Mechanism:** Unix stream socket `/bridge/app.sock` &rarr; host loopback `127.0.0.1:8092`.
- **Process Metrics:** Peak RSS = 1.89 MB, Peak VMS = 3.57 MB.
- **Screenshot (1366x768):** [candidate1_watercmy_default_1366x768.png](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R1_G2/run_g2_candidate1_watercmy/candidate1_watercmy_default_1366x768.png)  
  *(SHA-256: `abd3d7fd109a3e7c6c75277378d5afddd22c6f4df3efd7c2fbde9645f28ab947`)*.
- **Sealed Report:** [evidence_report_candidate1.json](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R1_G2/run_g2_candidate1_watercmy/evidence_report_candidate1.json).
- **Sequential Invariant:** Cleanly stopped prior to Candidate 2 live run.

---

## 3. Candidate 2 Execution Record: `spacejohnlf/tcm-acupoints` (Demo 2 of 3)

- **Status:** **PASS (VERIFIED)**
- **Pinned Commit:** `04e35abb66585eb29c7250ea8ab5243c8c744f64`
- **Licenses:** `MIT` (code in `LICENSE`), `CC BY-SA 4.0` (Z-Anatomy derived model in `ATTRIBUTION.md`).
- **Asset Integrity:** `public/models/body.glb` (8,249,484 bytes, SHA-256: `0886b6a068e655b284903664e2178d7964f80b1c0ce798461909ac806bcef2e3`, 1,872 nodes, 826 meshes).
- **Scoped Pre-fetch Compliance:** Downloaded 79 lockfile-declared packages from `https://registry.npmjs.org/` into `/tmp/msk-candidate2-cache` with verified SHA-512 hashes. Zero unapproved URLs, zero script execution outside sandbox.
- **Offline Sandboxed Build in Bubblewrap:** `npm ci --ignore-scripts --offline` (6s) and `npm run build` (1.15s) inside Bubblewrap with `--unshare-net`.
- **Restricted Unix Socket Bridge:** Served `dist/` over Unix socket `/tmp/msk-bridge-8093/app.sock` &rarr; host loopback `127.0.0.1:8093`.
- **HTTP 200 Endpoints:** `/index.html`, `/models/body.glb` (8.25 MB streaming, 9.29 ms), CSS, JS, WASM.
- **Process Resource Usage:** Peak RSS: **1.88 MB** | Peak VMS: **3.57 MB** (Budget: 500 MB).
- **Interactive Browser Verification:** Real Windows Chrome capture at 1366x768:  
  [candidate2_spacejohnlf_default_1366x768.png](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R1_G2/run_g2_candidate2_spacejohnlf/candidate2_spacejohnlf_default_1366x768.png)  
  *(Size: 281.31 KB, SHA-256: `895b7d6655befd57ce655d49b4bab7c4ab6816f821e92f339495233bc3a083fd`)*.
- **Sequential Invariant:** Cleanly stopped prior to Candidate 3 live run.
- **Sealed Report:** [evidence_report_candidate2.json](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R1_G2/run_g2_candidate2_spacejohnlf/evidence_report_candidate2.json).

---

## 4. Candidate 3 Execution Record: `JICio/tcm-3d` (Demo 3 of 3)

- **Status:** **PASS (VERIFIED)**
- **Pinned Commit:** `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a`
- **Licenses:** `MIT` (code in `LICENSE` and `public/CODE-LICENSE.txt`), `CC BY 4.0` (BodyParts3D chunked meshes in `public/ATTRIBUTION.md`).
- **Asset Scope:** Authentic BodyParts3D 4.0 chunked meshes in `public/models/`:
  - `atlas.json` (1.3 MB JSON index with FMA concept IDs, systems, vertex/index counts, bounds)
  - 15 binary mesh chunks (`body-0.bin` through `body-14.bin`, ~60 MB total).
- **Scoped Pre-fetch Compliance:**
  - Verified 699 lockfile-declared packages from `https://registry.npmjs.org/` into `/tmp/msk-candidate3-cache`.
  - Zero unapproved URLs, zero script execution outside sandbox.
- **Offline Sandboxed Build in Bubblewrap:**
  - Ran `npm ci --ignore-scripts --offline --cache /cache` inside Bubblewrap with `--unshare-net` (completed in 28s, 0 vulnerabilities).
  - Ran `npm run build` (`vite build`) inside Bubblewrap with `--unshare-net` (completed in 1.77s, generating `dist/`).
- **Restricted Unix Socket Bridge Execution:**
  - Bubblewrap container serving `dist/` over Unix socket `/tmp/msk-bridge-8094/app.sock` with `--unshare-net` and 500 MB `RLIMIT_AS`.
  - Host loopback proxy on `127.0.0.1:8094`.
- **HTTP Endpoint Latency & Delivery:**
  - `GET /index.html` (715 B) &rarr; HTTP 200 (9.94 ms)
  - `GET /assets/index-Db4oWrKp.css` (42.5 KB) &rarr; HTTP 200 (7.91 ms)
  - `GET /assets/index-CwpZVjqB.js` (1.75 MB) &rarr; HTTP 200 (8.05 ms)
  - `GET /models/atlas.json` (1.33 MB) &rarr; HTTP 200 (11.39 ms)
  - `GET /models/body-0.bin` (4.01 MB) &rarr; HTTP 200 (10.16 ms)
  - `GET /models/body-1.bin` (4.52 MB) &rarr; HTTP 200 (7.92 ms)
  - `GET /favicon.svg` (227 B) &rarr; HTTP 200 (7.28 ms)
- **Process Resource Usage:**
  - Observed Peak RSS: **1.88 MB** | Peak VMS: **3.57 MB** (Budget: 500 MB).
- **Interactive Browser Verification:**
  - Real Windows Chrome capture at 1366x768:  
    [candidate3_jicio_default_1366x768.png](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R1_G2/run_g2_candidate3_jicio/candidate3_jicio_default_1366x768.png)  
    *(Size: 186.86 KB, SHA-256: `e5da06820b0146be090f692e656c3810c8d2c1b57d4516b389ed70051b01ca85`)*.
- **Clean Process Termination:** Process group and temporary workspace cleanly terminated in 14.53s without orphaned children.
- **Sealed Report:** [evidence_report_candidate3.json](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/2data/evidence/R1_G2/run_g2_candidate3_jicio/evidence_report_candidate3.json)  
  *(SHA-256: `ba176a1ee1d8a81a98eb9b83e055018010c95067d8bf559860ab4adef49405fa`)*.

---

## 5. Verification Evidence & Artifact Manifest

| Artifact | Path | SHA-256 Hash |
|---|---|---|
| **Candidate 1 Chrome Screenshot (1366x768)** | `2data/evidence/R1_G2/run_g2_candidate1_watercmy/candidate1_watercmy_default_1366x768.png` | `abd3d7fd109a3e7c6c75277378d5afddd22c6f4df3efd7c2fbde9645f28ab947` |
| **Candidate 1 Evidence Report** | `2data/evidence/R1_G2/run_g2_candidate1_watercmy/evidence_report_candidate1.json` | Sealed JSON manifest |
| **Candidate 2 Chrome Screenshot (1366x768)** | `2data/evidence/R1_G2/run_g2_candidate2_spacejohnlf/candidate2_spacejohnlf_default_1366x768.png` | `895b7d6655befd57ce655d49b4bab7c4ab6816f821e92f339495233bc3a083fd` |
| **Candidate 2 Evidence Report** | `2data/evidence/R1_G2/run_g2_candidate2_spacejohnlf/evidence_report_candidate2.json` | Sealed JSON manifest |
| **Candidate 3 Chrome Screenshot (1366x768)** | `2data/evidence/R1_G2/run_g2_candidate3_jicio/candidate3_jicio_default_1366x768.png` | `e5da06820b0146be090f692e656c3810c8d2c1b57d4516b389ed70051b01ca85` |
| **Candidate 3 Evidence Report** | `2data/evidence/R1_G2/run_g2_candidate3_jicio/evidence_report_candidate3.json` | `ba176a1ee1d8a81a98eb9b83e055018010c95067d8bf559860ab4adef49405fa` |
| **G2 Master Evidence Report** | `2data/evidence/R1_G2/run_g2_bubblewrap_001/evidence_report_g2.json` | `PASS (VERIFIED - 3/3 UPSTREAM DEMOS)` |
| **Full Security Test Suite** | `tests/security/` | 12/12 passed |
| **Full Integration & Unit Test Suite** | `tests/` | 155/155 passed |

---

## 6. How to Verify the System

### Run All 155 Automated Tests
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
/home/tuan/.venvs/msk-lab/bin/pytest tests -v
```

### Verify Candidate 3 Live on Port 8094
```bash
/home/tuan/.venvs/msk-lab/bin/python3 scripts/serve_candidate_3_bridge.py &
curl -I http://127.0.0.1:8094/
curl -I http://127.0.0.1:8094/models/atlas.json
curl -I http://127.0.0.1:8094/models/body-0.bin
```

### Verify Lab OS Server on Port 8091 & Model Streaming
```bash
curl -s http://127.0.0.1:8091/api/v1/health
curl -s http://127.0.0.1:8091/api/v1/atlas/models
curl -s -D - http://127.0.0.1:8091/api/v1/atlas/models/watercmy_bp3d_z_anatomy/file -o /dev/null
curl -s -D - http://127.0.0.1:8091/api/v1/atlas/models/spacejohnlf_z_anatomy/file -o /dev/null
```
Visit `http://127.0.0.1:8091/dashboard` in a Windows web browser to view the interactive dashboard showing G2 at `PASS (VERIFIED)`.
