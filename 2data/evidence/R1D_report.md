# R1D Release Gate & Evidence Report — Repository Discovery & Research Pipeline

**Release:** R1D (Repository Discovery & Research Pipeline Addendum v3.1)  
**Status:** **PASS** (DISC-01, DISC-02, DISC-03, DISC-04, REV-01, REV-02)  
**Security Invariant:** **G2 Live Execution BLOCKED** (`SANDBOX_UNAVAILABLE` on WSL2 host; native untrusted code execution fail-closed disabled)  
**Host Platform:** Windows 10 / Ubuntu WSL2 (8 GiB RAM, C: drive exclusively)  
**Automated Tests:** **135 passed, 0 failed** in 77.21 seconds  
**Database Schema:** Migration 0007 applied transactionally with SQLite WAL and Foreign Keys ON.

---

## 1. Executive Summary

Release R1D introduces the Repository Discovery & Research Pipeline to MSK Research Lab OS as defined in `1docs/MSK_Research_Lab_OS_v3.1_Discovery_Research_Roadmap_Addendum.md`. It provides local Markdown reference importing, live GitHub search with rate-limiting and metadata caching, persistent research lifecycle queue, read-only static AST code inspection, candidate comparison, source-cited research report generation, and Tri-Ledger evidence ingestion.

Crucially, in accordance with safety and licensing mandates:
1. Discovered and imported repositories are registered as `DISCOVERED_UNVERIFIED` — importing a reference list never auto-clones, installs, or executes code.
2. Clone approval is strictly separated from execution approval.
3. Because rootless container isolation (Podman/Docker) is unavailable on this WSL2 host, untrusted code execution remains fail-closed **BLOCKED**.
4. The REA reverse-engineering adapter detects host capability and cleanly reports `OPTIONAL_UNAVAILABLE` without blocking operations.

---

## 2. Gate Verification Matrix

| Gate | Requirement | Status | Positive Proof | Negative Proof |
|---|---|---|---|---|
| **DISC-01** | Local Markdown Reference Import | **PASS** | `research/references/awesome_msk_biomedical_repos.md` imported with 5 canonical candidates deduplicated and 6 exact line/label occurrences tracked. | Path traversal (`/etc/passwd`), non-markdown files (`.sh`, `.exe`), and oversized files (>5MB) rejected with `ImportSecurityError`. Deceptive lookalike URLs skipped. |
| **DISC-02** | Live GitHub Discovery & Caching | **PASS** | Keyword, topic, and language searches query GitHub API, compute transparent heuristic scores (no false medical claims), and cache responses with 24-hour TTL in SQLite. | Rate limits (HTTP 403/429) return `RATE_LIMITED` backoff gracefully; network disconnects return `OFFLINE` without unhandled crashes. |
| **DISC-03** | Research Queue & State Machine | **PASS** | State transitions across 16 lifecycle states (`DISCOVERED_UNVERIFIED` &rarr; `RESEARCH_QUEUED` &rarr; `STATIC_ANALYZED` &rarr; `ADOPT/ADAPT/REJECT/DEFER`). Distinct operator clone approval token. | Invalid transitions rejected with `LifecycleTransitionError`. Untrusted run requests fail-closed with `ExecutionBlockedError` when sandbox is unavailable. |
| **DISC-04** | Compare & Research Reports | **PASS** | Side-by-side candidate comparison matrix. Reports generated in `research/reports/<repo-id>/v<rev>/` with `report.md`, `report.json`, and `manifest.sha256`. Ingested into Tri-Ledger `evidence` table. | Missing locators or untrusted claims flagged as `UNREVIEWED_SOURCE_FINDING`. |
| **REV-01** | Static Source Investigation | **PASS** | Python AST parser and manifest analyzer detect project entrypoints, dependencies (npm, PyPI), 3D formats (`.glb`, `.obj`), UI frameworks (Three.js), and high-risk install hooks (`postinstall`, `os.system`). Read-only; zero code executed. | Files containing malicious syntax or system calls identified as `HIGH/MEDIUM RISK` without executing them. |
| **REV-02** | Optional REA Adapter | **PASS** | `probe_rea_adapter()` cleanly detects tool absence and reports `OPTIONAL_UNAVAILABLE` with clear operator explanation. Never auto-installs. | System operates seamlessly without REA installed. |
| **G2** | Upstream Sandbox Execution | **BLOCKED** | Safe isolation (`SANDBOX_UNAVAILABLE`) probe returns `can_execute_untrusted: false`. | Attempting to launch untrusted upstream process raises `ExecutionBlockedError`. |

---

## 3. Cryptographic Evidence Manifest

The R1D evidence bundle is sealed under `2data/evidence/R1D/run_r1d_discovery_001/`:

```
9601360cea50c6b1d3afc58c5f88d8fe51b267a5281a058730e66ac7ddea72b6  candidates.json
5492a173d752ed505b31ce862260766baa0c4d50ebe682e78ec1c583b49d6b34  discovery_summary.json
dd04dcf104c26f078e0697fa472d3b2f23df31f062f8f55154009550f4952da6  report_sample.md
```

Sample Research Report manifest: `b07d911ed7bbb4df7bee0ea7b7fae2634457eb4fc3adbe293f3532393ff607ab`  
Tri-Ledger Ingested Evidence ID: `evi_disc_cand_openanatomy_open-anatomy-browser_b07d911e`

---

## 4. Verification Instructions

Run the full automated test suite (135 tests):
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
.venv/bin/python3 -m pytest -q
```

Test discovery import CLI:
```bash
cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
.venv/bin/python3 -m msk_research_lab discovery list
```
