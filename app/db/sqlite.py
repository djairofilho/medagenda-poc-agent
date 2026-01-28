"""SQLite database operations for medAgenda"""
import sqlite3
from datetime import datetime
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
    
    created_at = datetime.utcnow().isoformat()
    
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
