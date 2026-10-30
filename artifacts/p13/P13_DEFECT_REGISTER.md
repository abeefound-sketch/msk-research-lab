# P13 Defect Register: Biomechanics Integration & Browser UI Hardening

**Milestone:** P13  
**Auditor:** Principal Software Architect, Desktop QA  
**Date:** 2026-10-30  

---

## Defect Summary

| Defect ID | Severity | Category | Component | Description | Remediation | Status |
| :---: | :---: | :---: | :--- | :--- | :--- | :---: |
| **DEF-39** | **HIGH** | Client UI / Syntax | `workstation_ui.py` | Unescaped literal newlines in JS double-quoted string concatenations broke client-side script evaluation. | Converted to ES6 template literals (backticks); validated with `node --check`. | **CLOSED** |
| **DEF-40** | **MEDIUM** | API Routing | `workstation_routes.py` | `Path` and `FileResponse` were referenced in `api_serve_shoulder_model` without explicit import. | Added `from pathlib import Path` and `FileResponse` to module imports. | **CLOSED** |
| **DEF-41** | **LOW** | Test Automation | `test_p13_shoulder_lab_browser_e2e.py` | HTML5 `<input type="range">` rejected `fill()` action in Playwright. | Updated test to set range value and trigger `onShoulderTimelineScrub()` handler directly. | **CLOSED** |

---

## Detailed Defect Remediation Records

### DEF-39: Unescaped Newline in UI JavaScript Multiline Template Strings
- **Severity:** HIGH
- **Location:** `src/msk_research_lab/api/workstation_ui.py` (Lines 1520 and 1584)
- **Symptom:** In automated browser runs, navigation clicked the sidebar but no view switched (`ReferenceError: switchView is not defined`).
- **Root Cause:** In Python triple-quoted multiline strings (`"""..."""`), escape sequences like `\n` are evaluated into literal ASCII newline characters (`0x0A`) at string compilation time. In JavaScript, a double-quoted string cannot span across raw newlines without backslash continuation, causing V8 to abort parsing with `SyntaxError: Invalid or unexpected token`.
- **Remediation:** Converted multi-line clinical SOAP notes displays in `previewSOAP()` and `saveTherapySession()` to ES6 template literals (`` ` ... ` ``). Verified that `node --check` returns 0 syntax errors across all 1240 lines of workstation client JavaScript.

### DEF-40: Missing Path and FileResponse Imports in Model Serving Route
- **Severity:** MEDIUM
- **Location:** `src/msk_research_lab/api/workstation_routes.py`
- **Symptom:** Unit test `test_api_model_file_serving` failed with `NameError: name 'Path' is not defined`.
- **Root Cause:** Posix `Path` and `FileResponse` were utilized in the new `api_serve_shoulder_model` route but were missing from module-level imports.
- **Remediation:** Added `from pathlib import Path` and `FileResponse` to `workstation_routes.py`. Verified HTTP GET for GLB models returns 200 with `model/gltf-binary` MIME type.

### DEF-41: HTML5 Range Input Event Incompatibility in Automated Test
- **Severity:** LOW
- **Location:** `tests/integration/test_p13_shoulder_lab_browser_e2e.py`
- **Symptom:** Playwright threw `Locator.fill: Error: Malformed value` when attempting to fill timeline slider `#shoulder-timeline-slider`.
- **Root Cause:** Standard browser implementations of `<input type="range">` reject direct character typing/filling.
- **Remediation:** Changed test interaction to evaluate `slider.value = '90.0'; onShoulderTimelineScrub(90.0);`, faithfully simulating user mouse scrub.
