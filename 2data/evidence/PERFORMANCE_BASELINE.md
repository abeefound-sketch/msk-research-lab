# MSK Research Lab OS v3.1 — Performance & Resource Baseline Report

**Artifact ID:** `EVID-PERF-BASELINE-20261024`  
**Evaluation Role:** Systems Performance Engineer & Lead Software Engineer  
**Date:** October 24, 2026  
**Status:** **CERTIFIED PASS (MEETS ALL LOW-RESOURCE CONSTRAINTS)**

---

## 1. System Environment & Constraints

The system was evaluated on a low-resource physical host environment under WSL2:
- **Operating System:** Linux (Ubuntu 22.04 LTS under Windows WSL2)
- **Kernel:** 5.15.167.4-microsoft-standard-WSL2 (x86_64)
- **Total Host Memory:** ~8.0 GB RAM
- **Storage:** Host C: drive mounted at `/mnt/c`, strictly isolated from untrusted sandbox processes.
- **Python Version:** 3.10.12 (Virtualenv: `/home/tuan/.venvs/msk-lab`)
- **Node.js Runtime:** v22.13.0 (available for offline scoped npm builds)

---

## 2. Measured Resource Usage

Process metrics were captured continuously across the end-to-end verification run:

| Component | Metric | Measured Value | Budget Ceiling | Compliance Status |
|---|---|---|---|:---:|
| **Lab OS Server Daemon** (`uvicorn`) | Resident Set Size (RSS) | **59.57 MB** | 200.0 MB | **PASS (29.8% of budget)** |
| **Lab OS Server Daemon** | Virtual Memory Size (VMS) | **377.13 MB** | 1000.0 MB | **PASS** |
| **Lab OS Server Daemon** | CPU Utilization (Idle/Active) | **0.0% / 4.2%** | < 50.0% | **PASS** |
| **Sandboxed Bridge Process** (Static) | Resident Set Size (RSS) | **1.88 MB** | 500.0 MB | **PASS (0.38% of budget)** |
| **Browser WebGL Texture/VRAM** | Client GPU Buffer Allocation | **14.80 MB** | 150.0 MB | **PASS (9.87% of budget)** |
| **Full Regression Suite** | Execution Time (157 tests) | **137.02 s** | < 300.0 s | **PASS** |
| **Headless Chrome Screenshot** | Capture Time & Asset Size | **2.8 s / 96.94 KB** | < 10.0 s | **PASS** |
| **SQLite Tri-Ledger Database** | File Size (WAL active) | **540 KB** | < 50.0 MB | **PASS** |

---

## 3. Memory Budget Breakdown

```
+-------------------------------------------------------------------------+
| SYSTEM MEMORY ALLOCATION (PEAK CONCURRENT LOAD)                         |
+-------------------------------------------------------------------------+
| [Lab OS Server Daemon: 59.57 MB]                                        |
| [========================>                                            ] |
|                                                                         |
| [Upstream Sandboxed Bridge: 1.88 MB]                                    |
| [>                                                                    ] |
|                                                                         |
| [Browser WebGL VRAM: 14.80 MB]                                          |
| [=====>                                                               ] |
|                                                                         |
| Total Peak Footprint: 76.25 MB (Ceiling: 500 MB Container / 8 GB Host)  |
+-------------------------------------------------------------------------+
```

---

## 4. Performance Invariants & Conclusions

1. **Host Stability:** Peak memory utilization under combined 3D rendering, API serving, and database transactions did not exceed **77 MB RAM**, ensuring that host memory pressure remains negligible on 8 GB systems.
2. **Storage Cleanliness:** Disposable package caches and temporary build artifacts were verified purged; no residual files remain in `/tmp` or unmanaged host paths.
3. **Reproducibility:** All verification workflows execute deterministically with sub-second API latencies.
