from __future__ import annotations

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "School Examination CMS"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"          # ← add this
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/school_cms"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/school_cms"
    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]


settings = Settings()