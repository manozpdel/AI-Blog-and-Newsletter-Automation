import time

import redis.asyncio as aioredis
from fastapi import HTTPException, Request

from app.core.config import settings

_redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

RATE_LIMIT = 100       # requests
WINDOW_SECONDS = 60    # per minute


async def rate_limit(request: Request) -> None:
    """
    FastAPI dependency: Redis-based sliding-window rate limiter.
    Allows 100 requests/min per IP. Returns 429 when exceeded.
    """
    ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{ip}:{int(time.time() // WINDOW_SECONDS)}"

    count = await _redis.incr(key)
    if count == 1:
        await _redis.expire(key, WINDOW_SECONDS)

    if count > RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {RATE_LIMIT} requests per minute per IP.",
        )