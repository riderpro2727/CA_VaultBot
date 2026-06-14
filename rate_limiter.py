"""
CA Vault Bot - Rate Limiting Middleware
Prevents abuse and spam from users.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from telegram import Update
from telegram.ext import BaseHandler

from cache.redis_client import get_cache
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


async def check_rate_limit(
    telegram_id: int,
    action: str = "search",
    limit: Optional[int] = None,
    window: Optional[int] = None,
) -> bool:
    """
    Check if user has exceeded rate limit.
    Returns True if allowed, False if rate limited.
    """
    if limit is None:
        limit = settings.rate_limit_searches_per_minute
    if window is None:
        window = settings.rate_limit_window_seconds

    try:
        cache = await get_cache()
        allowed, count = await cache.check_rate_limit(telegram_id, action, limit, window)
        if not allowed:
            logger.warning(f"Rate limit exceeded: user={telegram_id} action={action} count={count}")
        return allowed
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True  # Allow on error


async def check_download_limit(telegram_id: int) -> bool:
    """Check download rate limit (stricter)."""
    return await check_rate_limit(
        telegram_id,
        action="download",
        limit=settings.rate_limit_downloads_per_hour,
        window=3600,
    )
