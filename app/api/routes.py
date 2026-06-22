from celery import chain
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import Article, ArticleStatus, Topic
from app.models.newsletter import Newsletter
from app.schemas.schemas import (
    ArticleOut,
    GenerateNewsletterResponse,
    NewsletterOut,
    TaskQueuedResponse,
    TaskStatusResponse,
    TopicCreate,
    TopicOut,
)
from app.services.llm_service import generate_newsletter_summary
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
    Background article generation via Celery chain (unchanged from Task 2).
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


# ---------------------------------------------------------------------------
# Added in Task 3: Newsletters
# ---------------------------------------------------------------------------


@router.post(
    "/generate-newsletter/{article_id}",
    response_model=GenerateNewsletterResponse,
    tags=["newsletters"],
)
async def generate_newsletter(article_id: int, db: AsyncSession = Depends(get_db)):
    """
    On-demand newsletter generation for an existing (already-generated) article.
    Synchronous, single LLM call -- the article content already exists, so there's
    no need to queue this through Celery.
    """
    article = await db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    if not article.content:
        raise HTTPException(status_code=400, detail="Article has no content yet")

    summary = await generate_newsletter_summary(title=article.title or "", article=article.content)

    newsletter = Newsletter(article_id=article.id, content=summary)
    db.add(newsletter)
    await db.commit()
    await db.refresh(newsletter)

    return GenerateNewsletterResponse(
        newsletter_id=newsletter.id, article_id=article.id, content=newsletter.content
    )


@router.get("/newsletters", response_model=list[NewsletterOut], tags=["newsletters"])
async def list_newsletters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Newsletter).order_by(Newsletter.id.desc()))
    return result.scalars().all()


@router.get("/newsletters/{newsletter_id}", response_model=NewsletterOut, tags=["newsletters"])
async def get_newsletter(newsletter_id: int, db: AsyncSession = Depends(get_db)):
    newsletter = await db.get(Newsletter, newsletter_id)
    if newsletter is None:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    return newsletter