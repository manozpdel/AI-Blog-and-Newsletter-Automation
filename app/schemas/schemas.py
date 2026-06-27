from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TopicCreate(BaseModel):
    name: str
    tone: str = "neutral"


class TopicOut(BaseModel):
    id: int
    name: str
    tone: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleOut(BaseModel):
    id: int
    topic_id: int
    title: str | None = None
    content: str | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerateResponse(BaseModel):
    """Kept from Task 1 (no longer used by /generate, available for reuse)."""

    article_id: int
    title: str
    status: str


class TaskQueuedResponse(BaseModel):
    task_id: str
    status: str = "queued"


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    result: Any | None = None


# ---------------------------------------------------------------------------
# Added in Task 3: Newsletters
# ---------------------------------------------------------------------------


class NewsletterOut(BaseModel):
    id: int
    article_id: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerateNewsletterResponse(BaseModel):
    newsletter_id: int
    article_id: int
    content: str