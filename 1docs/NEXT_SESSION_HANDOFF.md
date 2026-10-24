# Coding Session Handoff & Completion Record — Candidate 2 Audit & Sandbox Limitation Report, Candidate 3 Approval Proposal

**Project:** MSK Research Lab OS v3.1  
**Status:** **R0, R1 (Static), R1D, R2, R3, R4 (Authentic Models Ingested + Procedural Demo), R5, R6 VERIFIED (155 TESTS PASSING); G2 IN PROGRESS (1/3 DEMOS VERIFIED — CANDIDATE 1 VERIFIED; CANDIDATE 2 BLOCKED ON OFFLINE CACHE MISS; AWAITING APPROVAL)**  
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
| **R1 (G2)** | Live Upstream Sandbox Run | **G2, SEC** | **IN PROGRESS (1/3 DEMO VERIFIED)** | Bubblewrap rootless container sandbox with Unix domain stream socket bridge verified. Candidate 1 (`WaterCMY/anatomy-3d`) executed under `--unshare-net`, HTTP 200 on all assets, WebGL rendered, RSS 1.89 MB, screenshot captured at 1366x768 (SHA: `abd3d7...`), cleanly stopped. Candidate 2 verified statically & registered in Lab OS; offline build blocked (`ENOTCACHED`); awaiting network dependency staging approval. Candidate 3 awaiting approval. |
| **R1D** | Discovery & Research Pipeline | **DISC-01..04, REV-01..02** | **PASS (VERIFIED)** | Local MD import, live GitHub discovery, candidate queue, AST static analysis, reports. REA adapter is OPTIONAL_UNAVAILABLE. Real browser screenshots: `2data/evidence/R1D/run_r1d_discovery_001/dashboard_r1d_1366x768.png` |
| **R2** | Research Library & Disaster Recovery | **G5, G6** | **PASS (VERIFIED)** | Content-addressed originals (`2data/originals/`), FTS5 BM25 search, VACUUM INTO backup/restore. `2data/evidence/R2_report.md` |
| **R3** | Scholarly Tri-Ledger & Publisher | **G7, G8, G9, G10, SEC** | **PASS (VERIFIED)** | Tri-ledger (Claims, Evidence, Contradictions), ontology lookup, typed graph, snapshot publisher. `2data/evidence/R3_report.md` |
| **R4** | Unified Anatomy & Meridian Atlas | **ATLAS-01..06, SR-01..10** | **AUTHENTIC ASSETS INGESTED + PROCEDURAL DEMO** | Registered authentic BodyParts3D GLB model (`watercmy_bp3d_z_anatomy`, 9.29 MB) and Z-Anatomy mannequin (`spacejohnlf_z_anatomy`, 8.25 MB) with direct streaming endpoints. Retains calibrated 5-layer procedural benchmark demonstration with explicit epistemic disclaimers. 155 automated tests passing. |
| **R5** | Private Studio & 2D Diện Chẩn | **ATLAS-05, ATLAS-06** | **PASS (VERIFIED)** | Multi-tradition studio editor, transactional undo/redo, 2D Diện Chẩn maps, epistemic 2D->3D rejection. `2data/evidence/R5_report.md` |
| **R6** | Therapy Bridge & Offline Packages | **BRIDGE-01..03, SEC** | **PASS (VERIFIED)** | Scoped Bearer authentication, offline hashed research packages, mock consumer client, zero patient data boundary. `2data/evidence/R6_report.md` |

---

## 2. Candidate 1 Execution & Verification Record

- **Candidate ID:** `watercmy--anatomy-3d`
- **Status:** **PASS (VERIFIED)** (1 of 3 Upstream Demonstrations)
- **Canonical URL:** `https://github.com/WaterCMY/anatomy-3d`
- **Pinned Commit SHA:** `e8d40dca7b1f63f54567395df21d8b1b38a7e840`
- **Code License:** `MIT` | **Asset License:** `CC BY-SA 2.1 Japan`
- **Execution Architecture:** Bubblewrap rootless container (`bwrap`) with `--unshare-all`, `--unshare-net`, `--unshare-pid`, `--tmpfs /tmp`, read-only rootfs binds, read-only `/app`.
- **Bridging Mechanism:** Unix domain stream socket `/bridge/app.sock` inside container proxied via host loopback `127.0.0.1:8092`.
- **HTTP Latency & Delivery:**
  - `GET /index.html` (211 KB) &rarr; HTTP 200 (12.83 ms)
  - `GET /vendor/three/three.module.js` (1.27 MB) &rarr; HTTP 200 (28.84 ms)
  - `GET /models/anatomy.glb` (9.29 MB) &rarr; HTTP 200 (448.98 ms streaming)
