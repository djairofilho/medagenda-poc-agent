"""Configuration settings for medAgenda"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "medagenda.db"))

# Session settings
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

# Debug mode
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# API settings
API_TITLE = "medAgenda API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Appointment scheduling agent - POC"
