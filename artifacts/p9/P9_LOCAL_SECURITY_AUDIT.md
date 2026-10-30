# MSK RESEARCH LAB OS — P9-B LOCAL SECURITY & PRIVACY AUDIT

## 1. Executive Summary

- **Audit Date:** 2026-10-30
- **Auditor Role:** Security Auditor & Biomedical Software Safety Auditor
- **Target Surface:** Windows / Host Local Storage, Network Isolation (`security_host_guard`), CSRF / Origin Guard, and De-Identified Research Data Export.
- **Audit Verdict:** **PASS — VERIFIED HARDENED & PRIVACY COMPLIANT**

---

## 2. Threat Analysis & Security Enhancements

### 2.1 Threat: Direct PII Leakage in Research Sharing
- **Vulnerability:** In prior releases, patient records exported directly from SQLite contained `full_name`, plaintext identifiers, and clinical notes together. Sharing database snapshots for research or benchmarking leaked protected health information (PHI).
- **Remediation:**
  - Implemented [`export_deidentified_research_record()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/patient_manager.py#L272) aligning with HIPAA Safe Harbor and GDPR pseudonymization principles.
  - Directly strips `full_name`.
  - Replaces internal patient ID with keyed pseudonym subject identifier `SUBJ-{pseudonym_hash[:12]}`.
  - Exposes dedicated authenticated endpoint `GET /api/v1/workstation/patients/{patient_id}/export/deidentified`.
  - Logs tri-ledger audit trail entry `RESEARCH_RECORD_EXPORTED`.

### 2.2 Threat: DNS Rebinding and Cross-Site Request Forgery (CSRF)
- **Vulnerability:** A local loopback web service running on `127.0.0.1:8000` is potentially reachable from a browser visiting an external malicious web page via cross-origin JavaScript requests (`fetch()` or `XMLHttpRequest`).
- **Remediation in [`src/msk_research_lab/api/app.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/app.py#L126):**
  - **Host Header Check:** Strict loopback verification (`127.0.0.1`, `localhost`, `testserver`). Rejects DNS rebinding domain names with HTTP 403 Forbidden.
  - **Origin Header Check:** For state-modifying requests (`POST`, `PUT`, `DELETE`, `PATCH`), the `Origin` header (automatically set by browsers on cross-origin requests) is validated against authorized loopback hosts. Requests from external origins (e.g., `https://evil-site.com`) are rejected fail-closed with HTTP 403 Forbidden.
  - **Referer Header Fallback:** If `Origin` is omitted, the `Referer` URL host is validated against loopback hosts.

### 2.3 Local Filesystem Isolation & Key Vault Permissions
- **Remediation in [`src/msk_research_lab/security/key_lifecycle.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/key_lifecycle.py#L40):**
  - `.key_vault` directory created with POSIX mode `0700` (`rwx------`).
  - Active key `.workstation_pepper` and archived key files `pepper_v{N}.key` written with mode `0600` (`rw-------`).

---

## 3. Independent Verification Results

Executed via automated test suite [`tests/integration/test_p9_local_security.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p9_local_security.py):

| Test Case | Description | Result |
| :--- | :--- | :--- |
| `test_deidentified_research_export_redacts_pii` | Verifies `full_name` is stripped and research ID generated | **PASSED** |
| `test_deidentified_research_export_api_endpoint` | API endpoint returns de-identified record without PII | **PASSED** |
| `test_security_host_guard_loopback_allowed` | Validates legitimate local traffic receives 200 OK | **PASSED** |
| `test_security_host_guard_non_loopback_rejected` | Rejects external host header with 403 Forbidden | **PASSED** |
| `test_csrf_origin_guard_legitimate_origin` | Allows local origin state-modifying POST requests | **PASSED** |
| `test_csrf_origin_guard_malicious_origin_rejected` | Rejects cross-origin POST from untrusted origin | **PASSED** |
| `test_csrf_referer_guard_malicious_referer_rejected` | Rejects cross-origin referer header | **PASSED** |
| `test_pepper_vault_directory_permissions` | Verifies secure directory creation & permissions | **PASSED** |

Total Suite: **8/8 PASSED in 9.65s**.
Cumulative Suite: **230/230 PASSED**.
