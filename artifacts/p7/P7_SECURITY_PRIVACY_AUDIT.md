# MSK Research Lab OS — P7 Security, Privacy & Safety Audit

**Audit Role:** Biomedical Software Safety Engineer & Security Auditor  
**Date:** 2026-10-30  
**Scope:** Offline Threat Modeling, Pseudonymization Cryptography, Boundary Enforcement, Injection Protection, Clinical Governance  

---

## 1. Executive Summary & Clinical Governance Invariant

The MSK Research Lab OS is designated as an **Offline Educational, Documentation, and Synthetic Research Workstation**.

### Invariant: `CLINICAL_REALWORLD_GATE = BLOCKED`
- This status is permanent and server-authoritative.
- The software **contains zero device drivers or communication channels to command physical stimulation devices** (e.g. DDS bioelectric stimulators). Readouts are documented as passive text only.
- The software **never executes automated diagnosis or issues clinical treatment prescriptions**.
- A medical disclaimer banner is present, but **disclaimers never substitute for architectural code enforcement**.

---

## 2. Threat Modeling & Security Controls Matrix

| Threat Category | Potential Attack Vector | Applied Engineering Mitigation | Verification Mechanism | Status |
|---|---|---|---|---|
| **Patient Identification & Privacy** | Dictionary attack or rainbow tables against patient primary keys. | **HMAC-SHA256 Pseudonymization:** Keyed HMAC using a 32-byte secret pepper stored at `2data/db/.workstation_pepper` with filesystem permissions `0600`. | [`test_patient_keyed_pseudonym_and_red_flags`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_workstation_api.py#L32) | **VERIFIED** |
| **SQL Injection** | Malicious SQL fragments in patient names, complaints, or search terms. | **Strict Parameterization:** 100% of SQLite database queries in `patient_manager.py`, `therapy_manager.py`, and `camera_service.py` utilize parameterized `?` placeholders. | Static code audit + API fuzzing in [`test_workstation_api.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_workstation_api.py) | **VERIFIED** |
| **Cross-Site Scripting (XSS)** | Injection of `<script>` or `<img onerror=...>` in patient profiles rendered in SPA tables. | **Contextual Escaping:** All dynamically rendered table rows, modal fields, and citation snippets are filtered through `escapeHtml()` in [`workstation_ui.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/workstation_ui.py#L780). | [`test_e2e_11_dom_injection_sanitization`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_recovery_e2e_journeys.py#L351) | **VERIFIED** |
| **CSV Formula Injection** | Cells starting with `=CMD()`, `+`, `-`, `@` executing arbitrary code in Excel. | **Prefix Sanitization:** [`sanitize_csv_cell()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/progress_tracker.py#L77) prefixes any leading formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) with a single quote `'`. | [`test_e2e_05_progress_analytics_and_csv_export`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_recovery_e2e_journeys.py#L210) | **VERIFIED** |
| **Path Traversal** | Malicious relative paths (e.g. `../../etc/passwd`) in model file URLs or markdown import. | **Path Resolution Guard:** Endpoints in `app.py` resolve candidate paths strictly against allowed whitelisted base directories (`3refs/upstream` and `2data/models`). | [`test_api_get_model_chunk_and_traversal_guard`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_atlas_api.py#L110) | **VERIFIED** |
| **Network & Telemetry Leak** | Secret exfiltration, telemetry pings, unapproved cloud calls. | **Loopback-Only Interface:** Workstation binds strictly to `127.0.0.1` by default. Zero external network sockets or analytics beacons exist in the codebase. | Network socket audit + offline operation tests | **VERIFIED** |
| **Clinical Red-Flag Bypass** | Practitioner attempting routine manual or electrotherapy on patients with acute red flags. | **Server-Authoritative Hard Stop:** [`record_therapy_session()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/therapy_manager.py#L124) raises [`TherapySessionError`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/therapy_manager.py#L11) (`CLINICAL_RED_FLAG_BLOCKED`), returning HTTP 400. | [`test_e2e_03_red_flag_hard_stop`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_recovery_e2e_journeys.py#L100) | **VERIFIED** |

---

## 3. Cryptographic Key Handling & Pepper Rotation

### 3.1 Pepper Generation & Storage
- **Algorithm:** HMAC-SHA256 (RFC 2104).
- **Source:** [`src/msk_research_lab/workstation/patient_manager.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/patient_manager.py#L18-L45)
- **Key Generation:** High-entropy pseudo-random bytes generated via `secrets.token_bytes(32)`.
- **Local Storage:** `2data/db/.workstation_pepper`.
- **Permissions:** Restricted via `os.chmod(pepper_file, 0o600)` (read/write by owner only; inaccessible to other system users).
- **Environment Override:** Supports `MSK_WORKSTATION_PEPPER` environment variable for automated testing or institutional secret vaults.

### 3.2 Key Rotation Protocol & Requirements
1. **Pseudonym Hash Invariance:**
   The HMAC pseudonym hash is stored as `pseudonym_hash` in the `patients` table. If the secret pepper is rotated without migration, existing hashes would become un-linkable to new HMAC queries.
2. **Rotation Specification for Future Enterprise Release (P8+):**
   - Implement key versioning metadata in the database: `pepper_version` column.
   - When rotating keys:
     1. Retain the prior pepper $K_{old}$ as read-fallback.
     2. Write the new pepper $K_{new}$.
     3. Re-calculate and update `pseudonym_hash = HMAC(K_new, patient_id)` for all existing patient records in a single transactional migration.

---

## 4. Red-Flag Clinical Boundary Enforcement

In [`src/msk_research_lab/workstation/patient_manager.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/patient_manager.py#L58-L75), incoming clinical screening flags are audited:
- Fever
- Unexplained weight loss
- Bowel or bladder dysfunction (cauda equina)
- Progressive motor deficit
- Saddle anesthesia
- Unremitting night pain

### Verification of Server Enforcement
When any critical flag is set, `requires_referral` evaluates to `True`.  
In [`src/msk_research_lab/workstation/therapy_manager.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/therapy_manager.py#L124):
```python
if red_flags.get("requires_referral"):
    is_referral_only = (
        soap_notes and "REFERRAL" in soap_notes.get("assessment", "").upper()
        and not applied_modalities
        and not motion_assessment_ids
        and not (dds_device_records and dds_device_records.get("device_used"))
    )
    if not is_referral_only:
        raise TherapySessionError("CLINICAL_RED_FLAG_BLOCKED: Patient has active clinical red flags requiring specialist medical referral.")
```
Any attempt to submit routine modalities (massage, electrotherapy, active exercise) or kinematic assessments returns HTTP 400 and blocks database persistence.
