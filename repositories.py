"""
CA Vault Bot - Database Repositories
Data access layer with clean separation from business logic.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import delete, func, select, update, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import (
    Category,
    DriveFile,
    DriveSource,
    Favorite,
    FileCategory,
    IndexRun,
    SearchHistory,
    SearchKeyword,
    User,
    UserAnalytics,
)
from utils.logger import get_logger

logger = get_logger(__name__)


# ── User Repository ───────────────────────────────────────────────────────────

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        name: str,
        username: Optional[str],
        is_admin: bool = False,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            name=name,
            username=username,
            is_admin=is_admin,
            registration_complete=True,
            join_date=datetime.now(timezone.utc),
            last_active=datetime.now(timezone.utc),
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_last_active(self, telegram_id: int) -> None:
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(last_active=datetime.now(timezone.utc))
        )

    async def increment_search_count(self, telegram_id: int) -> None:
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(
                search_count=User.search_count + 1,
                last_active=datetime.now(timezone.utc),
                activity_score=User.activity_score + 1.0,
            )
        )

    async def increment_download_count(self, telegram_id: int) -> None:
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(
                download_count=User.download_count + 1,
                activity_score=User.activity_score + 2.0,
            )
        )

    async def update_favorites_count(self, telegram_id: int, delta: int) -> None:
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(favorites_count=User.favorites_count + delta)
        )

    async def get_all_users_count(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def get_active_users_today(self) -> int:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(User.id)).where(User.last_active >= today)
        )
        return result.scalar_one()

    async def get_top_users(self, limit: int = 10) -> List[User]:
        result = await self.session.execute(
            select(User)
            .where(User.registration_complete == True)
            .order_by(desc(User.activity_score))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all(self, offset: int = 0, limit: int = 50) -> List[User]:
        result = await self.session.execute(
            select(User)
            .where(User.registration_complete == True)
            .order_by(desc(User.last_active))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def complete_registration(self, telegram_id: int, name: str) -> None:
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(name=name, registration_complete=True)
        )

    async def set_admin(self, telegram_id: int, is_admin: bool) -> None:
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_admin=is_admin)
        )

    async def ban_user(self, telegram_id: int, banned: bool) -> None:
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_banned=banned)
        )


# ── Drive Source Repository ───────────────────────────────────────────────────

class DriveSourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active(self) -> List[DriveSource]:
        result = await self.session.execute(
            select(DriveSource).where(DriveSource.is_active == True)
        )
        return list(result.scalars().all())

    async def get_all(self) -> List[DriveSource]:
        result = await self.session.execute(
            select(DriveSource).order_by(DriveSource.created_at)
        )
        return list(result.scalars().all())

    async def get_by_drive_id(self, drive_id: str) -> Optional[DriveSource]:
        result = await self.session.execute(
            select(DriveSource).where(DriveSource.drive_id == drive_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        drive_id: str,
        name: str,
        description: Optional[str],
        is_shared_drive: bool,
        added_by: Optional[int],
    ) -> DriveSource:
        source = DriveSource(
            drive_id=drive_id,
            name=name,
            description=description,
            is_shared_drive=is_shared_drive,
            added_by=added_by,
            is_active=True,
        )
        self.session.add(source)
        await self.session.flush()
        return source

    async def remove(self, drive_id: str) -> bool:
        result = await self.session.execute(
            update(DriveSource)
            .where(DriveSource.drive_id == drive_id)
            .values(is_active=False)
        )
        return result.rowcount > 0

    async def update_scan_time(self, drive_id: str, file_count: int) -> None:
        await self.session.execute(
            update(DriveSource)
            .where(DriveSource.drive_id == drive_id)
            .values(
                last_scanned=datetime.now(timezone.utc),
                total_files=file_count,
            )
        )

    async def get_stats(self) -> dict:
        result = await self.session.execute(
            select(
                func.count(DriveSource.id).label("total"),
                func.sum(DriveSource.total_files).label("total_files"),
            ).where(DriveSource.is_active == True)
        )
        row = result.one()
        return {"total_drives": row.total or 0, "total_files": row.total_files or 0}


# ── Drive File Repository ─────────────────────────────────────────────────────

class DriveFileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_file_id(self, file_id: str) -> Optional[DriveFile]:
        result = await self.session.execute(
            select(DriveFile).where(DriveFile.file_id == file_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, db_id: int) -> Optional[DriveFile]:
        result = await self.session.execute(
            select(DriveFile).where(DriveFile.id == db_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, file_data: dict) -> Tuple[DriveFile, bool]:
        """Insert or update a file record. Returns (file, created)."""
        existing = await self.get_by_file_id(file_data["file_id"])
        if existing:
            for key, value in file_data.items():
                setattr(existing, key, value)
            existing.last_verified = datetime.now(timezone.utc)
            await self.session.flush()
            return existing, False
        else:
            file_data["file_name_lower"] = file_data.get("file_name", "").lower()
            drive_file = DriveFile(**file_data)
            self.session.add(drive_file)
            await self.session.flush()
            return drive_file, True

    async def mark_unavailable(self, file_ids: List[str]) -> int:
        if not file_ids:
            return 0
        result = await self.session.execute(
            update(DriveFile)
            .where(DriveFile.file_id.in_(file_ids))
            .values(is_available=False)
        )
        return result.rowcount

    async def get_all_file_ids_for_drive(self, drive_id: str) -> List[str]:
        result = await self.session.execute(
            select(DriveFile.file_id).where(
                and_(DriveFile.drive_id == drive_id, DriveFile.is_available == True)
            )
        )
        return [row[0] for row in result.all()]

    async def increment_click(self, file_id: str) -> None:
        await self.session.execute(
            update(DriveFile)
            .where(DriveFile.file_id == file_id)
            .values(
                click_count=DriveFile.click_count + 1,
                popularity_score=DriveFile.popularity_score + 0.5,
            )
        )

    async def increment_download(self, file_id: str) -> None:
        await self.session.execute(
            update(DriveFile)
            .where(DriveFile.file_id == file_id)
            .values(
                download_count=DriveFile.download_count + 1,
                popularity_score=DriveFile.popularity_score + 1.5,
            )
        )

    async def get_by_category(
        self, category: str, offset: int = 0, limit: int = 20
    ) -> Tuple[List[DriveFile], int]:
        base_q = select(DriveFile).where(
            and_(
                DriveFile.category == category,
                DriveFile.is_available == True,
                DriveFile.is_duplicate == False,
            )
        )
        count_result = await self.session.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total = count_result.scalar_one()
        result = await self.session.execute(
            base_q.order_by(desc(DriveFile.popularity_score)).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_total_files(self) -> int:
        result = await self.session.execute(
            select(func.count(DriveFile.id)).where(
                and_(DriveFile.is_available == True, DriveFile.is_duplicate == False)
            )
        )
        return result.scalar_one()

    async def get_all_for_search(self) -> List[DriveFile]:
        """Load all available, non-duplicate files for in-memory search index."""
        result = await self.session.execute(
            select(DriveFile).where(
                and_(DriveFile.is_available == True, DriveFile.is_duplicate == False)
            )
        )
        return list(result.scalars().all())

    async def find_duplicates(self) -> None:
        """Mark files with same name + size as duplicates, keeping highest-scored."""
        # Find groups of potential duplicates
        dup_query = (
            select(
                DriveFile.file_name_lower,
                DriveFile.file_size,
                func.count(DriveFile.id).label("cnt"),
            )
            .where(DriveFile.is_available == True)
            .group_by(DriveFile.file_name_lower, DriveFile.file_size)
            .having(func.count(DriveFile.id) > 1)
        )
        result = await self.session.execute(dup_query)
        dup_groups = result.all()

        for group in dup_groups:
            files_result = await self.session.execute(
                select(DriveFile)
                .where(
                    and_(
                        DriveFile.file_name_lower == group.file_name_lower,
                        DriveFile.file_size == group.file_size,
                        DriveFile.is_available == True,
                    )
                )
                .order_by(desc(DriveFile.popularity_score))
            )
            files = list(files_result.scalars().all())
            # Keep the first (highest score), mark the rest as duplicates
            canonical = files[0]
            for dup in files[1:]:
                dup.is_duplicate = True
                dup.duplicate_of_id = canonical.id
        await self.session.flush()

    async def get_top_files(self, limit: int = 10) -> List[DriveFile]:
        result = await self.session.execute(
            select(DriveFile)
            .where(and_(DriveFile.is_available == True, DriveFile.is_duplicate == False))
            .order_by(desc(DriveFile.download_count))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_category_stats(self) -> List[dict]:
        result = await self.session.execute(
            select(
                DriveFile.category,
                func.count(DriveFile.id).label("count"),
            )
            .where(and_(DriveFile.is_available == True, DriveFile.is_duplicate == False))
            .group_by(DriveFile.category)
            .order_by(desc(func.count(DriveFile.id)))
        )
        return [{"category": row.category, "count": row.count} for row in result.all()]

    async def get_dead_links(self, threshold_days: int = 7) -> List[DriveFile]:
        cutoff = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(DriveFile).where(
                and_(
                    DriveFile.is_available == False,
                    DriveFile.last_verified <= cutoff,
                )
            ).limit(50)
        )
        return list(result.scalars().all())


# ── Search History Repository ─────────────────────────────────────────────────

class SearchHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, query: str, results_count: int, category_filter: Optional[str] = None) -> None:
        entry = SearchHistory(
            user_id=user_id,
            query=query,
            results_count=results_count,
            category_filter=category_filter,
        )
        self.session.add(entry)
        await self.session.flush()

    async def get_user_history(self, user_id: int, limit: int = 20) -> List[SearchHistory]:
        result = await self.session.execute(
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(desc(SearchHistory.searched_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def clear_user_history(self, user_id: int) -> int:
        result = await self.session.execute(
            delete(SearchHistory).where(SearchHistory.user_id == user_id)
        )
        return result.rowcount

    async def get_top_searches(self, limit: int = 10) -> List[SearchKeyword]:
        result = await self.session.execute(
            select(SearchKeyword)
            .order_by(desc(SearchKeyword.search_count))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_today_count(self) -> int:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(SearchHistory.id)).where(SearchHistory.searched_at >= today)
        )
        return result.scalar_one()

    async def get_weekly_count(self) -> int:
        from datetime import timedelta
        week_ago = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0) - __import__("datetime").timedelta(days=7)
        from datetime import timedelta
        import datetime as dt
        week_ago = datetime.now(timezone.utc) - dt.timedelta(days=7)
        result = await self.session.execute(
            select(func.count(SearchHistory.id)).where(SearchHistory.searched_at >= week_ago)
        )
        return result.scalar_one()


# ── Keyword Repository ────────────────────────────────────────────────────────

class KeywordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_keyword(self, keyword: str, result_count: int) -> None:
        normalized = keyword.lower().strip()
        existing = await self.session.execute(
            select(SearchKeyword).where(SearchKeyword.keyword == normalized)
        )
        kw = existing.scalar_one_or_none()
        if kw:
            kw.search_count += 1
            kw.last_searched = datetime.now(timezone.utc)
            kw.result_count = result_count
        else:
            kw = SearchKeyword(
                keyword=normalized,
                search_count=1,
                result_count=result_count,
                last_searched=datetime.now(timezone.utc),
            )
            self.session.add(kw)
        await self.session.flush()

    async def get_top(self, limit: int = 10) -> List[SearchKeyword]:
        result = await self.session.execute(
            select(SearchKeyword).order_by(desc(SearchKeyword.search_count)).limit(limit)
        )
        return list(result.scalars().all())


# ── Favorites Repository ──────────────────────────────────────────────────────

class FavoriteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, file_id: int) -> bool:
        """Returns True if added, False if already exists."""
        existing = await self.session.execute(
            select(Favorite).where(
                and_(Favorite.user_id == user_id, Favorite.file_id == file_id)
            )
        )
        if existing.scalar_one_or_none():
            return False
        fav = Favorite(user_id=user_id, file_id=file_id)
        self.session.add(fav)
        await self.session.flush()
        return True

    async def remove(self, user_id: int, file_id: int) -> bool:
        result = await self.session.execute(
            delete(Favorite).where(
                and_(Favorite.user_id == user_id, Favorite.file_id == file_id)
            )
        )
        return result.rowcount > 0

    async def get_user_favorites(
        self, user_id: int, offset: int = 0, limit: int = 10
    ) -> Tuple[List[DriveFile], int]:
        count_result = await self.session.execute(
            select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(DriveFile)
            .join(Favorite, Favorite.file_id == DriveFile.id)
            .where(Favorite.user_id == user_id)
            .order_by(desc(Favorite.saved_at))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def is_favorite(self, user_id: int, file_id: int) -> bool:
        result = await self.session.execute(
            select(Favorite).where(
                and_(Favorite.user_id == user_id, Favorite.file_id == file_id)
            )
        )
        return result.scalar_one_or_none() is not None

    async def count_for_user(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        )
        return result.scalar_one()


# ── Analytics Repository ──────────────────────────────────────────────────────

class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def track(
        self,
        user_id: int,
        event_type: str,
        file_id: Optional[str] = None,
        query: Optional[str] = None,
        event_data: Optional[dict] = None,
    ) -> None:
        event = UserAnalytics(
            user_id=user_id,
            event_type=event_type,
            file_id=file_id,
            query=query,
            event_data=event_data,
        )
        self.session.add(event)
        await self.session.flush()

    async def get_user_stats(self, user_id: int) -> dict:
        result = await self.session.execute(
            select(
                func.count(UserAnalytics.id).label("total_events"),
            ).where(UserAnalytics.user_id == user_id)
        )
        row = result.one()
        return {"total_events": row.total_events}


# ── Category Repository ───────────────────────────────────────────────────────

class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active(self) -> List[Category]:
        result = await self.session.execute(
            select(Category)
            .where(Category.is_active == True)
            .order_by(asc(Category.sort_order), asc(Category.display_name))
        )
        return list(result.scalars().all())

    async def get_by_key(self, key: str) -> Optional[Category]:
        result = await self.session.execute(
            select(Category).where(Category.key == key)
        )
        return result.scalar_one_or_none()

    async def create(self, key: str, display_name: str, emoji: str, description: Optional[str] = None) -> Category:
        cat = Category(
            key=key,
            display_name=display_name,
            emoji=emoji,
            description=description,
        )
        self.session.add(cat)
        await self.session.flush()
        return cat

    async def ensure_defaults(self) -> None:
        """Insert default categories if they don't exist."""
        defaults = [
            ("ca_foundation", "CA Foundation", "📗"),
            ("ca_intermediate", "CA Intermediate", "📘"),
            ("ca_final", "CA Final", "📕"),
            ("class_11", "Class 11", "🏫"),
            ("class_12", "Class 12", "🎓"),
            ("commerce", "Commerce", "💼"),
            ("economics", "Economics", "📈"),
            ("accounts", "Accounts", "🧮"),
            ("business_studies", "Business Studies", "🏢"),
            ("taxation", "Taxation", "💰"),
            ("audit", "Audit", "🔍"),
            ("law", "Law", "⚖️"),
            ("general", "General", "📁"),
            ("uncategorized", "Uncategorized", "❓"),
        ]
        for i, (key, name, emoji) in enumerate(defaults):
            existing = await self.get_by_key(key)
            if not existing:
                cat = Category(key=key, display_name=name, emoji=emoji, sort_order=i)
                self.session.add(cat)
        await self.session.flush()


# ── Index Run Repository ──────────────────────────────────────────────────────

class IndexRunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def start_run(
        self,
        drive_source_id: Optional[int] = None,
        triggered_by: Optional[int] = None,
    ) -> IndexRun:
        run = IndexRun(
            drive_source_id=drive_source_id,
            triggered_by=triggered_by,
            status="running",
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def complete_run(
        self,
        run_id: int,
        files_scanned: int,
        files_added: int,
        files_removed: int,
        files_updated: int,
        status: str = "completed",
        error_message: Optional[str] = None,
    ) -> None:
        await self.session.execute(
            update(IndexRun)
            .where(IndexRun.id == run_id)
            .values(
                completed_at=datetime.now(timezone.utc),
                files_scanned=files_scanned,
                files_added=files_added,
                files_removed=files_removed,
                files_updated=files_updated,
                status=status,
                error_message=error_message,
            )
        )

    async def get_latest(self, limit: int = 5) -> List[IndexRun]:
        result = await self.session.execute(
            select(IndexRun).order_by(desc(IndexRun.started_at)).limit(limit)
        )
        return list(result.scalars().all())
