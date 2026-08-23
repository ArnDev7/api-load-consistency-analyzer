from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    ENABLE_TEST_ENDPOINTS: bool = True
    DEFAULT_CONCURRENCY_STRATEGY: Literal["atomic_update", "pessimistic_lock", "naive"] = "atomic_update"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://app:app@localhost:5432/loadlab"
    TEST_DATABASE_URL: str = "postgresql+psycopg://app:app@localhost:5432/loadlab_test"

    # Connection Pool
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: float = 30.0
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    # Observability
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
