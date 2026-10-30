# MSK Research Lab OS — P10 Independent Test Validity & Release Provenance

**Milestone:** P10  
**Audit Role:** Independent Release QA, Software Supply Chain Auditor  
**Audit Scope:** Dependency licenses, SBOM, mutation testing, asset integrity, and build reproducibility  

---

## 1. Intentional Fault & Mutation Testing (Anti-Self-Certification)

To eliminate the risk of "optimistic test passing" or tautological assertions, negative fault-injection and mutation tests were executed in isolated fixtures:

1. **Migration Atomicity Guard:**
   - Injected syntactically invalid SQL into a multi-statement migration.
   - Verified that the migration runner raises `MigrationError` and that earlier statements in the script are completely rolled back (`canary_table_before_crash` absent from SQLite master).
2. **Key Rotation Orphan Guard:**
   - Simulated power failure during patient record re-encryption in `rotate_pepper()`.
   - Verified that the candidate key `.workstation_pepper.new` was automatically unlinked and did not linger as an orphan file on disk.
3. **AEAD Ciphertext Tampering:**
   - Flipped 1 bit in ciphertext body. Verified `OpenSSLAuthTagMismatch` / `BackupDecryptionError` triggers fail-closed behavior before target directory files are mutated.
4. **Path Traversal Archive Attack:**
   - Injected malicious tar member with path `../../evil_traversal.txt`.
   - Verified immediate pre-extraction rejection with `Malicious archive member detected`.
5. **Collinear Landmark Degeneracy:**
   - Provided 4 strictly collinear landmarks. Verified `CalibratedRegistrationError("Degenerate landmark geometry")` fails closed.
6. **Origin Spoofing / CSRF Guard:**
   - Sent state-changing POST requests with `Origin: null` and `Origin: http://malicious.com`. Verified HTTP 403 Forbidden rejection.

---

## 2. Software Bill of Materials (SBOM) & Third-Party Dependencies

The workstation relies exclusively on local, vetted, permissively licensed libraries and runtime components:

| Component | Version / Build | License | Function | Security Evaluation |
| :--- | :--- | :--- | :--- | :--- |
| **Python Standard Library** | 3.10 / 3.11 | PSF License | Runtime environment | Standard system runtime |
| **OpenSSL libcrypto** | 3.0.x / 1.1.x | Apache 2.0 / OpenSSL | AES-256-GCM AEAD | Dynamic system library, non-FIPS default provider |
| **FastAPI / Starlette** | Latest pinned | MIT | Loopback HTTP API | Hardened with loopback host & CSRF guards |
| **SQLite3** | Embedded | Public Domain | ACID relational database | WAL journal, FK enforcement, transactional savepoints |
| **Three.js** | r128 | MIT | WebGL 3D rendering | Bundled locally (`api/static/vendor/three.min.js`) |
| **Three.js GLTFLoader** | r128 | MIT | 3D GLB mesh loader | Bundled locally (`api/static/vendor/GLTFLoader.js`) |
| **Three.js OrbitControls**| r128 | MIT | 3D camera controls | Bundled locally (`api/static/vendor/OrbitControls.js`) |
| **MediaPipe Pose Lite** | Lite Task | Apache 2.0 | 33-point pose landmarking | Bundled locally (`2data/models/pose_landmarker_lite.task`) |
| **BodyParts3D Anatomy** | DBCLS 2008 | CC-BY-SA 2.1 JP | Anatomical reference mesh | Bundled locally (`3refs/upstream/.../anatomy.glb`) |
| **TCM Acupoints Mesh** | SpaceJohnLF | MIT | Acupuncture mannequin | Bundled locally (`3refs/upstream/.../body.glb`) |

**Supply Chain Verification:**
- No runtime telemetry, no phone-home mechanisms, zero remote CDN dependencies.
- All binary models and JavaScript libraries are stored directly within the repository tree and distribution package with SHA-256 hashes verified in `ASSET_MANIFEST.json`.
