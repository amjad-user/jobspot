"""Tests for the GET /api/jobs search route (no internet needed)."""

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.main import app, get_job_source
from tests.fakes import FakeJobService, load_fake_answer


@pytest.fixture
def fake_service():
    """Make the app use a fake job service during the test, then undo it."""
    fake = FakeJobService(answer=load_fake_answer("jobsuche_search.json"))
    source = fake.make_source()
    app.dependency_overrides[get_job_source] = lambda: source
    yield fake
    app.dependency_overrides.clear()


client = TestClient(app)


def test_search_returns_jobs(fake_service):
    response = client.get("/api/jobs", params={"what": "Barista", "where": "Berlin"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 6
    assert data["place"] == "Berlin"
    assert len(data["jobs"]) == 4
    first_job = data["jobs"][0]
    assert first_job["title"] == "News Cafe Barista (m/f/d)"
    assert first_job["posted_date"] == "2026-10-05"


def test_filters_are_passed_to_job_service(fake_service):
    params = {
        "what": "Barista",
        "where": "Berlin",
        "distance": 50,
        "job_type": "full_time",
        "posted_days": 1,
        "page": 2,
    }
    client.get("/api/jobs", params=params)
    sent = fake_service.requests[0].url.params
    assert sent["umkreis"] == "50"
    assert sent["arbeitszeit"] == "vz"
    assert sent["veroeffentlichtseit"] == "1"
    assert sent["page"] == "2"


def test_spaces_around_words_are_removed(fake_service):
    client.get("/api/jobs", params={"what": "  Barista ", "where": " Berlin  "})
    sent = fake_service.requests[0].url.params
    assert sent["was"] == "Barista"
    assert sent["wo"] == "Berlin"


def test_missing_place_gives_friendly_message(fake_service):
    response = client.get("/api/jobs", params={"what": "Barista"})
    assert response.status_code == 400
    assert "where" in response.json()["message"]
    # We did not even ask the job service
    assert fake_service.requests == []


def test_bad_job_type_gives_friendly_message(fake_service):
    response = client.get("/api/jobs", params={"where": "Berlin", "job_type": "sometimes"})
    assert response.status_code == 422
    assert response.json() == {"message": "Something in your search doesn't look right. Please check it and try again."}


def test_distance_that_is_not_a_number_gives_friendly_message(fake_service):
    response = client.get("/api/jobs", params={"where": "Berlin", "distance": "far"})
    assert response.status_code == 422
    assert "message" in response.json()


def test_unknown_place_gives_friendly_message(fake_service):
    fake_service.answer = load_fake_answer("jobsuche_unknown_place.json")
    response = client.get("/api/jobs", params={"where": "Xqzv"})
    assert response.status_code == 404
    assert "couldn't find that place" in response.json()["message"]


def test_no_results_is_not_an_error(fake_service):
    fake_service.answer = load_fake_answer("jobsuche_no_results.json")
    response = client.get("/api/jobs", params={"what": "xyz", "where": "Berlin"})
    assert response.status_code == 200
    assert response.json()["jobs"] == []


def test_job_service_down_gives_friendly_message(fake_service):
    fake_service.status_code = 500
    response = client.get("/api/jobs", params={"where": "Berlin"})
    assert response.status_code == 503
    message = response.json()["message"]
    assert "try again" in message
    # No technical words on screen
    assert "500" not in message
    assert "API" not in message


def test_no_internet_gives_friendly_message(fake_service):
    fake_service.fail_with = httpx.ConnectError("no internet")
    response = client.get("/api/jobs", params={"where": "Berlin"})
    assert response.status_code == 503
    assert "internet connection" in response.json()["message"]
