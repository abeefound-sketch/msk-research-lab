# Coding Session Handoff & Completion Record — Candidate 1 Verified, Candidate 2 Approval Plan, R4 Authentic Model Ingested

**Project:** MSK Research Lab OS v3.1  
**Status:** **R0, R1 (Static), R1D, R2, R3, R4 (Authentic Model Ingested + Procedural Demo), R5, R6 VERIFIED (155 TESTS PASSING); G2 IN PROGRESS (1/3 DEMOS VERIFIED — CANDIDATE 1 VERIFIED; AWAITING CANDIDATE 2 APPROVAL)**  
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
| **R1 (G2)** | Live Upstream Sandbox Run | **G2, SEC** | **IN PROGRESS (1/3 DEMO VERIFIED)** | Bubblewrap rootless container sandbox with Unix domain stream socket bridge verified. Candidate 1 (`WaterCMY/anatomy-3d`) executed under `--unshare-net`, HTTP 200 on all assets, WebGL rendered, RSS 1.89 MB, screenshot captured at 1366x768 (SHA: `abd3d7...`), cleanly stopped. Candidate 2 & 3 awaiting operator execution approval. |
| **R1D** | Discovery & Research Pipeline | **DISC-01..04, REV-01..02** | **PASS (VERIFIED)** | Local MD import, live GitHub discovery, candidate queue, AST static analysis, reports. REA adapter is OPTIONAL_UNAVAILABLE. Real browser screenshots: `2data/evidence/R1D/run_r1d_discovery_001/dashboard_r1d_1366x768.png` |
| **R2** | Research Library & Disaster Recovery | **G5, G6** | **PASS (VERIFIED)** | Content-addressed originals (`2data/originals/`), FTS5 BM25 search, VACUUM INTO backup/restore. `2data/evidence/R2_report.md` |
| **R3** | Scholarly Tri-Ledger & Publisher | **G7, G8, G9, G10, SEC** | **PASS (VERIFIED)** | Tri-ledger (Claims, Evidence, Contradictions), ontology lookup, typed graph, snapshot publisher. `2data/evidence/R3_report.md` |
| **R4** | Unified Anatomy & Meridian Atlas | **ATLAS-01..06, SR-01..10** | **AUTHENTIC ASSET INGESTED + PROCEDURAL DEMO** | Registered authentic BodyParts3D GLB model (`watercmy_bp3d_z_anatomy`, 9.29 MB, CC BY-SA 2.1 Japan) with direct streaming endpoint `/api/v1/atlas/models/watercmy_bp3d_z_anatomy/file`. Retains calibrated 5-layer procedural benchmark demonstration with explicit epistemic disclaimers. 155 automated tests passing. Real browser screenshots: `2data/evidence/R4/run_r4_atlas_001/dashboard_r4_atlas_1366x768.png` |
| **R5** | Private Studio & 2D Diện Chẩn | **ATLAS-05, ATLAS-06** | **PASS (VERIFIED)** | Multi-tradition studio editor, transactional undo/redo, 2D Diện Chẩn maps, epistemic 2D->3D rejection. `2data/evidence/R5_report.md` |
| **R6** | Therapy Bridge & Offline Packages | **BRIDGE-01..03, SEC** | **PASS (VERIFIED)** | Scoped Bearer authentication, offline hashed research packages, mock consumer client, zero patient data boundary. `2data/evidence/R6_report.md` |

---

## 2. G2 Candidate Status & Verification Record

