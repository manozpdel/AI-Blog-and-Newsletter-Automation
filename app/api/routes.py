from celery import chain
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import Article, ArticleStatus, Topic
from app.schemas.schemas import (
    ArticleOut,
    TaskQueuedResponse,
    TaskStatusResponse,
    TopicCreate,
    TopicOut,
)
from app.tasks.content_tasks import (
    generate_article_task,
    generate_outline_task,
    generate_title_task,
)
from app.workers.celery_app import celery_app

router = APIRouter()


@router.post("/topics", response_model=TopicOut, status_code=201, tags=["topics"])
async def create_topic(payload: TopicCreate, db: AsyncSession = Depends(get_db)):
    topic = Topic(name=payload.name, tone=payload.tone)
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic


@router.get("/topics", response_model=list[TopicOut], tags=["topics"])
async def list_topics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Topic).order_by(Topic.id.desc()))
    return result.scalars().all()


@router.post("/generate/{topic_id}", response_model=TaskQueuedResponse, tags=["generate"])
async def generate_article(topic_id: int, db: AsyncSession = Depends(get_db)):
    """
    Task 2: article generation now runs in the background via Celery.

    1. Validate topic exists
    2. Create an Article row with status PENDING
    3. Dispatch a Celery chain: generate_title -> generate_outline -> generate_article
    4. Return the task_id immediately (no waiting for the LLM)
    """
    topic = await db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    article = Article(topic_id=topic.id, status=ArticleStatus.PENDING.value)
    db.add(article)
    await db.commit()
    await db.refresh(article)

    workflow = chain(
        generate_title_task.s(article.id, topic.id),
        generate_outline_task.s(),
        generate_article_task.s(),
    )
    async_result = workflow.apply_async()

    return TaskQueuedResponse(task_id=async_result.id, status="queued")


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse, tags=["tasks"])
async def get_task_status(task_id: str):
    """
    Check the state of a Celery task by id.

    state: PENDING / STARTED / SUCCESS / FAILURE
    result: present once the task has finished (success result or error message)
    """
    async_result = AsyncResult(task_id, app=celery_app)

    result_payload = None
    if async_result.state == "SUCCESS":
        result_payload = async_result.result
    elif async_result.state == "FAILURE":
        result_payload = str(async_result.result)

    return TaskStatusResponse(
        task_id=task_id,
        state=async_result.state,
        result=result_payload,
    )


@router.get("/articles", response_model=list[ArticleOut], tags=["articles"])
async def list_articles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).order_by(Article.id.desc()))
    return result.scalars().all()


@router.get("/articles/{article_id}", response_model=ArticleOut, tags=["articles"])
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    article = await db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article