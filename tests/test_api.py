import pytest
from fastapi.testclient import TestClient

def test_root_endpoint(client: TestClient):
    """Test the root endpoint returns expected metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "medAgenda API" in data["message"]
    assert "version" in data
    assert "endpoints" in data

def test_chat_endpoint_basic(client: TestClient):
    """Test the chat endpoint with a simple message."""
    payload = {
        "session_id": "test_session_123",
        "message": "Olá",
        "channel": "web"
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session_123"
    assert "reply" in data
    assert isinstance(data["reply"], str)

def test_chat_endpoint_debug(client: TestClient):
    """Test the chat endpoint with debug info enabled (if configured)."""
    from app.config import DEBUG
    payload = {
        "session_id": "test_session_debug",
        "message": "Quero agendar um médico",
        "channel": "web"
    }
    # Using query parameter debug=1
    response = client.post("/chat?debug=1", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    if DEBUG:
        assert "state_debug" in data
        assert "extracted" in data["state_debug"]
    else:
        assert data.get("state_debug") is None

def test_get_appointments(client: TestClient):
    """Test listing appointments."""
    response = client.get("/appointments")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "appointments" in data
    assert isinstance(data["appointments"], list)

def test_get_appointment_detail_not_found(client: TestClient):
    """Test getting a non-existent appointment detail."""
    # Use a likely non-existent ID
    response = client.get("/appointments/99999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_reset_session(client: TestClient):
    """Test resetting a user session."""
    session_id = "temp_session_to_reset"
    response = client.post(f"/sessions/{session_id}/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "reset successfully" in data["message"].lower()

def test_pagination_appointments(client: TestClient):
    """Test pagination for appointments list."""
    response = client.get("/appointments?limit=1&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["appointments"]) <= 1
