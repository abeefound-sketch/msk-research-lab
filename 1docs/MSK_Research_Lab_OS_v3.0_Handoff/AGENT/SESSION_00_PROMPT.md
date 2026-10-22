# Coding Agent Mission 00 — Implement R0 Only

You are the implementing coding agent for **MSK Research Lab OS v3.0**. The attached handoff directory contains the authoritative spec, roadmap, acceptance matrix, rights/security rules, schema seeds and four immutable reference specs. Read `00_START_HERE.md`, `AGENT/AGENTS.md`, `SPEC/MASTER_SPEC_v3.0.md`, `SPEC/ROADMAP_R0_R6.md`, `SPEC/ACCEPTANCE_MATRIX.md` and the R0-relevant technical docs before editing files.

**Scope of this session: R0 only.** Build a new **standalone** `msk-research-lab-os` application repository in a new directory. Do not modify MSK-Therapy-OS or any existing work. Do not execute new upstream GitHub apps, npm/pip install scripts from those repos, or download heavy model assets. Explicit approvals for those activities are not implied by this task.

## Execute the R0 tasks in order

1. Inspect real Windows/WSL environment and available workspaces, RAM, disk, Python, Git, Node, container runtime, GUI/browser and localhost port behavior. Document facts, measurements and unknowns; choose a safe independent path. Verify the supplied spec files/hashes.
2. Create project skeleton: Python 3.11+ package, pinned dependencies, `.gitignore`, README, core config, SQLite WAL+FKs+FTS5 and transactional migrations, CLI `doctor` and `serve`, basic audit state.
3. Implement `GET /api/v1/health`, a *real* minimal Dashboard on localhost `127.0.0.1:8091`, clear `READY/BLOCKED` indicators and easy restart. Validate from **actual Windows browser** at 1366x768 if accessible; record limitations otherwise.
4. Seed repo catalog as **unverified metadata only** (do not clone), disabled-by-default run profiles and explicit security policy; add static registration and validation tests if safely in R0 scope.
5. Inspect whether rootless Podman or equivalent containment can be verified on this host, including mount isolation, network denial and CPU/memory limits. Do not claim a functioning sandbox from config files alone. If unavailable, report `SANDBOX_UNAVAILABLE` and R1 dependency `BLOCKED`, but still finish independent R0 components.
6. Implement useful unit/integration tests, negative cases (path/port/missing dependency) and a basic browser smoke test; produce true command outputs, exit statuses, screenshots, real process logs, hashes and a Lab Git commit.
7. Produce `evidence/R0_report.md` following the supplied milestone template, update state of relevant G1/SEC subchecks precisely, record any `BLOCKED` and make `NEXT_SESSION_HANDOFF.md` for R1 only after honest R0 assessment.

**Never mark G2–G10, ATLAS-* or BRIDGE-* PASS in R0.** Do not claim a working Atlas, medical correctness, imported book library, repo execution sandbox or Therapy integration without evidence.

## Expected final response from agent

Provide created Lab repository path, Lab Git SHA, actual machine checks, exact reproducible setup/start/test commands with exit codes, Dashboard URL, real screenshot and evidence artifact paths, tests PASS/FAIL/BLOCKED/NOT_TESTED counts, security/sandbox status, file change summary and next-session handoff. If you cannot access the actual Windows GUI, state `BLOCKED` for that acceptance component and retain honest partial R0 output.

**Strict stop condition:** stop after implementing, testing, documenting R0. Await a separate explicitly authorized task for R1, especially for third-party clone/install/launch or system configuration modifications.
