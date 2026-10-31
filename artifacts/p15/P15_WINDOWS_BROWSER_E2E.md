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
| `p15_step03_scene1_anatomy_rest.png` | `f56b1006c538a69e20fc85b22854d637f571fae531148dc25c0e99d1875f62dc` | 134 KB | Guided Learning Scene 1 neutral resting shoulder girdle (full viewport) |
| `p15_step04_structure_scapula_inspector.png` | `0c30c38b3326fe8b3fa78c50309a5af2c37c67c95dc54e057ef5d1fb99a39d90` | 17 KB | Element: `#shoulder-insp-card` rendering Scapula FMA13395 details & provenance |
| `p15_step05_muscle_delt1_epistemic_badges.png` | `4448f90935fafa64c5dc475d574488d2c0541eedff2df3c70d2e31aac8183fb3` | 27 KB | Element: `#muscle-dynamics-card` showing 4 mandatory epistemic badges |
| `p15_step07_arm_90deg_abduction.png` | `eada654e2a7a9f85beb9b7155ef2503df9ed01ffb51737ae7487a5d8babbbc47` | 107 KB | Arm abducted to 90° under canonical 2:1 rhythm in 3D canvas (full viewport) |
| `p15_step08_delt1_shortened_metrics.png` | `feeac5937e0764b8869a229524f360d4c78b95d4e8d9eaab3a33a873ef1960cc` | 27 KB | Element: `#muscle-dynamics-card` showing shortened fiber length ($l_M$), $l_{MT}$, and passive force |
| `p15_step09_restricted_scapulohumeral_rhythm.png` | `05bb921b4f9b862445da37ba0d94b6d89558284eda99e4bc57142ece349602e8` | 108 KB | Restricted 4:1 rhythm with compromised subacromial status (full viewport) |
| `p15_step10_restricted_mode_caution_badge.png` | `81e8b74b76c6689732d5a0349caf893d10ac0ab102a7d004a674ed52230b48a8` | 5.8 KB | Element: `#dyn-alert-restricted` showing amber caution banner for unadjusted baseline dynamics |
| `p15_step11_motor_control_six_topics.png` | `ac748908ab9b0b8d07a0983877e43e8160087524cca1c1c641b319105e52d158` | 238 KB | Element: `#motor-control-container` rendering 6 comprehensive motor control educational modules |
| `p15_step12_scene6_why_tension_returns.png` | `689de010fb29b249249c319e047adf9b50cb24c0fe1718763b79742f4ceb44c8` | 42 KB | Element: `#guided-scene-content` dedicated Scene 6 card explaining why tension returns |
| `p15_step13_app_reloaded_shoulder_lab.png` | `a2479cde98c90ae9b227b578ceba30334e7801475def2baf0e7b3ac1b08f5a23` | 114 KB | Post-reload state persistence, scrubbed to 45° elevation (full viewport) |
| `p15_step14_anatomy_regression_intact.png` | `3ca3076753d5a0c18f3ed29c47a799e7877b3ba2e9793962d9e670124a739324` | 61 KB | 3D Anatomy Explorer view regression confirmation (full viewport) |