### Candidate 1: `WaterCMY/anatomy-3d` — VERIFIED (1 of 3)
- **Status:** **PASS (VERIFIED)**
- **Canonical URL:** `https://github.com/WaterCMY/anatomy-3d`
- **Pinned Commit SHA:** `e8d40dca7b1f63f54567395df21d8b1b38a7e840`
- **Code License:** `MIT` | **Asset License:** `CC BY-SA 2.1 Japan`
- **Execution Architecture:** Bubblewrap rootless container (`bwrap`) with `--unshare-all`, `--unshare-net`, `--unshare-pid`, `--tmpfs /tmp`, read-only rootfs binds, read-only `/app`.
- **Bridging Mechanism:** Unix domain stream socket `/bridge/app.sock` inside container proxied via host loopback `127.0.0.1:8092`.
- **HTTP Endpoint Verification:**
  - `GET /index.html` (211,418 bytes) &rarr; HTTP 200 OK (12.83 ms)
  - `GET /vendor/three/three.module.js` (1,272,972 bytes) &rarr; HTTP 200 OK (28.84 ms)
  - `GET /vendor/three/OrbitControls.js` (29,868 bytes) &rarr; HTTP 200 OK (9.91 ms)
  - `GET /vendor/three/loaders/GLTFLoader.js` (108,522 bytes) &rarr; HTTP 200 OK (16.16 ms)
  - `GET /models/anatomy.glb` (9,291,204 bytes) &rarr; HTTP 200 OK (448.98 ms streaming)
- **Process Metrics:** Peak RSS = 1.89 MB, Peak VMS = 3.57 MB (Enforced virtual memory limit: 500 MB `RLIMIT_AS`).
- **Interactive Browser Verification:** Real Windows Chrome headless capture at 1366x768:
  - File: `2data/evidence/R1_G2/run_g2_candidate1_watercmy/candidate1_watercmy_default_1366x768.png`
  - Size: 97,120 bytes
  - SHA-256: `abd3d7fd109a3e7c6c75277378d5afddd22c6f4df3efd7c2fbde9645f28ab947`
- **Clean Process Termination:** SIGTERM/SIGKILL lifecycle cleanly executed; zero orphaned child processes.
- **Sealed Report:** `2data/evidence/R1_G2/run_g2_candidate1_watercmy/evidence_report_candidate1.json`.

---

## 3. Proposal for Candidate 2 Execution (Awaiting Operator Approval)

### Candidate 2: `spacejohnlf/tcm-acupoints`
- **Canonical URL:** `https://github.com/spacejohnlf/tcm-acupoints`
- **Pinned Commit SHA:** `04e35abb66585eb29c7250ea8ab5243c8c744f64`
- **Code License:** `MIT` | **Asset License:** `CC BY-SA 4.0`
- **Asset Model:** `public/models/body.glb` (7.9 MB Z-Anatomy derivative)
- **Dependencies:** 13 npm packages (React 19, Vite 8, Three.js).
- **Security Audit:** Zero lifecycle scripts (`preinstall`, `postinstall`, `install`) in `package.json` and `package-lock.json`. AST clean.
- **Proposed Sandbox Bridge:** Port `8093` (`http://127.0.0.1:8093/`) via Unix domain stream socket `/bridge/app.sock`.
- **Proposed Safe Build & Execution Procedure:**
  1. Isolated offline npm dependency staging using `--ignore-scripts`:
     ```bash
     cd /mnt/c/Users/tuanh/Downloads/msk-research-lab/3refs/upstream/spacejohnlf--tcm-acupoints
     npm ci --ignore-scripts
     npm run build
     ```
  2. Launch Bubblewrap container serving the built static distribution (`dist/`) over Unix socket bridge with strict `--unshare-net`:
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
       --ro-bind /home/tuan/.venvs/msk-lab /home/tuan/.venvs/msk-lab \
       --ro-bind /mnt/c/Users/tuanh/Downloads/msk-research-lab/3refs/upstream/spacejohnlf--tcm-acupoints/dist /app \
       --tmpfs /tmp \
       --bind /tmp/msk-bridge-8093 /bridge \
       --chdir /app \
       --die-with-parent \
       -- /home/tuan/.venvs/msk-lab/bin/python3 /bridge/server.py --root /app --socket /bridge/app.sock
     ```
  3. Host proxy routes `http://127.0.0.1:8093/` to `/tmp/msk-bridge-8093/app.sock`.
  4. Capture 1366x768 Chrome screenshot, measure RSS/VMS, and cleanly stop.

