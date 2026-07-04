"""
conftest.py — sets required environment variables before any app module is
imported so that pydantic-settings does not raise validation errors during
test collection.
"""

import os

# These must be set before `from app.xxx import ...` anywhere in the test suite.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GROQ_API_KEY", "dummy_key_for_tests")
os.environ.setdefault("LLM_MODEL", "llama-3.3-70b-versatile")
os.environ.setdefault("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
os.environ.setdefault("SMTP_HOST", "smtp.gmail.com")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USERNAME", "test@example.com")
os.environ.setdefault("SMTP_PASSWORD", "testpassword")
os.environ.setdefault("EMAIL_FROM", "test@example.com")
os.environ.setdefault("SMTP_USE_TLS", "true")
