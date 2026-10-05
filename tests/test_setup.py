"""Checks that the basic project setup works."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_route_says_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "JobSpot" in response.text