- **Process Metrics:** Peak RSS = 1.89 MB, Peak VMS = 3.57 MB (Budget: 500 MB).
- **Chrome Screenshot (1366x768):** `2data/evidence/R1_G2/run_g2_candidate1_watercmy/candidate1_watercmy_default_1366x768.png` (SHA-256: `abd3d7fd109a3e7c6c75277378d5afddd22c6f4df3efd7c2fbde9645f28ab947`).
- **Sealed Report:** `2data/evidence/R1_G2/run_g2_candidate1_watercmy/evidence_report_candidate1.json`.

---

## 3. Candidate 2 Audit, Sandboxed Build Attempt, & Limitation Record

### Independent Pre-execution Verification
- **Candidate ID:** `spacejohnlf--tcm-acupoints`
- **Canonical URL:** `https://github.com/spacejohnlf/tcm-acupoints`
- **Pinned Commit SHA:** `04e35abb66585eb29c7250ea8ab5243c8c744f64`
- **Code License:** `MIT` | **Asset License:** `CC BY-SA 4.0` (Z-Anatomy derivative)
- **Asset Integrity:** `public/models/body.glb` (8,249,484 bytes, SHA-256: `0886b6a068e655b284903664e2178d7964f80b1c0ce798461909ac806bcef2e3`).
  - Binary glTF 2.0 with 1,872 nodes and 826 meshes representing axial skeleton, neurocranium, viscerocranium, pectoral girdle, etc.
  - Registered in Lab OS 3D model registry as `spacejohnlf_z_anatomy` with active streaming endpoint `GET /api/v1/atlas/models/spacejohnlf_z_anatomy/file`.
- **Acupoint & Meridian Data:** 14 meridians, 71 acupoints in `src/data/point-texts.json` and `src/lib/acupoint-data.ts`.
- **Script Security:** Zero `preinstall`, `postinstall`, or `install` scripts in `package.json` and `package-lock.json`. AST clean.

### Sandboxed Build Attempt inside Bubblewrap
- **Environment:** Bubblewrap container executed with:
  ```bash
  bwrap \
    --unshare-all \
    --unshare-net \
    --unshare-pid \
    --proc /proc \
    --ro-bind /bin /bin \
    --ro-bind /lib /lib \
    --ro-bind /lib64 /lib64 \
    --ro-bind /usr /usr \
    --ro-bind /home/tuan/.nvm /home/tuan/.nvm \
    --ro-bind /home/tuan/.npm /home/tuan/.npm \
    --bind /tmp/msk-build-spacejohnlf /app \
    --tmpfs /tmp \
    --setenv HOME /tmp \
    --setenv PATH "/home/tuan/.nvm/versions/node/v20.20.2/bin:/usr/bin:/bin" \
    --chdir /app \
    -- /home/tuan/.nvm/versions/node/v20.20.2/bin/npm ci --ignore-scripts --offline --cache /home/tuan/.npm
  ```
- **Execution Diagnostic Output:**
  ```
  npm error code ENOTCACHED
  npm error request to https://registry.npmjs.org/vite/-/vite-8.2.0.tgz failed: cache mode is 'only-if-cached' but no cached response is available.
  ```
- **Diagnosis:** The host's `~/.npm` cache does not contain the binary `.tgz` package archives for Vite 8.2.0 or its dependencies.
- **Epistemic Invariant Enforced:**
  In accordance with the operator directive (*"Any network-dependent installation requires separate approval. If the sandbox cannot safely support the Node.js build, keep Candidate 2 BLOCKED and report the precise limitation instead of weakening isolation"*), container network isolation was **strictly maintained**.
- **Candidate 2 Verdict:** **BLOCKED (OFFLINE_CACHE_MISS; AWAITING_NETWORK_DEP_APPROVAL)**.
- **Teardown & Cleanup:** `/tmp/msk-build-spacejohnlf` was wiped; zero unauthorized filesystem modifications; process tree cleanly terminated.

