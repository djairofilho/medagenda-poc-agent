from fastapi.testclient import TestClient


def test_root_and_chat_contract(client):
    root = client.get("/")
    assert root.status_code == 200
    assert "medAgenda API" in root.json()["message"]
    response = client.post("/chat", json={"session_id": "hello", "message": "Qual o endereço?", "channel": "web"})
    assert response.status_code == 200
    assert response.json()["session_id"] == "hello"
    assert isinstance(response.json()["reply"], str)
    assert "state_debug" not in response.json() or response.json()["state_debug"] is None


def test_session_survives_app_restart_and_can_be_reset(app_factory):
    with TestClient(app_factory()) as first:
        response = first.post("/chat", json={"session_id": "persistent", "message": "Quero agendar Cardiologia"})
        assert response.status_code == 200
    with TestClient(app_factory()) as second:
        state = second.app.state.conversations.state("persistent")
        assert state["draft"]["specialty"] == "Cardiologia"
        reset = second.post("/sessions/persistent/reset")
        assert reset.status_code == 200
        assert reset.json() == {"session_id": "persistent", "message": "Session reset successfully"}
        assert second.app.state.conversations.state("persistent") == {}


def test_emergency_bypasses_the_model_router(client):
    response = client.post("/chat", json={"session_id": "emergency", "message": "Meu filho bebeu cândida"})
    assert response.status_code == 200
    assert "192" in response.json()["reply"]
    assert client.app.state.conversations.state("emergency")["intent"] == "triage"


def test_symptom_request_does_not_offer_diagnosis(client):
    response = client.post("/chat", json={"session_id": "triage", "message": "Tenho febre, qual o diagnóstico?"})
    assert response.status_code == 200
    assert "Não posso" in response.json()["reply"]
