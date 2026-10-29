# MSK THERAPY PERSONAL WORKSTATION — INSTALLATION & SETUP GUIDE

**Product:** MSK Therapy Personal Workstation (Task 05P)  
**Edition:** Personal Offline Edition  
**Target Hardware:** Intel Core i7-5600U, 8 GB RAM, Intel HD Graphics 5500, Windows 10 x64 / WSL2  
**Status:** Product Ready & Preclinical Certified  

---

## 1. HARDWARE & PREREQUISITES

| Component | Minimum Requirement | Recommended Specification | Status on Target System |
|---|---|---|:---:|
| **Processor** | Dual-core 2.0 GHz x64 | Intel Core i7-5600U @ 2.60 GHz | **VERIFIED** |
| **System Memory** | 4 GB RAM | 8 GB RAM | **VERIFIED (8 GB)** |
| **Graphics** | Integrated Intel HD Graphics | Intel HD Graphics 5500 (WebGL 2.0) | **VERIFIED** |
| **Storage** | 1 GB free SSD space | Local SSD (zero cloud dependencies) | **VERIFIED** |
| **Camera** | 1 physical USB or integrated webcam | 720p / 1080p @ 30 FPS | **VERIFIED (Index 0)** |
| **Operating System** | Windows 10 x64 (Build 19041+) | Windows 10 Pro with WSL2 Ubuntu | **VERIFIED** |
| **Python Runtime** | Python 3.10+ | Python 3.11.9 Native / Python 3.10 WSL | **VERIFIED** |

---

## 2. ONE-COMMAND LAUNCH (INSTANT START)

### Method A: Windows Native (Direct Double-Click)
1. Navigate to the project root directory:
   ```
   C:\Users\tuanh\Downloads\msk-research-lab
   ```
2. Double-click `start-msk.bat` (or run in Command Prompt / PowerShell).
3. The launcher will automatically:
   - Verify Python runtime (`C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv\Scripts\python.exe`).
   - Run transactional SQLite database migrations.
   - Probe webcam index 0 via DirectShow.
   - Bind to loopback `http://127.0.0.1:8000`.
   - Automatically launch your default browser to `http://127.0.0.1:8000/workstation`.

### Method B: WSL / Linux Terminal
1. Open terminal and navigate to the directory:
   ```bash
   cd /mnt/c/Users/tuanh/Downloads/msk-research-lab
   ```
2. Execute the launcher script:
   ```bash
   ./start-msk.sh
   ```
3. Open `http://127.0.0.1:8000/workstation` in your web browser.

---

## 3. COMMAND-LINE INTERFACE (CLI) USAGE

The platform provides a unified CLI entry point via `python -m msk_research_lab`:

```bash
# Launch Personal Workstation on custom port
python -m msk_research_lab workstation --port 8000

# Launch Workstation without opening browser automatically
python -m msk_research_lab workstation --port 8000 --no-browser

# Run system doctor diagnostics
python -m msk_research_lab doctor

# Execute database migrations manually
python -m msk_research_lab migrate
```

---

## 4. OFFLINE VERIFICATION & NETWORK ISOLATION

The workstation is designed for 100% offline, local-first operation:
- **Zero Cloud API Calls:** All landmark tracking, kinematics, SOAP note generation, and knowledge retrieval execute entirely in local RAM and SQLite.
- **Local Assets:** Three.js, OrbitControls, and 3D glTF/GLB models are bundled locally in `src/msk_research_lab/api/static/vendor/`.
- **Host Boundary Guard:** The application enforces loopback-only binding (`127.0.0.1` / `localhost`). External requests are rejected with HTTP 403 Forbidden.

---

## 5. SHUTDOWN PROCEDURE

To stop the workstation cleanly:
- Press `Ctrl + C` in the launcher terminal window.
- The server will flush active SQLite WAL checkpoints, release the camera hardware handle, and terminate gracefully.
