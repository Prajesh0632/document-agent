import os
from functools import lru_cache
from typing import Optional

class Settings:
    """Configuration settings for different environments"""
    
    def __init__(self):
        self.environment: str = os.getenv("ENVIRONMENT", "local")
        self.log_level: str = os.getenv("LOG_LEVEL", "DEBUG")
        self.storage_connection: str = os.getenv("STORAGE_CONNECTION_STRING", "UseDevelopmentStorage=true")
        self.database_url: str = os.getenv("DATABASE_URL", "http://localhost:8000")
        self.api_key: str = os.getenv("API_KEY", "")
        self.enable_auth: bool = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    
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
            f"log_level={self.log_level})"
        )

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
