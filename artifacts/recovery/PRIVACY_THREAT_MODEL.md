# MSK Research Lab OS v3.2 — Privacy & Security Threat Model

**Date:** 2026-10-29  
**Version:** v3.2 Recovery  
**Target:** Workstation Security Architecture (`src/msk_research_lab/workstation/`)  
**Security Posture:** Offline-First, Zero-Cloud, Strict Pseudonymization, Synthetic-Only Invariant.

---

## 1. System Overview & Trust Boundaries

MSK Research Lab OS is engineered as a **Personal Offline Workstation** designed for education, documentation, and biomechanical research with synthetic data.

### Trust Boundary Architecture
```
+-------------------------------------------------------------------------------+
| UNTRUSTED EXTERNAL ENVIRONMENT (Internet / Cloud / External Networks)         |
| [BLOCKED: Outbound sockets disabled, zero telemetry, zero cloud dependencies] |
+-------------------------------------------------------------------------------+
                                      | (Airgap / No Network Calls)
+-------------------------------------------------------------------------------+
| LOCAL HOST ENVIRONMENT (Linux / WSL2 Host)                                    |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | MSK WORKSTATION BOUNDARY (Port 8091 Localhost Only)                     |  |
|  |                                                                         |  |
|  |  +------------------+       +-------------------+                       |  |
|  |  | Client Browser   | <---> | FastAPI Web Server|                       |  |
|  |  | (escapeHtml XSS) |       | (Input Validation)|                       |  |
|  |  +------------------+       +---------+---------+                       |  |
|  |                                       |                                 |  |
|  |                 +---------------------+---------------------+           |  |
|  |                 |                                           |           |  |
|  |        +--------v-------+                           +-------v-------+   |  |
|  |        | SQLite DB (v9) |                           | Camera Engine |   |  |
|  |        | (WAL mode,     |                           | (Fail-Closed) |   |  |
|  |        |  HMAC Pepper)  |                           +---------------+   |  |
|  |        +----------------+                                               |  |
|  |                 |                                                       |  |
|  |        +--------v---------------+                                       |  |
|  |        | Export Sanitizer       |                                       |  |
|  |        | (CSV Injection Defense)|                                       |  |
|  |        +------------------------+                                       |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | BUBBLEWRAP ROOTLESS SANDBOX (External Code Execution - SEC-01..05)      |  |
|  | (Network Denied, Host Mounts Denied, RAM Capped, PID Namespace Isolated) |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
```

---

## 2. Threat Analysis & Mitigations

### Threat 1: Formula Injection / CSV Injection (CWE-1236)
- **Vector:** An operator enters a patient complaint or note containing spreadsheet formula triggers (e.g. `=CMD|' /C calc'!A0`, `+1+1`, `-@SUM(A1:A10)`, or tab/carriage return control characters). When exporting progress data via `GET /patients/{id}/export/csv`, an external spreadsheet viewer (Microsoft Excel, LibreOffice Calc) could execute untrusted commands.
- **Mitigation:** Implemented `sanitize_csv_cell()` in `src/msk_research_lab/workstation/progress_tracker.py`. Any cell starting with `=, +, -, @, \t, \r` is automatically prepended with a single quote (`'`), rendering it inert plain text.

### Threat 2: Stored Cross-Site Scripting / DOM Injection (CWE-79)
- **Vector:** An adversary enters HTML or JavaScript payloads (`<script>alert(1)</script>`, `<img src=x onerror=...>`) into patient name, complaint, or citation fields. When rendered in the browser DOM, script execution occurs.
- **Mitigation:** Implemented strict `escapeHtml()` sanitization across `src/msk_research_lab/api/workstation_ui.py` for all dynamically generated HTML tables, modals, dropdowns, and search cards.

### Threat 3: Patient Identifiers & PII Exposure
- **Vector:** Accidental leakage of real patient identities in database dumps, backups, or terminal logs.
- **Mitigations:**
  1. **Strict Synthetic Data Policy:** The system enforces an invariant: only synthetic, de-identified profiles are registered (`is_synthetic = 1`).
  2. **Installation-Specific Secret Pepper:** Replaced hardcoded pepper strings with dynamic key generation (`2data/db/.workstation_pepper`, POSIX permissions `0600`). Patient pseudonym hashes are calculated via `HMAC-SHA256(full_name, pepper)`.
  3. **Diagnostic Anonymization:** System diagnostics and `baseline.json` record only counts and schema metadata, never raw patient records or notes.

### Threat 4: Fake Biometric Data Masquerading as Real Measurement
- **Vector:** A user or script attempts to record phantom kinematic ROM angles while the camera is disconnected, compromising research data integrity.
- **Mitigation:** Server enforces fail-closed error handling (`CameraUnavailableError`, `InsufficientLandmarksError`). All synthetic demonstration fixtures are explicitly segregated into `mode="DEMO"`, logged as `DEMO_FIXTURE`, and committed with `is_synthetic = 1`.

### Threat 5: Accidental Hardware Actuation (Clinical Safety Gate)
- **Vector:** Software driving electrotherapy or mechanical therapy stimulation devices without certified medical approval.
- **Mitigation:** The system has **zero hardware drivers or actuation interfaces** for physical stimulation devices. The `clinical_realworld_gate` is permanently locked to `BLOCKED`. Modality records (`dds_device_records_json`) are passive audit documentation only.
