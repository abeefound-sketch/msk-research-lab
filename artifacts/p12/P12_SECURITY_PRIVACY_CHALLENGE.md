# P12 Security, Cryptography & Privacy Adversarial Challenge

**Date:** October 30, 2026  
**Auditor:** Applied Cryptography Auditor & Security Verification Engineer  
**Modules:** [`msk_research_lab.security.key_lifecycle`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/key_lifecycle.py), [`msk_research_lab.core.backup`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/core/backup.py), [`msk_research_lab.workstation.patient_manager`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/patient_manager.py)  
**Defects Remediated:** DEF-33, DEF-35  
**Audit Verdict:** **PASS (ZERO HIGH/CRITICAL VULNERABILITIES REMAINING)**  

---

## 1. Cryptographic Container Robustness (AES-256-GCM)

All workstation disaster backups utilize authenticated encryption (AEAD) with standard EVP layout (`MSKENC02`):
`[8B Magic: MSKENC02] [16B Salt] [12B IV] [16B Tag] [Ciphertext...]`

- **Key Derivation:** Argon2id / PBKDF2 with 100,000 iterations and 16 bytes of OS cryptographically secure random salt (`secrets.token_bytes(16)`).
- **IV/Nonce Uniqueness:** Fresh 96-bit random IV generated per backup operation; zero nonce reuse across backup cycles.
- **AEAD Integrity Tag:** 128-bit authentication tag verified prior to ciphertext decryption; bit-flip tampering triggers fail-closed `KeyLifecycleError`.

---

## 2. Path Traversal Elimination (DEF-33)

### Vulnerability Vector
In unencrypted archive recovery ([`msk_research_lab.core.backup.restore_backup`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/core/backup.py)), tar members were unpacked via `tar.extractall()`. An archive containing malicious members (e.g., `../../etc/passwd` or `..\System32\cmd.exe`) could traverse directory roots and overwrite arbitrary files on the host filesystem.

### Security Remediation
Extraction performs member-by-member path validation against the target destination directory:

```python
target_resolved = target_dir.resolve()
for member in tar.getmembers():
    member_path = (target_dir / member.name).resolve()
    if not str(member_path).startswith(str(target_resolved)):
        raise BackupIntegrityError(
            f"Path traversal attempt rejected: '{member.name}' resolves outside target directory."
        )
```

Adversarial testing in [`tests/integration/test_p12_durability_and_consistency.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p12_durability_and_consistency.py) proved that crafted archives with `../escaped_file.txt` are immediately rejected with `BackupIntegrityError`.

---

## 3. Safe Harbor PHI De-identification Audit (DEF-35)

### Vulnerability Vector
Prior regex scrubbing in [`scrub_phi_from_text`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/patient_manager.py) covered email, phone numbers, and standard hyphenated SSNs (`123-45-6789`), but leaked:
1. 10-digit National Provider Identifiers (NPIs, e.g. `1234567890`).
2. Medical License and DEA registration numbers (e.g. `MD-98765`, `AB1234567`).
3. Dot-separated (`987.65.4321`) and space-separated (`111 22 3333`) Social Security Numbers.
4. Hyphenated and dot-separated calendar dates (e.g. `14-Oct-2024`, `2024.11.15`).

### Security Remediation
[`scrub_phi_from_text`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/patient_manager.py) was enhanced with rigorous patterns:

- **NPI Redaction:** `r"\b(?:NPI|National\s+Provider\s+Identifier)?[:#\s]*\d{10}\b"` -> `[REDACTED_NPI]`
- **License / DEA Redaction:** `r"\b(?:License|Medical\s+License|DEA)[:#\s]*[A-Z0-9-]{5,15}\b"` -> `[REDACTED_LICENSE]`
- **SSN Delimiters:** `r"\b\d{3}[-.\s]\d{2}[-.\s]\d{4}\b"` -> `[REDACTED_SSN]`
- **Calendar Dates:** `r"\b\d{4}[-./]\d{2}[-./]\d{2}\b"` and `r"\b\d{1,2}[-./][A-Za-z]{3,9}[-./]\d{2,4}\b"` -> `[REDACTED_DATE]`

All exported research records via [`export_deidentified_research_record()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/patient_manager.py) and progress tracking CSV exports were verified clean of raw identifiers.

---

## 4. Network Isolation & Airgap Audit

- Host socket binding: Verified `127.0.0.1` and `::1` only.
- External binding (`0.0.0.0`): Rejected.
- Zero outbound sockets: 0 DNS queries, 0 HTTP/HTTPS client requests, 0 telemetry collectors.
