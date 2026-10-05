"""Tests for the saved jobs routes: list, save, change status, remove, stats."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app, get_store
from backend.storage import SavedJobsStore

client = TestClient(app)


@pytest.fixture(autouse=True)
def temporary_store(tmp_path):
    """Every test gets its own empty database, never the real one."""
    store = SavedJobsStore(tmp_path / "test.db")
    app.dependency_overrides[get_store] = lambda: store
    yield store
    app.dependency_overrides.clear()


def job_data(job_id="jobsuche:10001-1003416537-S", title="Barista"):
    """A job as the web page sends it (the same shape /api/jobs gives)."""
    return {
        "id": job_id,
        "source": "jobsuche",
        "title": title,
        "company": "Café Mühle & Söhne",
        "location": "Berlin",
        "distance_km": 9,
        "job_type": "full_or_part_time",
        "posted_date": "2026-07-21",
        "url": "https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003416537-S",
    }


def test_list_is_empty_at_first():
    response = client.get("/api/saved")
    assert response.status_code == 200
    assert response.json() == []


def test_save_a_job_and_see_it_in_the_list():
    response = client.post("/api/saved", json=job_data())
    assert response.status_code == 201
    assert response.json()["status"] == "saved"

    saved = client.get("/api/saved").json()
    assert len(saved) == 1
    assert saved[0]["title"] == "Barista"
    assert saved[0]["company"] == "Café Mühle & Söhne"


def test_saving_the_same_job_twice_keeps_one():
    client.post("/api/saved", json=job_data())
    client.post("/api/saved", json=job_data())
    assert len(client.get("/api/saved").json()) == 1


def test_save_rejects_unsafe_link():
    bad_job = job_data()
    bad_job["url"] = "javascript:alert(1)"
    response = client.post("/api/saved", json=bad_job)
    assert response.status_code == 422
    assert "message" in response.json()
    assert client.get("/api/saved").json() == []


def test_save_rejects_missing_fields():
    response = client.post("/api/saved", json={"title": "Only a title"})
    assert response.status_code == 422
    assert "message" in response.json()


def test_change_status():
    client.post("/api/saved", json=job_data())
    response = client.put(
        "/api/saved/jobsuche:10001-1003416537-S/status", json={"status": "applied"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "applied"
    assert client.get("/api/saved").json()[0]["status"] == "applied"


def test_change_to_unknown_status_is_refused():
    client.post("/api/saved", json=job_data())
    response = client.put(
        "/api/saved/jobsuche:10001-1003416537-S/status", json={"status": "hired!!"}
    )
    assert response.status_code == 422


def test_change_status_of_job_that_is_not_saved():
    response = client.put("/api/saved/jobsuche:nope/status", json={"status": "applied"})
    assert response.status_code == 404
    assert "saved jobs" in response.json()["message"]


def test_remove_job():
    client.post("/api/saved", json=job_data())
    response = client.delete("/api/saved/jobsuche:10001-1003416537-S")
    assert response.status_code == 204
    assert client.get("/api/saved").json() == []


def test_remove_job_that_is_not_saved():
    response = client.delete("/api/saved/jobsuche:nope")
    assert response.status_code == 404
    assert "message" in response.json()


def test_stats():
    client.post("/api/saved", json=job_data("jobsuche:1"))
    client.post("/api/saved", json=job_data("jobsuche:2"))
    client.post("/api/saved", json=job_data("jobsuche:3"))
    client.put("/api/saved/jobsuche:2/status", json={"status": "applied"})
    client.put("/api/saved/jobsuche:3/status", json={"status": "interview"})

    response = client.get("/api/stats")
    assert response.status_code == 200
    assert response.json() == {"saved": 3, "applied": 2, "replies": 1, "interviews": 1}
