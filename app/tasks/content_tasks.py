# LangChain calls are async — we still need one small event loop bridge
import asyncio
from typing import Any

from app.db.session import SyncSessionLocal
from app.models.models import Article, ArticleStatus, Topic
from app.services.llm_service import (
    generate_full_article,
    generate_outline,
    generate_title,
)
from app.workers.celery_app import celery_app


def _run(coro):
    return asyncio.run(coro)


def _get_topic(topic_id: int) -> tuple[str, str]:
    with SyncSessionLocal() as db:
        topic = db.get(Topic, topic_id)
        if topic is None:
            raise ValueError(f"Topic {topic_id} not found")
        name = topic.name
        tone = topic.tone
    return name, tone


def _update_article(article_id: int, **fields: Any) -> None:
    with SyncSessionLocal() as db:
        article = db.get(Article, article_id)
        if article is None:
            return
        for key, value in fields.items():
            setattr(article, key, value)
        db.commit()


def _mark_failed(article_id: int) -> None:
    _update_article(article_id, status=ArticleStatus.FAILED.value)


@celery_app.task(name="content.generate_title", bind=True)
def generate_title_task(self, article_id: int, topic_id: int) -> dict:
    try:
        topic_name, tone = _get_topic(topic_id)
        _update_article(article_id, status=ArticleStatus.PROCESSING.value)

        title = _run(generate_title(topic=topic_name, tone=tone))
        _update_article(article_id, title=title)

        return {
            "article_id": article_id,
            "topic_id": topic_id,
            "topic_name": topic_name,
            "tone": tone,
            "title": title,
        }
    except Exception:
        _mark_failed(article_id)
        raise


@celery_app.task(name="content.generate_outline", bind=True)
def generate_outline_task(self, prev: dict) -> dict:
    article_id = prev["article_id"]
    try:
        outline = _run(
            generate_outline(
                topic=prev["topic_name"],
                tone=prev["tone"],
                title=prev["title"],
            )
        )
        prev["outline"] = outline
        return prev
    except Exception:
        _mark_failed(article_id)
        raise


@celery_app.task(name="content.generate_article", bind=True)
def generate_article_task(self, prev: dict) -> dict:
    article_id = prev["article_id"]
    try:
        content = _run(
            generate_full_article(
                topic=prev["topic_name"],
                tone=prev["tone"],
                title=prev["title"],
                outline=prev["outline"],
            )
        )
        _update_article(
            article_id,
            content=content,
            status=ArticleStatus.COMPLETED.value,
        )
        return {
            "article_id": article_id,
            "title": prev["title"],
            "status": ArticleStatus.COMPLETED.value,
        }
    except Exception:
        _mark_failed(article_id)
        raise
