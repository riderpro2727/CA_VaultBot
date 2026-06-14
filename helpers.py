"""
CA Vault Bot - General Helper Utilities
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Optional


def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special_chars = r"\_*[]()~`>#+-=|{}.!"
    return re.sub(r"([" + re.escape(special_chars) + r"])", r"\\\1", text)


def truncate(text: str, max_len: int = 200, suffix: str = "...") -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def format_datetime(dt: Optional[datetime], fmt: str = "%d %b %Y %H:%M") -> str:
    if not dt:
        return "N/A"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(fmt)


def time_ago(dt: Optional[datetime]) -> str:
    """Human-readable relative time."""
    if not dt:
        return "Never"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    if months < 12:
        return f"{months}mo ago"
    return f"{days // 365}y ago"


def chunk_list(lst: list, chunk_size: int) -> List[list]:
    """Split a list into chunks of given size."""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def build_progress_bar(current: int, total: int, width: int = 10) -> str:
    """Build a Unicode progress bar."""
    if total == 0:
        return "░" * width
    filled = int((current / total) * width)
    return "█" * filled + "░" * (width - filled)


def sanitize_query(query: str) -> str:
    """Clean and normalize a search query."""
    # Remove special characters except spaces and alphanumerics
    query = re.sub(r"[^\w\s]", " ", query)
    # Normalize whitespace
    query = re.sub(r"\s+", " ", query).strip()
    # Limit length
    return query[:200]


def is_valid_drive_id(drive_id: str) -> bool:
    """Basic validation for Google Drive folder/file ID."""
    # Drive IDs are alphanumeric with underscores/hyphens
    return bool(re.match(r"^[a-zA-Z0-9_\-]{10,}$", drive_id))


def get_page_info(current_page: int, total_results: int, per_page: int) -> dict:
    """Calculate pagination info."""
    total_pages = max(1, (total_results + per_page - 1) // per_page)
    return {
        "current_page": current_page,
        "total_pages": total_pages,
        "total_results": total_results,
        "per_page": per_page,
        "start": (current_page - 1) * per_page,
        "end": min(current_page * per_page, total_results),
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
    }
