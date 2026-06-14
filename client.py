"""
CA Vault Bot - Google Drive API Client
Handles authentication and all Drive API interactions.
"""
from __future__ import annotations

import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

FOLDER_MIME = "application/vnd.google-apps.folder"

FILE_FIELDS = (
    "id, name, mimeType, size, md5Checksum, "
    "createdTime, modifiedTime, parents, "
    "webViewLink, webContentLink, trashed"
)

LIST_FIELDS = f"nextPageToken, files({FILE_FIELDS})"

_executor = ThreadPoolExecutor(max_workers=10)


def _build_credentials() -> service_account.Credentials:
    """Build Google service account credentials from JSON file or env content."""
    json_content = settings.google_service_account_json_content
    if json_content:
        info = json.loads(json_content)
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

    json_path = settings.google_service_account_json
    if os.path.exists(json_path):
        return service_account.Credentials.from_service_account_file(json_path, scopes=SCOPES)

    raise FileNotFoundError(
        "Google service account credentials not found. "
        "Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT."
    )


class DriveClient:
    """Async wrapper around the synchronous Google Drive v3 API."""

    def __init__(self):
        self._service = None
        self._lock = asyncio.Lock()

    def _get_service(self):
        if self._service is None:
            credentials = _build_credentials()
            self._service = build("drive", "v3", credentials=credentials, cache_discovery=False)
        return self._service

    async def _run_sync(self, func, *args, **kwargs):
        """Execute a sync function in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, lambda: func(*args, **kwargs)
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def list_files_in_folder(
        self,
        folder_id: str,
        drive_id: Optional[str] = None,
        page_token: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """List files in a folder (one page). Returns (files, next_page_token)."""

        def _execute():
            service = self._get_service()
            params = {
                "q": f"'{folder_id}' in parents and trashed=false",
                "fields": LIST_FIELDS,
                "pageSize": 1000,
                "orderBy": "name",
            }
            if page_token:
                params["pageToken"] = page_token
            if drive_id:
                params["driveId"] = drive_id
                params["corpora"] = "drive"
                params["includeItemsFromAllDrives"] = True
                params["supportsAllDrives"] = True
            else:
                params["corpora"] = "user"
                params["includeItemsFromAllDrives"] = True
                params["supportsAllDrives"] = True

            response = service.files().list(**params).execute()
            return response.get("files", []), response.get("nextPageToken")

        try:
            return await self._run_sync(_execute)
        except HttpError as e:
            logger.error(f"Drive API error listing {folder_id}: {e}")
            raise

    async def get_all_files_recursive(
        self,
        root_folder_id: str,
        drive_id: Optional[str] = None,
        on_progress: Optional[callable] = None,
    ) -> List[Dict]:
        """
        Recursively scan a Drive folder and return all files (not folders).
        Uses BFS for memory efficiency.
        """
        all_files: List[Dict] = []
        folder_queue: List[Tuple[str, Optional[str]]] = [(root_folder_id, None)]  # (folder_id, parent_name)
        visited: set = set()

        while folder_queue:
            current_folder_id, parent_folder_name = folder_queue.pop(0)
            if current_folder_id in visited:
                continue
            visited.add(current_folder_id)

            page_token = None
            while True:
                try:
                    files, next_token = await self.list_files_in_folder(
                        current_folder_id, drive_id, page_token
                    )
                    for f in files:
                        if f.get("trashed"):
                            continue
                        if f.get("mimeType") == FOLDER_MIME:
                            folder_queue.append((f["id"], f.get("name")))
                        else:
                            f["_parent_folder_id"] = current_folder_id
                            f["_parent_folder_name"] = parent_folder_name or "Root"
                            f["_drive_id"] = drive_id
                            all_files.append(f)

                    if on_progress:
                        await on_progress(len(all_files))

                    page_token = next_token
                    if not page_token:
                        break
                except Exception as e:
                    logger.error(f"Error scanning folder {current_folder_id}: {e}")
                    break

        logger.info(f"Scanned {len(all_files)} files from folder {root_folder_id}")
        return all_files

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_file_metadata(self, file_id: str) -> Optional[Dict]:
        """Get metadata for a single file."""
        def _execute():
            service = self._get_service()
            return service.files().get(
                fileId=file_id,
                fields=FILE_FIELDS,
                supportsAllDrives=True,
            ).execute()

        try:
            return await self._run_sync(_execute)
        except HttpError as e:
            if e.resp.status == 404:
                return None
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_folder_metadata(self, folder_id: str) -> Optional[Dict]:
        """Get metadata for a folder."""
        def _execute():
            service = self._get_service()
            return service.files().get(
                fileId=folder_id,
                fields="id, name, mimeType, driveId",
                supportsAllDrives=True,
            ).execute()

        try:
            return await self._run_sync(_execute)
        except HttpError as e:
            if e.resp.status == 404:
                return None
            raise

    async def download_file_bytes(self, file_id: str) -> Optional[bytes]:
        """Download file content as bytes (for files < Telegram limit)."""
        def _execute():
            from googleapiclient.http import MediaIoBaseDownload
            import io
            service = self._get_service()
            request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return fh.getvalue()

        try:
            return await self._run_sync(_execute)
        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {e}")
            return None

    async def verify_file_exists(self, file_id: str) -> bool:
        """Check if a file is accessible."""
        meta = await self.get_file_metadata(file_id)
        return meta is not None and not meta.get("trashed", False)


# Singleton
_drive_client: Optional[DriveClient] = None


def get_drive_client() -> DriveClient:
    global _drive_client
    if _drive_client is None:
        _drive_client = DriveClient()
    return _drive_client
