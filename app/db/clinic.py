"""Clinic information database operations for medAgenda"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict
from .base import get_connection

def init_clinic_info_table() -> None:
    """Initialize the clinic_info table."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clinic_info (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    
    _insert_default_clinic_info()

def _insert_default_clinic_info() -> None:
    """Insert default clinic information if not exists."""
    default_info = {
        'name': 'Clínica MedAgenda',
        'address': 'Av. Paulista, 1000 - São Paulo/SP',
        'phone': '(11) 3000-0000',
        'whatsapp': '(11) 99000-0000',
        'hours': 'Segunda a Sexta: 8h às 20h',
        'services': 'Consultas médicas em diversas especialidades:\n- Dermatologia\n- Cardiologia\n- Clínico Geral\n- Pediatria\n- Ginecologia\n- Ortopedia',
        'insurance': 'Aceitamos os principais convênios médicos',
        'parking': 'Estacionamento gratuito no local',
        'accessibility': 'Clínica totalmente acessível para cadeirantes'
    }
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for key, value in default_info.items():
        cursor.execute("SELECT key FROM clinic_info WHERE key = ?", (key,))
        if not cursor.fetchone():
            created_at = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                INSERT INTO clinic_info (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, created_at))
    
    conn.commit()
    conn.close()

def get_clinic_info(key: str) -> Optional[str]:
    """Get clinic information by key."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM clinic_info WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row['value']
    return None

def get_all_clinic_info() -> Dict[str, str]:
    """Get all clinic information."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT key, value FROM clinic_info")
    rows = cursor.fetchall()
    conn.close()
    
    return {row['key']: row['value'] for row in rows}

def update_clinic_info(key: str, value: str) -> bool:
    """Update clinic information."""
    conn = get_connection()
    cursor = conn.cursor()
    
    updated_at = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
        UPDATE clinic_info 
        SET value = ?, updated_at = ?
        WHERE key = ?
    """, (value, updated_at, key))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return affected > 0

def set_clinic_info(key: str, value: str) -> None:
    """Set clinic information (insert or update)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    updated_at = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
        INSERT INTO clinic_info (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
    """, (key, value, updated_at))
    
    conn.commit()
    conn.close()
