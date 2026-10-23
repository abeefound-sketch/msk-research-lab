# Coding Session Handoff & Completion Record — Bubblewrap Sandbox Verified & R4 Anatomical Honesty Reassessment

**Project:** MSK Research Lab OS v3.1  
**Status:** **R0, R1 (Static), R1D, R2, R3, R4 (Procedural Demo), R5, R6 VERIFIED (154 TESTS PASSING); G2 (Bubblewrap Rootless Sandbox Verified, Execution Fail-Closed Awaiting Per-Repo Approval)**  
**Target Platform:** Windows 10 / Ubuntu WSL2 (Intel HD 5500, 8 GiB RAM, 1366x768 Display)  
**Lab Repository Path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`) strictly on C: drive  
**MSK-Therapy-OS Status:** Untouched / Immutable at `/mnt/d/5Projects/msk-therapy-os` (Zero changes made to Therapy OS)  
**Total Automated Tests:** **154 passed, 0 failed** in 123.93 seconds  
**Database Schema Version:** v7 (Migrations 0001 through 0007 applied transactionally with WAL and Foreign Keys ON)  

---

## 1. Executive Summary & Release Gates State

| Release | Focus Area | Acceptance Gates | Verified Result | Evidence Manifest & Caveats |
|---|---|---|---|---|
| **R0** | Local Foundation & Diagnostics | **G1** | **PASS (VERIFIED)** | SQLite WAL, loopback port 8091 guard, doctor diagnostics. `2data/evidence/R0_report.md` |
| **R1 (Static)** | Repo Lab Static & Surface Benchmark | **G3, G4, SEC, SR-01..10** | **PASS (VERIFIED)** | Static AST analysis, license auditor, SR-01..10 registration benchmark 100% pass. `2data/evidence/R1_report.md` |
| **R1 (G2)** | Live Upstream Sandbox Run | **G2, SEC** | **BLOCKED (APPROVAL REQ)** | Bubblewrap rootless container sandbox installed & isolated on WSL2. Filesystem, network, PID, memory isolation, and Unix domain socket bridge verified (9/9 security tests pass). Native execution strictly fail-closed; awaiting separate per-repo operator execution approval. |
| **R1D** | Discovery & Research Pipeline | **DISC-01..04, REV-01..02** | **PASS (VERIFIED)** | Local MD import, live GitHub discovery, candidate queue, AST static analysis, reports. REA adapter is OPTIONAL_UNAVAILABLE. Real browser screenshots: `2data/evidence/R1D/run_r1d_discovery_001/dashboard_r1d_1366x768.png` |
| **R2** | Research Library & Disaster Recovery | **G5, G6** | **PASS (VERIFIED)** | Content-addressed originals (`2data/originals/`), FTS5 BM25 search, VACUUM INTO backup/restore. `2data/evidence/R2_report.md` |
| **R3** | Scholarly Tri-Ledger & Publisher | **G7, G8, G9, G10, SEC** | **PASS (VERIFIED)** | Tri-ledger (Claims, Evidence, Contradictions), ontology lookup, typed graph, snapshot publisher. `2data/evidence/R3_report.md` |
| **R4** | Unified Anatomy & Meridian Atlas | **ATLAS-01..06, SR-01..10** | **PROTOTYPE (PROCEDURAL)** | Production Three.js WebGL multi-layer Atlas Workbench with calibrated torso, 5 tissue layers, 5 anchored points, GB/SI meridians, 6-view occlusion QA, interactive raycasting, region filters, resilient 2D fallback. Epistemic reassessment: procedural benchmark demonstration only; does NOT constitute clinical BodyParts3D asset. Real DBCLS OBJ parser and authentic BodyParts3D GLB model discovered in upstream `WaterCMY/anatomy-3d`. Memory ~1.4 MB VRAM. Real browser screenshots: `2data/evidence/R4/run_r4_atlas_001/dashboard_r4_atlas_1366x768.png` |
| **R5** | Private Studio & 2D Diện Chẩn | **ATLAS-05, ATLAS-06** | **PASS (VERIFIED)** | Multi-tradition studio editor, transactional undo/redo, 2D Diện Chẩn maps, epistemic 2D->3D rejection. `2data/evidence/R5_report.md` |
| **R6** | Therapy Bridge & Offline Packages | **BRIDGE-01..03, SEC** | **PASS (VERIFIED)** | Scoped Bearer authentication, offline hashed research packages, mock consumer client, zero patient data boundary. `2data/evidence/R6_report.md` |

---

## 2. Phase 1: Audit & Correction of G2 Candidate Repositories

### Inaccessible Candidates (GitHub 404)
The three previously proposed candidates returned HTTP 404 upon independent verification and have been marked **REJECT** in `repository_candidates`:
- `mockbiomed/msk-tools` (`cand_mockbiomed_msk-tools` &rarr; `REJECT: GITHUB_404_NOT_FOUND`)
- `openanatomy/open-anatomy-browser` (`cand_openanatomy_open-anatomy-browser` &rarr; `REJECT: GITHUB_404_NOT_FOUND`)
- `whomed/acupuncture-3d` (`cand_whomed_acupuncture-3d` &rarr; `REJECT: GITHUB_404_NOT_FOUND`)

### Verified Public Alternatives Evaluation
Three authentic public alternatives were evaluated and cloned safely with hooks disabled (`core.hooksPath=/dev/null`) into `3refs/upstream/`:

1. **`WaterCMY/anatomy-3d`**
   - **Canonical URL:** `https://github.com/WaterCMY/anatomy-3d`
   - **Pinned Commit SHA:** `e8d40dca7b1f63f54567395df21d8b1b38a7e840`
   - **Code License:** `MIT` (stated in `LICENSE`)
   - **Asset License:** `CC BY-SA 2.1 Japan` (stated in `LICENSE-MODEL`, BodyParts3D MRI segmentation mesh `models/anatomy.glb`, 8.9 MB)
   - **Dependencies:** 0 external npm or pip dependencies. Three.js r160, OrbitControls, and GLTFLoader are self-contained in `vendor/three/`.
   - **Executable Scripts:** `serve.py` (Python stdlib HTTP server), `index.html` (browser client).
   - **Security Risks:** None. AST analysis shows no `os.system`, `subprocess`, `eval`, or high-risk hooks.
   - **Research Report:** `research/reports/watercmy--anatomy-3d/v1/report.md`

