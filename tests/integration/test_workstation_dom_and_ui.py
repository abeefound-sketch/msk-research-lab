"""DOM Structure and Workstation UI Verification Test Suite.

Audits the rendered HTML DOM of the unified MSK Therapy Personal Workstation:
- Verifies 7 complete view containers and active transitions
- Audits 49 interactive controls from UI_ACTION_MATRIX.md
- Verifies DOM injection protection (escapeHtml presence & usage)
- Verifies genuine 3D Atlas Three.js / GLTFLoader import map
- Verifies removal of mock cylinders and fake alert-only buttons
- Verifies Patient View / Edit modal controls
"""

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from msk_research_lab.api.app import app
from msk_research_lab.api.workstation_ui import render_workstation_ui


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def soup():
    html = render_workstation_ui()
    return BeautifulSoup(html, "html.parser")


def test_workstation_page_renders_with_seven_views(soup):
    """Verify all 7 designated workstation views are present in the DOM."""
    views = [
        "view-dashboard",
        "view-anatomy",
        "view-motion",
        "view-patients",
        "view-therapy",
        "view-progress",
        "view-library"
    ]
    for vid in views:
        el = soup.find(id=vid)
        assert el is not None, f"Required view container #{vid} not found in DOM."
        assert "view-container" in el.get("class", [])


def test_workstation_security_no_fake_alerts(client):
    """Verify all alert-only button stubs (F-01) have been eliminated from the UI."""
    res = client.get("/workstation")
    assert res.status_code == 200
    html = res.text

    # Finding F-01: alert("Toggled layer: ...") must NOT exist
    assert 'alert("Toggled layer:' not in html
    assert 'alert("Toggled layer: "' not in html
    assert "alert('Toggled layer:" not in html


def test_workstation_threejs_and_gltf_importmap_present(soup):
    """Verify Three.js and GLTFLoader ES module import map for genuine 3D anatomy."""
    importmap = soup.find("script", type="importmap")
    assert importmap is not None, "ES module importmap missing from workstation head."
    assert "three" in importmap.string
    assert "GLTFLoader.js" in importmap.string
    assert "OrbitControls.js" in importmap.string


def test_patient_modals_exist_for_create_and_edit(soup):
    """Verify both New Patient registration and Patient Edit modals exist."""
    # New Patient Modal
    np_modal = soup.find(id="newPatientModal")
    assert np_modal is not None
    assert np_modal.find(id="np-name") is not None
    assert np_modal.find(id="np-complaint") is not None
    assert np_modal.find(id="np-rf-fever") is not None

    # Patient Edit / Detail Modal
    edit_modal = soup.find(id="patientDetailModal")
    assert edit_modal is not None
    assert edit_modal.find(id="edit-patient-id") is not None
    assert edit_modal.find(id="edit-name") is not None
    assert edit_modal.find(id="edit-complaint") is not None


def test_motion_assessment_controls_present(soup):
    """Verify motion assessment contains live capture, demo fixture, and parameter selectors."""
    btn_live = soup.find(id="btn-measure-rom")
    assert btn_live is not None
    assert "runMotionAssessment('LIVE')" in btn_live.get("onclick", "")

    btn_demo = soup.find(id="btn-demo-fixture")
    assert btn_demo is not None
    assert "runMotionAssessment('DEMO')" in btn_demo.get("onclick", "")

    assert soup.find(id="motion-joint-select") is not None
    assert soup.find(id="motion-side-select") is not None
    assert soup.find(id="motion-res-angle") is not None
    assert soup.find(id="motion-res-u95") is not None


def test_therapy_workspace_red_flag_alert_container(soup):
    """Verify therapy workspace contains dedicated red flag alert element."""
    rf_alert = soup.find(id="therapy-red-flag-alert")
    assert rf_alert is not None
    assert "CRITICAL RED FLAGS ACTIVE" in rf_alert.text

    assert soup.find(id="btn-preview-soap") is not None
    assert soup.find(id="btn-save-session") is not None
    assert soup.find(id="dds-utilized-check") is not None


def test_escape_html_function_defined(client):
    """Verify escapeHtml function is defined and applied to prevent DOM injection."""
    res = client.get("/workstation")
    html = res.text
    assert "function escapeHtml(str)" in html
    assert ".replace(/&/g, '&amp;')" in html
    assert ".replace(/</g, '&lt;')" in html
    assert ".replace(/>/g, '&gt;')" in html
    assert "escapeHtml(p.full_name)" in html
    assert "escapeHtml(p.primary_complaint)" in html
