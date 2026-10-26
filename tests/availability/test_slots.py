from datetime import datetime, timedelta

from app.availability.service import LOCAL_TZ


def test_create_list_filter_and_delete_slots(client):
    day = datetime.now(LOCAL_TZ) + timedelta(days=2)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    future = day.strftime("%Y-%m-%d 10:00")
    payload = {"slots": [{"specialty": "Pediatria", "slot_datetime": future}]}
    created = client.post("/slots", json=payload)
    assert created.status_code == 200
    assert created.json()["affected_count"] == 1
    assert client.post("/slots", json=payload).json()["affected_count"] == 0
    listed = client.get(f"/slots?specialty=Pediatria&date={future[:10]}")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    slot = listed.json()["slots"][0]
    assert slot["slot_datetime"] == future
    assert slot["created_at"].endswith("+00:00")
    deleted = client.request("DELETE", "/slots", json={"ids": [slot["id"]]})
    assert deleted.json()["affected_count"] == 1
    assert client.get("/slots?specialty=Pediatria").json()["total"] == 0


def test_rejects_past_slot(client):
    response = client.post("/slots", json={"slots": [{"specialty": "Pediatria", "slot_datetime": "2020-01-01 10:00"}]})
    assert response.status_code == 422