2. **`spacejohnlf/tcm-acupoints`**
   - **Canonical URL:** `https://github.com/spacejohnlf/tcm-acupoints`
   - **Pinned Commit SHA:** `04e35abb66585eb29c7250ea8ab5243c8c744f64`
   - **Code License:** `MIT` (stated in `LICENSE`)
   - **Asset License:** `CC BY-SA 4.0` (stated in `ATTRIBUTION.md`, Z-Anatomy derived model `public/models/body.glb`)
   - **Dependencies:** 13 npm dependencies (`three`, `react`, `react-dom`, `vite`, `gsap`, `lucide-react`).
   - **Executable Scripts:** `vite` (dev), `tsc -b && vite build` (build), `vite preview` (preview).
   - **Security Risks:** Standard Node.js build footprint. No `preinstall`/`postinstall` lifecycle scripts in `package.json`.
   - **Research Report:** `research/reports/spacejohnlf--tcm-acupoints/v1/report.md`

3. **`JICio/tcm-3d`**
   - **Canonical URL:** `https://github.com/JICio/tcm-3d`
   - **Pinned Commit SHA:** `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a`
   - **Code License:** `MIT` (stated in `LICENSE`)
   - **Asset License:** `CC BY 4.0` (stated in `NOTICE` and `public/ATTRIBUTION.md`, BodyParts3D 4.0 chunked mesh assets in `public/models/`)
   - **Dependencies:** 38 npm dependencies.
   - **Executable Scripts:** `npm run dev`, `npm run build`.
   - **Security Risks:** Standard Node.js build footprint. No high-risk lifecycle hooks.
   - **Research Report:** `research/reports/jicio--tcm-3d/v1/report.md`

---

## 3. Restricted Sandbox Web Bridging Architecture

To allow the Windows web browser to interact with isolated 3D WebGL applications without disabling container network isolation:

