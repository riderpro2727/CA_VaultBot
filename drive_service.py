"""
CA Vault Bot - Drive Service
Business logic for managing Drive sources, files, favorites, downloads.
"""
from __future__ import annotations

import asyncio
from typing import List, Optional, Tuple

from config.settings import settings
from database.engine import get_session
from database.models import DriveFile, DriveSource
from database.repositories import (
    DriveSourceRepository,
    DriveFileRepository,
    FavoriteRepository,
    UserRepository,
)
from google_drive.client import get_drive_client
from utils.logger import get_logger

logger = get_logger(__name__)


class DriveService:

    async def add_drive(
        self,
        drive_id: str,
        name: str,
        description: Optional[str],
        is_shared_drive: bool,
        added_by: int,
    ) -> Tuple[Optional[DriveSource], str]:
        """Add a new Google Drive source. Returns (source, error_msg)."""
        # Validate the drive ID with API
        client = get_drive_client()
        try:
            meta = await client.get_folder_metadata(drive_id)
            if not meta:
                return None, "❌ Drive folder not found or not accessible."
        except Exception as e:
            return None, f"❌ Could not verify drive: {e}"

        async with get_session() as session:
            repo = DriveSourceRepository(session)
            existing = await repo.get_by_drive_id(drive_id)
            if existing:
                if not existing.is_active:
                    # Re-activate
                    existing.is_active = True
                    return existing, ""
                return None, f"⚠️ Drive '{existing.name}' already exists."

            # Use API-provided name if not given
            if not name:
                name = meta.get("name", drive_id)

            source = await repo.create(
                drive_id=drive_id,
                name=name,
                description=description,
                is_shared_drive=is_shared_drive,
                added_by=added_by,
            )
            return source, ""

    async def remove_drive(self, drive_id: str) -> bool:
        async with get_session() as session:
            repo = DriveSourceRepository(session)
            return await repo.remove(drive_id)

    async def list_drives(self) -> List[DriveSource]:
        async with get_session() as session:
            repo = DriveSourceRepository(session)
            return await repo.get_all()

    async def get_file(self, file_id: str) -> Optional[DriveFile]:
        async with get_session() as session:
            repo = DriveFileRepository(session)
            return await repo.get_by_file_id(file_id)

    async def get_file_by_db_id(self, db_id: int) -> Optional[DriveFile]:
        async with get_session() as session:
            repo = DriveFileRepository(session)
            return await repo.get_by_id(db_id)

    async def record_file_click(self, file_id: str) -> None:
        async with get_session() as session:
            repo = DriveFileRepository(session)
            await repo.increment_click(file_id)

    async def record_file_download(self, file_id: str) -> None:
        async with get_session() as session:
            repo = DriveFileRepository(session)
            await repo.increment_download(file_id)

    async def add_favorite(self, telegram_id: int, file_id: str) -> Tuple[bool, str]:
        """Add file to favorites. Returns (success, message)."""
        async with get_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                return False, "User not found."

            file_repo = DriveFileRepository(session)
            file = await file_repo.get_by_file_id(file_id)
            if not file:
                return False, "File not found."

            fav_repo = FavoriteRepository(session)
            added = await fav_repo.add(user.id, file.id)
            if added:
                await user_repo.update_favorites_count(telegram_id, 1)
                return True, "⭐ Added to favorites!"
            else:
                return False, "Already in favorites."

    async def remove_favorite(self, telegram_id: int, file_id: str) -> Tuple[bool, str]:
        """Remove file from favorites."""
        async with get_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                return False, "User not found."

            file_repo = DriveFileRepository(session)
            file = await file_repo.get_by_file_id(file_id)
            if not file:
                return False, "File not found."

            fav_repo = FavoriteRepository(session)
            removed = await fav_repo.remove(user.id, file.id)
            if removed:
                await user_repo.update_favorites_count(telegram_id, -1)
                return True, "✅ Removed from favorites."
            else:
                return False, "Not in favorites."

    async def get_favorites(
        self, telegram_id: int, page: int = 1, per_page: int = 5
    ) -> Tuple[List[DriveFile], int]:
        async with get_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                return [], 0
            fav_repo = FavoriteRepository(session)
            return await fav_repo.get_user_favorites(
                user.id, offset=(page - 1) * per_page, limit=per_page
            )

    async def is_favorite(self, telegram_id: int, file_id: str) -> bool:
        async with get_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                return False
            file_repo = DriveFileRepository(session)
            file = await file_repo.get_by_file_id(file_id)
            if not file:
                return False
            fav_repo = FavoriteRepository(session)
            return await fav_repo.is_favorite(user.id, file.id)

    async def try_direct_download(self, file: DriveFile) -> Optional[bytes]:
        """Attempt to download file bytes if within Telegram limits."""
        size = file.file_size or 0
        if size > settings.telegram_max_file_size:
            return None
        try:
            client = get_drive_client()
            return await client.download_file_bytes(file.file_id)
        except Exception as e:
            logger.error(f"Direct download failed for {file.file_id}: {e}")
            return None


_drive_service: Optional[DriveService] = None


def get_drive_service() -> DriveService:
    global _drive_service
    if _drive_service is None:
        _drive_service = DriveService()
    return _drive_service
