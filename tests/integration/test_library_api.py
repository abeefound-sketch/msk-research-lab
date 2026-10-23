"""Integration tests for Document Library, Search, and Research Notes API."""

from fastapi.testclient import TestClient
from msk_research_lab.api.app import app

client = TestClient(app)


def test_library_documents_api():
    res = client.get("/api/v1/library/documents")
    assert res.status_code == 200
    assert "documents" in res.json()


def test_library_search_api():
    res = client.get("/api/v1/library/search?q=anatomy")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert "query" in data


def test_get_knowledge_point_returns_404_prepublication():
    """G5 / Contract Reconciliation: Point knowledge returns 404 until R3 publication."""
    res = client.get("/api/v1/knowledge/points/GB21")
    assert res.status_code == 404
    data = res.json()
    assert data["detail"]["code"] == "UNREVIEWED_NOT_PUBLISHED"


def test_research_note_auth():
    # 1. Missing bearer token -> 401
    res1 = client.get("/api/v1/research/notes/note-12345")
    assert res1.status_code == 401

    # 2. Invalid bearer token -> 403
    res2 = client.get("/api/v1/research/notes/note-12345", headers={"Authorization": "Bearer bad-token"})
    assert res2.status_code == 403
