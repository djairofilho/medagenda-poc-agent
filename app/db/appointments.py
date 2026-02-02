"""Appointment database operations for medAgenda"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .base import get_connection

def init_appointments_table() -> None:
    """Initialize the appointments table."""
    conn = get_connection()
    cursor = conn.cursor()
    
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
    """Insert a new appointment into the database."""
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
    """Get a single appointment by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def list_appointments(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """List appointments with pagination."""
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

def cancel_appointments_bulk(appointment_ids: List[int]) -> int:
    """
    Cancel multiple appointments by ID.
    
    Returns:
        Number of appointments cancelled
    """
    if not appointment_ids:
        return 0
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Using parameterized query with dynamic number of placeholders
    placeholders = ",".join(["?"] * len(appointment_ids))
    query = f"UPDATE appointments SET status = 'cancelled' WHERE id IN ({placeholders})"
    
    cursor.execute(query, appointment_ids)
    affected = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return affected
