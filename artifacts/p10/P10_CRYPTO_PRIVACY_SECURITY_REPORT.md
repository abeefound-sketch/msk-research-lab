# MSK Research Lab OS — P10 Cryptography, Privacy & Local Security Audit

**Milestone:** P10  
**Security Role:** Applied Cryptography Security Auditor, Privacy Engineer, and Application Security Reviewer  
**Target Files:**
- [`src/msk_research_lab/security/openssl_gcm.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/openssl_gcm.py)
- [`src/msk_research_lab/security/permissions.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/permissions.py)
- [`src/msk_research_lab/security/key_lifecycle.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/key_lifecycle.py)
- [`src/msk_research_lab/workstation/patient_manager.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/patient_manager.py)
- [`src/msk_research_lab/api/app.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/api/app.py)

---

## 1. Cryptographic Architecture Audit (P10-A1)

### Standard AES-256-GCM AEAD Container (`MSKENC02`)
The primary backup container format standardizes on NIST SP 800-38D AES-256-GCM with 128-bit GMAC authentication tags and hardware acceleration via dynamic system OpenSSL `libcrypto`.

```
Container Format: MSKENC02
[8 Bytes Magic: b"MSKENC02"]
[16 Bytes Salt (CSPRNG os.urandom)]
[12 Bytes IV / Nonce (96-bit standard GCM nonce)]
[16 Bytes GMAC Tag (128-bit authentication tag)]
[N Bytes AES-256 Ciphertext Payload]
AAD: b"MSKENC02" + salt + iv
```

### Clarification of FIPS Compliance Claim (DEF-20)
- **Finding:** Milestone P9 referred to the module as "FIPS-compliant". Direct runtime inspection via `ctypes` querying `EVP_default_properties_is_fips_enabled(None)` confirmed that standard Linux/Windows system `libcrypto` distributions operate under the default (non-FIPS) provider (`is_fips: False`). Calling standard OpenSSL EVP functions does not constitute CMVP FIPS 140-2/3 validation.
- **Remediation:**
  1. Implemented `probe_fips_status() -> Dict[str, Any]` in `openssl_gcm.py`.
  2. Corrected all documentation, comments, and export metadata to state: **"NIST SP 800-38D standard-aligned AES-256-GCM AEAD (Non-FIPS default provider)"**.
  3. Added regression test `test_openssl_fips_status_probe_reporting` verifying accurate reporting of provider status.

---

## 2. De-Identification & HIPAA Safe Harbor Audit (P10-A2)

### Deficiencies in Prior P9 Export (DEF-21)
- Prior implementation only stripped `full_name` and replaced patient ID with `SUBJ-...`.
- Free-text clinical notes (`medical_history`, `primary_complaint`, `red_flags["referral_notes"]`) were exported verbatim, exposing provider names (`Dr. ...`), clinic emails, direct phone numbers, and consultation dates.
- Ages $> 89$ were exported as exact integers, violating HIPAA Safe Harbor 45 CFR § 164.514(b)(2)(i)(C).
- Prior export docstrings claimed "HIPAA Safe Harbor aligned" without certified de-identification.

### Remediation & Safe Harbor Scrubber Implementation
1. **Clinical Free-Text Pattern Scrubber (`scrub_phi_from_text`):**
   - Redacts email addresses to `[REDACTED_EMAIL]`.
   - Redacts Social Security Numbers to `[REDACTED_SSN]`.
   - Redacts domestic and international telephone numbers to `[REDACTED_PHONE]`.
   - Redacts clinician names (`Dr. ...`, `Doctor ...`, `Prof. ...`) to `[REDACTED_PROVIDER]`.
   - Redacts specific calendar dates to `[REDACTED_DATE]`.
2. **Safe Harbor Age Aggregation:**
   - For all subjects aged $> 89$, `export_deidentified_research_record()` aggregates age to `"90+"`.
3. **Clear Non-PHI Research Labeling:**
   - Export record explicitly specifies:
     ```json
     {
       "hipaa_safe_harbor_certified": false,
       "deidentification_method": "SYNTHETIC_RESEARCH_SCRUBBED_NOT_CERTIFIED_FOR_PHI",
       "compliance_disclaimer": "SYNTHETIC/EDUCATIONAL RESEARCH ONLY — NOT CERTIFIED FOR REAL PHI"
     }
     ```
   - No claim of certified medical privacy compliance is made.

---

## 3. Windows NTFS Permissions & Browser Attack Surface (P10-A3)

### Native Windows NTFS File DACLs (DEF-22)
- **Vulnerability:** `os.chmod(0o600 / 0o700)` is a POSIX-specific call. On Windows NTFS filesystems, `os.chmod` only controls the read-only file attribute, leaving Discretionary Access Control Lists (DACLs) inherited and allowing any local user to read secret key material.
- **Remediation:** Created [`src/msk_research_lab/security/permissions.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/permissions.py):
  - `secure_file_permissions(path: Path)`: On Windows, invokes `icacls.exe <path> /inheritance:r /grant:r "%USERNAME%":F`. On POSIX, sets `0o600`.
  - `secure_directory_permissions(path: Path)`: On Windows, invokes `icacls.exe <path> /inheritance:r /grant:r "%USERNAME%":(OI)(CI)F`. On POSIX, sets `0o700`.

### Loopback Host & CSRF Guard Hardening (DEF-26)
- **Vulnerability:** In `security_host_guard` middleware, `host_header.split(":")[0]` was used. When an IPv6 loopback request arrived (`Host: [::1]:8000`), splitting on colon returned `"["`, resulting in false HTTP 403 Forbidden rejections. Additionally, state-changing requests with `Origin: null` (from sandboxed iframes or local files) could potentially bypass origin checks.
- **Remediation:**
  - Upgraded parsing to `urllib.parse.urlsplit(f"//{host_header}").hostname.lower()`.
  - Added IPv6 loopback `::1` to `ALLOWED_LOOPBACK_HOSTS`.
  - Strictly reject `Origin: null` on state-changing POST, PUT, DELETE, and PATCH endpoints with HTTP 403 Forbidden.
  - Retain loopback-only restriction rejecting DNS rebinding and cross-site attack requests.
