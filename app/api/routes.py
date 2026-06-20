from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import Article, ArticleStatus, Topic
from app.schemas.schemas import ArticleOut, GenerateResponse, TopicCreate, TopicOut
from app.services.llm_service import generate_article_content

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


@router.post("/generate/{topic_id}", response_model=GenerateResponse, tags=["generate"])
async def generate_article(topic_id: int, db: AsyncSession = Depends(get_db)):
    """
    Synchronous article generation (no Celery yet):
    1. Validate topic exists
    2. Call LLM service
    3. Persist article in PostgreSQL
    """
    topic = await db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    article = Article(topic_id=topic.id, status=ArticleStatus.PROCESSING.value)
    db.add(article)
    await db.commit()
    await db.refresh(article)

    try:
        generated = await generate_article_content(topic=topic.name, tone=topic.tone)
    except Exception as exc:
        article.status = ArticleStatus.FAILED.value
        await db.commit()
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {exc}") from exc

    article.title = generated["title"]
    article.content = generated["article"]
    article.status = ArticleStatus.COMPLETED.value
    await db.commit()
    await db.refresh(article)

    return GenerateResponse(article_id=article.id, title=article.title, status=article.status)


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