---

## 4. Proposed Resolution for Candidate 2 (Awaiting Operator Decision)

To proceed with Candidate 2 execution on port `8093`, the operator may select one of two reviewed paths:

### Option A: Authorize Scoped Pre-fetch of Pinned npm Dependencies
Allow a one-time restricted download of the 79 pinned packages from `registry.npmjs.org` with `--ignore-scripts` to populate the local npm cache:
```bash
npm cache fetch / staging with --ignore-scripts
```
Once cached, the build (`npm ci --ignore-scripts --offline && npm run build`) will run inside Bubblewrap with `--unshare-net` (strictly 0 network interfaces), serving the resulting `dist/` on port `8093`.

### Option B: Zero-Dependency Three.js Standalone Runner
Mount Candidate 2's verified Z-Anatomy `body.glb` model, 14 meridians, and 71 acupoint texts into an isolated Three.js r160 static viewer inside Bubblewrap on port `8093`, requiring zero external npm packages and zero network access.

---

## 5. Candidate 3 Approval Proposal: `JICio/tcm-3d`

- **Canonical URL:** `https://github.com/JICio/tcm-3d`
- **Pinned Commit SHA:** `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a`
- **Code License:** `MIT` (stated in `LICENSE` and `public/CODE-LICENSE.txt`)
- **Asset License:** `CC BY 4.0` (stated in `NOTICE` and `public/ATTRIBUTION.md`)
- **Asset Model:** Authentic BodyParts3D 4.0 chunked mesh assets in `public/models/`:
  - `atlas.json` (1.3 MB)
  - 15 binary mesh chunks (`body-0.bin` through `body-14.bin`, ~60 MB total)
- **Dependencies:** 38 npm dependencies (Next.js / Vinext / React 19 / Three.js).
- **Security Audit:** Zero lifecycle install scripts. AST clean.
- **Proposed Bridge Port:** `http://127.0.0.1:8094/` via `/tmp/msk-bridge-8094/app.sock` under Bubblewrap isolation with `--unshare-net`.
- **Scheduled Phase:** Following Candidate 2 resolution.

---

## 6. Verification Evidence & Artifact Manifest

| Artifact | Path | SHA-256 Hash |
|---|---|---|
| **Candidate 1 Chrome Screenshot (1366x768)** | `2data/evidence/R1_G2/run_g2_candidate1_watercmy/candidate1_watercmy_default_1366x768.png` | `abd3d7fd109a3e7c6c75277378d5afddd22c6f4df3efd7c2fbde9645f28ab947` |
| **Candidate 1 Evidence Report** | `2data/evidence/R1_G2/run_g2_candidate1_watercmy/evidence_report_candidate1.json` | Sealed JSON manifest |
| **Candidate 2 Model Asset** | `3refs/upstream/spacejohnlf--tcm-acupoints/public/models/body.glb` | `0886b6a068e655b284903664e2178d7964f80b1c0ce798461909ac806bcef2e3` |
| **G2 Master Evidence Report** | `2data/evidence/R1_G2/run_g2_bubblewrap_001/evidence_report_g2.json` | Updated: 1/3 Verified, Candidate 2 Blocked on Offline Cache |
| **Full Security Test Suite** | `tests/security/` | 12/12 passed |
| **Full Integration & Unit Test Suite** | `tests/` | 155/155 passed |

---

## 7. How to Verify the System

### Run All 155 Automated Tests
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
/home/tuan/.venvs/msk-lab/bin/pytest tests -v
```

### Verify Candidate 1 Live on Port 8092
```bash
curl -I http://127.0.0.1:8092/
curl -I http://127.0.0.1:8092/models/anatomy.glb
```

### Verify Lab OS Server on Port 8091 & Model Streaming
```bash
curl -s http://127.0.0.1:8091/api/v1/health
curl -s http://127.0.0.1:8091/api/v1/atlas/models
curl -s -D - http://127.0.0.1:8091/api/v1/atlas/models/watercmy_bp3d_z_anatomy/file -o /dev/null
curl -s -D - http://127.0.0.1:8091/api/v1/atlas/models/spacejohnlf_z_anatomy/file -o /dev/null
```
