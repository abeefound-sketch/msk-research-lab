# P14 Real-Browser Visual Evidence & Kinematic Verification Dossier
**MSK Research Lab OS — Milestone P14**  
**Role:** Independent Release QA, Biomedical Visualization Auditor  
**Date:** 2026-10-30  
**Browser Engine:** Microsoft Edge (Chromium Channel `msedge`, Desktop Viewport 1440x1000)  
**Evidence Directory:** [`artifacts/p14/screenshots/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p14/screenshots/)  

---

## 1. Executive Summary

Milestone P14 qualification executed real-browser automated acceptance testing using Microsoft Edge and Playwright. Seven high-resolution evidence screenshots were captured across distinct physiological arm elevation angles and educational states.

All visual assets have been verified for:
1. Physical rendering integrity on Three.js WebGL canvas without rendering artifacts or black frames.
2. Synchronized coordinate readouts matching the declared mathematical model.
3. Visible rendering of structured scientific provenance cards and disclaimers.
4. Correct display of the 3 Motor Control Education cards with physiological mechanisms and peer-reviewed citations.

---

## 2. Screenshot Evidence Inventory & Cryptographic Checksums

| Screenshot Filename | File Size | SHA-256 Checksum | Movement / UI State | Key Rendered Visual Elements |
|---|---|---|---|---|
| `shoulder_lab_000deg_neutral_rest.png` | 116 KB | `d8e0fbccc039503daef1f39215913f35d27ee836a7c2f40f1b5144f695570b06` | Neutral Rest (0.0°) | Arm hanging vertically; GH: 0.0°, ST: 0.0°, SC: 0.0°; Subacromial Adequate; Inman 2:1 Badge |
| `shoulder_lab_045deg_normal_rhythm.png` | 118 KB | `db2da5b80dc4910226a0ca7cbcae6f134468a07958264a9a844be5e2a0744992` | Setting / Early Abduction (45.0°) | Clavicle beginning elevation; GH: 40.0°, ST: 5.0°, SC: 8.1°; Arm abducted in coronal plane |
| `shoulder_lab_090deg_normal_rhythm.png` | 118 KB | `83814eadb112c3946bc7a6d1fcda725b5a09581305664146487aef81677d6559` | Mid-Range Abduction (90.0°) | Horizontal arm; GH: 70.0°, ST: 20.0°, SC: 16.2°; OpenSim muscle table rendered with `[BENCHMARK]` |
| `shoulder_lab_120deg_normal_rhythm.png` | 117 KB | `2456bc4383b0f62e2aed21be5db5361887b30d7cfe82588ed8567f0842d4be9c` | High Abduction (120.0°) | Arm elevated above horizontal; GH: 90.0°, ST: 30.0°, SC: 21.6°; Smooth scapular upward rotation |
| `shoulder_lab_180deg_overhead_full.png` | 118 KB | `e0c65927a63efb25180b8879471b2286540bfe9f4e673078c0c64b86f59a9057` | Full Overhead Reach (180.0°) | Humerus pointing vertically overhead; GH: 130.0°, ST: 50.0°, SC: 32.4°; Elbow elevated to $z > 1.6\text{ m}$ |
| `shoulder_lab_090deg_forward_shoulder_restricted.png` | 118 KB | `c928bceb9bd31dee6dd5f56dff031c3a67bdf175a26331d91b45632df13c86d6` | Restricted Model B (90.0°) | Badge: "Restricted 4:1 Rhythm"; GH: 78.0°, ST: 12.0°; Status: "Compromised"; `[BASELINE (UNADJUSTED)]` |
| `shoulder_lab_motor_control_education.png` | 174 KB | `2f667ac7281032c33b2f208e072fecbb154c602db1d59ad5f5fcb03d68cd5c0e` | Motor Control Module | 3 responsive educational cards detailing Spindles, Viscoelastic relaxation vs coordination, and Neuroplasticity |

---

## 3. Detailed Screenshot Observations

### 3.1 State 1: Neutral Anatomical Rest (0.0°)
- **File:** `artifacts/p14/screenshots/shoulder_lab_000deg_neutral_rest.png`
- **Visual Evidence:** All 13 calibrated BodyParts3D GLB meshes assemble in their rest position. The clavicle is oriented along the superior-medial thorax wall, the scapula rests against the rib cage, and the humerus hangs vertically along $-Z$. Numerical readouts confirm GH: 0.0°, ST: 0.0°, SC: 0.0°. Subacromial clearance is marked `Adequate`.

### 3.2 State 2: Setting Phase & Early Abduction (45.0°)
- **File:** `artifacts/p14/screenshots/shoulder_lab_045deg_normal_rhythm.png`
- **Visual Evidence:** The humerus is abducted $45^\circ$ laterally. Because the setting phase spans $0^\circ - 30^\circ$, the glenohumeral joint contributes $40.0^\circ$ and the scapula has initiated upward rotation with $5.0^\circ$. Clavicular elevation has progressed to $8.1^\circ$.

### 3.3 State 3: Mid-Range Coronal Elevation (90.0°)
- **File:** `artifacts/p14/screenshots/shoulder_lab_090deg_normal_rhythm.png`
- **Visual Evidence:** The humerus is oriented horizontally along the $-X$ lateral axis. Readouts show GH: 70.0°, ST: 20.0°, SC: 16.2°, exactly satisfying $70^\circ + 20^\circ = 90^\circ$. The OpenSim muscle table indicates anterior deltoid shortening ($\tilde{l}_M = 0.932$) and middle deltoid active engagement. Every muscle row bears a green `[BENCHMARK]` badge.

### 3.4 State 4: High Abduction (120.0°)
- **File:** `artifacts/p14/screenshots/shoulder_lab_120deg_normal_rhythm.png`
- **Visual Evidence:** The arm has passed horizontal and reaches $120.0^\circ$. Glenohumeral elevation reaches $90.0^\circ$ and scapulothoracic upward rotation reaches $30.0^\circ$. Scapular posterior tilt is visibly maintained.

### 3.5 State 5: Full Overhead Elevation (180.0°)
- **File:** `artifacts/p14/screenshots/shoulder_lab_180deg_overhead_full.png`
- **Visual Evidence:** The humerus is positioned straight upward along $+Z$. World humerus rotation is verified at $180.0^\circ$, composed of $130.0^\circ$ glenohumeral elevation and $50.0^\circ$ scapular upward rotation. The clavicle is elevated by $32.4^\circ$. The elbow pivot has moved from $z = 1.05\text{ m}$ to $z = 1.61\text{ m}$.

### 3.6 State 6: Comparative Model B — Forward Shoulder Restrained (90.0°)
- **File:** `artifacts/p14/screenshots/shoulder_lab_090deg_forward_shoulder_restricted.png`
- **Visual Evidence:** The top rhythm badge switches to a red badge: `Restricted 4:1 Rhythm`. Scapular upward rotation is restricted to $12.0^\circ$, forcing compensatory glenohumeral elevation to $78.0^\circ$. The Subacromial Clearance readout highlights in rose: `Compromised (Impingement Risk)`. The muscle table renders an amber warning badge on every row: `[BASELINE (UNADJUSTED)]`, cautioning researchers that values reflect unadjusted baseline coordinates.

### 3.7 State 7: Motor Control, Sensory Feedback & Neuroplasticity
- **File:** `artifacts/p14/screenshots/shoulder_lab_motor_control_education.png`
- **Visual Evidence:** Three rich educational cards rendered side by side:
  1. *Sensory Feedback: Muscle Spindles, Golgi Tendon Organs & Proprioception* (with Kandel 2021 citations).
  2. *Why Temporary Muscle Tension Relief Does Not Equal Lasting Coordination Change* (explaining viscoelastic stress relaxation vs habitual motor maps, citing Weppler & Magnusson 2010).
  3. *Motor Learning, Sensorimotor Integration & Active Movement Practice* (explaining deliberate practice and cortical remapping, citing Hodges 1996 and Kleim 2008).

---

## 4. Verification Conclusion

All visual evidence has been captured directly from real browser execution on Microsoft Edge and archived with cryptographic SHA-256 hashes. The user interface demonstrates complete fidelity between numerical predictions, 3D WebGL scene rendering, and educational provenance displays.
