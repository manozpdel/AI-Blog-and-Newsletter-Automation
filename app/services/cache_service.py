from datetime import date

import redis.asyncio as redis

from app.core.config import settings

_redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours


def _cache_key(topic_name: str) -> str:
    return f"content_generated:{topic_name}:{date.today().isoformat()}"


async def is_already_generated_today(topic_name: str) -> bool:
    """Check whether content was already generated for this topic today."""
    return bool(await _redis_client.exists(_cache_key(topic_name)))


async def mark_generated_today(topic_name: str) -> None:
    """Mark a topic as generated for today, with a 24h TTL."""
    await _redis_client.set(_cache_key(topic_name), "1", ex=CACHE_TTL_SECONDS)