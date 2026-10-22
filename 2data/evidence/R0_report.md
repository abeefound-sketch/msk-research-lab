# [R0] Milestone Validation Report

**Project:** MSK Research Lab OS v3.0  
**Release:** R0 — Verified Local Foundation and Isolation Feasibility  
**State:** PASS (Foundation components verified; Sandbox isolation truthfully classified as `SANDBOX_UNAVAILABLE` / Gate: `BLOCKED`)  
**Execution timestamp / timezone:** 2026-10-23T01:03:00+07:00 (UTC+7)  
**Lab repo path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`)  
**Target display resolution:** 1366x768 (Windows Browser)  
**Database:** SQLite 3.37.2 (WAL Mode = True, Foreign Keys = True, Migrations = v1)  

---

## 1. Scope and Actual Changed Files

### Planned work packages:
- **R0-01:** Inspect workspace, `AGENTS.md`, 4 source specs, disk/CPU/RAM/WSL/network, Git, Python, Node, browser, and FTS5.
- **R0-02:** Clean Lab-owned repository layout, `pyproject.toml`, `.gitignore`, README, config, transactional migrations.
- **R0-03:** SQLite WAL, FKs, transactional migration runner, `GET /api/v1/health`.
- **R0-04:** `doctor` CLI, `serve` on `127.0.0.1:8091`, lifecycle logs, clean shutdown/restart, responsive Dashboard HTML at 1366x768.
- **R0-05:** Threat model and sandbox readiness probe (measured container runtime and isolation).
- **R0-06:** Candidate repo catalog seeded as unverified metadata (no automatic clone/execution).
- **R0-07:** Automated test harness (14 passing tests), security negative tests, evidence manifest.

### Explicitly NOT implemented (deferred to future authorized releases):
- No cloning or executing upstream candidate repositories (R1 scope).
- No document imports or OCR processing (R2 scope).
- No claims promotion or knowledge publication (R3 scope).
- No 3D WebGL renderer integration or medical claims (R4/R5 scope).
- No modification of MSK-Therapy-OS (R6 scope).

### Files added / updated:
- `src/msk_research_lab/core/config.py`: Configuration loader with TOML and env support.
- `src/msk_research_lab/core/db.py`: SQLite connection with WAL, FKs, timeout, health check.
- `src/msk_research_lab/core/migrations.py`: Transactional migration runner, migration 0001.
- `src/msk_research_lab/repos/catalog.py`: Catalog loader and repository seeder.
- `src/msk_research_lab/sandbox/probe.py`: Sandbox capability and container isolation probe.
- `src/msk_research_lab/api/app.py`: FastAPI dashboard, health API, loopback host guard.
- `src/msk_research_lab/__main__.py`: CLI commands (`doctor`, `serve`, `migrate`).
- `config/`: Seed configurations (`repo_catalog.json`, `run_profiles.json`, `release_gates.json`, `budgets.json`, `ontology_seed.json`, `task_backlog.json`).
- `schemas/`: JSON schemas and OpenAPI specification.
- `tests/unit/`: `test_config.py`, `test_db.py`, `test_sandbox.py`, `test_catalog.py`.
- `tests/integration/`: `test_health_api.py`, `test_dashboard.py`.
- `tests/security/`: `test_security_r0.py`.
- `2data/evidence/`: `R0_doctor.json`, `R0_health_response.json`, `browser_dashboard.html`, `pytest_results.txt`, `sha256-manifest.txt`.

---

## 2. Verified Environment, Rights and Permissions

| Property | Measured value | Status |
|---|---|---|
| OS / Kernel | Linux 6.18.54.1-microsoft-standard-WSL2 (x86_64 Ubuntu) | VERIFIED |
| Python Version | 3.10.12 (venv at `/home/tuan/.venvs/msk-lab`, symlinked to `.venv`) | VERIFIED |
| SQLite Version | 3.37.2 (FTS5 enabled, WAL mode enabled, FKs enabled) | VERIFIED |
| RAM (WSL Allocation) | 3.77 GiB total, 3.14 GiB available | VERIFIED |
| Disk C: (Windows SSD) | 149.4 GiB total, 44.7 GiB free (71% used) | VERIFIED |
| Disk D: | 89.0 GiB total, 12.64 GiB free (86% used — space-constrained) | VERIFIED |
| Git | `/usr/bin/git` v2.34.1 | VERIFIED |
| Node / npm | Node v20.20.2, npm 10.8.2 | VERIFIED |
| Container Isolation | Neither Podman nor Docker found in WSL environment | **SANDBOX_UNAVAILABLE** |
| Four Source Specs | All 4 SHA256 hashes matched against handoff manifest | VERIFIED |

---

## 3. Commands and Raw Evidence

| Step | Exact argv / cwd | Exit | Captured raw evidence |
|---|---|---|---|
| Static Handoff Validation | `python3 validate_handoff.py` | 0 | `1docs/MSK_Research_Lab_OS_v3.0_Handoff` |
| Environment Doctor | `python3 -m msk_research_lab doctor` | 0 | `2data/evidence/R0_doctor.json` |
| Migration Runner | `python3 -m msk_research_lab migrate` | 0 | `2data/db/lab.sqlite3` |
| Server Startup & Health | `curl http://127.0.0.1:8091/api/v1/health` | 0 | `2data/evidence/R0_health_response.json` |
| Dashboard UI | `curl http://127.0.0.1:8091/` | 0 | `2data/evidence/browser_dashboard.html` |
| Port Collision Detection | `python3 -m msk_research_lab serve --port 8091` | 1 | CLI stderr logged |
| Automated Test Suite | `pytest -v` (14 test cases) | 0 | `2data/evidence/pytest_results.txt` |
| Manifest Fingerprints | `sha256sum 2data/evidence/*` | 0 | `2data/evidence/sha256-manifest.txt` |

