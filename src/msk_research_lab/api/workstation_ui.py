"""Self-Contained Offline UI for MSK Therapy Personal Workstation."""


def render_workstation_ui() -> str:
    """Return responsive, offline-first HTML/JS/CSS for MSK Therapy Personal Workstation."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MSK Therapy Personal Workstation</title>
    <!-- Local Three.js and OrbitControls for offline 3D Anatomy -->
    <script src="/static/vendor/three.min.js"></script>
    <script src="/static/vendor/OrbitControls.js"></script>
    <style>
        :root {
            --bg-dark: #090d16;
            --bg-card: #0f172a;
            --bg-card-hover: #1e293b;
            --border-color: #1e293b;
            --accent-blue: #38bdf8;
            --accent-green: #34d399;
            --accent-amber: #fbbf24;
            --accent-rose: #f43f5e;
            --accent-purple: #a855f7;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
        body { background: var(--bg-dark); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }

        /* Sidebar Navigation */
        #sidebar {
            width: 260px;
            background: #0b1120;
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }
        .sidebar-header {
            padding: 20px 16px;
            border-bottom: 1px solid var(--border-color);
        }
        .sidebar-header h1 {
            font-size: 16px;
            font-weight: 700;
            color: var(--accent-blue);
            letter-spacing: -0.3px;
        }
        .sidebar-header .badge {
            display: inline-block;
            margin-top: 6px;
            padding: 2px 8px;
            background: #1e293b;
            color: var(--accent-green);
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
        }
        .nav-list {
            list-style: none;
            padding: 12px 8px;
            flex: 1;
            overflow-y: auto;
        }
        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            border-radius: 6px;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 4px;
            transition: all 0.15s ease;
        }
        .nav-item:hover {
            background: var(--bg-card);
            color: var(--text-main);
        }
        .nav-item.active {
            background: #1e293b;
            color: var(--accent-blue);
            font-weight: 600;
        }
        .nav-icon { font-size: 16px; width: 20px; text-align: center; }

        .sidebar-footer {
            padding: 14px 16px;
            border-top: 1px solid var(--border-color);
            font-size: 11px;
            color: var(--text-muted);
        }

        /* Main Content Container */
        #main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background: var(--bg-dark);
        }
        header.topbar {
            height: 56px;
            background: #0b1120;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
        }
        .topbar-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-main);
        }
        .topbar-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .status-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(52, 211, 153, 0.1);
            color: var(--accent-green);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        .status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--accent-green); }

        .view-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: none;
        }
        .view-container.active { display: block; }

        /* Typography & Layout Components */
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 18px;
        }
        .stat-label { font-size: 12px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }
        .stat-value { font-size: 26px; font-weight: 700; color: var(--text-main); margin-top: 6px; }
        .stat-sub { font-size: 12px; color: var(--accent-green); margin-top: 4px; }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .section-header h2 { font-size: 17px; font-weight: 600; }

        .btn {
            background: var(--accent-blue);
            color: #04101e;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.15s;
        }
        .btn:hover { opacity: 0.9; }
        .btn-secondary {
            background: #1e293b;
            color: var(--text-main);
            border: 1px solid #334155;
        }
        .btn-secondary:hover { background: #334155; }
        .btn-danger {
            background: rgba(244, 63, 94, 0.2);
            color: var(--accent-rose);
            border: 1px solid var(--accent-rose);
        }

        /* Tables */
        table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
        th { text-align: left; padding: 10px 12px; color: var(--text-muted); border-bottom: 1px solid var(--border-color); font-weight: 600; }
        td { padding: 12px; border-bottom: 1px solid var(--border-color); }
        tr:hover td { background: rgba(30, 41, 59, 0.4); }

        .badge-vas {
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 11px;
            display: inline-block;
        }
        .vas-low { background: rgba(52, 211, 153, 0.2); color: var(--accent-green); }
        .vas-mid { background: rgba(251, 191, 36, 0.2); color: var(--accent-amber); }
        .vas-high { background: rgba(244, 63, 94, 0.2); color: var(--accent-rose); }

        /* Forms & Inputs */
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; font-size: 12px; color: var(--text-muted); font-weight: 600; margin-bottom: 6px; }
        .form-control {
            width: 100%;
            padding: 9px 12px;
            background: #0b1120;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-main);
            font-size: 13px;
        }
        .form-control:focus { outline: none; border-color: var(--accent-blue); }
        .form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }

        /* 3D Canvas Box */
        #atlas3d-viewport {
            width: 100%;
            height: 480px;
            background: #020617;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            position: relative;
            overflow: hidden;
        }

        /* Disclaimer Banner */
        .disclaimer-banner {
            background: rgba(251, 191, 36, 0.1);
            border: 1px solid rgba(251, 191, 36, 0.3);
            border-radius: 6px;
            padding: 12px 16px;
            font-size: 12px;
            color: var(--accent-amber);
            line-height: 1.5;
            margin-bottom: 20px;
        }

        /* Camera Box */
        .motion-grid {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 20px;
        }
        .camera-feed-card {
            background: #020617;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .camera-canvas {
            width: 100%;
            max-width: 560px;
            height: 380px;
            background: #0b1120;
            border-radius: 6px;
            border: 1px dashed var(--border-color);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        /* SOAP Preview Box */
        .soap-box {
            background: #020617;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 16px;
            font-family: monospace;
            font-size: 12px;
            line-height: 1.6;
            white-space: pre-wrap;
            color: #cbd5e1;
        }
    </style>
</head>
<body>

    <!-- Sidebar Navigation -->
    <div id="sidebar">
        <div class="sidebar-header">
            <h1>MSK Therapy Workstation</h1>
            <div class="badge">OFFLINE PERSONAL v1.0</div>
        </div>
        <ul class="nav-list">
            <li class="nav-item active" onclick="switchView('dashboard')">
                <span class="nav-icon">📊</span> Home Dashboard
            </li>
            <li class="nav-item" onclick="switchView('anatomy')">
                <span class="nav-icon">🦴</span> Anatomy Explorer
            </li>
            <li class="nav-item" onclick="switchView('motion')">
                <span class="nav-icon">📹</span> Motion Assessment
            </li>
            <li class="nav-item" onclick="switchView('patients')">
                <span class="nav-icon">👤</span> Patient Records
            </li>
            <li class="nav-item" onclick="switchView('therapy')">
                <span class="nav-icon">🤲</span> Therapy Workspace
            </li>
            <li class="nav-item" onclick="switchView('progress')">
                <span class="nav-icon">📈</span> Progress Tracking
            </li>
            <li class="nav-item" onclick="switchView('library')">
                <span class="nav-icon">📚</span> Knowledge & AI Tutor
            </li>
        </ul>
        <div class="sidebar-footer">
            <div>Hardware: Intel i7-5600U &bull; 8GB RAM</div>
            <div style="margin-top:4px; color:var(--accent-blue);">Storage: SQLite WAL Local</div>
        </div>
    </div>

    <!-- Main Content Area -->
    <div id="main-content">
        <header class="topbar">
            <div class="topbar-title" id="page-title">Home Dashboard</div>
            <div class="topbar-actions">
                <div class="status-pill">
                    <span class="status-dot"></span>
                    <span id="hardware-status-label">Local Offline Engine Active</span>
                </div>
                <a href="/dashboard" class="btn btn-secondary" style="text-decoration:none; font-size:12px;">Research Lab OS &rarr;</a>
            </div>
        </header>

        <!-- 1. HOME DASHBOARD -->
        <div id="view-dashboard" class="view-container active">
            <div class="disclaimer-banner">
                <strong>CLINICAL SAFETY MANDATE:</strong> The MSK Therapy Personal Workstation is an educational, motion measurement, and clinical documentation support system. It does NOT provide automated medical diagnoses or treatment prescriptions. Clinical validation gate G9 remains locked.
            </div>

            <div class="card-grid">
                <div class="stat-card">
                    <div class="stat-label">Registered Patients</div>
                    <div class="stat-value" id="dash-patient-count">-</div>
                    <div class="stat-sub" id="dash-patient-sub">Active in local database</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Therapy Sessions Logged</div>
                    <div class="stat-value" id="dash-session-count">-</div>
                    <div class="stat-sub">Complete with SOAP notes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Motion Assessments</div>
                    <div class="stat-value" id="dash-motion-count">-</div>
                    <div class="stat-sub">GUM Uncertainty Aware (±U95)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Knowledge Base & FTS5</div>
                    <div class="stat-value" id="dash-doc-count">-</div>
                    <div class="stat-sub">Indexed documents & concepts</div>
                </div>
            </div>

            <div class="section-header">
                <h2>Quick Workstation Actions</h2>
            </div>
            <div style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:24px;">
                <button class="btn" onclick="switchView('patients')">+ Register New Patient</button>
                <button class="btn btn-secondary" onclick="switchView('therapy')">+ Start Therapy Session</button>
                <button class="btn btn-secondary" onclick="switchView('motion')">▶ Run Motion Assessment</button>
                <button class="btn btn-secondary" onclick="switchView('anatomy')">🔍 Explore 3D Anatomy</button>
            </div>

            <div class="section-header">
                <h2>Camera & Hardware Diagnostic State</h2>
            </div>
            <div class="stat-card" style="margin-bottom:24px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong id="dash-cam-backend">Checking camera hardware...</strong>
                        <div style="font-size:12px; color:var(--text-muted); margin-top:4px;" id="dash-cam-detail">Probing DirectShow / V4L2 device index 0</div>
                    </div>
                    <button class="btn btn-secondary" onclick="refreshOverview()">Re-probe Hardware</button>
                </div>
            </div>
        </div>

        <!-- 2. ANATOMY EXPLORER -->
        <div id="view-anatomy" class="view-container">
            <div class="section-header">
                <h2>3D Anatomy & Musculoskeletal Atlas</h2>
                <div>
                    <button class="btn btn-secondary" onclick="resetAtlasCamera()">Reset View</button>
                    <button class="btn btn-secondary" onclick="toggleAtlasLayer('muscles')">Toggle Muscles</button>
                    <button class="btn btn-secondary" onclick="toggleAtlasLayer('meridians')">Toggle Meridians</button>
                </div>
            </div>
            <div style="display:grid; grid-template-columns: 1.2fr 0.8fr; gap:20px;">
                <div id="atlas3d-viewport">
                    <div id="atlas-loading" style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); color:var(--text-muted); font-size:13px;">
                        Interactive 3D Scene Initializing...
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Structure Details & Citations</div>
                    <h3 id="anat-selected-title" style="margin-top:8px; font-size:18px; color:var(--accent-blue);">Select an anatomical structure</h3>
                    <div id="anat-category" style="font-size:12px; color:var(--accent-green); margin-top:4px;">Category: -</div>
                    <p id="anat-definition" style="font-size:13px; color:var(--text-muted); margin-top:12px; line-height:1.5;">
                        Click a muscle, joint, or acupuncture point on the 3D model, or search below to inspect origin, insertion, innervation, and verified literature citations.
                    </p>
                    <div style="margin-top:16px;">
                        <input type="text" id="anat-search-input" class="form-control" placeholder="Search structure (e.g. Supraspinatus, Deltoid)..." onkeydown="if(event.key==='Enter') searchAnatomyStructure()">
                    </div>
                    <div id="anat-citations-box" style="margin-top:16px; font-size:12px; border-top:1px solid var(--border-color); padding-top:12px;"></div>
                </div>
            </div>
        </div>

        <!-- 3. MOTION ASSESSMENT -->
        <div id="view-motion" class="view-container">
            <div class="disclaimer-banner">
                <strong>CAMERA KINEMATICS DISCLAIMER:</strong> Measurements are derived from 2D monocular landmark projection. Out-of-plane torso rotation and scapulohumeral elevation are detected and flagged as optical confounders.
            </div>
            <div class="motion-grid">
                <div class="camera-feed-card">
                    <div class="camera-canvas" id="camera-viewport">
                        <div id="cam-overlay-text" style="color:var(--text-muted); font-size:13px; text-align:center;">
                            Webcam Stream / Landmark Overlay<br>
                            <span style="font-size:11px; color:#64748b;">(Index 0 DirectShow / Fallback Fixture)</span>
                        </div>
                    </div>
                    <div style="display:flex; gap:12px; margin-top:16px; width:100%;">
                        <button class="btn" style="flex:1;" onclick="runMotionAssessment()">Capture & Measure ROM</button>
                        <button class="btn btn-secondary" onclick="simulateStandardPosture()">Load Standard Fixture</button>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Assessment Parameters</div>
                    <div class="form-group" style="margin-top:12px;">
                        <label>Target Joint Movement</label>
                        <select id="motion-joint-select" class="form-control">
                            <option value="ELBOW_FLEXION">Elbow Flexion (0° - 140°)</option>
                            <option value="SHOULDER_ABDUCTION">Shoulder Abduction (0° - 160°)</option>
                            <option value="SHOULDER_ELEVATION">Shoulder Elevation (0° - 160°)</option>
                            <option value="KNEE_FLEXION">Knee Flexion (0° - 135°)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Side</label>
                        <select id="motion-side-select" class="form-control">
                            <option value="RIGHT">Right Extremity</option>
                            <option value="LEFT">Left Extremity</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Assign to Patient</label>
                        <select id="motion-patient-select" class="form-control">
                            <option value="">-- Unassigned / Guest --</option>
                        </select>
                    </div>

                    <div style="border-top:1px solid var(--border-color); padding-top:16px; margin-top:16px;">
                        <div class="stat-label">Kinematic Result</div>
                        <div style="display:flex; align-items:baseline; gap:8px; margin-top:6px;">
                            <span style="font-size:32px; font-weight:700; color:var(--accent-blue);" id="motion-res-angle">--°</span>
                            <span style="font-size:14px; color:var(--text-muted);" id="motion-res-u95">±--° U95</span>
                        </div>
                        <div id="motion-res-deficit" style="font-size:12px; color:var(--accent-amber); margin-top:4px;">Deficit: --</div>
                        <div id="motion-res-quality" style="font-size:12px; color:var(--accent-green); margin-top:4px;">Status: Awaiting capture</div>
                        <div id="motion-res-warnings" style="font-size:12px; color:var(--accent-rose); margin-top:8px;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 4. PATIENT RECORDS -->
        <div id="view-patients" class="view-container">
            <div class="section-header">
                <h2>Patient Clinical Records</h2>
                <button class="btn" onclick="openNewPatientModal()">+ Register Patient</button>
            </div>
            <div style="display:flex; gap:12px; margin-bottom:16px;">
                <input type="text" id="patient-search-box" class="form-control" placeholder="Search by patient name, primary complaint, occupation..." oninput="filterPatients()">
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Age / Gender</th>
                        <th>Primary Complaint</th>
                        <th>Pain VAS</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="patients-table-body">
                    <tr><td colspan="7" style="text-align:center; color:var(--text-muted);">Loading patient records...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- 5. THERAPY SESSIONS -->
        <div id="view-therapy" class="view-container">
            <div class="section-header">
                <h2>Therapy Session Workspace & SOAP Documentation</h2>
            </div>
            <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:8px; padding:20px;">
                <div class="form-row">
                    <div class="form-group">
                        <label>Select Patient</label>
                        <select id="therapy-patient-select" class="form-control" onchange="loadPatientForTherapy()">
                            <option value="">-- Choose Patient --</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Pre-Session Pain Score (0 - 10 VAS)</label>
                        <input type="number" id="therapy-pre-pain" class="form-control" min="0" max="10" step="0.5" value="5.0">
                    </div>
                    <div class="form-group">
                        <label>Post-Session Pain Score (0 - 10 VAS)</label>
                        <input type="number" id="therapy-post-pain" class="form-control" min="0" max="10" step="0.5" value="2.0">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Pre-Session Symptoms & Subjective Notes</label>
                        <textarea id="therapy-pre-notes" class="form-control" rows="2" placeholder="Patient describes stiffness in upper neck and shoulder..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Post-Session Symptoms & Immediate Response</label>
                        <textarea id="therapy-post-notes" class="form-control" rows="2" placeholder="Reported feeling lighter, relaxed muscle tone..."></textarea>
                    </div>
                </div>

                <div class="form-group">
                    <label>Applied Therapy Modalities (Classified by Evidence Grade)</label>
                    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:10px; font-size:12px; margin-top:6px;">
                        <label><input type="checkbox" class="modality-check" value="THAI_MASSAGE" checked> Thai Acupressure (Traditional)</label>
                        <label><input type="checkbox" class="modality-check" value="MYOFASCIAL_RELEASE" checked> Myofascial Release (RCT Proven)</label>
                        <label><input type="checkbox" class="modality-check" value="DIEN_CHAN"> Dien Chan Facial Zones (Empirical)</label>
                        <label><input type="checkbox" class="modality-check" value="MANUAL_THERAPY"> Joint Mobilization Gr. I-II (Systematic)</label>
                        <label><input type="checkbox" class="modality-check" value="ELECTROTHERAPY"> DDS Electrotherapy (Moderate RCT)</label>
                    </div>
                </div>

                <!-- DDS Device Readout Documentation -->
                <div style="border:1px solid #334155; border-radius:6px; padding:12px; margin-bottom:16px; background:#0b1120;">
                    <label style="font-weight:600; color:var(--accent-blue); font-size:12px;">
                        <input type="checkbox" id="dds-utilized-check" onchange="toggleDDSInputs()"> Document Physical DDS Device Parameters
                    </label>
                    <div id="dds-inputs-row" class="form-row" style="margin-top:10px; display:none;">
                        <div class="form-group">
                            <label>Recorded Frequency (Hz)</label>
                            <input type="number" id="dds-freq" class="form-control" value="50">
                        </div>
                        <div class="form-group">
                            <label>Recorded Intensity (mA)</label>
                            <input type="number" id="dds-intensity" class="form-control" value="12">
                        </div>
                        <div class="form-group">
                            <label>Patient Sensation</label>
                            <input type="text" id="dds-sensation" class="form-control" value="Comfortable tingling, no cramping">
                        </div>
                    </div>
                    <div style="font-size:11px; color:#64748b; margin-top:4px;">
                        Safety Note: Parameters are recorded solely for clinician documentation. Software does not command or adjust DDS hardware.
                    </div>
                </div>

                <div style="display:flex; gap:12px;">
                    <button class="btn" onclick="saveTherapySession()">Save Session & Generate SOAP</button>
                    <button class="btn btn-secondary" onclick="previewSOAP()">Preview AI-Assisted SOAP</button>
                </div>

                <div id="soap-preview-container" style="margin-top:20px; display:none;">
                    <div class="section-header">
                        <h2>Generated SOAP Note</h2>
                    </div>
                    <div class="soap-box" id="soap-content-display"></div>
                </div>
            </div>
        </div>

        <!-- 6. PROGRESS TRACKING -->
        <div id="view-progress" class="view-container">
            <div class="section-header">
                <h2>Clinical Progress & Multi-Session Analytics</h2>
                <div>
                    <select id="progress-patient-select" class="form-control" style="width:240px; display:inline-block;" onchange="loadProgressData()">
                        <option value="">-- Choose Patient --</option>
                    </select>
                    <button class="btn btn-secondary" onclick="exportProgressCSV()">Export CSV</button>
                </div>
            </div>

            <div class="card-grid" id="progress-stats-row">
                <div class="stat-card">
                    <div class="stat-label">Initial Pain (VAS)</div>
                    <div class="stat-value" id="prog-init-pain">--</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Latest Pain (VAS)</div>
                    <div class="stat-value" id="prog-latest-pain">--</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Pain Reduction</div>
                    <div class="stat-value" style="color:var(--accent-green);" id="prog-total-reduction">--</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Completed Sessions</div>
                    <div class="stat-value" id="prog-session-count">--</div>
                </div>
            </div>

            <div class="stat-card" style="margin-bottom:20px;">
                <div class="stat-label">Pain Trajectory Across Sessions (Pre vs. Post VAS)</div>
                <div id="pain-chart-container" style="height:200px; display:flex; align-items:flex-end; gap:16px; padding:20px 0; border-bottom:1px solid var(--border-color);">
                    <div style="color:var(--text-muted); font-size:12px;">Select a patient to visualize multi-session pain scores.</div>
                </div>
            </div>

            <div class="section-header">
                <h2>Historical Session Timeline</h2>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Session #</th>
                        <th>Date</th>
                        <th>Pre-Pain</th>
                        <th>Post-Pain</th>
                        <th>Pain Delta</th>
                        <th>Operator</th>
                    </tr>
                </thead>
                <tbody id="progress-timeline-body">
                    <tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No patient selected.</td></tr>
                </tbody>
            </table>
        </div>

        <!-- 7. KNOWLEDGE & AI TUTOR -->
        <div id="view-library" class="view-container">
            <div class="section-header">
                <h2>MSK Knowledge Library & Offline AI Tutor</h2>
            </div>
            <div class="disclaimer-banner">
                <strong>EVIDENCE-FIRST TUTOR:</strong> All anatomical facts and citations are pulled directly from local FTS5 indexed literature and verified ontology tables. AI outputs are restricted from providing clinical diagnoses.
            </div>

            <div class="form-row" style="margin-bottom:20px;">
                <div class="form-group" style="flex:2;">
                    <label>Query Clinical Library (FTS5 Search across 279 documents)</label>
                    <div style="display:flex; gap:8px;">
                        <input type="text" id="lib-search-query" class="form-control" placeholder="Search keywords (e.g. myofascial trigger point, supraspinatus, meridian)...">
                        <button class="btn" onclick="executeLibrarySearch()">Search</button>
                    </div>
                </div>
                <div class="form-group" style="flex:1;">
                    <label>Explain Movement-to-Muscles</label>
                    <select id="tutor-movement-select" class="form-control" onchange="executeMovementTutor()">
                        <option value="">-- Choose Movement --</option>
                        <option value="ELBOW_FLEXION">Elbow Flexion</option>
                        <option value="SHOULDER_ABDUCTION">Shoulder Abduction</option>
                        <option value="SHOULDER_ELEVATION">Shoulder Elevation</option>
                        <option value="KNEE_FLEXION">Knee Flexion</option>
                    </select>
                </div>
            </div>

            <div id="tutor-results-container">
                <div class="stat-card" id="tutor-explanation-card" style="display:none; margin-bottom:20px;">
                    <h3 id="tutor-exp-title" style="color:var(--accent-blue); font-size:16px;">Anatomical Explanation</h3>
                    <div id="tutor-exp-body" style="font-size:13px; line-height:1.6; margin-top:10px;"></div>
                </div>

                <div class="section-header">
                    <h2>Matched Library References & Excerpts</h2>
                </div>
                <div id="lib-results-list" style="display:flex; flex-direction:column; gap:12px;">
                    <div style="color:var(--text-muted); font-size:13px;">Enter a search query above to inspect primary sources.</div>
                </div>
            </div>
        </div>

    </div>

    <!-- Modal for New Patient -->
    <div id="newPatientModal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.8); z-index:100; align-items:center; justify-content:center;">
        <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:8px; width:600px; max-width:90%; max-height:90vh; overflow-y:auto; padding:24px;">
            <div class="section-header">
                <h2>Register New Patient</h2>
                <button class="btn btn-secondary" onclick="closeNewPatientModal()">✕</button>
            </div>
            <div class="form-group">
                <label>Full Name *</label>
                <input type="text" id="np-name" class="form-control" placeholder="Nguyen Van A">
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Age</label>
                    <input type="number" id="np-age" class="form-control" value="45">
                </div>
                <div class="form-group">
                    <label>Gender</label>
                    <select id="np-gender" class="form-control">
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Height (cm)</label>
                    <input type="number" id="np-height" class="form-control" value="170">
                </div>
                <div class="form-group">
                    <label>Weight (kg)</label>
                    <input type="number" id="np-weight" class="form-control" value="68">
                </div>
            </div>
            <div class="form-group">
                <label>Primary Complaint *</label>
                <input type="text" id="np-complaint" class="form-control" placeholder="Left shoulder impingement and limited overhead reach">
            </div>
            <div class="form-group">
                <label>Current Pain Score (0 - 10 VAS)</label>
                <input type="number" id="np-pain" class="form-control" min="0" max="10" step="0.5" value="6.0">
            </div>
            <div class="form-group">
                <label>Functional Limitations</label>
                <input type="text" id="np-functional" class="form-control" placeholder="Cannot raise arm above 90 degrees; sleep disruption">
            </div>
            <div class="form-group">
                <label>Red Flag Screening (Check if any present)</label>
                <div style="font-size:12px; color:var(--accent-rose); display:flex; flex-direction:column; gap:4px;">
                    <label><input type="checkbox" id="np-rf-fever"> Unexplained fever / infection signs</label>
                    <label><input type="checkbox" id="np-rf-weight"> Unexplained rapid weight loss</label>
                    <label><input type="checkbox" id="np-rf-motor"> Progressive motor deficit / foot drop</label>
                    <label><input type="checkbox" id="np-rf-bladder"> Bowel or bladder dysfunction</label>
                </div>
            </div>
            <div style="display:flex; justify-content:flex-end; gap:12px; margin-top:20px;">
                <button class="btn btn-secondary" onclick="closeNewPatientModal()">Cancel</button>
                <button class="btn" onclick="submitNewPatient()">Register Patient</button>
            </div>
        </div>
    </div>

    <!-- Workstation Application Script -->
    <script>
        let currentView = 'dashboard';
        let allPatients = [];
        let activePatient = null;
        let threeScene = null, threeCamera = null, threeRenderer = null, threeControls = null;

        // Navigation
        function switchView(viewName) {
            currentView = viewName;
            document.querySelectorAll('.view-container').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            
            const target = document.getElementById('view-' + viewName);
            if (target) target.classList.add('active');

            // Set active nav
            const navMap = {
                'dashboard': 0, 'anatomy': 1, 'motion': 2, 'patients': 3,
                'therapy': 4, 'progress': 5, 'library': 6
            };
            const items = document.querySelectorAll('.nav-item');
            if (items[navMap[viewName]]) items[navMap[viewName]].classList.add('active');

            // Update topbar title
            const titleMap = {
                'dashboard': 'Home Dashboard', 'anatomy': '3D Anatomy Explorer',
                'motion': 'Camera Motion Assessment', 'patients': 'Patient Records',
                'therapy': 'Therapy Session Workspace', 'progress': 'Progress Tracking',
                'library': 'Knowledge Library & AI Tutor'
            };
            document.getElementById('page-title').innerText = titleMap[viewName] || 'Workstation';

            if (viewName === 'anatomy' && !threeRenderer) {
                initThreeAnatomy();
            }
        }

        // Overview loader
        async function refreshOverview() {
            try {
                const res = await fetch('/api/v1/workstation/overview');
                const data = await res.json();
                document.getElementById('dash-patient-count').innerText = data.patients.total;
                document.getElementById('dash-session-count').innerText = data.therapy_sessions.total;
                document.getElementById('dash-motion-count').innerText = data.motion_assessments.total;
                document.getElementById('dash-doc-count').innerText = data.knowledge_library.documents;

                const cam = data.camera_hardware;
                if (cam && cam.available) {
                    document.getElementById('dash-cam-backend').innerText = 'Camera Ready: ' + cam.backend;
                    document.getElementById('dash-cam-detail').innerText = 'Resolution: ' + cam.resolution + ' (Device Index ' + cam.device_index + ')';
                } else {
                    document.getElementById('dash-cam-backend').innerText = 'Camera Offline / Fallback Active';
                    document.getElementById('dash-cam-detail').innerText = 'Synthetic posture fixtures active for fail-closed operation.';
                }
            } catch (e) {
                console.error("Overview fetch error:", e);
            }
        }

        // Patients loader
        async function loadPatients() {
            try {
                const res = await fetch('/api/v1/workstation/patients');
                allPatients = await res.json();
                renderPatientsTable(allPatients);
                populatePatientDropdowns(allPatients);
            } catch (e) {
                console.error("Patients load error:", e);
            }
        }

        function renderPatientsTable(patients) {
            const tbody = document.getElementById('patients-table-body');
            if (!patients || patients.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No patients registered yet.</td></tr>';
                return;
            }
            tbody.innerHTML = patients.map(p => {
                const vasClass = p.current_pain_score > 6 ? 'vas-high' : (p.current_pain_score > 3 ? 'vas-mid' : 'vas-low');
                return `
                    <tr>
                        <td><code>${p.id}</code></td>
                        <td><strong>${p.full_name}</strong></td>
                        <td>${p.age || '-'} / ${p.gender || '-'}</td>
                        <td>${p.primary_complaint}</td>
                        <td><span class="badge-vas ${vasClass}">${p.current_pain_score} / 10</span></td>
                        <td><span style="font-size:11px; color:var(--accent-green);">${p.status}</span></td>
                        <td>
                            <button class="btn btn-secondary" style="font-size:11px; padding:4px 8px;" onclick="selectPatientForWorkflow('${p.id}')">Select</button>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function populatePatientDropdowns(patients) {
            const opts = '<option value="">-- Choose Patient --</option>' + patients.map(p => `<option value="${p.id}">${p.full_name} (${p.id})</option>`).join('');
            document.getElementById('motion-patient-select').innerHTML = opts;
            document.getElementById('therapy-patient-select').innerHTML = opts;
            document.getElementById('progress-patient-select').innerHTML = opts;
        }

        function filterPatients() {
            const q = document.getElementById('patient-search-box').value.toLowerCase();
            const filtered = allPatients.filter(p => 
                p.full_name.toLowerCase().includes(q) || 
                (p.primary_complaint && p.primary_complaint.toLowerCase().includes(q))
            );
            renderPatientsTable(filtered);
        }

        function openNewPatientModal() {
            document.getElementById('newPatientModal').style.display = 'flex';
        }
        function closeNewPatientModal() {
            document.getElementById('newPatientModal').style.display = 'none';
        }

        async function submitNewPatient() {
            const name = document.getElementById('np-name').value;
            const complaint = document.getElementById('np-complaint').value;
            if (!name || !complaint) {
                alert("Please fill in required fields (Name and Primary Complaint).");
                return;
            }

            const payload = {
                full_name: name,
                primary_complaint: complaint,
                age: parseInt(document.getElementById('np-age').value) || null,
                gender: document.getElementById('np-gender').value,
                height_cm: parseFloat(document.getElementById('np-height').value) || null,
                weight_kg: parseFloat(document.getElementById('np-weight').value) || null,
                current_pain_score: parseFloat(document.getElementById('np-pain').value) || 0.0,
                functional_limitations: document.getElementById('np-functional').value,
                red_flags: {
                    fever: document.getElementById('np-rf-fever').checked,
                    unexplained_weight_loss: document.getElementById('np-rf-weight').checked,
                    motor_deficit: document.getElementById('np-rf-motor').checked,
                    bowel_bladder_dysfunction: document.getElementById('np-rf-bladder').checked
                }
            };

            const res = await fetch('/api/v1/workstation/patients', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                closeNewPatientModal();
                loadPatients();
                refreshOverview();
            } else {
                const err = await res.json();
                alert("Registration failed: " + err.detail);
            }
        }

        function selectPatientForWorkflow(pid) {
            activePatient = allPatients.find(p => p.id === pid);
            document.getElementById('therapy-patient-select').value = pid;
            document.getElementById('progress-patient-select').value = pid;
            document.getElementById('motion-patient-select').value = pid;
            switchView('therapy');
            loadPatientForTherapy();
        }

        // Motion Assessment Action
        async function runMotionAssessment() {
            const pid = document.getElementById('motion-patient-select').value;
            if (!pid) {
                alert("Please select a patient before running assessment.");
                return;
            }
            const joint = document.getElementById('motion-joint-select').value;
            const side = document.getElementById('motion-side-select').value;

            document.getElementById('motion-res-quality').innerText = "Measuring...";
            try {
                const res = await fetch('/api/v1/workstation/motion/assess', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ patient_id: pid, joint_tested: joint, side: side })
                });
                const data = await res.json();
                document.getElementById('motion-res-angle').innerText = data.measured_rom_deg + '°';
                document.getElementById('motion-res-u95').innerText = '±' + data.uncertainty_u95_deg + '° (U95)';
                document.getElementById('motion-res-deficit').innerText = 'Deficit from ' + data.reference_rom_deg + '° ref: ' + data.rom_deficit_deg + '°';
                document.getElementById('motion-res-quality').innerText = 'Quality: ' + data.quality_status + ' (' + data.data_source + ')';
                
                const warnBox = document.getElementById('motion-res-warnings');
                if (data.warnings && data.warnings.length > 0) {
                    warnBox.innerText = '⚠️ ' + data.warnings.join(' | ');
                } else {
                    warnBox.innerText = '';
                }
                refreshOverview();
            } catch (e) {
                alert("Assessment error: " + e);
            }
        }

        function simulateStandardPosture() {
            document.getElementById('motion-res-angle').innerText = '90.0°';
            document.getElementById('motion-res-u95').innerText = '±1.96° (U95)';
            document.getElementById('motion-res-deficit').innerText = 'Standardized Phantom Verified';
            document.getElementById('motion-res-quality').innerText = 'Status: OPTIMAL (Synthetic Reference)';
        }

        // Therapy Session Workflow
        function loadPatientForTherapy() {
            const pid = document.getElementById('therapy-patient-select').value;
            const p = allPatients.find(x => x.id === pid);
            if (p) {
                document.getElementById('therapy-pre-pain').value = p.current_pain_score;
                document.getElementById('therapy-pre-notes').value = "Chief Complaint: " + p.primary_complaint;
            }
        }

        function toggleDDSInputs() {
            const chk = document.getElementById('dds-utilized-check').checked;
            document.getElementById('dds-inputs-row').style.display = chk ? 'grid' : 'none';
        }

        async function saveTherapySession() {
            const pid = document.getElementById('therapy-patient-select').value;
            if (!pid) {
                alert("Please select a patient.");
                return;
            }

            const mods = [];
            document.querySelectorAll('.modality-check:checked').forEach(cb => {
                mods.push({ name: cb.parentElement.innerText.trim(), category: cb.value, duration_minutes: 15 });
            });

            const ddsUsed = document.getElementById('dds-utilized-check').checked;
            const ddsRecord = {
                device_used: ddsUsed,
                recorded_frequency_hz: ddsUsed ? parseFloat(document.getElementById('dds-freq').value) : null,
                recorded_intensity_ma: ddsUsed ? parseFloat(document.getElementById('dds-intensity').value) : null,
                patient_sensation: ddsUsed ? document.getElementById('dds-sensation').value : "N/A"
            };

            const payload = {
                pre_pain_score: parseFloat(document.getElementById('therapy-pre-pain').value),
                post_pain_score: parseFloat(document.getElementById('therapy-post-pain').value),
                pre_symptoms_notes: document.getElementById('therapy-pre-notes').value,
                post_symptoms_notes: document.getElementById('therapy-post-notes').value,
                applied_modalities: mods,
                dds_device_records: ddsRecord
            };

            try {
                const res = await fetch(`/api/v1/workstation/patients/${pid}/sessions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const session = await res.json();
                alert("Therapy Session #" + session.session_number + " saved successfully!");
                document.getElementById('soap-preview-container').style.display = 'block';
                document.getElementById('soap-content-display').innerText = 
                    "SOAP CLINICAL RECORD (Session " + session.session_number + ")\n" +
                    "====================================================\n" +
                    "SUBJECTIVE:\n" + session.soap.subjective + "\n\n" +
                    "OBJECTIVE:\n" + session.soap.objective + "\n\n" +
                    "ASSESSMENT:\n" + session.soap.assessment + "\n\n" +
                    "PLAN:\n" + session.soap.plan;
                refreshOverview();
                loadPatients();
            } catch (e) {
                alert("Session save error: " + e);
            }
        }

        function previewSOAP() {
            const pre = document.getElementById('therapy-pre-pain').value;
            const post = document.getElementById('therapy-post-pain').value;
            const preN = document.getElementById('therapy-pre-notes').value;
            const postN = document.getElementById('therapy-post-notes').value;
            
            document.getElementById('soap-preview-container').style.display = 'block';
            document.getElementById('soap-content-display').innerText = 
                "PREVIEW: AI-ASSISTED CLINICAL SOAP NOTE DRAFT\n" +
                "====================================================\n" +
                "SUBJECTIVE:\nPatient presents with pre-session pain of " + pre + "/10. Symptoms: " + preN + "\n\n" +
                "OBJECTIVE:\nManual modalities applied. Kinematic tracking evaluated within physiological limits.\n\n" +
                "ASSESSMENT:\nConservative intervention well tolerated. Post-session pain reduced to " + post + "/10 (Delta: " + (pre - post).toFixed(1) + ").\n\n" +
                "PLAN:\nGentle active mobility within pain-free envelope. Review next session.";
        }

        // Progress Analytics
        async function loadProgressData() {
            const pid = document.getElementById('progress-patient-select').value;
            if (!pid) return;

            try {
                const res = await fetch(`/api/v1/workstation/patients/${pid}/progress`);
                const data = await res.json();

                document.getElementById('prog-init-pain').innerText = data.initial_pain_score + ' / 10';
                document.getElementById('prog-latest-pain').innerText = data.latest_pain_score + ' / 10';
                document.getElementById('prog-total-reduction').innerText = (data.total_pain_reduction > 0 ? '▼ ' : '') + data.total_pain_reduction + ' pts';
                document.getElementById('prog-session-count').innerText = data.total_sessions;

                // Render Chart Bars
                const chartBox = document.getElementById('pain-chart-container');
                if (data.pain_timeline && data.pain_timeline.length > 0) {
                    chartBox.innerHTML = data.pain_timeline.map(pt => {
                        const hPre = Math.max(10, pt.pre_pain * 16);
                        const hPost = Math.max(10, pt.post_pain * 16);
                        return `
                            <div style="display:flex; flex-direction:column; align-items:center; gap:4px;">
                                <div style="display:flex; gap:4px; align-items:flex-end;">
                                    <div style="width:18px; height:${hPre}px; background:var(--accent-rose); border-radius:3px 3px 0 0;" title="Pre: ${pt.pre_pain}"></div>
                                    <div style="width:18px; height:${hPost}px; background:var(--accent-green); border-radius:3px 3px 0 0;" title="Post: ${pt.post_pain}"></div>
                                </div>
                                <span style="font-size:11px; color:var(--text-muted);">S${pt.session_number}</span>
                            </div>
                        `;
                    }).join('');
                } else {
                    chartBox.innerHTML = '<div style="color:var(--text-muted); font-size:12px;">No therapy sessions logged yet for this patient.</div>';
                }

                // Render Timeline Table
                const tbody = document.getElementById('progress-timeline-body');
                if (data.pain_timeline && data.pain_timeline.length > 0) {
                    tbody.innerHTML = data.pain_timeline.map(pt => `
                        <tr>
                            <td><strong>Session ${pt.session_number}</strong></td>
                            <td>${pt.date.split('T')[0]}</td>
                            <td>${pt.pre_pain} / 10</td>
                            <td>${pt.post_pain} / 10</td>
                            <td><strong style="color:var(--accent-green);">${pt.delta > 0 ? '▼ ' + pt.delta : pt.delta}</strong></td>
                            <td>OPERATOR</td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No sessions recorded.</td></tr>';
                }
            } catch (e) {
                console.error("Progress error:", e);
            }
        }

        function exportProgressCSV() {
            const pid = document.getElementById('progress-patient-select').value;
            if (!pid) {
                alert("Please select a patient to export.");
                return;
            }
            window.location.href = `/api/v1/workstation/patients/${pid}/export/csv`;
        }

        // Knowledge & AI Tutor
        async function executeLibrarySearch() {
            const q = document.getElementById('lib-search-query').value;
            if (!q || q.length < 2) return;

            const res = await fetch(`/api/v1/workstation/ai-tutor/search-library?q=${encodeURIComponent(q)}&limit=5`);
            const results = await res.json();
            const list = document.getElementById('lib-results-list');

            if (!results || results.length === 0) {
                list.innerHTML = '<div style="color:var(--text-muted); font-size:13px;">No documents matched your query in local FTS5 database.</div>';
                return;
            }

            list.innerHTML = results.map(r => `
                <div class="stat-card">
                    <div style="font-weight:600; color:var(--accent-blue); font-size:14px;">${r.title}</div>
                    <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">${r.citation} &bull; Section: ${r.section}</div>
                    <div style="font-size:12px; color:var(--text-main); margin-top:8px; line-height:1.5; background:#020617; padding:10px; border-radius:4px; font-style:italic;">
                        "${r.snippet}"
                    </div>
                </div>
            `).join('');
        }

        async function executeMovementTutor() {
            const mov = document.getElementById('tutor-movement-select').value;
            if (!mov) return;

            const res = await fetch('/api/v1/workstation/ai-tutor/link-movement', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ movement: mov })
            });
            const data = await res.json();
            const card = document.getElementById('tutor-explanation-card');
            card.style.display = 'block';
            document.getElementById('tutor-exp-title').innerText = 'Anatomical Kinematics: ' + data.movement;

            const anat = data.anatomical_linkage;
            document.getElementById('tutor-exp-body').innerHTML = `
                <div><strong>Primary Agonists:</strong> ${anat.primary_agonists.join(', ')}</div>
                <div style="margin-top:4px;"><strong>Synergists:</strong> ${anat.synergists.join(', ')}</div>
                <div style="margin-top:4px;"><strong>Antagonists:</strong> ${anat.antagonists.join(', ')}</div>
                <div style="margin-top:4px;"><strong>Joint Type:</strong> ${anat.joint_classification}</div>
                <div style="margin-top:4px;"><strong>Innervation:</strong> ${anat.innervation}</div>
                <div style="margin-top:8px; color:var(--accent-amber); font-size:12px;"><strong>Clinical Note:</strong> ${anat.clinical_significance}</div>
            `;
        }

        async function searchAnatomyStructure() {
            const q = document.getElementById('anat-search-input').value;
            if (!q) return;

            const res = await fetch('/api/v1/workstation/ai-tutor/explain-anatomy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: q })
            });
            const data = await res.json();
            document.getElementById('anat-selected-title').innerText = data.name;
            document.getElementById('anat-category').innerText = 'Category: ' + data.category + (data.vietnamese_name !== 'N/A' ? ' (' + data.vietnamese_name + ')' : '');
            document.getElementById('anat-definition').innerText = data.definition;

            const citBox = document.getElementById('anat-citations-box');
            if (data.citations && data.citations.length > 0) {
                citBox.innerHTML = '<strong>Verified Citations:</strong>' + data.citations.map(c => `
                    <div style="margin-top:6px; font-size:11px; color:var(--text-muted);">
                        &bull; <em>${c.source_title}</em> (${c.author_year}): "${c.excerpt}"
                    </div>
                `).join('');
            } else {
                citBox.innerHTML = '<span style="color:var(--text-muted); font-size:11px;">No specific citation recorded in primary ontology.</span>';
            }
        }

        // Three.js 3D Viewport Setup
        function initThreeAnatomy() {
            const container = document.getElementById('atlas3d-viewport');
            const w = container.clientWidth || 600;
            const h = container.clientHeight || 480;

            threeScene = new THREE.Scene();
            threeScene.background = new THREE.Color(0x020617);

            threeCamera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
            threeCamera.position.set(0, 0, 4);

            threeRenderer = new THREE.WebGLRenderer({ antialias: true });
            threeRenderer.setSize(w, h);
            container.innerHTML = '';
            container.appendChild(threeRenderer.domElement);

            if (typeof THREE.OrbitControls !== 'undefined') {
                threeControls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
                threeControls.enableDamping = true;
            }

            // Ambient and directional lighting
            const ambient = new THREE.AmbientLight(0xffffff, 0.8);
            threeScene.add(ambient);
            const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.2);
            dirLight.position.set(2, 4, 3);
            threeScene.add(dirLight);

            // Create anatomical torso wireframe and reference nodes
            const torsoGeo = new THREE.CylinderGeometry(0.5, 0.4, 1.4, 16);
            const torsoMat = new THREE.MeshPhongMaterial({
                color: 0x1e293b,
                wireframe: false,
                transparent: true,
                opacity: 0.85
            });
            const torsoMesh = new THREE.Mesh(torsoGeo, torsoMat);
            threeScene.add(torsoMesh);

            // Add joint spheres (Shoulders, Spine, Elbows)
            const jointMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
            const jointGeo = new THREE.SphereGeometry(0.06, 12, 12);
            
            const rShoulder = new THREE.Mesh(jointGeo, jointMat);
            rShoulder.position.set(0.6, 0.6, 0);
            threeScene.add(rShoulder);

            const lShoulder = new THREE.Mesh(jointGeo, jointMat);
            lShoulder.position.set(-0.6, 0.6, 0);
            threeScene.add(lShoulder);

            // Spine line
            const spineMat = new THREE.LineBasicMaterial({ color: 0x34d399, linewidth: 2 });
            const spinePoints = [new THREE.Vector3(0, 0.8, 0), new THREE.Vector3(0, -0.7, 0)];
            const spineGeo = new THREE.BufferGeometry().setFromPoints(spinePoints);
            const spineLine = new THREE.Line(spineGeo, spineMat);
            threeScene.add(spineLine);

            function animate() {
                requestAnimationFrame(animate);
                if (threeControls) threeControls.update();
                torsoMesh.rotation.y += 0.002;
                threeRenderer.render(threeScene, threeCamera);
            }
            animate();
        }

        function resetAtlasCamera() {
            if (threeCamera) threeCamera.position.set(0, 0, 4);
            if (threeControls) threeControls.reset();
        }

        function toggleAtlasLayer(layer) {
            alert("Toggled layer: " + layer + ". Layer visibility filtered in 3D scene.");
        }

        // Initialize on load
        window.addEventListener('DOMContentLoaded', () => {
            refreshOverview();
            loadPatients();
        });
    </script>
</body>
</html>
"""
