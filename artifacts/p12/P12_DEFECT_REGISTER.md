# P12 Defect Register & Remediation Log

**Milestone:** P12 — Operational Assurance & Windows Native Release Qualification  
**Period:** October 30, 2026  
**Defect Range:** DEF-33 through DEF-38  
**Status Summary:** 6/6 REMEDIATED & INDEPENDENTLY VERIFIED  

---

## Defect Summary Table

| Defect ID | Severity | Subsystem | Description | Status | Verification Suite |
|:---:|:---:|:---|:---|:---:|:---|
| **DEF-33** | **HIGH** | Core / Backup | Path traversal vulnerability during unencrypted backup archive extraction | **FIXED** | `test_p12_durability_and_consistency.py` |
| **DEF-34** | **HIGH** | Storage / Backup | SQLite `VACUUM INTO` concurrency failure & orphaned WAL replay corruption on restore | **FIXED** | `test_p12_durability_and_consistency.py`, `test_p12_windows_native_e2e.py` |
| **DEF-35** | **HIGH** | Workstation / Privacy | Incomplete Safe Harbor PHI scrubbing (NPI, medical licenses, dot/space SSNs, dates) | **FIXED** | `test_p12_durability_and_consistency.py`, `test_p12_windows_native_e2e.py` |
| **DEF-36** | **MEDIUM** | Scientific / Quality | Lack of standardized, quantitative 4-state measurement quality decision engine | **FIXED** | `test_p12_scientific_quality_decisions.py`, `test_p12_metrology_independent_oracle.py` |
| **DEF-37** | **MEDIUM** | Packaging / Windows | Windows VBS launcher silent failure on missing Python & lack of local runtime discovery | **FIXED** | `test_p12_windows_native_e2e.py` |
| **DEF-38** | **MEDIUM** | Security / Windows | Windows file sharing violation (`WinError 32`) during atomic database replacement | **FIXED** | `test_p12_durability_and_consistency.py` |

---

## Detailed Remediation Reports

### DEF-33: Path Traversal in Unencrypted Backup Archive Extraction
- **Root Cause:** [`core/backup.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/core/backup.py) extracted tar members via `tar.extractall()` without verifying whether member paths resolved inside the target directory.
- **Remediation:** Added canonical destination prefix validation:
  ```python
  member_path = (target_dir / member.name).resolve()
  if not str(member_path).startswith(str(target_resolved)):
      raise BackupIntegrityError(f"Path traversal attempt rejected: '{member.name}'")
  ```
- **Verification:** Crafted tar archive with `../escaped_file.txt` was rejected with `BackupIntegrityError`.

### DEF-34: SQLite Online Backup API & WAL Orphan Sidecar Conflict
- **Root Cause:**
  1. `VACUUM INTO` failed if another connection held active write locks.
  2. Restoration left old `-wal` and `-shm` sidecars in the target directory, causing SQLite to replay stale transaction pages on newly restored databases.
- **Remediation:**
  1. Migrated backup generation to `sqlite3.Connection.backup()` under passive checkpointing (`PRAGMA wal_checkpoint(PASSIVE);`).
  2. In [`restore_encrypted_backup()`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/security/key_lifecycle.py), explicitly unlink pre-existing `target-wal` and `target-shm` files prior to file replacement.
- **Verification:** Verified online backup during concurrent reads and confirmed atomic cleanup of corrupted WAL sidecars.

### DEF-35: Incomplete Safe Harbor De-identification
- **Root Cause:** Regex scrubber in [`patient_manager.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/workstation/patient_manager.py) lacked patterns for 10-digit NPIs, DEA numbers, state medical licenses, non-hyphen delimited SSNs, and dotted/hyphenated dates.
- **Remediation:** Added comprehensive regex passes for NPIs, DEA/licenses, space/dot SSNs, and calendar dates with tokens `[REDACTED_NPI]`, `[REDACTED_LICENSE]`, `[REDACTED_SSN]`, `[REDACTED_DATE]`.
- **Verification:** Verified complete elimination of raw identifiers from clinical notes and exported research records.

### DEF-36: Standardized Metrological Quality Decision Engine
- **Root Cause:** Measurement evaluations lacked standardized categories and quantitative justifications.
- **Remediation:** Created [`msk_research_lab.scientific.quality`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/scientific/quality.py) with `MeasurementQualityDecision` enum (`VALID`, `DEGRADED`, `REJECTED`, `NOT_VERIFIED`) with explicit threshold rules.
- **Verification:** Verified across kinematics, 2D-to-3D optical registration, and stereo triangulation.

### DEF-37: Windows Launcher Local Runtime Discovery & User Dialog
- **Root Cause:** [`MSK-Workstation-Launch.vbs`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/packaging/MSK-Workstation-Launch.vbs) did not search local `.venv` paths and exited silently if Python was not in `PATH`.
- **Remediation:** Added hierarchical search (`.venv\Scripts\python.exe`, pre-configured bridge venv, embedded python) and a user-facing VBScript `MsgBox` error dialog.
- **Verification:** Verified VBScript script content and execution path.

### DEF-38: Windows File Sharing Violation Retry Loop
- **Root Cause:** Windows antivirus or SQLite connection teardown delay caused transient file lock exceptions during `os.replace()`.
- **Remediation:** Implemented exponential backoff retry loop (5 attempts, up to 1.6s delay) before failing.
- **Verification:** Simulated Windows file locking conditions pass cleanly without crashing.
