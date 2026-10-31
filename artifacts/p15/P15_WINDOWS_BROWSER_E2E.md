# P15 Windows Microsoft Edge End-to-End Acceptance Report
**MSK Research Lab OS — Milestone P15**  
**Role:** Desktop QA Engineer, Independent Verification Auditor  
**Date:** 2026-10-31  
**Harness:** Playwright 1.64.1 on Microsoft Edge (`channel="msedge"`)  
**Test Script:** [`tests/integration/test_p15_guided_learning_e2e.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p15_guided_learning_e2e.py)  
**Screenshots Path:** [`artifacts/p15/screenshots/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p15/screenshots/)

---

## 1. Executive Summary

Milestone P15 executed the complete 15-step interactive acceptance challenge on **native Microsoft Edge** running in the Windows host environment.

All 15 steps passed with zero errors. High-resolution screenshots were captured and cryptographically hashed with SHA-256 digests.

---

## 2. 15-Step Acceptance Execution Log

| Step # | Verified Action | Observed Result | Evidence Screenshot |
|---|---|---|---|
| **Step 1** | Launch Workstation on loopback | Workstation loads at `http://127.0.0.1:8098/workstation`, title displays `Home Dashboard`. | — |
| **Step 2** | Open Shoulder Movement Lab | `#view-shoulder` activates, Three.js canvas initializes, title updates to `Shoulder Movement & Biomechanics Lab`. | — |
| **Step 3** | Enter Guided Learning | Scene 1 loads (`Anatomical Architecture of the Shoulder Girdle`), dots rendered, arm at $0^\circ$ rest. | `p15_step03_scene1_anatomy_rest.png` |
| **Step 4** | Select Scapula | Scapula (`FMA13395`) selected in inspector; provenance details rendered. | `p15_step04_structure_scapula_inspector.png` |
| **Step 5** | Highlight DELT1 & Verify 4 Badges | Anterior Deltoid selected; all 4 mandatory badges rendered: `MODELED_LENGTH_CHANGE`, `MODELED_PASSIVE_FORCE`, `MUSCLE_ACTIVATION_NOT_MEASURED`, `EDUCATIONAL_ILLUSTRATION`. | `p15_step05_muscle_delt1_epistemic_badges.png` |
| **Step 6** | Play Shoulder Movement | Animation toggles between Play and Pause seamlessly. | — |
| **Step 7** | Timeline Scrub to 90° | Slider set to $90^\circ$; readouts verify GH: $70.0^\circ$, ST: $20.0^\circ$. | `p15_step07_arm_90deg_abduction.png` |
| **Step 8** | Observe DELT1 Dynamics at 90° | DELT1 fiber length verified in cm, delta length verified, KMSI chip shows `SHORTENED` (blue). | `p15_step08_delt1_shortened_metrics.png` |
| **Step 9** | Switch to Restricted Mode | Scapular rhythm switches to Restricted 4:1; GH: $78.0^\circ$, ST: $12.0^\circ$; status shows `Compromised`. | `p15_step09_restricted_scapulohumeral_rhythm.png` |
| **Step 10** | Verify Baseline Caveat Alert | Alert box `#dyn-alert-restricted` displays amber `CAUTION: Unadjusted baseline estimate...`. | `p15_step10_restricted_mode_caution_badge.png` |
| **Step 11** | Verify 6 Motor Control Topics | 6 educational cards rendered detailing planning, proprioception, recruitment, learning, synergies, and tension relief. | `p15_step11_motor_control_six_topics.png` |
| **Step 12** | Sequential Scenes 1 to 6 | All 6 Guided Learning scenes navigated sequentially, ending on Scene 6 (Why Tension Returns). | `p15_step12_scene6_why_tension_returns.png` |
| **Step 13** | Reload & Persistence | Page refreshed; workstation recovers intact and re-enters Shoulder Lab without state corruption. | `p15_step13_app_reloaded_shoulder_lab.png` |
| **Step 14** | Regression Confirmation | Switched back to Dashboard and 3D Anatomy views; all existing 3D models and controls functional. | `p15_step14_anatomy_regression_intact.png` |
| **Step 15** | Offline Loopback Verification | Base URL confirmed strictly on `127.0.0.1:8098`; no external network sockets opened. | Verified |

---

## 3. Cryptographic Screenshot Evidence Inventory

| Screenshot Filename | SHA-256 Digest | File Size | Description |
|---|---|---|---|
| `p15_step03_scene1_anatomy_rest.png` | `5803298b9484552b5c919e8fac49b58c56682b2850c4c926f8af7ec81cdba2b9` | 134 KB | Guided Learning Scene 1 neutral resting shoulder girdle |
| `p15_step04_structure_scapula_inspector.png` | `5803298b9484552b5c919e8fac49b58c56682b2850c4c926f8af7ec81cdba2b9` | 134 KB | Scapula FMA13395 structural and provenance inspector |
| `p15_step05_muscle_delt1_epistemic_badges.png` | `08c8cd69d6ff3fe35e3a4d68ff084e083ce53931e382f53cea377f3529f58c15` | 135 KB | Muscle dynamics inspector with 4 mandatory epistemic badges |
| `p15_step07_arm_90deg_abduction.png` | `613513a91d202463979ce815aee0a45461df7264cf5206a9526ead02373dd0e6` | 136 KB | Arm abducted to 90° under canonical 2:1 rhythm |
| `p15_step08_delt1_shortened_metrics.png` | `613513a91d202463979ce815aee0a45461df7264cf5206a9526ead02373dd0e6` | 136 KB | DELT1 shortened fiber length, delta length, and passive force |
| `p15_step09_restricted_scapulohumeral_rhythm.png` | `742aa8a3cf6de829407814035b9b28f01adf3c0b6e28ca83d0e79230bb46a5f2` | 137 KB | Restricted 4:1 rhythm with compromised subacromial status |
| `p15_step10_restricted_mode_caution_badge.png` | `742aa8a3cf6de829407814035b9b28f01adf3c0b6e28ca83d0e79230bb46a5f2` | 137 KB | Amber caution banner for unadjusted baseline dynamics |
| `p15_step11_motor_control_six_topics.png` | `1820b432227cd7903beac5b8063fb17e68ebea1dee7a8d9ec7b0e2ff67c17255` | 158 KB | 6 comprehensive motor control educational modules |
| `p15_step12_scene6_why_tension_returns.png` | `7dfe134e31c8bdff6a1df516bda7111d1b77faaa0d6a43101b2d4808b183037a` | 138 KB | Scene 6: Why Tension Returns and principles of lasting change |
| `p15_step13_app_reloaded_shoulder_lab.png` | `ca9fbecf4059a75137a0b482925121a6c4a892d0fe6f454b96b1dc4929dcf2c9` | 134 KB | Post-reload state persistence and clean canvas re-initialization |
| `p15_step14_anatomy_regression_intact.png` | `2b2e1bc148ec40951b8b3c44e9d8ebc3dedd5f4c6025cb84526d9ccd56147380` | 129 KB | 3D Anatomy Explorer view regression confirmation |
