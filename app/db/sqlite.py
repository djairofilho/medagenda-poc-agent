"""SQLite database operations for medAgenda"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

from app import config

# Module-level variable that can be patched in tests
DB_PATH = config.DB_PATH


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create appointments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            specialty TEXT NOT NULL,
            preferred_datetime TEXT NOT NULL,
            mode TEXT NOT NULL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            channel TEXT NOT NULL DEFAULT 'unknown'
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_appointments_phone 
        ON appointments(phone)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_appointments_created_at 
        ON appointments(created_at)
    """)
    
    conn.commit()
    conn.close()
    
    # Initialize patients table
    init_patients_table()


def insert_appointment(
    name: str,
    phone: str,
    specialty: str,
    preferred_datetime: str,
    mode: str,
    reason: Optional[str] = None,
    status: str = "new",
    channel: str = "unknown"
) -> int:
    """
    Insert a new appointment into the database.
    
    Args:
        name: Patient's full name
        phone: Patient's phone number
        specialty: Medical specialty
        preferred_datetime: Preferred date/time as text
        mode: presencial|online|nao_informado
        reason: Optional reason for appointment
        status: new|confirmed|needs_followup
        channel: web|whatsapp|instagram|unknown
    
    Returns:
        The ID of the inserted appointment
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
        INSERT INTO appointments (
            created_at, name, phone, specialty, preferred_datetime,
            mode, reason, status, channel
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (created_at, name, phone, specialty, preferred_datetime, 
          mode, reason, status, channel))
    
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return appointment_id


def get_appointment(appointment_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single appointment by ID.
    
    Args:
        appointment_id: The appointment ID
    
    Returns:
        Dictionary with appointment data or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM appointments WHERE id = ?
    """, (appointment_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def list_appointments(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """
    List appointments with pagination.
    
    Args:
        limit: Maximum number of appointments to return
        offset: Number of appointments to skip
    
    Returns:
        List of appointment dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM appointments 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def count_appointments() -> int:
    """Get total count of appointments."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM appointments")
    result = cursor.fetchone()
    conn.close()
    
    return result["count"] if result else 0


# ============================================================================
# PATIENT MANAGEMENT (Onboarding)
# ============================================================================

def init_patients_table() -> None:
    """Initialize the patients table for onboarding."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create patients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            channel TEXT NOT NULL DEFAULT 'unknown'
        )
    """)
    
    # Create index on phone for fast lookup
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_patients_phone 
        ON patients(phone)
    """)
    
    conn.commit()
    conn.close()


def get_patient_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """
    Get patient by phone number.
    
    Args:
        phone: Patient's phone number
    
    Returns:
        Patient dictionary or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM patients WHERE phone = ?
    """, (phone,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def create_patient(
    name: str,
    phone: str,
    channel: str = "unknown"
) -> int:
    """
    Create a new patient (onboarding).
    
    Args:
        name: Patient's full name
        phone: Patient's phone number
        channel: Communication channel
    
    Returns:
        The ID of the created patient
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
        INSERT INTO patients (created_at, name, phone, channel)
        VALUES (?, ?, ?, ?)
    """, (created_at, name, phone, channel))
    
    patient_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return patient_id


def update_patient(
    phone: str,
    name: Optional[str] = None
) -> bool:
    """
    Update patient information.
    
    Args:
        phone: Patient's phone number
        name: New name (if provided)
    
    Returns:
        True if updated, False if patient not found
    """
    patient = get_patient_by_phone(phone)
    if not patient:
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if name:
        cursor.execute("""
            UPDATE patients SET name = ? WHERE phone = ?
        """, (name, phone))
    
    conn.commit()
    conn.close()
    
    return True