> [!IMPORTANT]
> **Operator Approval Required:** Candidate 2 will NOT be executed until the operator grants explicit approval for `spacejohnlf/tcm-acupoints`.

---

## 4. Candidate 3: `JICio/tcm-3d` (Scheduled Next)
- **Canonical URL:** `https://github.com/JICio/tcm-3d`
- **Pinned Commit SHA:** `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a`
- **Code License:** `MIT` | **Asset License:** `CC BY 4.0`
- **Asset Model:** BodyParts3D 4.0 chunked meshes (`public/models/atlas.json` + `body-*.bin`).
- **Status:** Cloned at pinned SHA; static research report completed; queued for Phase 3.

---

## 5. R4 Unified 3D Atlas Remediation & Epistemic Honesty

1. **Authentic Model Registration:**
   - Model ID: `watercmy_bp3d_z_anatomy`
   - Name: `BodyParts3D / Z-Anatomy Full Torso & Musculoskeletal GLB`
   - Source: `3refs/upstream/watercmy--anatomy-3d/models/anatomy.glb` (9.29 MB)
   - SHA-256: `318347f91e4989da0c271e9662df536943df1149b413fef01cf21586073ea73e`
   - Serving Endpoint: `GET /api/v1/atlas/models/watercmy_bp3d_z_anatomy/file` (HTTP 200 OK, `model/gltf-binary`).
2. **Epistemic Invariant Maintained:**
   - The calibrated multi-layer torso (`build_calibrated_bp3d_torso_scene()`) is explicitly labeled:
     `asset_kind = "PROCEDURAL_BENCHMARK_DEMONSTRATION"`
     `clinical_validation_status = "NOT_CLINICALLY_VALIDATED; PROCEDURAL_BENCHMARK_ONLY"`
   - Users and research clients can switch between procedural demonstration geometry and authentic BodyParts3D polygon meshes without false claims of clinical validation.

---

## 6. Verification Evidence & Artifact Manifest

| Artifact | Path | SHA-256 Hash |
|---|---|---|
| **Candidate 1 Chrome Screenshot (1366x768)** | `2data/evidence/R1_G2/run_g2_candidate1_watercmy/candidate1_watercmy_default_1366x768.png` | `abd3d7fd109a3e7c6c75277378d5afddd22c6f4df3efd7c2fbde9645f28ab947` |
| **Candidate 1 Evidence Report** | `2data/evidence/R1_G2/run_g2_candidate1_watercmy/evidence_report_candidate1.json` | Sealed JSON manifest |
| **G2 Master Evidence Report** | `2data/evidence/R1_G2/run_g2_bubblewrap_001/evidence_report_g2.json` | Updated: 1/3 Verified |
| **R4 Authentic GLB Asset** | `3refs/upstream/watercmy--anatomy-3d/models/anatomy.glb` | `318347f91e4989da0c271e9662df536943df1149b413fef01cf21586073ea73e` |
| **R4 Dashboard Screenshot (1366x768)** | `2data/evidence/R4/run_r4_atlas_001/dashboard_r4_atlas_1366x768.png` | `909557c64c2c0ac6204a317a1fc201aa2aed77cf2954f2083846446e5ebac879` |
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

### Verify Lab OS Server on Port 8091
```bash
curl -s http://127.0.0.1:8091/api/v1/health
curl -s http://127.0.0.1:8091/api/v1/atlas/models
curl -s -D - http://127.0.0.1:8091/api/v1/atlas/models/watercmy_bp3d_z_anatomy/file -o /dev/null
```
Visit `http://127.0.0.1:8091/dashboard` in a Windows web browser to view the interactive dashboard.
