"""Playwright End-to-End Real Browser Acceptance Test for Shoulder Movement Lab (P14).

Verifies the complete interactive educational experience on system Microsoft Edge:
1. Multi-state kinematic scrubbing (0°, 45°, 90°, 120°, 180°)
2. Anatomical structure inspector with structured scientific provenance
3. Comparative movement model switching (Normal 2:1 vs Restricted Forward Shoulder)
4. Model-delineated muscle responses (Baseline Benchmark vs Unadjusted Caution Badge)
5. Evidence-based Motor Control Education module (Sensory Feedback, Transient Relief, Neuroplasticity)
6. Captures real evidence screenshots into artifacts/p14/screenshots/
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path

# Ensure project src is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import uvicorn
import pytest
from playwright.sync_api import sync_playwright

from msk_research_lab.api.app import app

TEST_PORT = 8099
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"
SCREENSHOT_DIR = PROJECT_ROOT / "artifacts" / "p14" / "screenshots"


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=TEST_PORT):
        super().__init__()
        self.server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))
        self.daemon = True

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def test_p14_shoulder_educational_browser_acceptance():
    """Verify all P14 educational, kinematic, and epistemic controls on real Microsoft Edge."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    server = ServerThread(app, host="127.0.0.1", port=TEST_PORT)
    server.start()
    time.sleep(1.5)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 1000})
            page = context.new_page()

            # 1. Open Workstation
            page.goto(f"{BASE_URL}/workstation", timeout=15000)
            page.wait_for_selector("#page-title", timeout=10000)
            assert "Home Dashboard" in page.inner_text("#page-title")

            # 2. Switch to Shoulder Movement Lab
            page.evaluate("switchView('shoulder')")
            page.wait_for_selector("#view-shoulder.active", timeout=5000)
            assert "Shoulder Movement & Biomechanics Lab" in page.inner_text("#page-title")
            time.sleep(2.0)

            # 3. Verify Initial 0° Rest Position
            assert page.inner_text("#val-arm-deg") == "0.0"
            assert page.inner_text("#readout-gh-deg") == "0.0°"
            assert page.inner_text("#readout-st-deg") == "0.0°"
            assert page.inner_text("#readout-sc-deg") == "0.0°"
            assert "Adequate" in page.inner_text("#readout-subacromial-status")
            assert "Inman 2:1 Rhythm" in page.inner_text("#shoulder-rhythm-badge")

            # Screenshot at 0° Neutral
            page.screenshot(path=str(SCREENSHOT_DIR / "shoulder_lab_000deg_neutral_rest.png"))
            print("[E2E] Captured: shoulder_lab_000deg_neutral_rest.png")

            # 4. Scrub to 45° Setting / Early Abduction Phase
            page.evaluate("document.getElementById('shoulder-timeline-slider').value = '45.0'; onShoulderTimelineScrub(45.0);")
            time.sleep(0.5)
            assert page.inner_text("#val-arm-deg") == "45.0"
            assert page.inner_text("#readout-st-deg") == "5.0°"
            assert page.inner_text("#readout-gh-deg") == "40.0°"
            page.screenshot(path=str(SCREENSHOT_DIR / "shoulder_lab_045deg_normal_rhythm.png"))
            print("[E2E] Captured: shoulder_lab_045deg_normal_rhythm.png")

            # 5. Scrub to 90° Coronal Abduction
            page.evaluate("document.getElementById('shoulder-timeline-slider').value = '90.0'; onShoulderTimelineScrub(90.0);")
            time.sleep(0.5)
            assert page.inner_text("#val-arm-deg") == "90.0"
            assert page.inner_text("#readout-st-deg") == "20.0°"
            assert page.inner_text("#readout-gh-deg") == "70.0°"
            assert page.inner_text("#readout-sc-deg") == "16.2°"
            page.screenshot(path=str(SCREENSHOT_DIR / "shoulder_lab_090deg_normal_rhythm.png"))
            print("[E2E] Captured: shoulder_lab_090deg_normal_rhythm.png")

            # 6. Scrub to 120° Mid-to-High Abduction
            page.evaluate("document.getElementById('shoulder-timeline-slider').value = '120.0'; onShoulderTimelineScrub(120.0);")
            time.sleep(0.5)
            assert page.inner_text("#val-arm-deg") == "120.0"
            assert page.inner_text("#readout-st-deg") == "30.0°"
            assert page.inner_text("#readout-gh-deg") == "90.0°"
            page.screenshot(path=str(SCREENSHOT_DIR / "shoulder_lab_120deg_normal_rhythm.png"))
            print("[E2E] Captured: shoulder_lab_120deg_normal_rhythm.png")

            # 7. Scrub to 180° Full Overhead Elevation
            page.evaluate("document.getElementById('shoulder-timeline-slider').value = '180.0'; onShoulderTimelineScrub(180.0);")
            time.sleep(0.5)
            assert page.inner_text("#val-arm-deg") == "180.0"
            assert page.inner_text("#readout-st-deg") == "50.0°"
            assert page.inner_text("#readout-gh-deg") == "130.0°"
            assert page.inner_text("#readout-sc-deg") == "32.4°"
            page.screenshot(path=str(SCREENSHOT_DIR / "shoulder_lab_180deg_overhead_full.png"))
            print("[E2E] Captured: shoulder_lab_180deg_overhead_full.png")

            # 8. Test Structure Inspector with Epistemic Provenance
            page.select_option("#shoulder-structure-select", "FMA13322")
            page.evaluate("selectShoulderStructure('FMA13322')")
            time.sleep(0.5)
            assert "Right Clavicle" in page.inner_text("#shoulder-insp-title")
            prov_text = page.inner_text("#shoulder-insp-provenance")
            assert "Epistemic Provenance" in prov_text
            assert "MOBL_ARMS_41_CLAVICLE" in prov_text
            assert "VERIFIED_BASELINE_BENCHMARK" in prov_text

            # 9. Verify Baseline Muscle Table
            page.evaluate("document.getElementById('shoulder-timeline-slider').value = '90.0'; onShoulderTimelineScrub(90.0);")
            time.sleep(1.0)
            tbody_html = page.inner_html("#shoulder-muscle-tbody")
            assert "DELT1" in tbody_html
            assert "BENCHMARK" in tbody_html

            # 10. Switch to Model B: Forward Shoulder Restrained
            page.select_option("#shoulder-comparison-select", "forward_shoulder_restricted")
            page.evaluate("changeShoulderComparisonMode()")
            time.sleep(0.8)
            assert "Restricted 4:1 Rhythm" in page.inner_text("#shoulder-rhythm-badge")
            assert page.inner_text("#readout-st-deg") == "12.0°"  # 40% restricted: (90-30)/3 * 0.6 = 12°
            assert page.inner_text("#readout-gh-deg") == "78.0°"  # Compensatory over-elevation
            assert "Compromised" in page.inner_text("#readout-subacromial-status")

            # Verify unadjusted muscle response caution badge appears
            time.sleep(1.0)
            restr_tbody = page.inner_html("#shoulder-muscle-tbody")
            assert "BASELINE (UNADJUSTED)" in restr_tbody

            page.screenshot(path=str(SCREENSHOT_DIR / "shoulder_lab_090deg_forward_shoulder_restricted.png"))
            print("[E2E] Captured: shoulder_lab_090deg_forward_shoulder_restricted.png")

            # 11. Verify Motor Control Education Cards
            page.evaluate("loadMotorControlEducation()")
            time.sleep(0.8)
            mc_html = page.inner_html("#motor-control-container")
            assert "Sensory Feedback: Muscle Spindles" in mc_html
            assert "Why Temporary Muscle Tension Relief Does Not Equal" in mc_html
            assert "Motor Learning, Sensorimotor Integration" in mc_html
            assert "Kandel" in mc_html
            assert "Weppler" in mc_html
            assert "Hodges" in mc_html

            # Element screenshot capturing Motor Control cards specifically
            mc_locator = page.locator("#motor-control-container")
            mc_locator.scroll_into_view_if_needed()
            time.sleep(0.5)
            mc_locator.screenshot(path=str(SCREENSHOT_DIR / "shoulder_lab_motor_control_education.png"))
            print("[E2E] Captured: shoulder_lab_motor_control_education.png")

            # 12. Verify Animation Loop Toggle
            page.click("#btn-shoulder-play")
            time.sleep(0.5)
            assert "Pause" in page.inner_text("#btn-shoulder-play")
            time.sleep(0.5)
            page.click("#btn-shoulder-play")
            assert "Play" in page.inner_text("#btn-shoulder-play")

            # 13. Layer Toggles
            page.click("#toggle-layer-muscles")
            time.sleep(0.2)
            page.click("#toggle-layer-muscles")
            time.sleep(0.2)

            browser.close()

    finally:
        server.stop()

    print("[SUCCESS] All P14 Shoulder Educational Acceptance checks VERIFIED on Microsoft Edge.")


if __name__ == "__main__":
    test_p14_shoulder_educational_browser_acceptance()
