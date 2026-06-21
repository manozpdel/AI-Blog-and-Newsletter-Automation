import asyncio
from typing import Any

from app.db.session import AsyncSessionLocal
from app.models.models import Article, ArticleStatus, Topic
from app.services.llm_service import (
    generate_full_article,
    generate_outline,
    generate_title,
)
from app.workers.celery_app import celery_app


def _run_async(coro):
    """Bridge: run an async coroutine to completion from inside a sync Celery task."""
    return asyncio.run(coro)


async def _load_topic(topic_id: int) -> Topic:
    async with AsyncSessionLocal() as db:
        topic = await db.get(Topic, topic_id)
        if topic is None:
            raise ValueError(f"Topic {topic_id} not found")
        return topic


async def _update_article(article_id: int, **fields: Any) -> None:
    async with AsyncSessionLocal() as db:
        article = await db.get(Article, article_id)
        if article is None:
            return
        for key, value in fields.items():
            setattr(article, key, value)
        await db.commit()


async def _mark_failed(article_id: int) -> None:
    await _update_article(article_id, status=ArticleStatus.FAILED.value)


@celery_app.task(name="content.generate_title", bind=True)
def generate_title_task(self, article_id: int, topic_id: int) -> dict:
    """Step 1 of the chain: fetch topic, generate title, mark article PROCESSING."""
    try:
        topic = _run_async(_load_topic(topic_id))
        _run_async(_update_article(article_id, status=ArticleStatus.PROCESSING.value))

        title = _run_async(generate_title(topic=topic.name, tone=topic.tone))
        _run_async(_update_article(article_id, title=title))

        return {
            "article_id": article_id,
            "topic_id": topic_id,
            "topic_name": topic.name,
            "tone": topic.tone,
            "title": title,
        }
    except Exception:
        _run_async(_mark_failed(article_id))
        raise


@celery_app.task(name="content.generate_outline", bind=True)
def generate_outline_task(self, prev: dict) -> dict:
    """Step 2 of the chain: generate outline from the title produced in step 1."""
    article_id = prev["article_id"]
    try:
        outline = _run_async(
            generate_outline(topic=prev["topic_name"], tone=prev["tone"], title=prev["title"])
        )
        prev["outline"] = outline
        return prev
    except Exception:
        _run_async(_mark_failed(article_id))
        raise


@celery_app.task(name="content.generate_article", bind=True)
def generate_article_task(self, prev: dict) -> dict:
    """Step 3 of the chain: generate full article, persist it, mark COMPLETED."""
    article_id = prev["article_id"]
    try:
        content = _run_async(
            generate_full_article(
                topic=prev["topic_name"],
                tone=prev["tone"],
                title=prev["title"],
                outline=prev["outline"],
            )
        )
        _run_async(
            _update_article(
                article_id,
                content=content,
                status=ArticleStatus.COMPLETED.value,
            )
        )

        return {
            "article_id": article_id,
            "title": prev["title"],
            "status": ArticleStatus.COMPLETED.value,
        }
    except Exception:
        _run_async(_mark_failed(article_id))
        raise