"""
CA Vault Bot - Redis Cache Client
High-performance caching layer for searches, sessions, and analytics.
"""
from __future__ import annotations

import json
from typing import Any, Optional, Union
from datetime import timedelta

import redis.asyncio as aioredis

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed.")


class CacheService:
    """Unified cache service with namespaced keys."""

    SEARCH_PREFIX = "cavault:search:"
    USER_PREFIX = "cavault:user:"
    SESSION_PREFIX = "cavault:session:"
    HOT_PREFIX = "cavault:hot:"
    RATE_PREFIX = "cavault:rate:"
    INDEX_PREFIX = "cavault:index:"

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    # ── Generic ───────────────────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[Any]:
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        try:
            serialized = json.dumps(value, default=str)
            await self.redis.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False

    async def delete(self, key: str) -> None:
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")

    async def exists(self, key: str) -> bool:
        try:
            return bool(await self.redis.exists(key))
        except Exception:
            return False

    # ── Search Cache ──────────────────────────────────────────────────────────

    def _search_key(self, query: str, category: Optional[str] = None) -> str:
        cat = category or "all"
        return f"{self.SEARCH_PREFIX}{query.lower().strip()}:{cat}"

    async def get_search_results(
        self, query: str, category: Optional[str] = None
    ) -> Optional[list]:
        key = self._search_key(query, category)
        return await self.get(key)

    async def set_search_results(
        self,
        query: str,
        results: list,
        category: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        key = self._search_key(query, category)
        cache_ttl = ttl or settings.search_cache_ttl
        await self.set(key, results, ttl=cache_ttl)

    async def invalidate_search_cache(self) -> None:
        """Clear all cached search results (called after reindex)."""
        try:
            keys = await self.redis.keys(f"{self.SEARCH_PREFIX}*")
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} search cache entries.")
        except Exception as e:
            logger.warning(f"Search cache invalidation error: {e}")

    # ── User Session ──────────────────────────────────────────────────────────

    def _session_key(self, telegram_id: int) -> str:
        return f"{self.SESSION_PREFIX}{telegram_id}"

    async def get_session(self, telegram_id: int) -> Optional[dict]:
        return await self.get(self._session_key(telegram_id))

    async def set_session(self, telegram_id: int, data: dict, ttl: int = 3600) -> None:
        await self.set(self._session_key(telegram_id), data, ttl=ttl)

    async def update_session(self, telegram_id: int, updates: dict) -> None:
        existing = await self.get_session(telegram_id) or {}
        existing.update(updates)
        await self.set_session(telegram_id, existing)

    async def clear_session(self, telegram_id: int) -> None:
        await self.delete(self._session_key(telegram_id))

    # ── Rate Limiting ─────────────────────────────────────────────────────────

    async def check_rate_limit(
        self, telegram_id: int, action: str, limit: int, window_seconds: int
    ) -> tuple[bool, int]:
        """Returns (allowed, current_count)."""
        key = f"{self.RATE_PREFIX}{action}:{telegram_id}"
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            results = await pipe.execute()
            current_count = results[0]
            allowed = current_count <= limit
            return allowed, current_count
        except Exception as e:
            logger.warning(f"Rate limit check error: {e}")
            return True, 0  # Allow on error

    # ── Hot Results ───────────────────────────────────────────────────────────

    async def get_hot_results(self, query: str) -> Optional[list]:
        key = f"{self.HOT_PREFIX}{query.lower().strip()}"
        return await self.get(key)

    async def set_hot_results(self, query: str, results: list) -> None:
        key = f"{self.HOT_PREFIX}{query.lower().strip()}"
        await self.set(key, results, ttl=settings.redis_hot_cache_ttl)

    # ── Index Status ──────────────────────────────────────────────────────────

    async def get_index_status(self) -> Optional[dict]:
        return await self.get(f"{self.INDEX_PREFIX}status")

    async def set_index_status(self, status: dict) -> None:
        await self.set(f"{self.INDEX_PREFIX}status", status, ttl=600)

    async def is_indexing_running(self) -> bool:
        val = await self.redis.get(f"{self.INDEX_PREFIX}running")
        return val == "1"

    async def set_indexing_running(self, running: bool) -> None:
        key = f"{self.INDEX_PREFIX}running"
        if running:
            await self.redis.set(key, "1", ex=1800)
        else:
            await self.redis.delete(key)

    # ── Analytics Cache ───────────────────────────────────────────────────────

    async def increment_counter(self, key: str, ttl: int = 86400) -> int:
        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, ttl)
            return count
        except Exception:
            return 0

    async def get_counter(self, key: str) -> int:
        try:
            val = await self.redis.get(key)
            return int(val) if val else 0
        except Exception:
            return 0


_cache_service: Optional[CacheService] = None


async def get_cache() -> CacheService:
    global _cache_service
    if _cache_service is None:
        redis = await get_redis()
        _cache_service = CacheService(redis)
    return _cache_service
