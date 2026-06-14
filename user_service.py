"""
CA Vault Bot - User Service
Business logic for user management, registration, and dashboard.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from config.settings import settings
from database.engine import get_session
from database.repositories import UserRepository
from database.models import User
from utils.logger import get_logger

logger = get_logger(__name__)


class UserService:

    async def get_or_create_user(
        self,
        telegram_id: int,
        name: str,
        username: Optional[str],
    ) -> tuple[User, bool]:
        """Get existing user or create new one. Returns (user, is_new)."""
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(telegram_id)
            if user:
                await repo.update_last_active(telegram_id)
                return user, False
            else:
                is_admin = telegram_id in settings.admin_ids
                user = await repo.create(
                    telegram_id=telegram_id,
                    name=name,
                    username=username,
                    is_admin=is_admin,
                )
                return user, True

    async def get_user(self, telegram_id: int) -> Optional[User]:
        async with get_session() as session:
            repo = UserRepository(session)
            return await repo.get_by_telegram_id(telegram_id)

    async def is_registered(self, telegram_id: int) -> bool:
        user = await self.get_user(telegram_id)
        return user is not None and user.registration_complete

    async def is_banned(self, telegram_id: int) -> bool:
        user = await self.get_user(telegram_id)
        return user is not None and user.is_banned

    async def is_admin(self, telegram_id: int) -> bool:
        if telegram_id in settings.admin_ids:
            return True
        user = await self.get_user(telegram_id)
        return user is not None and user.is_admin

    async def complete_registration(self, telegram_id: int, name: str) -> User:
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(telegram_id)
            if not user:
                is_admin = telegram_id in settings.admin_ids
                user = await repo.create(
                    telegram_id=telegram_id,
                    name=name,
                    username=None,
                    is_admin=is_admin,
                )
            else:
                await repo.complete_registration(telegram_id, name)
                user = await repo.get_by_telegram_id(telegram_id)
            return user

    async def update_last_active(self, telegram_id: int) -> None:
        async with get_session() as session:
            repo = UserRepository(session)
            await repo.update_last_active(telegram_id)

    async def increment_search_count(self, telegram_id: int) -> None:
        async with get_session() as session:
            repo = UserRepository(session)
            await repo.increment_search_count(telegram_id)

    async def increment_download_count(self, telegram_id: int) -> None:
        async with get_session() as session:
            repo = UserRepository(session)
            await repo.increment_download_count(telegram_id)

    async def get_dashboard_data(self, telegram_id: int) -> dict:
        """Get all data needed for user dashboard."""
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(telegram_id)
            if not user:
                return {}
            from database.repositories import FavoriteRepository
            fav_repo = FavoriteRepository(session)
            fav_count = await fav_repo.count_for_user(user.id)
            return {
                "name": user.name,
                "username": user.username,
                "search_count": user.search_count,
                "download_count": user.download_count,
                "favorites_count": fav_count,
                "activity_score": user.activity_score,
                "join_date": user.join_date,
                "last_active": user.last_active,
            }

    async def get_admin_stats(self) -> dict:
        """Get statistics for admin dashboard."""
        async with get_session() as session:
            user_repo = UserRepository(session)
            from database.repositories import (
                SearchHistoryRepository, DriveFileRepository,
                DriveSourceRepository, IndexRunRepository
            )
            search_repo = SearchHistoryRepository(session)
            file_repo = DriveFileRepository(session)
            drive_repo = DriveSourceRepository(session)
            index_repo = IndexRunRepository(session)
            kw_repo_cls = __import__("database.repositories", fromlist=["KeywordRepository"]).KeywordRepository
            kw_repo = kw_repo_cls(session)

            total_users = await user_repo.get_all_users_count()
            active_today = await user_repo.get_active_users_today()
            today_searches = await search_repo.get_today_count()
            weekly_searches = await search_repo.get_weekly_count()
            top_searches = await kw_repo.get_top(10)
            top_files = await file_repo.get_top_files(10)
            top_users = await user_repo.get_top_users(10)
            drive_stats = await drive_repo.get_stats()
            total_files = await file_repo.get_total_files()
            category_stats = await file_repo.get_category_stats()
            recent_runs = await index_repo.get_latest(3)

            return {
                "total_users": total_users,
                "active_today": active_today,
                "today_searches": today_searches,
                "weekly_searches": weekly_searches,
                "top_searches": top_searches,
                "top_files": top_files,
                "top_users": top_users,
                "drive_stats": drive_stats,
                "total_files": total_files,
                "category_stats": category_stats,
                "recent_runs": recent_runs,
            }


_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service
