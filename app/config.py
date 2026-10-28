"""Configuration shared by the API, migrations and evaluation runner."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://medagenda:medagenda@localhost:5432/medagenda"
)
CHECKPOINT_DATABASE_URL = os.getenv("CHECKPOINT_DATABASE_URL") or None
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
API_TITLE = "medAgenda API"
API_VERSION = "3.1"
API_DESCRIPTION = "Appointment scheduling agent - POC"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
CODEX_MODEL = os.getenv("CODEX_MODEL") or None
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1")
