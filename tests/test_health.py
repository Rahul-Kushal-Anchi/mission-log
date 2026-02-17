from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_home_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "Mission Log" in r.text
