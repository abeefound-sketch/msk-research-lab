# P11 DESKTOP PACKAGING & E2E INTEGRITY REPORT
**MSK Research Lab OS — Packaged Distribution & Desktop Reliability Verification**

- **Audit Date:** 2026-10-30
- **Auditor:** Desktop QA & Release Verification Engineer
- **Distribution Directory:** `dist/MSK-Workstation/`
- **Verification Status:** ALL ASSETS & LAUNCHERS VALIDATED

---

## 1. Executive Summary

Milestone P11 independently validated the distribution packaging pipeline [`packaging/package_windows_distribution.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/packaging/package_windows_distribution.py) and inspected the resulting standalone distribution folder.

All 6 critical assets, license files, Windows batch/VBS launchers, and application source trees were validated with matching SHA-256 digests.

---

## 2. Bundled Asset SHA-256 Cryptographic Verification

| Asset Identifier | File Path | Expected SHA-256 | Actual SHA-256 | Status |
|---|---|---|---|---|
| `watercmy_anatomy_glb` | `3refs/upstream/watercmy--anatomy-3d/models/anatomy.glb` | `318347f9...` | `318347f9...` | **VALID** |
| `spacejohnlf_body_glb` | `3refs/upstream/spacejohnlf--tcm-acupoints/public/models/body.glb` | `0886b6a0...` | `0886b6a0...` | **VALID** |
| `pose_landmarker_lite` | `2data/models/pose_landmarker_lite.task` | `59929e1d...` | `59929e1d...` | **VALID** |
| `vendor_three_js` | `src/msk_research_lab/api/static/vendor/three.min.js` | `9274bbce...` | `9274bbce...` | **VALID** |
| `vendor_gltf_loader` | `src/msk_research_lab/api/static/vendor/GLTFLoader.js` | `d073b438...` | `d073b438...` | **VALID** |
| `vendor_orbit_controls` | `src/msk_research_lab/api/static/vendor/OrbitControls.js` | `02bb4ade...` | `02bb4ade...` | **VALID** |

---

## 3. Launchers & Control Scripts

The distribution bundle in `dist/MSK-Workstation/` contains full desktop lifecycle management scripts:
1. `MSK-Workstation-Launch.vbs`: Windowless background launch invoking `python -m msk_research_lab` on localhost port 8000.
2. `Stop-MSK-Workstation.bat`: Graceful termination script looking up PID from lockfile or bound loopback port.
3. `start-msk.bat`: Interactive Windows batch launcher with environment probing and browser launch.
4. `rollback_release.bat`: Instant snapshot rollback utility restoring prior verified runtime state.

---

## 4. License Notices & Attribution Compliance

The distribution includes `dist/MSK-Workstation/LICENSE_NOTICES.txt` aggregating all third-party licenses:
- BodyParts3D / Z-Anatomy (CC-BY-SA 2.1 JP)
- MediaPipe Pose Landmarker Lite (Apache 2.0)
- Three.js & Loaders (MIT)
- spacejohnlf Acupuncture Mannequin (MIT)
- FastAPI / Starlette / Uvicorn / Pydantic (MIT / BSD)
