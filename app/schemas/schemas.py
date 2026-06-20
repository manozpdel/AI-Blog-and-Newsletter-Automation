from datetime import datetime

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
    article_id: int
    title: str
    status: str