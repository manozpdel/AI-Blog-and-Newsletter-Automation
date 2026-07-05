from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.page_routes import page_router
from app.api.routes import health_router
from app.api.routes import router as api_router
from app.core.logging import RequestLoggingMiddleware
from app.db.base import Base
from app.db.session import async_engine
from app.models import email_log, models, newsletter, subscriber  # noqa: F401


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(  # type: ignore[assignment]
    title="AI Blog + Newsletter Automation Platform",
    description="AI Content Automation backend powered by FastAPI, LangChain and Groq",
    version="0.6.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(RequestLoggingMiddleware)  # type: ignore[attr-defined]
app.mount("/static", StaticFiles(directory="app/static"), name="static")  # type: ignore[attr-defined]
app.include_router(health_router)  # type: ignore[attr-defined]
app.include_router(page_router)  # type: ignore[attr-defined]
app.include_router(api_router)  # type: ignore[attr-defined]
