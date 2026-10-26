from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from app.appointments.service import book_appointment, list_appointments
from app.availability.service import LOCAL_TZ


def _future_weekday() -> str:
    day = datetime.now(LOCAL_TZ) + timedelta(days=2)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day.strftime("%Y-%m-%d 14:00")


def _chat(client, session, message):
    response = client.post("/chat", json={"session_id": session, "message": message, "channel": "web"})
    assert response.status_code == 200, response.text
    return response.json()["reply"]


def test_booking_requires_real_slot_patient_data_and_confirmation(client):
    when = _future_weekday()
    assert client.post("/slots", json={"slots": [{"specialty": "Cardiologia", "slot_datetime": when}]}).status_code == 200
    assert "nome" in _chat(client, "booking", f"Quero agendar Cardiologia em {when}").lower()
    assert client.get("/appointments").json()["total"] == 0
    reply = _chat(client, "booking", "Nome: Ana Souza CPF: 529.982.247-25 telefone: (11) 99999-9999 teleconsulta")
    assert "Posso confirmar" in reply
    assert "529" not in reply
    assert client.get("/appointments").json()["total"] == 0
    confirmed = _chat(client, "booking", "sim")
    assert "Número do agendamento: 1" in confirmed
    assert "Número do agendamento: 1" in _chat(client, "booking", "sim")
    listed = client.get("/appointments").json()
    assert listed["total"] == 1
    assert "cpf" not in listed["appointments"][0]
    assert listed["appointments"][0]["mode"] == "teleconsulta"
    assert client.get("/slots?specialty=Cardiologia").json()["total"] == 0
    assert client.get("/appointments/1").json()["name"] == "Ana Souza"

    next_reply = _chat(client, "booking", "Quero agendar outra consulta")
    assert "especialidade" in next_reply.lower()
    next_state = client.app.state.conversations.state("booking")
    assert next_state["appointment_id"] is None
    assert next_state["draft"] == {}


def test_no_slot_or_missing_data_never_claims_booking(client):
    when = _future_weekday()
    reply = _chat(client, "no-slot", f"Quero agendar Pediatria em {when}")
    assert "não há horários" in reply.lower()
    assert client.get("/appointments").json()["total"] == 0
    client.post("/slots", json={"slots": [{"specialty": "Cardiologia", "slot_datetime": when}]})
    reply = _chat(client, "incomplete", f"Quero agendar Cardiologia em {when}")
    assert "nome" in reply.lower()
    assert "confirmada" not in reply.lower()
    assert client.get("/appointments").json()["total"] == 0


def test_switching_intent_invalidates_pending_confirmation(client):
    when = _future_weekday()
    client.post("/slots", json={"slots": [{"specialty": "Cardiologia", "slot_datetime": when}]})
    _chat(client, "switch", f"Quero agendar Cardiologia em {when}")
    assert "Posso confirmar" in _chat(
        client, "switch", "Nome: Ana Souza CPF: 529.982.247-25 telefone: (11) 99999-9999 presencial"
    )
    _chat(client, "switch", "Qual o endereço?")
    reply = _chat(client, "switch", "sim")
    assert "Posso confirmar" in reply
    assert client.get("/appointments").json()["total"] == 0


def test_atomic_reservation_and_idempotent_key(client):
    when = _future_weekday()
    client.post("/slots", json={"slots": [{"specialty": "Cardiologia", "slot_datetime": when}]})
    slot_id = client.get("/slots?specialty=Cardiologia").json()["slots"][0]["id"]
    factory = client.app.state.session_factory

    def book(key):
        return book_appointment(
            factory, slot_id=slot_id, name="Ana Souza", cpf="52998224725",
            phone="11999999999", mode="presencial", channel="web", confirmation_key=key,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(book, ("first", "second")))
    assert sorted(result.status for result in results) == ["booked", "unavailable"]
    winner = next(key for key, result in zip(("first", "second"), results) if result.status == "booked")
    assert book(winner).status == "already_booked"
    assert list_appointments(factory, 10, 0)[0] == 1
