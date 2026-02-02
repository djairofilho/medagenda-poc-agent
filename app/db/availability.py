"""Availability slot management database operations for medAgenda"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .base import get_connection

def init_availability_table() -> None:
    """Initialize the availability table."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            specialty TEXT NOT NULL,
            slot_datetime TEXT NOT NULL,
            is_available INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_availability_specialty 
        ON availability(specialty)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_availability_datetime 
        ON availability(slot_datetime)
    """)
    
    conn.commit()
    conn.close()

def insert_slots_bulk(slots_data: List[Dict[str, str]]) -> int:
    """
    Insert multiple available slots.
    
    Args:
        slots_data: List of dicts with 'specialty' and 'slot_datetime'
        
    Returns:
        Number of slots inserted
    """
    if not slots_data:
        return 0
        
    conn = get_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now(timezone.utc).isoformat()
    
    data = [
        (s['specialty'], s['slot_datetime'], 1, created_at)
        for s in slots_data
    ]
    
    cursor.executemany("""
        INSERT INTO availability (specialty, slot_datetime, is_available, created_at)
        VALUES (?, ?, ?, ?)
    """, data)
    
    count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return count

def delete_slots_bulk(slot_ids: List[int]) -> int:
    """
    Delete multiple availability slots.
    
    Returns:
        Number of slots deleted
    """
    if not slot_ids:
        return 0
        
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholders = ",".join(["?"] * len(slot_ids))
    query = f"DELETE FROM availability WHERE id IN ({placeholders})"
    
    cursor.execute(query, slot_ids)
    affected = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return affected

def list_available_slots(
    specialty: Optional[str] = None, 
    date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List available slots with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM availability WHERE is_available = 1"
    params = []
    
    if specialty:
        query += " AND specialty = ?"
        params.append(specialty)
    
    if date:
        query += " AND slot_datetime LIKE ?"
        params.append(f"{date}%")
        
    query += " ORDER BY slot_datetime ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
