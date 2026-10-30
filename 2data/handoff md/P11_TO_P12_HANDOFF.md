# P11 TO P12 HANDOFF DIRECTIVE
**MSK Research Lab OS — Personal Offline Workstation**

- **Handoff Date:** 2026-10-30
- **From:** Milestone P11 Lead Engineer
- **To:** Milestone P12 Incoming Verification & Release Engineering Team
- **Current Branch:** `fix/workstation-real-functional-acceptance`
- **Total Tests:** 269 PASSED, 0 FAILED, 1 WARNING (Starlette deprecation)
- **Release Verdict:** `GO — PERSONAL OFFLINE WORKSTATION / SYNTHETIC & RESEARCH ONLY`

---

## 1. Checkpoint Status

Milestone P11 has remediated defects DEF-27 through DEF-32:
- **DEF-27:** Atomic database replacement during backup restoration via temporary staging file and `os.replace`.
- **DEF-28:** Brown-Conrady forward and inverse lens distortion compensation in optical ray back-projection.
- **DEF-29:** Expanded clinical free-text PHI scrubber detecting textual dates, MRNs, IPs, and ZIP codes with Safe Harbor disclosures.
- **DEF-30:** Standardized 4-state measurement provenance classification (`LIVE_MEASURED`, `SYNTHETIC_TEST`, `NOT_MEASURABLE`, `INVALID_INPUT`).
- **DEF-31:** Resilient Windows identity resolution fallback for `icacls` DACL enforcement.
- **DEF-32:** 6-DoF Levenberg-Marquardt spatial covariance eigenvalues, condition number, and planarity ratio calculation.

---

## 2. Invariant Rules for P12

Incoming engineers MUST preserve the following non-negotiable boundaries:
1. `CLINICAL_REALWORLD_GATE`: **Strictly BLOCKED**. Do not attempt to rebrand or certify the software as a medical device or clinical diagnostic tool.
2. `PHYSICAL_STEREO_HARDWARE_GATE`: **Strictly BLOCKED (DUAL_CAMERA_UNAVAILABLE)**. Do not synthesize or emulate stereo camera hardware unless 2 real genlocked physical cameras are detected.
3. `CANNOT_IMPLICITLY_PROJECT_2D_TO_3D`: Strictly enforced fail-closed. Uncalibrated 2D projections must raise `DienChanError`.
4. **Air-Gapped Offline Operation**: Keep network bindings strictly on `127.0.0.1` and `::1`. Do not introduce outbound network requests.

---

## 3. Recommended P12 Focus Areas

1. **Long-Term Multi-Session Analytics**: Verify longitudinal ROM trend stability across multi-month synthetic therapy simulations.
2. **Advanced Anisotropic Surface Snapping**: Integrate Kd-tree accelerated mesh raycasting for high-poly head meshes (> 100k polygons).
3. **Automated Windows Standalone Installer**: Package an InnoSetup or MSI installer bundling the verified Python 3.11 embedded runtime and desktop distribution.
