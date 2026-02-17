import pytest
from fastapi.testclient import TestClient
from app import app
from db import init_db


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Initialize database before tests"""
    init_db()


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_home_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "Mission Log" in r.text