```
[ Windows Browser / Host ]
          |
     (TCP Loopback)
          v
[ 127.0.0.1:8092 Host Proxy ] (Threaded Unix Socket Bridge)
          |
    (Unix Domain Socket)
          v
[/bridge/app.sock on shared /tmp/msk-bridge-8092]
          |
[ Bubblewrap Sandbox Container ]
  - --unshare-all
  - --unshare-net (Strictly NO network interfaces / NO internet / NO host LAN access)
  - --unshare-pid (Isolated PID namespace)
  - --ro-bind /bin, /lib, /usr, venv
  - --ro-bind upstream_repo /app
  - --tmpfs /tmp (Volatile in-memory scratch)
  - RLIMIT_AS: 500 MB Virtual Address Space Ceiling
  - RSS Monitored via /proc/<pid>/status
```

Verified in `tests/security/test_sandbox_bridge.py`: Container remains detached from host network while delivering interactive WebGL pages to `127.0.0.1:<port>`.

---

## 4. Proposed Execution Commands (Awaiting Operator Approval)

In strict adherence to Directive 5, untrusted upstream execution remains blocked until separate operator approval is granted. The exact proposed commands for the three candidates are:

### Candidate 1: `WaterCMY/anatomy-3d` (Recommended First Candidate)
- **Status:** Already cloned at pinned commit `e8d40dca7b1f63f54567395df21d8b1b38a7e840`. Zero installation required.
- **Proposed Sandbox Launch Command:**
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
    --ro-bind /mnt/c/Users/tuanh/Downloads/msk-research-lab/3refs/upstream/watercmy--anatomy-3d /app \
    --tmpfs /tmp \
    --bind /tmp/msk-bridge-8092 /bridge \
    --chdir /app \
    --die-with-parent \
    -- /home/tuan/.venvs/msk-lab/bin/python3 /bridge/server.py --root /app --socket /bridge/app.sock
  ```
- **Host Bridge:** `http://127.0.0.1:8092/`
- **Memory Ceiling:** 500 MB `RLIMIT_AS`.

### Candidate 2: `spacejohnlf/tcm-acupoints`
- **Status:** Cloned at pinned commit `04e35abb66585eb29c7250ea8ab5243c8c744f64`.
- **Proposed Command:** Sandboxed Node.js preview or static build bridged to `http://127.0.0.1:8093/`.

### Candidate 3: `JICio/tcm-3d`
- **Status:** Cloned at pinned commit `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a`.
- **Proposed Command:** Sandboxed execution bridged to `http://127.0.0.1:8094/`.

---

## 5. Verification Evidence & Artifact Manifest

| Artifact | Path | SHA-256 Hash |
|---|---|---|
| **G2 Sandbox Screenshot (1366x768)** | `2data/evidence/R1_G2/run_g2_bubblewrap_001/dashboard_bubblewrap_sandbox_1366x768.png` | `03be7923f6af68098b4ffb6121d4c5e6b49cde9ba70c6080c18af8c6a6a30b01` |
| **G2 Evidence Report** | `2data/evidence/R1_G2/run_g2_bubblewrap_001/evidence_report_g2.json` | Sealed JSON manifest |
| **R4 Dashboard Screenshot (1366x768)** | `2data/evidence/R4/run_r4_atlas_001/dashboard_r4_atlas_1366x768.png` | `909557c64c2c0ac6204a317a1fc201aa2aed77cf2954f2083846446e5ebac879` |
| **R4 Evidence Report** | `2data/evidence/R4/run_r4_atlas_001/evidence_report_r4.json` | Sealed JSON manifest |
| **R1D Dashboard Screenshot** | `2data/evidence/R1D/run_r1d_discovery_001/dashboard_r1d_updated_1366x768.png` | Verified in commit `2966adf` |
| **Bubblewrap Security Suite** | `tests/security/test_sandbox_bubblewrap.py` | 8/8 passed |
| **Restricted Bridge Suite** | `tests/security/test_sandbox_bridge.py` | 1/1 passed |

---

## 6. How to Run and Verify the System

### Full Regression Test Suite (154 Tests)
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
/home/tuan/.venvs/msk-lab/bin/pytest tests
```
*Result: 154 passed, 0 failed in 123.93s.*

### Run Bubblewrap Security & Bridge Verification
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
/home/tuan/.venvs/msk-lab/bin/pytest tests/security/ -v
```

### Start MSK Research Lab OS Daemon
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
/home/tuan/.venvs/msk-lab/bin/python3 -m msk_research_lab serve --port 8091
```
Then visit `http://127.0.0.1:8091/` or `http://127.0.0.1:8091/dashboard` in a Windows web browser.

### Run System Diagnostics Doctor
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
bash scripts/doctor.sh
```
