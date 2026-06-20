from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Simple startup table creation (no Alembic yet -- keeping things minimal).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="AI Blog + Newsletter Automation Platform",
    description="AI Content Automation backend powered by FastAPI, LangChain and Groq",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "service": "ai-content-automation"}