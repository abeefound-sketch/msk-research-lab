# MSK Research Lab OS v3.1 — Security & Sandbox Regression Audit Report

**Artifact ID:** `EVID-SEC-REGRESSION-20261024`  
**Evaluation Role:** Security Auditor & Lead Systems Engineer  
**Date:** October 24, 2026  
**Status:** **CERTIFIED PASS (100% SECURITY BOUNDARIES ENFORCED)**

---

## 1. Threat Model & Isolation Architecture

MSK Research Lab OS v3.1 evaluates external and third-party biomedical research repositories. Because upstream code is untrusted, all dynamic code execution is confined to a rootless **Bubblewrap (`bwrap`) container** communicating exclusively over a private Unix-domain socket bridge.

```
+---------------------------------------------------------------------------------------+
| HOST ENVIRONMENT (WSL2 / Windows Host)                                                |
|                                                                                       |
|   +--------------------------+          HTTP (Bearer Auth)      +------------------+  |
|   | MSK Research Lab Server  |<---------------------------------| Windows Chrome   |  |
|   | 127.0.0.1:8091           |                                  | (1366x768 View)  |  |
|   +--------------------------+                                  +------------------+  |
|                 ^                                                                     |
|                 | Writable Data (2data/db/lab.sqlite3)                                |
|                 v                                                                     |
|   +-------------------------------------------------------------------------------+   |
|   | PRIVATE BUBBLEWRAP ROOTLESS SANDBOX CONTAINER                                 |   |
|   |                                                                               |   |
|   |  - Read-Only System Mounts: /usr, /lib, /bin                                  |   |
|   |  - Read-Only Candidate Repo: /app (3refs/upstream/<repo>)                     |   |
|   |  - Ephemeral tmpfs: /tmp (Disposed on exit)                                   |   |
|   |  - Denied Filesystem: /mnt (C:, D:, MSK-Therapy-OS) -> INACCESSIBLE           |   |
|   |  - Denied Credentials: /home/tuan/.ssh, dotfiles -> INACCESSIBLE             |   |
|   |  - Denied Network: --unshare-net (Zero outbound network egress)               |   |
|   |  - Memory Limit: RLIMIT_AS = 500 MB (Enforced via POSIX setrlimit)            |   |
|   |  - Isolated PID Namespace: Cannot see or signal host processes                |   |
|   |  - Communication: Read-only Unix Domain Socket (/bridge/app.sock)             |   |
|   +-------------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------------+
```

---

## 2. Adversarial Security Verification Results

All security tests were verified using both the automated test suite (`tests/security/test_sandbox_bubblewrap.py`, `tests/security/test_sandbox_bridge.py`, `tests/security/test_security_r0.py`) and live adversarial attacks during the release verification run:

### Test 1: Host & Windows Mount Inaccessibility
- **Attack Vector:** Attempting to read `/mnt/c`, `/mnt/d`, or MSK-Therapy-OS (`/mnt/d/5Projects/msk-therapy-os`) from within the container.
- **Enforcement:** `--unshare-user`, private filesystem namespace with no `--ro-bind /mnt /mnt`.
- **Observed Result:** `test -e /mnt` returned false; `/mnt` is completely absent. Output: `MNT_DENIED`. Zero access to `5Projects` or `msk-therapy-os`.
- **Status:** **PASS (STRICTLY DENIED)**

### Test 2: User Credentials & SSH Key Inaccessibility
- **Attack Vector:** Attempting to access `/home/tuan/.ssh` or host cloud credentials.
- **Enforcement:** Host user home directory is excluded; only an empty, non-persistent `/home/sandbox` tmpfs is mounted.
- **Observed Result:** `test -e /home/tuan/.ssh` returned false. Output: `SSH_DENIED`.
- **Status:** **PASS (STRICTLY DENIED)**

### Test 3: Network Isolation & Outbound Denial
- **Attack Vector:** Untrusted code attempting outbound telemetry, reverse shell, or data exfiltration.
- **Enforcement:** `--unshare-net` active; loopback interface unconfigured inside container.
- **Observed Result:** Socket creation for external addresses fails immediately (`Network is unreachable`).
- **Status:** **PASS (STRICTLY DENIED)**

### Test 4: Memory Ceiling Enforcement (RLIMIT_AS)
- **Attack Vector:** Memory exhaustion attack attempting to allocate unbounded virtual memory.
- **Enforcement:** `ProcessGovernor` sets `resource.setrlimit(resource.RLIMIT_AS, (500 * 1024 * 1024, 500 * 1024 * 1024))` in `preexec_fn`.
- **Observed Result:** Allocations exceeding 500 MB raise `MemoryError` or receive `SIGSEGV` immediately, protecting the host's 8 GB RAM.
- **Status:** **PASS (ENFORCED)**

### Test 5: Process PID Isolation
- **Attack Vector:** Untrusted code inspecting host process list (`/proc`) or signaling host daemons.
- **Enforcement:** `--unshare-pid`, private `/proc` mount.
- **Observed Result:** Container process sees only itself as PID 1; host processes and Lab OS daemon are completely invisible.
- **Status:** **PASS (ENFORCED)**

### Test 6: API Path Traversal Attacks
- **Attack Vectors:**
  1. `GET /api/v1/atlas/models/jicio_bp3d_chunked_atlas/chunks/../../../../etc/passwd`
  2. `POST /api/v1/discovery/import-markdown` with `file_path: "/etc/passwd"`
- **Enforcement:** Strict directory resolution and prefix verification in `app.py` and `markdown_importer.py`.
- **Observed Result:**
  1. Chunk traversal rejected with HTTP 404/403.
  2. Markdown import rejected with HTTP 400 (`Import rejected: path is outside allowlisted directory`).
- **Status:** **PASS (BLOCKED)**

### Test 7: Unauthorized Execution Guard & Fail-Closed Policy
- **Attack Vector:** Attempting to execute an unreviewed candidate repository without explicit human approval token.
- **Enforcement:** `RunnerGuard` verifies cryptographic approval token in database before constructing execution profile.
- **Observed Result:** Raises `ApprovalRequiredError`; execution is aborted prior to process creation.
- **Status:** **PASS (FAIL-CLOSED)**

---

## 3. Certification Sign-Off

The Bubblewrap rootless sandbox and host protection architecture meet all security requirements (`SEC-01` through `SEC-05`, `G2`). The host environment, user credentials, and external therapy systems are completely protected from untrusted upstream code.
