from datetime import datetime, timedelta
import random

def check_availability(specialty: str, date_str: str) -> bool:
    """
    Mock checking availability. 
    Rule: Always available unless time is '00:00'.
    """
    if "00:00" in date_str:
        return False
    return True

def suggest_next_slots(specialty: str):
    """Return mock next available slots."""
    base_time = datetime.now() + timedelta(days=1)
    return [
        (base_time + timedelta(hours=9)).strftime("%d/%m %H:00"),
        (base_time + timedelta(hours=14)).strftime("%d/%m %H:00"),
        (base_time + timedelta(hours=16)).strftime("%d/%m %H:00")
    ]

def book_appointment_mock(name: str, cpf: str, specialty: str, time: str) -> dict:
    """Mock booking action."""
    return {
        "id": random.randint(1000, 9999),
        "status": "confirmed",
        "details": f"{specialty} em {time}",
        "patient": name
    }
