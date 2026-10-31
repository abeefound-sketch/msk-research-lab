# P15 Defect Register & Resolution Log
**MSK Research Lab OS — Milestone P15**  
**Role:** Independent Release QA, Software Reliability Auditor  
**Date:** 2026-10-31  

---

## 1. Defect Summary

| Defect ID | Severity | Category | Description | Root Cause | Status |
|---|---|---|---|---|---|
| **DEF-13** | Medium | Test Regression | `test_p14_geometry_and_animation_oracle.py` failed with `assert len(topics) == 3`. | P15 expanded motor control education from 3 to 6 comprehensive topics, causing the exact length check in P14 test to fail. | **RESOLVED** (Updated assertion to `>= 3`, preserving backward compatibility for original 3 topic IDs while supporting all 6). |
| **DEF-14** | High | OS Interop | Calling Windows `python.exe` or `powershell.exe` from WSL hung when executed as background task. | Windows console executables invoked across WSL interop attempt to attach to an interactive terminal/conhost handle or block on stdin unless redirected. | **RESOLVED** (Appended `< /dev/null` to standard execution commands, ensuring non-blocking sub-process execution). |
| **DEF-15** | Low | E2E Selector Mismatch | Initial Playwright test timed out looking for `#muscle-dynamics-select` and `#view-atlas`. | DOM IDs in `workstation_ui.py` were defined as `#dyn-muscle-select` and `#view-anatomy`, and fiber length metric is formatted in `cm`. | **RESOLVED** (Aligned test selectors with verified DOM structure; 15/15 steps passing). |

---

## 2. Detailed Defect Investigations & Verification Evidence

### 2.1 DEF-13: Motor Control Educational Topics Expansion
- **Impact:** Pytest reported 1 failure in P14 geometry test suite.
- **Resolution:** Modified `test_p14_geometry_and_animation_oracle.py::test_motor_control_education_topics_and_references` to assert `len(topics) >= 3`. Verified that original core topics (`sensory_feedback_proprioception`, `transient_tone_relief_vs_coordination`, `motor_learning_neuroplasticity`) and their cited mechanisms/authors remain intact.
- **Verification:** 41/41 biomechanics unit tests PASS.

### 2.2 DEF-14: WSL/Windows Host Python Subprocess Stdin Blocking
- **Impact:** Background process probe hung awaiting stdin.
- **Resolution:** Redirected stdin with `< /dev/null` when launching Windows Playwright test from WSL bash.
- **Verification:** Test completes synchronously and headlessly in ~30 seconds, generating all expected visual evidence.

### 2.3 DEF-15: DOM Element ID Alignment
- **Impact:** Playwright test script failed at Step 5 and Step 14 on mismatched selector names.
- **Resolution:** Corrected `#muscle-dynamics-select` to `#dyn-muscle-select`, fiber length assertion to check for `'cm'`, and `#view-atlas` to `#view-anatomy`.
- **Verification:** `test_p15_guided_learning_e2e.py` completed with exit code 0 (`[SUCCESS] All 15 P15 Acceptance Steps VERIFIED on Microsoft Edge`).
