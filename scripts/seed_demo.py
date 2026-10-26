"""Insert administrative defaults and a few future synthetic slots."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.dialects.postgresql import insert

from app import config
from app.availability.service import LOCAL_TZ
from app.infrastructure.database import make_session_factory
from app.infrastructure.models import AvailabilitySlot, ClinicInfo


def seed(session_factory):
    details = {
        "name": "Clínica MedAgenda",
        "address": "Av. Paulista, 1000 - São Paulo/SP",
        "phone": "(11) 3000-0000",
        "hours": "Segunda a sexta, das 8h às 20h",
    }
    today = datetime.now(LOCAL_TZ)
    days = [today + timedelta(days=offset) for offset in range(1, 8)]
    slots = [day.replace(hour=hour, minute=0, second=0, microsecond=0)
             for day in days if day.weekday() < 5 for hour in (9, 14)]
    with session_factory.begin() as session:
        for key, value in details.items():
            session.execute(
                insert(ClinicInfo).values(key=key, value=value, updated_at=datetime.now(timezone.utc))
                .on_conflict_do_nothing(index_elements=[ClinicInfo.key])
            )
        for value in slots:
            session.execute(
                insert(AvailabilitySlot)
                .values(specialty="Cardiologia", slot_datetime=value,
                        is_available=True, created_at=datetime.now(timezone.utc))
                .on_conflict_do_nothing(constraint="uq_availability_slot")
            )


if __name__ == "__main__":
    engine, factory = make_session_factory(config.DATABASE_URL)
    try:
        seed(factory)
    finally:
        engine.dispose()
