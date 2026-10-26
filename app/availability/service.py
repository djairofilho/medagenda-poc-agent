"""Slot queries and mutations shared by HTTP and the conversation graph."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select

from app.infrastructure.database import dialect_insert, utc_isoformat
from app.infrastructure.models import AvailabilitySlot

LOCAL_TZ = ZoneInfo("America/Sao_Paulo")


def parse_slot_datetime(value: str) -> datetime:
    """Accept the existing API's YYYY-MM-DD HH:MM local-time format."""
    parsed = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=LOCAL_TZ)
    now = datetime.now(LOCAL_TZ)
    if not now < parsed <= now + timedelta(days=180) or parsed.weekday() >= 5 or not 8 <= parsed.hour < 20:
        raise ValueError("O horário deve ser futuro, em dia útil, entre 8h e 20h, nos próximos 180 dias")
    return parsed


def display_slot_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        # SQLite drops timezone metadata but retains the local wall time.
        value = value.replace(tzinfo=LOCAL_TZ)
    return value.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")


def serialize_slot(slot: AvailabilitySlot) -> dict:
    return {
        "id": slot.id,
        "specialty": slot.specialty,
        "slot_datetime": display_slot_datetime(slot.slot_datetime),
        "is_available": slot.is_available,
        "created_at": utc_isoformat(slot.created_at),
    }


def list_slots(session_factory, specialty: str | None = None, date: str | None = None) -> list[dict]:
    with session_factory() as session:
        query = select(AvailabilitySlot).where(AvailabilitySlot.is_available.is_(True))
        if specialty:
            query = query.where(AvailabilitySlot.specialty.ilike(specialty))
        if date:
            start = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=LOCAL_TZ)
            query = query.where(
                AvailabilitySlot.slot_datetime >= start,
                AvailabilitySlot.slot_datetime < start + timedelta(days=1),
            )
        slots = session.scalars(query.order_by(AvailabilitySlot.slot_datetime)).all()
        return [serialize_slot(slot) for slot in slots]


def create_slots(session_factory, slots: list[dict]) -> int:
    if not slots:
        return 0
    values = [
        {
            "specialty": item["specialty"].strip(),
            "slot_datetime": parse_slot_datetime(item["slot_datetime"]),
            "is_available": True,
            "created_at": datetime.now(timezone.utc),
        }
        for item in slots
    ]
    with session_factory.begin() as session:
        result = session.execute(
            dialect_insert(session, AvailabilitySlot)
            .values(values)
            .on_conflict_do_nothing()
            .returning(AvailabilitySlot.id)
        )
        return len(result.all())


def delete_slots(session_factory, ids: list[int]) -> int:
    if not ids:
        return 0
    with session_factory.begin() as session:
        result = session.execute(
            delete(AvailabilitySlot)
            .where(AvailabilitySlot.id.in_(ids), AvailabilitySlot.is_available.is_(True))
            .returning(AvailabilitySlot.id)
        )
        return len(result.all())
