"""Basic health check tests."""
import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app("testing")
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "evently-api"


def test_404_handler(client):
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
