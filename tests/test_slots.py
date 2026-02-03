import pytest
from fastapi.testclient import TestClient

def test_create_slots(client: TestClient):
    """Test bulk creating slots."""
    payload = {
        "slots": [
            {"specialty": "Test Specialty", "slot_datetime": "2026-05-01 10:00"},
            {"specialty": "Test Specialty", "slot_datetime": "2026-05-01 11:00"}
        ]
    }
    response = client.post("/slots", json=payload)
    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert data["affected_count"] == 2
    assert "created successfully" in data["message"]

def test_list_slots(client: TestClient):
    """Test listing created slots."""
    spec = "ListTest_Unique"
    # Ensure they exist
    client.post("/slots", json={"slots": [{"specialty": spec, "slot_datetime": "2026-06-01 10:00"}]})
    
    response = client.get(f"/slots?specialty={spec}")
    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert data["total"] >= 1
    assert data["slots"][0]["specialty"] == spec

def test_delete_slots(client: TestClient):
    """Test bulk deleting slots."""
    spec = "DelTest_Unique"
    # Create one to delete
    create_resp = client.post("/slots", json={"slots": [{"specialty": spec, "slot_datetime": "2026-07-01 10:00"}]})
    assert create_resp.status_code == 200, f"Setup Error: {create_resp.text}"
    
    # List to get ID
    list_resp = client.get(f"/slots?specialty={spec}")
    assert list_resp.status_code == 200, f"List Error: {list_resp.text}"
    slots = list_resp.json()["slots"]
    assert len(slots) > 0, "No slots found for deletion test"
    slot_id = slots[0]["id"]
    
    # Delete
    payload = {"ids": [slot_id]}
    response = client.request("DELETE", "/slots", json=payload)
    assert response.status_code == 200, f"Delete Error: {response.text}"
    data = response.json()
    assert data["affected_count"] == 1, f"Expected 1 deletion, got {data['affected_count']}"
