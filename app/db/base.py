"""Shared database connection logic for medAgenda"""
import sqlite3
from app import config

DB_PATH = config.DB_PATH

def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
