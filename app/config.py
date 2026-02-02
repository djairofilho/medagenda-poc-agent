"""Configuration settings for medAgenda"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

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

# LLM Provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "fallback")  # gemini|openai|anthropic|fallback

# Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
