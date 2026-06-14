"""
CA Vault Bot - Search Service
Wraps the search engine with analytics tracking and history.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from database.engine import get_session
from database.models import DriveFile
from database.repositories import (
    SearchHistoryRepository,
    KeywordRepository,
    UserRepository,
)
from search.engine import get_search_engine
from utils.logger import get_logger

logger = get_logger(__name__)


class SearchService:

    async def search(
        self,
        telegram_id: int,
        query: str,
        category_filter: Optional[str] = None,
        page: int = 1,
        per_page: int = 5,
    ) -> Tuple[List[DriveFile], int]:
        """
        Perform search and record analytics.
        Returns (files, total_count).
        """
        engine = get_search_engine()
        results, total = await engine.search(
            query=query,
            category_filter=category_filter,
            page=page,
            per_page=per_page,
        )

        # Record search history & analytics (only on page 1)
        if page == 1:
            await self._record_search(telegram_id, query, total, category_filter)

        return results, total

    async def _record_search(
        self,
        telegram_id: int,
        query: str,
        results_count: int,
        category_filter: Optional[str],
    ) -> None:
        """Record search in history and analytics."""
        try:
            async with get_session() as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_telegram_id(telegram_id)
                if not user:
                    return

                # Increment search count
                await user_repo.increment_search_count(telegram_id)

                # Add to search history
                history_repo = SearchHistoryRepository(session)
                await history_repo.add(
                    user_id=user.id,
                    query=query,
                    results_count=results_count,
                    category_filter=category_filter,
                )

                # Update global keyword stats
                kw_repo = KeywordRepository(session)
                await kw_repo.upsert_keyword(query, results_count)
        except Exception as e:
            logger.warning(f"Failed to record search analytics: {e}")

    async def get_history(
        self, telegram_id: int, limit: int = 20
    ) -> list:
        """Get user's search history."""
        async with get_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                return []
            history_repo = SearchHistoryRepository(session)
            return await history_repo.get_user_history(user.id, limit=limit)

    async def clear_history(self, telegram_id: int) -> int:
        """Clear user's search history. Returns deleted count."""
        async with get_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                return 0
            history_repo = SearchHistoryRepository(session)
            return await history_repo.clear_user_history(user.id)

    async def search_by_category(
        self,
        category: str,
        page: int = 1,
        per_page: int = 5,
    ) -> Tuple[List[DriveFile], int]:
        engine = get_search_engine()
        return await engine.get_by_category(category, page=page, per_page=per_page)


_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
