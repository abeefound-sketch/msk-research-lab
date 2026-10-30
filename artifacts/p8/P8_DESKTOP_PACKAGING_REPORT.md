# MSK Research Lab OS — P8-A Desktop Packaging Report

**Report Date:** 2026-10-30  
**Author:** Principal Software Architect, Desktop Application Engineer, and Independent Release QA  
**Target Package:** MSK Research Lab OS Desktop Workstation Distribution (`dist/MSK-Workstation/`)  
**Status:** **`VERIFIED — PRODUCTION READY`**  
**Safety Invariant:** `CLINICAL_REALWORLD_GATE = BLOCKED` (Immutable Invariant)  

---

## 1. Executive Summary

Workstream **P8-A (Native Desktop Packaging)** establishes a self-contained, reproducible Windows desktop workstation distribution for personal and educational research use. 

Key achievements:
1. **Desktop Storage Mode:** Implemented `MSK_STORAGE_MODE=desktop` in [`src/msk_research_lab/core/config.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/core/config.py#L24-L35) routing user databases, audit journals, and evidence to standard OS application data paths (`%LOCALAPPDATA%\MSKResearchLab` or `%APPDATA%\MSKResearchLab` on Windows; `~/.local/share/msk_research_lab` on Linux). Non-administrative users can run and persist clinical simulations without modifying installation directories.
2. **Cryptographic Asset Manifest:** Implemented [`src/msk_research_lab/packaging/asset_verifier.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/packaging/asset_verifier.py) and generated [`packaging/ASSET_MANIFEST.json`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/packaging/ASSET_MANIFEST.json). All bundled 3D anatomical models, neural models, and frontend runtimes are verified against SHA-256 signatures before execution.
3. **Third-Party License Aggregation:** Implemented [`src/msk_research_lab/packaging/license_notices.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/src/msk_research_lab/packaging/license_notices.py) compiling complete legal notices for DBCLS BodyParts3D (CC-BY-SA 2.1 JP), spacejohnlf TCM acupoints (MIT), Google MediaPipe (Apache 2.0), Three.js (MIT), and OpenCV into [`dist/LICENSE_NOTICES.txt`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/dist/LICENSE_NOTICES.txt).
4. **Desktop Launch & Lifecycle Utilities:** Created silent desktop launcher [`packaging/MSK-Workstation-Launch.vbs`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/packaging/MSK-Workstation-Launch.vbs), graceful shutdown utility [`packaging/Stop-MSK-Workstation.bat`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/packaging/Stop-MSK-Workstation.bat), and versioned rollback script [`packaging/rollback_release.bat`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/packaging/rollback_release.bat).
5. **Distribution Packaging Engine:** Implemented automated packager [`packaging/package_windows_distribution.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/packaging/package_windows_distribution.py) producing verified build `dist/MSK-Workstation`.

---

## 2. Bundled Asset Cryptographic Verification Matrix

| Asset Identifier | Bundled Path | Size (Bytes) | SHA-256 Digest | Upstream License | Status |
|---|---|---|---|---|---|
| `watercmy_anatomy_glb` | `3refs/upstream/watercmy--anatomy-3d/models/anatomy.glb` | 9,291,204 | `318347f91e4989da0c271e9662df536943df1149b413fef01cf21586073ea73e` | CC-BY-SA 2.1 JP | **VALID** |
| `spacejohnlf_body_glb` | `3refs/upstream/spacejohnlf--tcm-acupoints/public/models/body.glb` | 8,249,484 | `0886b6a068e655b284903664e2178d7964f80b1c0ce798461909ac806bcef2e3` | MIT | **VALID** |
| `pose_landmarker_lite` | `2data/models/pose_landmarker_lite.task` | 5,777,746 | `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a` | Apache 2.0 | **VALID** |
| `vendor_three_js` | `src/msk_research_lab/api/static/vendor/three.min.js` | 603,445 | `9274bbcec8d96168626c732b5d31c775aa8cfb7eaa0599bec0c175908a2c1ce2` | MIT | **VALID** |
| `vendor_gltf_loader` | `src/msk_research_lab/api/static/vendor/GLTFLoader.js` | 108,522 | `d073b438e6a07e1359741dd5d6c76c953420cc0d4fd84eb1bdde94315540e6a3` | MIT | **VALID** |
| `vendor_orbit_controls` | `src/msk_research_lab/api/static/vendor/OrbitControls.js` | 26,375 | `02bb4ade710f3e607329e37a21f098bc3ac70eb6e33daf8a65e79f4db785e7b2` | MIT | **VALID** |

---

## 3. Desktop Application Architecture & Lifecycle

```mermaid
flowchart TD
    User([User Clicks MSK-Workstation-Launch.vbs]) --> VBS[VBScript Launcher (Background)]
    VBS --> Env[Configure MSK_STORAGE_MODE=desktop<br/>MSK_LAB_PORT=8091]
    Env --> Server[Start Local Uvicorn Instance (127.0.0.1:8091)]
    Server --> StorageCheck{Resolve Database Path}
    StorageCheck -->|Desktop Mode| AppData[%LOCALAPPDATA%\MSKResearchLab\db\lab.sqlite3]
    StorageCheck -->|Portable Mode| Portable[2data\db\lab.sqlite3]
    AppData --> Migrations[Execute Pending SQLite Migrations (v1..v10)]
    Migrations --> PortWait[Port 8091 Available]
    PortWait --> Browser[Launch Default Browser to http://127.0.0.1:8091/workstation]
    Browser --> UI[Workstation UI Active]

    Stop([User Clicks Stop-MSK-Workstation.bat]) --> Netstat[Find Port 8091 PID]
    Netstat --> Terminate[Taskkill Process Gracefully]
    Terminate --> UIClosed[Workstation Stopped]

    Rollback([User Runs rollback_release.bat [BACKUP_DIR]]) --> VerifyBackup[Check Backup Integrity]
    VerifyBackup --> StopActive[Ensure Workstation Stopped]
    StopActive --> RestoreCode[Restore Codebase (Preserve User DB & Keys)]
```

---

## 4. Test Verification Evidence

Automated test suite [`tests/integration/test_p8_desktop_packaging.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p8_desktop_packaging.py):
- `test_desktop_user_data_dir_resolution`: **PASSED** (verifies `%LOCALAPPDATA%` environment binding)
- `test_storage_mode_desktop`: **PASSED** (verifies redirection of SQLite database to user AppData)
- `test_standard_asset_manifest_and_verification`: **PASSED** (verifies 6/6 critical assets valid)
- `test_license_notices_generation`: **PASSED** (verifies all third-party license notices present)

**Workstream Verdict:** **`PASS`**
