from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application settings, loaded from environment variables / .env file.
    """

    DATABASE_URL: str
    REDIS_URL: str
    GROQ_API_KEY: str
    LLM_MODEL: str = "llama-3.3-70b-versatile"

    # --- Added in Task 2: Celery (RabbitMQ broker, Redis result backend) ---
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()