"""Application configuration."""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "OpsPilot"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:8848", "http://localhost:5173", "http://localhost:3000"]

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    SALT_API_KEY: str = "change-this-to-a-secure-random-key"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5438/opspilot"

    # Redis
    REDIS_URL: str = "redis://localhost:6384/0"

    # Vault
    vault_url: str = "http://localhost:8201"
    vault_token: str = "dev-root-token"
    vault_engine: str = "secret"
    vault_verify_ssl: bool = False

    # Email
    app_url: str = "http://localhost:8848"
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    email_smtp_username: str = ""
    email_smtp_password: str = ""
    email_smtp_from: str = ""
    email_smtp_use_tls: bool = True

    # SaltStack
    salt_api_url: str = "http://localhost:8000"
    salt_api_username: str = "saltapi"
    salt_api_password: str = "saltapi"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6384/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6384/2"

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
