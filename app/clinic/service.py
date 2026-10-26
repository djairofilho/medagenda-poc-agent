"""Clinic information supplied to the information node."""

import json
from pathlib import Path

from sqlalchemy import select

from app.availability.service import list_slots
from app.infrastructure.models import ClinicInfo

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def clinic_context(session_factory) -> str:
    with session_factory() as session:
        values = {item.key: item.value for item in session.scalars(select(ClinicInfo)).all()}
    with (DATA_DIR / "insurance.json").open(encoding="utf-8") as file:
        insurance = json.load(file)
    with (DATA_DIR / "exam_prep.json").open(encoding="utf-8") as file:
        exam_prep = json.load(file)
    slots = list_slots(session_factory)[:10]
    return "\n".join(
        [f"{key}: {value}" for key, value in values.items()]
        + [f"Convênios: {', '.join(insurance.get('accepted_plans', []))}"]
        + [f"Preparo {key}: {value}" for key, value in exam_prep.items()]
        + [f"Horário disponível: {s['specialty']} {s['slot_datetime']}" for s in slots]
    )
