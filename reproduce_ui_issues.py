"""Reproduction and diagnostic script for MSK Workstation UI/UX failures.

Tests Microsoft Edge across viewports:
- 1840 x 800
- 1366 x 768
- 1920 x 1080
Audits layout, 3D canvas visibility, sidebar navigation clickability, and OpenSim table placement.
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
OUT_DIR = PROJECT_ROOT / "artifacts" / "ui-recovery" / "reproduction_screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=TEST_PORT):
        super().__init__()
        self.server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))
        self.daemon = True

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def reproduce():
    server = ServerThread(app, host="127.0.0.1", port=TEST_PORT)
    server.start()
    time.sleep(2.0)

    viewports = [
        {"name": "1840x800", "width": 1840, "height": 800},
        {"name": "1366x768", "width": 1366, "height": 768},
        {"name": "1920x1080", "width": 1920, "height": 1080},
    ]

    diagnostics = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)

            for vp in viewports:
                vp_name = vp["name"]
                print(f"[*] Testing reproduction on {vp_name}...")
                context = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
                page = context.new_page()

                console_messages = []
                page_errors = []
                request_failures = []

                page.on("console", lambda msg: console_messages.append({"type": msg.type, "text": msg.text}))
                page.on("pageerror", lambda err: page_errors.append(str(err)))
                page.on("requestfailed", lambda req: request_failures.append({"url": req.url, "error": req.failure}))

                page.goto(f"{BASE_URL}/workstation", timeout=15000)
                page.wait_for_selector("#page-title", timeout=5000)

                # Capture Home Dashboard view
                page.screenshot(path=str(OUT_DIR / f"repro_{vp_name}_01_dashboard.png"))

                # Test real click on Shoulder Movement Lab nav item
                # Find the nav item
                nav_items = page.locator(".nav-item")
                count = nav_items.count()
                shoulder_nav_index = -1
                for i in range(count):
                    text = nav_items.nth(i).inner_text()
                    if "Shoulder Movement Lab" in text:
                        shoulder_nav_index = i
                        break

                nav_click_success = False
                nav_click_error = None
                if shoulder_nav_index >= 0:
                    try:
                        # Real click without force
                        nav_items.nth(shoulder_nav_index).click(timeout=3000)
                        nav_click_success = True
                    except Exception as e:
                        nav_click_error = str(e)
                
                time.sleep(2.5) # Allow Three.js & GLB assets to load

                # Capture current viewport view (above the fold)
                page.screenshot(path=str(OUT_DIR / f"repro_{vp_name}_02_shoulder_fold.png"), full_page=False)
                # Capture full page
                page.screenshot(path=str(OUT_DIR / f"repro_{vp_name}_03_shoulder_full.png"), full_page=True)

                # Inspect DOM elements and geometry
                metrics = page.evaluate("""() => {
                    const vpHeight = window.innerHeight;
                    const vpWidth = window.innerWidth;
                    
                    const shoulderView = document.getElementById('view-shoulder');
                    const canvasCont = document.getElementById('shoulder3d-viewport');
                    const canvas = canvasCont ? canvasCont.querySelector('canvas') : null;
                    const banner = shoulderView ? shoulderView.querySelector('.disclaimer-banner') : null;
                    const guidedCard = shoulderView ? shoulderView.querySelector('.stat-card') : null;
                    const table = document.getElementById('shoulder-muscle-table');
                    const tableCard = table ? table.closest('.stat-card') : null;

                    function getInfo(el) {
                        if (!el) return null;
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        return {
                            top: rect.top,
                            bottom: rect.bottom,
                            left: rect.left,
                            right: rect.right,
                            width: rect.width,
                            height: rect.height,
                            visibleInViewport: (rect.top >= 0 && rect.top < vpHeight) || (rect.bottom > 0 && rect.bottom <= vpHeight) || (rect.top <= 0 && rect.bottom >= vpHeight),
                            display: style.display,
                            visibility: style.visibility,
                            zIndex: style.zIndex,
                            position: style.position,
                            overflow: style.overflow
                        };
                    }

                    return {
                        viewport: { width: vpWidth, height: vpHeight },
                        scroll: {
                            scrollTop: shoulderView ? shoulderView.scrollTop : 0,
                            scrollHeight: shoulderView ? shoulderView.scrollHeight : 0,
                            clientHeight: shoulderView ? shoulderView.clientHeight : 0
                        },
                        elements: {
                            viewShoulder: getInfo(shoulderView),
                            disclaimerBanner: getInfo(banner),
                            guidedCard: getInfo(guidedCard),
                            canvasContainer: getInfo(canvasCont),
                            canvasElement: getInfo(canvas),
                            tableCard: getInfo(tableCard)
                        },
                        webgl: {
                            canvasExists: !!canvas,
                            canvasWidth: canvas ? canvas.width : 0,
                            canvasHeight: canvas ? canvas.height : 0,
                            canvasClientWidth: canvas ? canvas.clientWidth : 0,
                            canvasClientHeight: canvas ? canvas.clientHeight : 0,
                            webglContextOk: !!(canvas && (canvas.getContext('webgl2') || canvas.getContext('webgl')))
                        }
                    };
                }""")

                diagnostics[vp_name] = {
                    "nav_click_success": nav_click_success,
                    "nav_click_error": nav_click_error,
                    "metrics": metrics,
                    "console_messages": console_messages,
                    "page_errors": page_errors,
                    "request_failures": request_failures,
                }
                context.close()

            browser.close()

    finally:
        server.stop()

    out_file = PROJECT_ROOT / "artifacts" / "ui-recovery" / "reproduction_diagnostics.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(diagnostics, f, indent=2)
    print(f"[+] Diagnostics written to {out_file}")


if __name__ == "__main__":
    reproduce()
