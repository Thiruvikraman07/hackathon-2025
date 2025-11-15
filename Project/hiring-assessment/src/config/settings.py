"""Configuration settings for the hiring assessment system."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    openai_api_key: str
    valyu_api_key: Optional[str] = None

    # Model Configuration
    openai_model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7

    # Vector Store Configuration
    chroma_persist_directory: str = "./chroma_db"

    # Logging
    log_level: str = "INFO"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = str(Path(__file__).parent.parent.parent.parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
