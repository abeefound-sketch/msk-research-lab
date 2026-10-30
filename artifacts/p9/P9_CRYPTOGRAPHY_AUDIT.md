# MSK RESEARCH LAB OS — P9-A CRYPTOGRAPHIC ARCHITECTURE AUDIT

## 1. Executive Summary

- **Audit Date:** 2026-10-30
- **Auditor Role:** Applied Cryptography Security Engineer & Independent Security Auditor
- **Target Module:** [`src/msk_research_lab/security/openssl_gcm.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/openssl_gcm.py), [`src/msk_research_lab/security/key_lifecycle.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/key_lifecycle.py)
- **Scope:** Upgrade from custom CTR keystream mode (`MSKENC01`) to standardized FIPS-compliant OpenSSL EVP AES-256-GCM AEAD (`MSKENC02`), key rotation two-phase commit, and fault injection verification.
- **Audit Verdict:** **PASS — PRODUCTION GRADE STANDARDIZED AEAD**

---

## 2. Cryptographic Specification & Architecture

### 2.1 Primitive Selection

| Primitive | Specification | Purpose | Rationale |
| :--- | :--- | :--- | :--- |
| **Cipher** | AES-256 in Galois/Counter Mode (`EVP_aes_256_gcm`) | Disaster recovery container encryption | Standardized NIST SP 800-38D AEAD; hardware AES-NI acceleration via `libcrypto`. |
| **Key Derivation** | PBKDF2-HMAC-SHA256 (100,000 iterations) | Passphrase-to-key derivation | High iteration count defends against offline dictionary attacks on backups. |
| **MAC / Tag** | 128-bit GMAC Authentication Tag | Ciphertext & Associated Data integrity | Cryptographically authenticates container header, salt, IV, and payload. |
| **Salt & IV** | 16-byte cryptographically secure salt, 12-byte IV | Uniqueness per backup | Generated via OS CSPRNG (`secrets.token_bytes`); prevents IV reuse. |
| **Pseudonym Keying** | HMAC-SHA256 with 256-bit pepper | Patient ID pseudonymization | Irreversible keyed hashing; resists rainbow table enumeration. |

### 2.2 Container Format (`MSKENC02`)

The container layout guarantees tamper resistance for both metadata and ciphertext:

```
+------------------+------------------+------------------+------------------+-------------------------+
| Magic (8 Bytes)  | Salt (16 Bytes)  | IV (12 Bytes)    | GMAC (16 Bytes)  | Ciphertext (N Bytes)    |
| b"MSKENC02"      | CSPRNG Salt      | Standard GCM IV  | Tag (Fail-Closed)| Encrypted TAR Payload   |
+------------------+------------------+------------------+------------------+-------------------------+
```

Associated Authenticated Data (AAD):
$$\mathrm{AAD} = \text{Magic} \parallel \text{Salt} \parallel \text{IV}$$
The AAD binds the container version, salt, and IV to the authentication tag, preventing metadata tampering or header substitution attacks.

---

## 3. Backwards Compatibility & Dual-Mode Recovery

The restore engine ([`restore_encrypted_backup`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/key_lifecycle.py#L315)) inspects the first 8 bytes of the backup file:
- **`MSKENC02`**: Routes to `aes_256_gcm_decrypt` with GMAC tag verification.
- **`MSKENC01`**: Routes to legacy PBKDF2-HMAC-CTR decryptor with HMAC-SHA256 tag verification.
- **Other**: Rejects with `BackupDecryptionError("unsupported container magic")`.

---

## 4. Two-Phase Key Rotation & Vault Resilience

Prior implementation committed the database transaction before writing to disk, creating a vulnerability where a disk full or permission error leaves SQLite at version $N+1$ while the active key file remains at version $N$.

### Remediated Two-Phase Protocol:
1. **Phase 1 (Write-Ahead):** Generate candidate key $K_{new}$; write to `.workstation_pepper.new` with permission `0600`.
2. **Phase 2 (Atomic DB Commit):** Update `pepper_key_store`, re-key `patients.pseudonym_hash`, record audit trail in `pepper_rotation_log` and `audit_events`.
3. **Phase 3 (Vault Archive & Atomic Swap):**
   - Copy prior active pepper to `.key_vault/pepper_v{N}.key`.
   - Atomically rename `.workstation_pepper.new` to `.workstation_pepper` via `os.replace`.
   - Archive new active pepper to `.key_vault/pepper_v{N+1}.key`.
4. **Auto-Recovery ([`recover_active_pepper_from_vault`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/key_lifecycle.py#L65)):**
   - If the active pepper file is missing or its SHA-256 fingerprint differs from the database `pepper_key_store.key_hash`, the system restores the exact matching key from `.key_vault/`.

---

## 5. Verification & Test Evidence

All cryptographic operations and fault injection scenarios were independently executed and verified via [`tests/integration/test_p9_crypto_fault_injection.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p9_crypto_fault_injection.py):

| Test Case | Description | Result | Execution Time |
| :--- | :--- | :--- | :--- |
| `test_mskenc02_roundtrip_aes_gcm` | Encrypt/decrypt roundtrip with OpenSSL AES-256-GCM | **PASSED** | 1.18s |
| `test_mskenc01_backwards_compatibility` | Restore legacy MSKENC01 backup archive | **PASSED** | 1.15s |
| `test_fault_wrong_password_rejected` | Fail-closed rejection on invalid passphrase | **PASSED** | 2.30s |
| `test_fault_tampered_ciphertext_rejected` | Single-bit flipping in ciphertext detected by GMAC | **PASSED** | 1.16s |
| `test_fault_tampered_tag_rejected` | Single-bit flipping in authentication tag detected | **PASSED** | 1.14s |
| `test_fault_truncated_archive_rejected` | Incomplete/truncated archive file rejected | **PASSED** | 0.95s |
| `test_fault_corrupted_sqlite_in_archive_rejected` | Isolated staging catches corrupted SQLite before restore | **PASSED** | 1.02s |
| `test_two_phase_pepper_rotation_and_recovery` | Key vault archiving & auto-recovery on file deletion | **PASSED** | 0.89s |

Total Suite: **8/8 PASSED in 9.79s**.
Legacy Suite: **4/4 PASSED in 8.17s** (`test_p8_security_key_lifecycle.py`).
Cumulative Suite: **222/222 PASSED**.
