# P16 Windows Microsoft Edge End-to-End Acceptance Report
**MSK Research Lab OS — Milestone P16**  
**Role:** Desktop QA Engineer, Independent Verification Auditor  
**Date:** 2026-10-31  
**Harness:** Playwright 1.64.1 on native Microsoft Edge (`channel="msedge"`)  
**Test Script:** [`tests/integration/test_p15_guided_learning_e2e.py`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/tests/integration/test_p15_guided_learning_e2e.py)  
**Screenshots Path:** [`artifacts/p15/screenshots/`](file:///mnt/c/Users/tuanh/Downloads/msk-research-lab/artifacts/p15/screenshots/)  

---

## 1. Executive Summary

Milestone P16 verified the interactive Shoulder Movement Lab on **native Microsoft Edge** running in the host Windows environment. All 15 acceptance steps passed with zero failures. High-resolution visual evidence was captured using element-isolated bounding boxes, ensuring that every screenshot has an independent visual subject and a distinct SHA-256 cryptographic digest.

---

## 2. 15-Step Acceptance Execution Log

| Step # | Executed Action | Observed System Behavior | Evidence Screenshot |
|---|---|---|---|
| **Step 1** | Launch Workstation on loopback | Fast startup at `http://127.0.0.1:8098/workstation`; title renders `Home Dashboard`. | — |
| **Step 2** | Navigate to Shoulder Movement Lab | `#view-shoulder` displays; WebGL canvas initializes; title updates to `Interactive Shoulder Movement & Biomechanics Lab`. | — |
| **Step 3** | Enter Guided Learning Scene 1 | Scene 1 loads (`Anatomical Architecture of the Shoulder Girdle`); arm positioned at neutral rest ($0.0^\circ$). | `p15_step03_scene1_anatomy_rest.png` |
| **Step 4** | Select Scapula (`FMA13395`) | Structure inspector displays Scapula provenance, anatomical landmarks, and kinematic roles. | `p15_step04_structure_scapula_inspector.png` |
| **Step 5** | Highlight DELT1 & Verify Badges | Anterior Deltoid dynamics loaded; displays 4 mandatory epistemic distinction tags. | `p15_step05_muscle_delt1_epistemic_badges.png` |
| **Step 6** | Test Play/Pause Animation | Arm elevates smoothly; button toggles between `▶ Play` and `⏸ Pause`. | — |
| **Step 7** | Scrub Timeline to 90° | Slider set to $90.0^\circ$; GH: $70.0^\circ$, ST: $20.0^\circ$, SC: $16.2^\circ$; action line endpoints track moving bone frames. | `p15_step07_arm_90deg_abduction.png` |
| **Step 8** | Observe DELT1 Dynamics at 90° | DELT1 fiber length shortened to $8.17\text{ cm}$; $l_{MT} = 17.47\text{ cm}$; KMSI chip displays `SHORTENED` (blue). | `p15_step08_delt1_shortened_metrics.png` |
| **Step 9** | Switch to Restricted Rhythm | Mode set to Model B; scapular upward rotation restricted to $12.0^\circ$ at $90^\circ$ elevation; red `Restricted 4:1 Rhythm` badge active. | `p15_step09_restricted_scapulohumeral_rhythm.png` |
| **Step 10** | Verify Baseline Data Caveat | Amber alert `#dyn-alert-restricted` displays caution: unadjusted baseline estimate. | `p15_step10_restricted_mode_caution_badge.png` |
| **Step 11** | Verify 6 Motor Control Topics | Renders all 6 peer-reviewed motor control topics with physiological mechanisms and citations. | `p15_step11_motor_control_six_topics.png` |
| **Step 12** | Sequential Navigation (Scenes 1–6) | Seamlessly navigates scenes 1 through 6; Scene 6 explains why tension returns with non-dogmatic neurophysiology. | `p15_step12_scene6_why_tension_returns.png` |
| **Step 13** | Refresh & State Recovery | Page reloaded; state re-enters Shoulder Lab; scrubs to $45.0^\circ$ confirming active post-reload responsiveness. | `p15_step13_app_reloaded_shoulder_lab.png` |
| **Step 14** | Regression Confirmation | Navigates back to Dashboard and 3D Anatomy Explorer; Three.js torso and organ layers functional. | `p15_step14_anatomy_regression_intact.png` |
| **Step 15** | Offline Loopback Verification | Base URL confirmed strictly loopback (`127.0.0.1:8098`); zero external network sockets opened. | Verified |

---

## 3. Cryptographic Screenshot Evidence Inventory

All 11 screenshots verified with 100% unique SHA-256 digests:

| Screenshot Filename | SHA-256 Digest | Size | Verified Visual Subject |
|---|---|---|---|
| `p15_step03_scene1_anatomy_rest.png` | `f56b1006c538a69e20fc85b22854d637f571fae531148dc25c0e99d1875f62dc` | 134 KB | Neutral resting shoulder girdle ($0.0^\circ$) |
| `p15_step04_structure_scapula_inspector.png` | `0c30c38b3326fe8b3fa78c50309a5af2c37c67c95dc54e057ef5d1fb99a39d90` | 17 KB | Element: `#shoulder-insp-card` (Scapula details & provenance) |
| `p15_step05_muscle_delt1_epistemic_badges.png` | `4448f90935fafa64c5dc475d574488d2c0541eedff2df3c70d2e31aac8183fb3` | 27 KB | Element: `#muscle-dynamics-card` (4 Epistemic Badges) |
| `p15_step07_arm_90deg_abduction.png` | `fe6fb7e80b0b86a5d679d3164371428bc09435ea75884b2a2813e6367ca0e23f` | 107 KB | 3D Viewport at $90.0^\circ$ Abduction (GH: $70^\circ$, ST: $20^\circ$) |
| `p15_step08_delt1_shortened_metrics.png` | `b77af38a02cc5bad657c898d73cb9da76a8de9d0ff9c093ed2b4c4a1355f3821` | 27 KB | Element: `#muscle-dynamics-card` ($l_M = 8.17\text{ cm}$, $l_{MT} = 17.47\text{ cm}$) |
| `p15_step09_restricted_scapulohumeral_rhythm.png` | `dc2aba79c17d1e609828ec449374a56ec0ef9a537d124a060d40087aeab2577c` | 108 KB | Restricted 4:1 Rhythm (GH: $78^\circ$, ST: $12^\circ$, compromised clearance) |
| `p15_step10_restricted_mode_caution_badge.png` | `81e8b74b76c6689732d5a0349caf893d10ac0ab102a7d004a674ed52230b48a8` | 5.8 KB | Element: `#dyn-alert-restricted` (Amber Caution Alert) |
| `p15_step11_motor_control_six_topics.png` | `ac748908ab9b0b8d07a0983877e43e8160087524cca1c1c641b319105e52d158` | 238 KB | Element: `#motor-control-container` (6 Educational Topics) |
| `p15_step12_scene6_why_tension_returns.png` | `689de010fb29b249249c319e047adf9b50cb24c0fe1718763b79742f4ceb44c8` | 42 KB | Element: `#guided-scene-content` (Scene 6 Case Study) |
| `p15_step13_app_reloaded_shoulder_lab.png` | `a2479cde98c90ae9b227b578ceba30334e7801475def2baf0e7b3ac1b08f5a23` | 114 KB | Post-Reload State Scrubbed to $45.0^\circ$ |
| `p15_step14_anatomy_regression_intact.png` | `3ca3076753d5a0c18f3ed29c47a799e7877b3ba2e9793962d9e670124a739324` | 61 KB | Viewport: `#view-anatomy` (3D Atlas Intact) |

---

## 4. Acceptance Sign-Off

**P16-F Windows Browser Gate: PASSED.**  
All 15 steps verified on Microsoft Edge. Zero JavaScript console errors; 100% loopback offline compliance.
