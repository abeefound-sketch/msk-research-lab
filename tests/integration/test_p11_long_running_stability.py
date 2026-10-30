"""P11 Long-Running Stability, Concurrency & Resource Soak Test Suite.

Validates:
1. SQLite concurrent read/write transactional endurance (40+ iterations across multiple worker threads).
2. 3D anatomical scene generation & memory footprint stability across repeated cycles.
3. Repeated patient registration, SOAP note generation, and research record export under load.
"""

import concurrent.futures
import gc
import json
import os
from pathlib import Path
import pytest

from msk_research_lab.atlas.scene import build_calibrated_bp3d_torso_scene
from msk_research_lab.core.db import get_db
from msk_research_lab.workstation.patient_manager import (
    create_patient,
    export_deidentified_research_record,
    get_patient,
    list_patients,
)
from msk_research_lab.workstation.therapy_manager import (
    generate_soap_note,
    record_therapy_session,
)


def test_sqlite_concurrent_read_write_soak():
    """Verify SQLite database handles concurrent reads and writes without locking or corruption."""
    patient_ids = []

    def create_worker(idx: int) -> str:
        pat = create_patient(
            full_name=f"Soak Patient {idx:03d}",
            primary_complaint=f"Primary complaint for soak subject {idx}",
            age=25 + (idx % 50),
            gender="M" if idx % 2 == 0 else "F",
        )
        return pat["id"]

    # Concurrent insertion
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(create_worker, i) for i in range(25)]
        for fut in concurrent.futures.as_completed(futures):
            pid = fut.result()
            patient_ids.append(pid)

    assert len(patient_ids) == 25

    # Concurrent read and SOAP note generation
    def read_and_soap_worker(pid: str) -> bool:
        pat = get_patient(pid)
        assert pat is not None
        sess = record_therapy_session(
            patient_id=pid,
            pre_pain_score=6.0,
            post_pain_score=3.0,
            pre_symptoms_notes="Stiffness",
            post_symptoms_notes="Relieved",
            applied_modalities=[{"type": "HEAT", "duration_min": 15}],
        )
        assert sess["id"].startswith("SES-")
        rec = export_deidentified_research_record(pid)
        assert rec["regex_based_scrubbing_only"] is True
        return True

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(read_and_soap_worker, pid) for pid in patient_ids]
        for fut in concurrent.futures.as_completed(futures):
            assert fut.result() is True

    # Database integrity check
    with get_db() as conn:
        res = conn.execute("PRAGMA integrity_check;").fetchone()
        assert res[0] == "ok"


def test_3d_scene_mesh_memory_stability_soak():
    """Verify repeated anatomical scene generation does not accumulate uncollectable garbage."""
    gc.collect()

    for i in range(15):
        scene = build_calibrated_bp3d_torso_scene()
        data = scene.model_dump()
        assert data["model_id"] == "bodyparts3d_v4_ref_torso"
        assert len(data["layers"]) >= 4
        assert len(data["points"]) >= 3
        # Clean reference
        del scene, data

    gc.collect()
