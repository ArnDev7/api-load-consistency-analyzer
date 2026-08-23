from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Verify /health returns 200 OK and database connectivity info."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert data["database"]["healthy"] is True
    assert "pool" in data["database"]
    assert "version" in data
