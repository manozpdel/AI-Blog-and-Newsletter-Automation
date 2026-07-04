"""
Unit tests for Pydantic schemas.
No database, no HTTP, no external services required.
"""

import pytest
from pydantic import ValidationError

from app.schemas.schemas import TopicCreate
from app.schemas.subscriber import SubscriberCreate

# ── TopicCreate ────────────────────────────────────────────────


def test_topic_create_valid() -> None:
    topic = TopicCreate(name="Remote Work Benefits", tone="professional")
    assert topic.name == "Remote Work Benefits"
    assert topic.tone == "professional"


def test_topic_create_default_tone() -> None:
    topic = TopicCreate(name="AI Trends")
    assert topic.tone == "neutral"


def test_topic_create_missing_name() -> None:
    with pytest.raises(ValidationError):
        TopicCreate()  # type: ignore[call-arg]


# ── SubscriberCreate ───────────────────────────────────────────


def test_subscriber_create_valid() -> None:
    sub = SubscriberCreate(name="Jane Doe", email="jane@example.com")
    assert sub.name == "Jane Doe"
    assert sub.email == "jane@example.com"
    assert sub.is_active is True


def test_subscriber_create_invalid_email() -> None:
    with pytest.raises(ValidationError):
        SubscriberCreate(name="Bad Email", email="not-an-email")


def test_subscriber_create_inactive() -> None:
    sub = SubscriberCreate(name="Jane", email="jane@example.com", is_active=False)
    assert sub.is_active is False
