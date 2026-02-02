"""SQLite database operations facade for medAgenda"""

from .base import get_connection, DB_PATH
from .appointments import (
    init_appointments_table,
    insert_appointment,
    get_appointment,
    list_appointments,
    count_appointments,
    cancel_appointments_bulk
)
from .patients import (
    init_patients_table,
    get_patient_by_phone,
    create_patient,
    update_patient
)
from .clinic import (
    init_clinic_info_table,
    get_clinic_info,
    get_all_clinic_info,
    update_clinic_info,
    set_clinic_info
)
from .availability import (
    init_availability_table,
    insert_slots_bulk,
    delete_slots_bulk,
    list_available_slots
)

def init_db() -> None:
    """Initialize all database tables."""
    init_appointments_table()
    init_patients_table()
    init_clinic_info_table()
    init_availability_table()
