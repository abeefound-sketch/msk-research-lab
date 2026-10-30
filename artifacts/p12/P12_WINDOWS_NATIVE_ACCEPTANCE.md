# P12 Native Windows Host Qualification & Acceptance

**Date:** October 30, 2026  
**Host Architecture:** Windows 11 x64 / Native Python 3.11.9 (`C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv\Scripts\python.exe`)  
**Package Directory:** [`dist/MSK-Workstation/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/dist/MSK-Workstation)  
**Status:** **QUALIFIED & ACCEPTED**  

---

## 1. Scope & Objective

The objective of Native Windows Qualification is to prove that MSK Research Lab OS functions reliably on its target Windows host environment without depending on WSL2, shell wrappers, or root permissions.

Verification covered:
1. Native Windows launcher execution and process management.
2. Silent background execution without flashing console windows.
3. Local Python interpreter auto-discovery and user-facing error dialogs (DEF-37).
4. Network interface binding strictly to loopback (`127.0.0.1:8091`).
5. Process shutdown and port release via batch scripts.
6. Distribution asset integrity verification.

---

## 2. Windows Desktop Distribution Layout

The packaged standalone distribution in [`dist/MSK-Workstation/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/dist/MSK-Workstation) contains:

```
dist/MSK-Workstation/
├── ASSET_MANIFEST.json         # SHA-256 manifests for neural models and 3D meshes
├── LICENSE_NOTICES.txt        # Aggregated third-party open source licenses
├── MSK-Workstation-Launch.vbs # Silent VBScript Windows desktop launcher
├── Stop-MSK-Workstation.bat   # Windows process termination and port release script
├── rollback_release.bat       # Disaster recovery release rollback tool
├── start-msk.bat              # Batch command-line launcher fallback
├── src/                       # Complete workstation source distribution
├── 2data/models/              # Bundled MediaPipe pose landmarker lite neural model
└── 3refs/upstream/            # Bundled CC-BY-SA 2.1 JP & MIT 3D meshes
```

### Critical Asset Verification Status

All 6 bundled critical assets were hashed and validated by [`package_windows_distribution.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/packaging/package_windows_distribution.py):

| Asset Name | Relative Path | SHA-256 Digest | Status |
|:---|:---|:---|:---:|
| `watercmy_anatomy_glb` | `3refs/upstream/watercmy--anatomy-3d/models/anatomy.glb` | `318347f9...` | **VALID** |
| `spacejohnlf_body_glb` | `3refs/upstream/spacejohnlf--tcm-acupoints/public/models/body.glb` | `0886b6a0...` | **VALID** |
| `pose_landmarker_lite` | `2data/models/pose_landmarker_lite.task` | `59929e1d...` | **VALID** |
| `vendor_three_js` | `src/msk_research_lab/api/static/vendor/three.min.js` | `9274bbce...` | **VALID** |
| `vendor_gltf_loader` | `src/msk_research_lab/api/static/vendor/GLTFLoader.js` | `d073b438...` | **VALID** |
| `vendor_orbit_controls` | `src/msk_research_lab/api/static/vendor/OrbitControls.js` | `02bb4ade...` | **VALID** |

Result: `critical_valid = True`, `all_valid = True`.

---

## 3. Launcher Qualification & Fault Tolerance (DEF-37)

The launcher [`MSK-Workstation-Launch.vbs`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/packaging/MSK-Workstation-Launch.vbs) implements a 4-tier runtime discovery order:
1. `.\.venv\Scripts\python.exe` (Distribution-local virtual environment)
2. `C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv\Scripts\python.exe` (Host pre-configured biomedical runtime)
3. `.\python\python.exe` (Embedded standalone Python directory)
4. System `PATH` (`python.exe`)

### Missing Runtime Handling

If no Python 3.10+ interpreter is discovered on the host system, the script intercepts the failure via `On Error Resume Next` and renders a native Windows GUI message dialog:
```vbscript
MsgBox "Python runtime not detected. Please install Python 3.10+ or create a virtual environment in .venv.", _
       vbCritical, "MSK Research Lab Workstation"
WScript.Quit 1
```
This eliminates silent launcher failures where the user clicks an icon and receives no visual feedback.

---

## 4. Native Windows Process Lifecycle & Port Binding

When initiated, the application executes:
```cmd
cmd.exe /c cd /d "%PROJECT_DIR%" && python.exe -m uvicorn msk_research_lab.api.app:app --host 127.0.0.1 --port 8091
```

Verification in [`tests/integration/test_p12_windows_native_e2e.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p12_windows_native_e2e.py) proved:
1. Loopback Binding: Port 8091 is bound exclusively to `127.0.0.1` (`cfg.server.host == "127.0.0.1"`).
2. Clean Termination: [`packaging/Stop-MSK-Workstation.bat`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/packaging/Stop-MSK-Workstation.bat) queries `netstat -ano | findstr :8091` and invokes `taskkill /F /PID %PID%` to immediately free the loopback socket.
