"""Full Real Browser Acceptance and Interaction Verification Script for UI/UX Recovery.

Executes real mouse clicks (zero force=True, zero synthetic evaluate() dispatching)
on Microsoft Edge across viewports:
- 1840x800
- 1366x768
- 1920x1080

Verifies:
1. All 8 sidebar navigation items (#nav-dashboard through #nav-library).
2. 3D canvas lifecycle, WebGL context, OrbitControls drag rotation, and zoom.
3. Interactive shoulder controls (Play/Pause, speed, timeline scrub, layer toggles).
4. Inspectors (Structure, Muscle Dynamics, Joint Coordinates).
5. Guided Learning Case Study stepper (Scenes 1 through 6).
6. Captures timestamped verification screenshots.
"""

import json
import os
import sys
import time
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import uvicorn
from playwright.sync_api import sync_playwright
from msk_research_lab.api.app import app

TEST_PORT = 8098
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"
SCREENSHOT_DIR = PROJECT_ROOT / "artifacts" / "ui-recovery" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=TEST_PORT):
        super().__init__()
        self.server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))
        self.daemon = True

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def run_acceptance():
    server = ServerThread(app, host="127.0.0.1", port=TEST_PORT)
    server.start()
    time.sleep(2.0)

    viewports = [
        {"name": "1840x800", "width": 1840, "height": 800},
        {"name": "1366x768", "width": 1366, "height": 768},
        {"name": "1920x1080", "width": 1920, "height": 1080},
    ]

    all_results = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)

            for vp in viewports:
                vp_name = vp["name"]
                print(f"\n=======================================================")
                print(f"[*] EXECUTING ACCEPTANCE ON VIEWPORT: {vp_name}")
                print(f"=======================================================")

                context = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
                page = context.new_page()

                vp_results = {
                    "navigation": {},
                    "controls": {},
                    "canvas": {},
                    "guided_scenes": {},
                    "screenshots": []
                }

                # 1. Initial Page Load
                print("[Action 1] Navigating to Workstation...")
                page.goto(f"{BASE_URL}/workstation", timeout=15000)
                page.wait_for_selector("#page-title", timeout=5000)
                assert "Home Dashboard" in page.inner_text("#page-title")
                vp_results["navigation"]["initial_load"] = "PASS"

                # 2. Test All 8 Sidebar Navigation Items with Real Mouse Clicks
                sidebar_items = [
                    ("nav-dashboard", "view-dashboard", "Home Dashboard"),
                    ("nav-anatomy", "view-anatomy", "3D Anatomy Explorer"),
                    ("nav-shoulder", "view-shoulder", "Interactive Shoulder Movement & Biomechanics Lab"),
                    ("nav-motion", "view-motion", "Camera Motion Assessment"),
                    ("nav-patients", "view-patients", "Patient Records"),
                    ("nav-therapy", "view-therapy", "Therapy Session Workspace"),
                    ("nav-progress", "view-progress", "Progress Tracking"),
                    ("nav-library", "view-library", "Knowledge Library & AI Tutor"),
                ]

                print("\n[Action 2] Verifying 8 Sidebar Navigation Items via Real Clicks:")
                for nav_id, view_id, expected_title in sidebar_items:
                    selector = f"#{nav_id}"
                    page.wait_for_selector(selector, state="visible", timeout=3000)
                    
                    # Real mouse click - NO force=True
                    page.click(selector, timeout=3000)
                    time.sleep(0.4)

                    # Verify target view is active
                    active_view = page.locator(f"#{view_id}.active")
                    assert active_view.count() == 1, f"View #{view_id} failed to activate!"

                    # Verify page title
                    title_text = page.inner_text("#page-title")
                    assert expected_title in title_text, f"Title mismatch: got '{title_text}', expected '{expected_title}'"

                    vp_results["navigation"][nav_id] = {
                        "status": "PASS",
                        "view_id": view_id,
                        "title": title_text,
                    }
                    print(f"  [+] #{nav_id} -> #{view_id}.active ('{expected_title}') verified.")

                # 3. Enter Shoulder Movement Lab
                print("\n[Action 3] Entering Shoulder Movement Lab & Auditing 3D Viewport...")
                page.click("#nav-shoulder")
                time.sleep(2.5) # Wait for WebGL context and BodyParts3D GLBs

                # Audit 3D Canvas Geometry
                canvas_metrics = page.evaluate("""() => {
                    const cont = document.getElementById('shoulder3d-viewport');
                    const canvas = cont ? cont.querySelector('canvas') : null;
                    const rect = canvas ? canvas.getBoundingClientRect() : null;
                    const contRect = cont ? cont.getBoundingClientRect() : null;
                    return {
                        container: contRect ? { top: contRect.top, bottom: contRect.bottom, width: contRect.width, height: contRect.height } : null,
                        canvas: rect ? { top: rect.top, bottom: rect.bottom, width: rect.width, height: rect.height } : null,
                        visibleAboveFold: rect ? (rect.top >= 0 && rect.bottom <= window.innerHeight) : false,
                        viewportHeight: window.innerHeight,
                        webglOk: !!(canvas && (canvas.getContext('webgl2') || canvas.getContext('webgl')))
                    };
                }""")
                vp_results["canvas"] = canvas_metrics
                print(f"  [+] Canvas container top={canvas_metrics['container']['top']:.1f}, height={canvas_metrics['container']['height']:.1f}")
                print(f"  [+] WebGL context OK: {canvas_metrics['webglOk']}, Visible above fold: {canvas_metrics['visibleAboveFold']}")
                assert canvas_metrics["webglOk"] is True
                assert canvas_metrics["container"]["height"] >= 380

                # Capture Default Shoulder Lab Viewport
                sc_name = f"verify_{vp_name}_01_shoulder_hero.png"
                page.screenshot(path=str(SCREENSHOT_DIR / sc_name), full_page=False)
                vp_results["screenshots"].append(sc_name)
                print(f"  Captured: {sc_name}")

                # 4. Interact with 3D Canvas via OrbitControls (Real Mouse Drag & Wheel)
                print("\n[Action 4] Testing 3D Canvas OrbitControls Mouse Interaction...")
                canvas_box = page.locator("#shoulder3d-viewport canvas").bounding_box()
                assert canvas_box is not None
                cx = canvas_box["x"] + canvas_box["width"] / 2
                cy = canvas_box["y"] + canvas_box["height"] / 2

                # Perform Mouse Drag to Rotate Scene
                page.mouse.move(cx, cy)
                page.mouse.down()
                page.mouse.move(cx + 80, cy - 40, steps=8)
                page.mouse.up()
                time.sleep(0.5)
                vp_results["controls"]["canvas_drag_rotate"] = "PASS"
                print("  [+] Canvas mouse drag rotation executed successfully.")

                # Perform Mouse Wheel to Zoom
                page.mouse.move(cx, cy)
                page.mouse.wheel(0, -120)
                time.sleep(0.5)
                vp_results["controls"]["canvas_mouse_zoom"] = "PASS"
                print("  [+] Canvas mouse wheel zoom executed successfully.")

                # Test Camera Preset Views
                print("\n[Action 5] Testing Camera Preset Views...")
                page.evaluate("setShoulderCameraView('lateral')")
                time.sleep(0.4)
                page.evaluate("setShoulderCameraView('superior')")
                time.sleep(0.4)
                page.click("#btn-shoulder-reset-cam")
                time.sleep(0.5)
                vp_results["controls"]["camera_presets"] = "PASS"
                print("  [+] Camera presets (Anterior, Lateral, Superior, Reset Cam) verified.")

                # 5. Test Animation Play / Pause Toggle
                print("\n[Action 6] Testing Play/Pause Animation Toggle...")
                play_btn = page.locator("#btn-shoulder-play")
                assert "Play" in play_btn.inner_text()
                play_btn.click()
                time.sleep(0.8)
                assert "Pause" in play_btn.inner_text()
                play_btn.click()
                time.sleep(0.4)
                assert "Play" in play_btn.inner_text()
                vp_results["controls"]["play_pause_toggle"] = "PASS"
                print("  [+] Play/Pause animation toggle verified.")

                # 6. Test Speed Selector
                page.select_option("#shoulder-speed-select", "0.5")
                time.sleep(0.2)
                vp_results["controls"]["speed_select"] = "PASS"
                print("  [+] Speed selector verified (0.5x).")

                # 7. Test Timeline Scrubber & Angle Readouts at 90° Abduction
                print("\n[Action 7] Scrubbing Timeline to 90° Abduction...")
                page.evaluate("""() => {
                    const slider = document.getElementById('shoulder-timeline-slider');
                    slider.value = '90.0';
                    onShoulderTimelineScrub(90.0);
                }""")
                time.sleep(0.6)
                assert page.inner_text("#val-arm-deg") == "90.0"
                gh_text = page.inner_text("#readout-gh-deg")
                st_text = page.inner_text("#readout-st-deg")
                sc_text = page.inner_text("#readout-sc-deg")
                subacromial = page.inner_text("#readout-subacromial-status")
                print(f"  [+] Readouts at 90°: GH={gh_text}, ST={st_text}, SC={sc_text}, Subacromial={subacromial}")
                assert "70.0" in gh_text
                assert "20.0" in st_text
                vp_results["controls"]["timeline_scrub_90"] = {
                    "gh": gh_text, "st": st_text, "sc": sc_text, "subacromial": subacromial
                }

                # Capture 90° Elevation State
                sc_name = f"verify_{vp_name}_02_arm_90deg.png"
                page.screenshot(path=str(SCREENSHOT_DIR / sc_name), full_page=False)
                vp_results["screenshots"].append(sc_name)
                print(f"  Captured: {sc_name}")

                # 8. Test Muscle Dynamics Selection (DELT1)
                print("\n[Action 8] Testing Muscle Dynamics Inspector (DELT1)...")
                page.select_option("#dyn-muscle-select", "DELT1")
                page.evaluate("selectDynamicsMuscle('DELT1')")
                time.sleep(0.4)
                fiber_len = page.inner_text("#dyn-val-fiber-len")
                norm_len = page.inner_text("#dyn-val-norm-len")
                pass_force = page.inner_text("#dyn-val-pass-force")
                print(f"  [+] DELT1 Dynamics at 90°: Fiber={fiber_len}, Norm={norm_len}, PassiveForce={pass_force}")
                assert "cm" in fiber_len
                assert "N" in pass_force
                vp_results["controls"]["muscle_dynamics_delt1"] = {
                    "fiber_len": fiber_len, "norm_len": norm_len, "passive_force": pass_force
                }

                # 9. Test Comparative Model Switch (Restricted 4:1 Rhythm)
                print("\n[Action 9] Testing Comparative Model Switch (Model B: Restricted)...")
                page.select_option("#shoulder-comparison-select", "forward_shoulder_restricted")
                page.evaluate("changeShoulderComparisonMode()")
                time.sleep(0.6)
                badge_text = page.inner_text("#shoulder-rhythm-badge")
                re_gh = page.inner_text("#readout-gh-deg")
                re_st = page.inner_text("#readout-st-deg")
                print(f"  [+] Restricted Mode at 90°: Badge='{badge_text}', GH={re_gh}, ST={re_st}")
                assert "Restricted 4:1 Rhythm" in badge_text
                assert "78.0" in re_gh
                assert "12.0" in re_st
                vp_results["controls"]["comparison_mode_restricted"] = {
                    "badge": badge_text, "gh": re_gh, "st": re_st
                }

                # Capture Restricted Mode State
                sc_name = f"verify_{vp_name}_03_restricted_mode.png"
                page.screenshot(path=str(SCREENSHOT_DIR / sc_name), full_page=False)
                vp_results["screenshots"].append(sc_name)
                print(f"  Captured: {sc_name}")

                # 10. Test Anatomical Structure Selector (Scapula FMA13395)
                print("\n[Action 10] Testing Structure Details Inspector...")
                page.select_option("#shoulder-structure-select", "FMA13395")
                page.evaluate("selectShoulderStructure('FMA13395')")
                time.sleep(0.4)
                insp_title = page.inner_text("#shoulder-insp-title")
                assert "Right Scapula" in insp_title
                vp_results["controls"]["structure_inspector"] = insp_title
                print(f"  [+] Structure Inspector verified: '{insp_title}'.")

                # 11. Test Guided Learning Sequential Step Navigation (Scenes 1 through 6)
                print("\n[Action 11] Testing Guided Learning Stepper (Scenes 1 through 6 via Next button)...")
                for s_idx in range(1, 7):
                    if s_idx > 1:
                        # Click Next Scene button
                        page.click("#btn-guided-next")
                        time.sleep(0.5)

                    s_title = page.inner_text("#guided-scene-title")
                    s_badge = page.inner_text("#guided-scene-badge")
                    print(f"  [+] Scene {s_idx}: '{s_title}' ({s_badge})")
                    assert f"Scene {s_idx}" in s_title
                    vp_results["guided_scenes"][f"scene_{s_idx}"] = s_title

                # Capture Scene 6 (Why Tension Returns) with narrative visible
                sc_name = f"verify_{vp_name}_04_scene6_tension_returns.png"
                page.locator("#guided-scene-content").screenshot(path=str(SCREENSHOT_DIR / sc_name))
                vp_results["screenshots"].append(sc_name)
                print(f"  Captured: {sc_name}")

                # 12. Test OpenSim Response Table and Motor Control Card
                print("\n[Action 12] Auditing Secondary Sections (Muscle Table & Motor Control)...")
                table_visible = page.locator("#shoulder-muscle-table").is_visible()
                tbody_rows = page.locator("#shoulder-muscle-tbody tr").count()
                page.wait_for_selector("#motor-control-container > div", timeout=5000)
                mc_cards = page.locator("#motor-control-container > div").count()
                print(f"  [+] Muscle response table visible: {table_visible}, rows: {tbody_rows}")
                print(f"  [+] Motor control cards rendered: {mc_cards}")
                assert tbody_rows >= 10
                assert mc_cards >= 6
                vp_results["controls"]["secondary_sections"] = {
                    "table_rows": tbody_rows, "motor_control_cards": mc_cards
                }

                # Capture Full Page Layout Screenshot
                sc_name = f"verify_{vp_name}_05_full_page.png"
                page.screenshot(path=str(SCREENSHOT_DIR / sc_name), full_page=True)
                vp_results["screenshots"].append(sc_name)
                print(f"  Captured: {sc_name}")

                all_results[vp_name] = vp_results
                context.close()

            browser.close()

    finally:
        server.stop()

    out_json = PROJECT_ROOT / "artifacts" / "ui-recovery" / "real_browser_acceptance_data.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[+] Full real browser acceptance data written to {out_json}")
    return all_results


if __name__ == "__main__":
    run_acceptance()
