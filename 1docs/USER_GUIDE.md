# MSK THERAPY PERSONAL WORKSTATION — USER MANUAL

**Edition:** Personal Offline Workstation  
**Application URL:** `http://127.0.0.1:8000/workstation`  
**Intended Audience:** Biomechanics Researchers, Physical Therapists, Manual Therapy Practitioners, and Anatomy Students  

---

## 1. WORKSTATION OVERVIEW & NAVIGATION

The **MSK Therapy Personal Workstation** provides a unified clinical and educational environment accessible through 7 dedicated views in the left sidebar:

```
[MSK Therapy Personal Workstation]
├── 📊 1. Home Dashboard        ── Overview metrics, quick actions & camera status
├── 🦴 2. Anatomy Explorer      ── 3D Three.js atlas with verified structural citations
├── 📹 3. Motion Assessment     ── 2D webcam kinematics, ROM measurement & GUM uncertainty
├── 👤 4. Patient Records       ── Comprehensive profiles, VAS pain scores & red flag screening
├── 🤲 5. Therapy Workspace     ── Modality recording, DDS device readouts & auto SOAP notes
├── 📈 6. Progress Tracking     ── Longitudinal pain curves, ROM trajectories & CSV export
└── 📚 7. Knowledge & AI Tutor  ── FTS5 literature search, movement linkage & uncertainty audit
```

---

## 2. MODULE WALKTHROUGHS

### 2.1 Home Dashboard
- **Diagnostic Cards:** Displays registered patient count, recorded therapy sessions, completed motion assessments, and indexed library documents.
- **Hardware Diagnostics:** Displays real-time webcam probe status (resolution, DirectShow/V4L2 backend). If the camera is disconnected, the workstation automatically activates fail-closed synthetic fixtures.
- **Quick Actions:** Single-click buttons to register a patient, start a therapy session, or open the 3D atlas.

### 2.2 3D Anatomy Explorer
- **Interactive Three.js Viewport:** Rotate, pan, and zoom using standard mouse controls.
- **Structure Selection & Citation:** Enter any muscle, joint, or nerve name in the search box (e.g. `Supraspinatus`, `Trapezius`, `Middle Deltoid`) and press Enter. The system retrieves verified definitions, category namespaces, and primary literature citations directly from the local SQLite FTS5 database.
- **Atlas Layers:** Toggle muscle layers and meridian paths for targeted biomechanical review.

### 2.3 Camera Motion Assessment
1. Select target movement:
   - *Elbow Flexion* ($0^\circ \to 140^\circ$)
   - *Shoulder Abduction* ($0^\circ \to 160^\circ$)
   - *Shoulder Elevation* ($0^\circ \to 160^\circ$)
   - *Knee Flexion* ($0^\circ \to 135^\circ$)
2. Select side (Right / Left) and assign to an active patient profile.
3. Click **"Capture & Measure ROM"**:
   - The engine captures camera frames, extracts landmarks, and computes the 2D planar angle using vector geometry.
   - Evaluates the GUM Uncertainty Budget ($U_{95} = k \times u_c$, $k=1.96$).
   - Flags optical confounders (e.g., `HUMERAL_ELEVATION_CONFOUNDER` or `EXCESSIVE_TORSO_YAW`).
   - Displays measured angle, normal reference range, and deficit degrees.

> [!CAUTION]
> **CLINICAL NOTICE:** Camera angles are 2D optical screening estimates. Do NOT use camera estimates to infer internal structural pathology (e.g. deep rotator cuff tears or spinal subluxations).

### 2.4 Patient Clinical Records
- **Registration Form:** Capture full name, age, gender, height, weight, occupation, activity level, medical history, primary complaint, pain VAS score (0-10), radiating symptoms, and functional limitations.
- **Red Flag Screening:** Mandatory questionnaire covering unexplained fever, weight loss, progressive motor deficits, and bowel/bladder dysfunction. Any positive response triggers an immediate **CRITICAL MEDICAL REFERRAL ALERT**.
- **Privacy Hardening:** Each patient receives a keyed HMAC-SHA256 pseudonym hash (`P_***`), eliminating dictionary attack vulnerability.

### 2.5 Therapy Session Workspace & SOAP Generator
1. **Select Patient:** Pre-session symptoms and previous pain score load automatically.
2. **Review & Measure:** Attach motion assessment findings from the camera.
3. **Select Applied Modalities (Evidence-Graded):**
   - *Thai Acupressure* (Traditional Empirical Documented)
   - *Myofascial Trigger Point Release* (Moderate Evidence RCT)
   - *Dien Chan Facial Reflexology* (Traditional Empirical Documented)
   - *Passive Joint Mobilization Grade I-II* (High Evidence Systematic Review)
   - *DDS Bioelectric Electrotherapy* (Moderate Evidence RCT)
4. **Document Physical DDS Device Readout (Optional):**
   - Check *"Document Physical DDS Device Parameters"*.
   - Enter measured frequency (Hz), intensity (mA), and patient reported sensation.
   - *Safety Rule:* Parameters are recorded for clinical documentation only; the software does NOT control or recommend electrical stimulation parameters.
5. **Post-Treatment Evaluation:** Enter post-session pain score (0-10) and notes.
6. **Save Session & Generate SOAP Note:**
   - Automatically drafts complete SOAP note (Subjective, Objective, Assessment, Plan).
   - Updates patient's current pain score in the master registry.

### 2.6 Progress Tracking & Longitudinal Analytics
- **Pain Score Trajectory:** Dual-bar visualization comparing pre-session (red) and post-session (green) pain across all visits.
- **Statistical Summaries:** Computes total pain reduction in VAS points and total completed sessions.
- **Session History Ledger:** Chronological table of all visits with calculated pain deltas.
- **Export Progress CSV:** Click **"Export CSV"** to download an audit-ready clinical summary spreadsheet.

### 2.7 Knowledge Library & Local AI Tutor
- **Full-Text FTS5 Search:** Fast local search across 279 indexed textbooks and clinical documents. Displays exact document filename, section heading, page number, and text excerpts.
- **Movement-to-Muscles Educational Engine:** Select any joint movement to inspect primary agonists, synergists, antagonists, joint classification, and spinal segmental innervation.
- **Measurement Uncertainty Explainer:** Scientific breakdown of camera pixel quantization, operator jitter, and out-of-plane perspective error.
