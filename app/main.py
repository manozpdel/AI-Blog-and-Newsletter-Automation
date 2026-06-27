from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.logging import RequestLoggingMiddleware
from app.db.base import Base
from app.db.session import async_engine  # ← was: engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:  # ← was: engine.begin()
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="AI Blog + Newsletter Automation Platform",
    description="AI Content Automation backend powered by FastAPI, LangChain and Groq",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router)


@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "service": "ai-content-automation"}