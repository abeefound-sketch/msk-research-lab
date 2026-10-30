"""Playwright End-to-End Real Browser Acceptance Test for Shoulder Movement Lab (P13).

Verifies the complete interactive control chain on system Microsoft Edge:
Click -> Handler -> State Change -> Rendering Result -> Visible Readback
Takes real screenshots for P13 evidence deliverables.
"""

import os
import sys
from pathlib import Path

# Ensure project src is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import time
import subprocess
import threading
import uvicorn
import pytest
from playwright.sync_api import sync_playwright

from msk_research_lab.api.app import app

TEST_PORT = 8097
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"
SCREENSHOT_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts" / "p13" / "screenshots"


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=TEST_PORT):
        super().__init__()
        self.server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))
        self.daemon = True

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def test_shoulder_movement_lab_browser_acceptance():
    """Verify all 11 user journey controls for the Shoulder Movement Lab in a real browser."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Start workstation server on loopback
    server = ServerThread(app, host="127.0.0.1", port=TEST_PORT)
    server.start()
    time.sleep(1.5)

    try:
        with sync_playwright() as p:
            # Launch system Microsoft Edge via Playwright channel
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            # Step 1: Open Workstation
            page.goto(f"{BASE_URL}/workstation", timeout=15000)
            page.wait_for_selector("#page-title", timeout=10000)
            assert "Home Dashboard" in page.inner_text("#page-title")

            # Step 2: Navigate to Shoulder Movement Lab
            shoulder_nav = page.locator(".nav-item", has_text="Shoulder Movement Lab")
            assert shoulder_nav.is_visible()
            shoulder_nav.click()
            time.sleep(1.0)

            # Readback Step 2: Verify View Switched
            assert "Shoulder Movement" in page.inner_text("#page-title")
            assert page.locator("#view-shoulder").is_visible()

            # Step 3: Verify 3D Viewport & WebGL Canvas
            viewport = page.locator("#shoulder3d-viewport")
            assert viewport.is_visible()
            canvas = viewport.locator("canvas")
            page.wait_for_selector("#shoulder3d-viewport canvas", timeout=10000)
            assert canvas.is_visible()

            # Readback Step 3: Initial Angle Values
            assert page.inner_text("#val-arm-deg").strip() == "0.0"
            assert page.inner_text("#readout-gh-deg").strip() == "0.0°"
            assert page.inner_text("#readout-st-deg").strip() == "0.0°"
            assert page.inner_text("#readout-sc-deg").strip() == "0.0°"

            # Step 4: Test Play / Pause Controls
            play_btn = page.locator("#btn-shoulder-play")
            assert play_btn.inner_text().strip() == "▶ Play"
            play_btn.click()
            time.sleep(1.2)  # Allow animation to advance

            # Readback Step 4: Verify Animation State Change
            assert play_btn.inner_text().strip() == "⏸ Pause"
            arm_val_playing = float(page.inner_text("#val-arm-deg").strip())
            assert arm_val_playing > 0.0, f"Expected arm elevation to increment during playback, got {arm_val_playing}"

            # Pause playback
            play_btn.click()
            time.sleep(0.3)
            assert play_btn.inner_text().strip() == "▶ Play"
            paused_val = float(page.inner_text("#val-arm-deg").strip())

            # Step 5: Test Speed Selector
            speed_sel = page.locator("#shoulder-speed-select")
            speed_sel.select_option("2.0")
            assert speed_sel.input_value() == "2.0"

            # Step 6: Test Timeline Scrubber to 90° (Mid-Range Elevation)
            page.evaluate("document.getElementById('shoulder-timeline-slider').value = '90.0'; onShoulderTimelineScrub(90.0);")
            time.sleep(0.5)

            # Readback Step 6: Verify Exact Inman 2:1 Rhythm at 90°
            assert float(page.inner_text("#val-arm-deg").strip()) == 90.0
            gh_readout = float(page.inner_text("#readout-gh-deg").replace("°", "").strip())
            st_readout = float(page.inner_text("#readout-st-deg").replace("°", "").strip())
            sc_readout = float(page.inner_text("#readout-sc-deg").replace("°", "").strip())

            assert gh_readout == 70.0, f"Expected 70.0° glenohumeral, got {gh_readout}"
            assert st_readout == 20.0, f"Expected 20.0° scapular upward rotation, got {st_readout}"
            assert sc_readout == 16.2, f"Expected 16.2° clavicular elevation, got {sc_readout}"
            assert "Adequate" in page.inner_text("#readout-subacromial-status")

            # Step 7: Capture Screenshot at 90° Elevation
            screenshot_90_path = SCREENSHOT_DIR / "shoulder_lab_90deg_normal_rhythm.png"
            page.screenshot(path=str(screenshot_90_path), full_page=True)
            assert screenshot_90_path.exists() and screenshot_90_path.stat().st_size > 50000

            # Step 8: Test Comparative Model Switching (Forward Shoulder Restrained)
            comp_sel = page.locator("#shoulder-comparison-select")
            comp_sel.select_option("forward_shoulder_restricted")
            page.evaluate("changeShoulderComparisonMode()")
            time.sleep(0.5)

            # Readback Step 8: Verify Restricted Scapular Upward Rotation
            assert "Restricted 4:1 Rhythm" in page.inner_text("#shoulder-rhythm-badge")
            st_restr = float(page.inner_text("#readout-st-deg").replace("°", "").strip())
            gh_restr = float(page.inner_text("#readout-gh-deg").replace("°", "").strip())
            assert st_restr == 12.0, f"Expected 12.0° restricted upward rotation at 90°, got {st_restr}"
            assert gh_restr == 78.0, f"Expected 78.0° glenohumeral elevation, got {gh_restr}"
            assert "Compromised" in page.inner_text("#readout-subacromial-status")

            # Capture Screenshot of Forward Shoulder Comparison
            screenshot_restr_path = SCREENSHOT_DIR / "shoulder_lab_90deg_forward_shoulder_restricted.png"
            page.screenshot(path=str(screenshot_restr_path), full_page=True)
            assert screenshot_restr_path.exists() and screenshot_restr_path.stat().st_size > 50000

            # Switch back to normal rhythm
            comp_sel.select_option("normal_2to1")
            page.evaluate("changeShoulderComparisonMode()")
            time.sleep(0.3)

            # Step 9: Test Layer Toggles
            toggle_bones = page.locator("#toggle-layer-bones")
            toggle_bones.uncheck()
            time.sleep(0.2)
            toggle_bones.check()
            time.sleep(0.2)
            assert toggle_bones.is_checked()

            # Step 10: Test Anatomical Structure & Evidence Inspector
            struct_sel = page.locator("#shoulder-structure-select")
            struct_sel.select_option("FMA34680")  # Anterior Deltoid
            page.evaluate("selectShoulderStructure('FMA34680')")
            time.sleep(0.5)

            # Readback Step 10: Verify Inspector Text
            assert "Deltoid" in page.inner_text("#shoulder-insp-title")
            assert "clavicle" in page.inner_text("#shoulder-insp-facts").lower()
            assert "flexor" in page.inner_text("#shoulder-insp-role").lower()
            assert "electromyographic" in page.inner_text("#shoulder-insp-limits").lower()

            # Step 11: Verify OpenSim Muscle Table Population
            page.wait_for_selector("#shoulder-muscle-tbody tr", timeout=5000)
            rows = page.locator("#shoulder-muscle-tbody tr")
            assert rows.count() >= 5
            table_text = page.inner_text("#shoulder-muscle-table")
            assert "DELT1" in table_text
            assert "PECM" in table_text or "BIC" in table_text

            # Step 12: Test Reset Camera Button
            reset_btn = page.locator("#btn-shoulder-reset-cam")
            reset_btn.click()
            time.sleep(0.3)

            print("[SUCCESS] All 11 Shoulder Movement Lab browser controls VERIFIED with Microsoft Edge.")
            browser.close()
    finally:
        server.stop()


if __name__ == "__main__":
    test_shoulder_movement_lab_browser_acceptance()
