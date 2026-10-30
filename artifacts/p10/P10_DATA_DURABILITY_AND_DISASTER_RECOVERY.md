# MSK Research Lab OS — P10 Data Durability & Disaster Recovery Report

**Milestone:** P10  
**Audit Role:** Biomedical Software Verification Engineer, Database Reliability Engineer, and Security Auditor  
**Target Files:**
- [`src/msk_research_lab/core/migrations.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/core/migrations.py)
- [`src/msk_research_lab/security/key_lifecycle.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/key_lifecycle.py)
- [`tests/integration/test_p10_disaster_fault_injection.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p10_disaster_fault_injection.py)

---

## 1. Executive Summary

Milestone P10-B performed fault-injection testing against SQLite transactional migrations, cryptographic key rotation, and disaster recovery restore operations. All operations adhere strictly to the principle of **strict crash-consistency**: the system must transition either to the complete new valid state or remain in its previous valid state, with zero partial state corruption or silent data loss.

---

## 2. Migration Atomicity & Savepoint Isolation (DEF-23)

### The Vulnerability in `sqlite3.executescript`
- Python's standard `sqlite3.Connection.executescript(sql)` issues an implicit `COMMIT` prior to script execution.
- If a multi-statement DDL migration failed halfway through (e.g. statement 1 creates a table, statement 2 has an invalid constraint), statement 1 was permanently committed to the database file while the `schema_migrations` record for that migration was never inserted.
- Upon next application startup, the migration runner attempted to re-run the failed migration, crashing immediately on `sqlite3.OperationalError: table already exists`.

### Remediation & Verification
- Replaced `conn.executescript(sql)` with individual statement parsing via `_split_sql_statements(sql)` enclosed in transactional savepoint blocks:
  ```python
  cur.execute(f"SAVEPOINT mig_sp_{version};")
  try:
      for stmt in _split_sql_statements(sql):
          cur.execute(stmt)
      cur.execute("INSERT INTO schema_migrations ...")
      cur.execute(f"RELEASE SAVEPOINT mig_sp_{version};")
  except Exception as e:
      cur.execute(f"ROLLBACK TO SAVEPOINT mig_sp_{version};")
      cur.execute(f"RELEASE SAVEPOINT mig_sp_{version};")
      raise MigrationError(...) from e
  ```
- **Fault Injection Test:** Injected synthetic multi-statement migration `0999_fault_injection_test` containing a valid table creation followed by an intentional syntax error. Verified that `canary_table_before_crash` was completely rolled back and did not exist in `sqlite_master`.

---

## 3. Cryptographic Key Rotation Durability

### Two-Phase Candidate Key Write-Ahead
1. Key rotation writes the new pepper to a write-ahead candidate file: `.workstation_pepper.new`.
2. The database updates the `pepper_key_store`, re-encrypts/re-pseudonymizes patient records, logs to `pepper_rotation_log`, and records an audit event in a single atomic transaction.
3. If an error occurs during the database transaction, an explicit exception handler unlinks `.workstation_pepper.new`, preventing orphan key files from corrupting subsequent boots.
4. Following database transaction commitment, `shutil.copy2` archives the old active key to `.key_vault/pepper_v{old}.key`, and `os.replace` atomically promotes `.workstation_pepper.new` to `.workstation_pepper`.
5. The committed key is also archived to `.key_vault/pepper_v{new}.key`.

---

## 4. Disaster Recovery Staging & Negative Testing

| Fault Injection Scenario | Test Case | Mechanism | Acceptance Verdict |
| :--- | :--- | :--- | :---: |
| **Ciphertext Tampering** | 1 byte flipped in body | OpenSSL EVP GMAC tag mismatch | **FAIL-CLOSED (PASS)** |
| **Passphrase Corruption** | Incorrect password | PBKDF2 derived key tag mismatch | **FAIL-CLOSED (PASS)** |
| **Path Traversal Attack** | Tar member `../../evil.txt` | Pre-extraction path validation | **FAIL-CLOSED (PASS)** |
| **Corrupted SQLite Header** | Bad magic in staging | `PRAGMA integrity_check` | **FAIL-CLOSED (PASS)** |
| **FK Constraint Violation** | Inconsistent child rows | `PRAGMA foreign_key_check` | **FAIL-CLOSED (PASS)** |
