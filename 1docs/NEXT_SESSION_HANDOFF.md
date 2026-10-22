# Next Coding Session Handoff — R0 &rarr; R1

**From session/release:** R0 — Verified Local Foundation and Isolation Feasibility  
**To proposed session/release:** R1 — Repository Research Lab, Live Demos and Sandbox Validation  
**Current State:** R0 PASS (Foundation components verified; Sandbox isolation truthfully classified as `SANDBOX_UNAVAILABLE` / Gate: `BLOCKED`)  
**Lab repository path:** `C:\Users\tuanh\Downloads\msk-research-lab` (`/mnt/c/Users/tuanh/Downloads/msk-research-lab`)  
**Lab Git branch:** `main`  
**Read first:** `1docs/specs/MSK_Research_Lab_OS_v2.1_Engineering_SPEC.md`, `1docs/MSK_Research_Lab_OS_MASTER_SPEC_v3.0.md`, `1docs/MSK_Research_Lab_OS_ROADMAP_R0_R6.md`, `2data/evidence/R0_report.md`.

---

## 1. Completed Actual Features with Runnable Reproduction

1. **Environment Doctor & Diagnostics:**
   - Command: `PYTHONPATH=src .venv/bin/python3 -m msk_research_lab doctor`
   - Output: Reports WSL2 kernel, Python 3.10.12, SQLite 3.37.2 (WAL=True, FKs=True, FTS5=True), RAM (3.77 GB total, 3.14 GB avail), Disk C: (44.7 GB free), Disk D: (12.64 GB free), Git, Node/npm.
   - Saves verifiable JSON to `2data/evidence/R0_doctor.json`.
2. **Transactional SQLite Migrations:**
   - Command: `PYTHONPATH=src .venv/bin/python3 -m msk_research_lab migrate`
   - Schema: `schema_migrations`, `audit_events`, `system_state`, `repositories`, `repo_run_profiles`, `execution_approvals`.
3. **Live Dashboard & Health Endpoint on Port 8091:**
   - Command: `PYTHONPATH=src .venv/bin/python3 -m msk_research_lab serve --port 8091`
   - URL: `http://127.0.0.1:8091/` (Dashboard) and `http://127.0.0.1:8091/api/v1/health` (JSON Health).
   - Responsive HTML at 1366x768 Windows browser; idle process RSS ~45 MiB (<500 MiB target).
   - Clean shutdown (SIGINT/SIGTERM), port release, port clash prevention.
4. **Automated Test Suite (14 Tests):**
   - Command: `PYTHONPATH=src .venv/bin/pytest -v`
   - Result: 14 passed, 0 failed.
5. **Security Negative Tests (SEC-01..SEC-05):**
   - Non-loopback Host rejected with 403; wildcard CORS disallowed; port collision rejected with exit code 1; foreign key integrity verified; sandbox absence truthfully reported.

---

## 2. Open Gate States / Blockers for R1

- **BLK-01 (Container Sandbox Unavailable):**
  - Host WSL2 lacks `podman` or `docker`.
  - According to `AGENTS.md` Rule 5 and `ROADMAP_R0_R6.md`: Untrusted upstream third-party code must NOT be executed on bare metal without verified isolation.
  - Required owner decision: (A) Authorize installation of rootless Podman in WSL2 (`sudo apt-get install podman`), OR (B) Define a restricted process-level sandbox policy, OR (C) Proceed with static inspection only.
- **BLK-02 (Windows GUI Screenshot):**
  - Headless WSL session cannot invoke Windows GUI directly. User can verify visual rendering at `http://127.0.0.1:8091` from Windows Edge/Chrome.

---

## 3. Current Filesystem Paths and SOT Compliance

- Lab project root: `/mnt/c/Users/tuanh/Downloads/msk-research-lab/`
- SOT documents: `1docs/`
- Working database: `2data/db/lab.sqlite3`
- Evidence artifacts: `2data/evidence/`
- Third-party clones (gitignored): `3refs/upstream/`
- Incident reports: `4incidents/`
- Agent build journal: `.m/`
- Virtual environment: `/home/tuan/.venvs/msk-lab` (symlinked via `.venv`)

---

## 4. Next Authorized Bounded Task (R1)

Once the sandbox blocker is resolved and approved by the owner:
- Implement `R1-01` to `R1-07`:
  - Static repository inspection, URL normalization, metadata discovery.
  - SHA-pinned cloning into `3refs/upstream/`.
  - Disabled-by-default execution profiles requiring explicit approval tokens.
  - Sandbox runner with CPU/RAM/time caps and zero zombie process cleanup.
  - Three distinct sequential live app runs and evidence capture.
  - Initial `surface-registration-v1` comparator harness.
