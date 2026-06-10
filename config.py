"""
config.py
---------
Centralised, environment-aware settings for the Document Agent.
All values are read from environment variables (or .env.local in local dev).
"""

import os
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env.local")


class Settings:
    """Configuration settings for different environments."""

    def __init__(self):
        self.environment:            str  = os.getenv("ENVIRONMENT",              "local")
        self.log_level:              str  = os.getenv("LOG_LEVEL",                "DEBUG")
        self.storage_connection:     str  = os.getenv("STORAGE_CONNECTION_STRING", "UseDevelopmentStorage=true")
        self.database_url:           str  = os.getenv("DATABASE_URL",             "http://localhost:8000")
        self.api_key:                str  = os.getenv("API_KEY",                  "")
        self.enable_auth:            bool = os.getenv("ENABLE_AUTH",              "false").lower() == "true"

        # Gemini Flash (free tier) — required for field extraction
        self.gemini_api_key:         str  = os.getenv("GEMINI_API_KEY",           "")

        # Poppler binary path (Windows only; leave blank if Poppler is on PATH)
        self.poppler_path:           str  = os.getenv("POPPLER_PATH",             "")

        # Tesseract executable path (Windows only; leave blank if on PATH)
        self.tesseract_cmd:          str  = os.getenv("TESSERACT_CMD",            "")

    @property
    def is_local(self) -> bool:
        return self.environment == "local"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def __repr__(self) -> str:
        return (
            f"Settings(environment={self.environment}, "
            f"is_local={self.is_local}, "
            f"log_level={self.log_level}, "
            f"gemini_key_set={bool(self.gemini_api_key)})"
        )


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance (singleton per process)."""
    return Settings()