---

## 4. Gate-by-Gate Acceptance

| Gate ID | Requirement | Result | Evidence / Notes |
|---|---|---|---|
| **G1 (Base)** | Windows browser reaches WSL backend on `127.0.0.1:8091`; health/doctor, restart, 1366x768 friendly | **PASS** (Service & API) / **BLOCKED** (GUI screenshot from Windows GUI) | Service reachable, HTML dashboard rendered, loopback verified. Headless WSL session cannot invoke Windows GUI directly. |
| **SEC (Base)** | Loopback enforcement, deny-by-default execution, no secret leakage, sandboxing truth reporting | **PASS** | Non-loopback Host rejected with 403; wildcard CORS rejected; `SANDBOX_UNAVAILABLE` truthfully declared. |
| **G2** | 3 approved repos cloned, clicked, stopped | **NOT_TESTED** | Strictly deferred to R1 (Awaiting sandbox resolution / authorization). |
| **G3–G6** | Document library, FTS5 search, notes, backup/restore | **NOT_TESTED** | R2 scope. |
| **G7–G10** | Tri-Ledger, comparison, ontology, snapshots | **NOT_TESTED** | R3 scope. |
| **ATLAS-01..06** | 3D unified atlas & studio | **NOT_TESTED** | R4/R5 scope. |
| **BRIDGE-01..03** | MSK-Therapy-OS bridge & offline packages | **NOT_TESTED** | R6 scope. |

---

## 5. Failure and Security-Negative Tests

1. **SEC-01 (Non-Loopback Host Rejection):** `GET /api/v1/health` with `Host: malicious-domain.com` returned `403 Forbidden` (`{"detail": "Forbidden: MSK Research Lab OS only permits loopback access."}`).
2. **SEC-02 (CORS Wildcard Denial):** Preflight `OPTIONS` request with `Origin: http://evil-site.com` did NOT return `Access-Control-Allow-Origin: *` or allow evil-site.
3. **SEC-03 (Port Collision Guard):** Starting a second server instance on occupied port 8091 failed cleanly with exit code 1 and error `ERROR: Port 8091 on 127.0.0.1 is already in use by another process`.
4. **SEC-04 (Foreign Key Constraint Enforcement):** Inserting an execution approval referencing a non-existent repository was blocked with `sqlite3.IntegrityError: FOREIGN KEY constraint failed`.
5. **SEC-05 (Isolation Capability Truth):** `probe_sandbox_capabilities()` reported `can_execute_untrusted: False` and `readiness_gate: BLOCKED`, preventing unauthorized bare-metal execution.

---

## 6. Performance and Telemetry

- **Lab process idle RSS:** `45.25 MiB` (well below the `<~500 MiB` target budget).
- **Service startup latency:** `< 1.2 seconds`.
- **Database size:** `lab.sqlite3` is `32 KiB` with WAL journal.
- **Disk growth in R0:** `< 150 MiB` (mostly Python packages in virtual environment).

---

## 7. Known Problems and Blockers for R1

| Blocker ID | Observed Cause | Impacted Gate | Proposed Action / Workaround | Owner Approval Needed? |
|---|---|---|---|---|
| **BLK-01** | Podman and Docker are not installed in Ubuntu WSL2 | R1 (Gate G2: repo launch in sandbox) | Install rootless Podman in WSL2 or evaluate process-level sandbox before R1 live execution | **YES** |
| **BLK-02** | Direct invocation of Windows GUI browser from headless WSL session | G1 (visual screenshot artifact) | User opens `http://127.0.0.1:8091` in Windows Chrome/Edge to view live UI; HTML capture preserved | Optional / Informational |

---

## 8. Rollback and Cleanup

- Process stopped via SIGINT/SIGTERM without leaving orphan processes.
- Database reset can be achieved by removing `2data/db/lab.sqlite3` and re-running `python3 -m msk_research_lab migrate`.
- MSK-Therapy-OS was completely untouched.
