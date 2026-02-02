"""Patient database operations for medAgenda (Onboarding)"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .base import get_connection

def init_patients_table() -> None:
    """Initialize the patients table."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            channel TEXT NOT NULL DEFAULT 'unknown'
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_patients_phone 
        ON patients(phone)
    """)
    
    conn.commit()
    conn.close()

def get_patient_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """Get patient by phone number."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM patients WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def create_patient(name: str, phone: str, channel: str = "unknown") -> int:
    """Create a new patient (onboarding)."""
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

def update_patient(phone: str, name: Optional[str] = None) -> bool:
    """Update patient information."""
    patient = get_patient_by_phone(phone)
    if not patient:
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if name:
        cursor.execute("UPDATE patients SET name = ? WHERE phone = ?", (name, phone))
    
    conn.commit()
    conn.close()
    
    return True
