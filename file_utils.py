"""
CA Vault Bot - File Utility Functions
File type detection, icon mapping, size formatting, category inference.
"""
from __future__ import annotations

import re
from typing import Optional

from database.models import FileCategory, FileType


# ── Extension → FileType mapping ─────────────────────────────────────────────

EXT_TO_TYPE: dict[str, FileType] = {
    "pdf": FileType.PDF,
    "docx": FileType.DOCX,
    "doc": FileType.DOC,
    "ppt": FileType.PPT,
    "pptx": FileType.PPTX,
    "zip": FileType.ZIP,
    "rar": FileType.RAR,
    "mp4": FileType.MP4,
    "mkv": FileType.MKV,
    "avi": FileType.AVI,
    "mp3": FileType.MP3,
    "m4a": FileType.MP3,
    "wav": FileType.MP3,
    "xlsx": FileType.XLSX,
    "xls": FileType.XLS,
    "jpg": FileType.JPEG,
    "jpeg": FileType.JPEG,
    "png": FileType.PNG,
    "txt": FileType.TXT,
}

# ── FileType → Emoji icon ─────────────────────────────────────────────────────

TYPE_ICONS: dict[FileType, str] = {
    FileType.PDF: "📄",
    FileType.DOCX: "📝",
    FileType.DOC: "📝",
    FileType.PPT: "📊",
    FileType.PPTX: "📊",
    FileType.ZIP: "📦",
    FileType.RAR: "📦",
    FileType.MP4: "🎬",
    FileType.MKV: "🎬",
    FileType.AVI: "🎬",
    FileType.MP3: "🎵",
    FileType.XLSX: "📊",
    FileType.XLS: "📊",
    FileType.JPEG: "🖼️",
    FileType.PNG: "🖼️",
    FileType.TXT: "📃",
    FileType.OTHER: "📁",
}

# ── MIME type → FileType ──────────────────────────────────────────────────────

MIME_TO_TYPE: dict[str, FileType] = {
    "application/pdf": FileType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCX,
    "application/msword": FileType.DOC,
    "application/vnd.ms-powerpoint": FileType.PPT,
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": FileType.PPTX,
    "application/zip": FileType.ZIP,
    "application/x-rar-compressed": FileType.RAR,
    "application/x-rar": FileType.RAR,
    "video/mp4": FileType.MP4,
    "video/x-matroska": FileType.MKV,
    "video/avi": FileType.AVI,
    "audio/mpeg": FileType.MP3,
    "audio/mp4": FileType.MP3,
    "application/vnd.ms-excel": FileType.XLS,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": FileType.XLSX,
    "image/jpeg": FileType.JPEG,
    "image/png": FileType.PNG,
    "text/plain": FileType.TXT,
}

# ── Category keywords ─────────────────────────────────────────────────────────

CATEGORY_KEYWORDS: dict[FileCategory, list[str]] = {
    FileCategory.CA_FOUNDATION: [
        "foundation", "ca foundation", "cf", "caf", "ipcc foundation",
        "bos foundation", "study material foundation",
    ],
    FileCategory.CA_INTERMEDIATE: [
        "intermediate", "ca inter", "ipcc", "ca ipcc", "inter group",
        "group 1", "group 2", "ca intermediate",
    ],
    FileCategory.CA_FINAL: [
        "final", "ca final", "caf", "ca final group", "finalgroup",
    ],
    FileCategory.CLASS_11: [
        "class 11", "class xi", "11th", "eleventh", "std 11",
    ],
    FileCategory.CLASS_12: [
        "class 12", "class xii", "12th", "twelfth", "std 12",
        "board", "boards",
    ],
    FileCategory.COMMERCE: [
        "commerce", "commercial", "trade",
    ],
    FileCategory.ECONOMICS: [
        "economics", "eco", "macroeconomics", "microeconomics",
        "economy", "gdp", "monetary",
    ],
    FileCategory.ACCOUNTS: [
        "accounts", "accounting", "financial accounting", "cost accounting",
        "account", "ledger", "balance sheet", "journal",
    ],
    FileCategory.BUSINESS_STUDIES: [
        "business studies", "bst", "business", "management",
        "organisation", "organization",
    ],
    FileCategory.TAXATION: [
        "taxation", "tax", "gst", "income tax", "indirect tax",
        "direct tax", "tds", "tax law", "vat",
    ],
    FileCategory.AUDIT: [
        "audit", "auditing", "auditor", "assurance",
        "internal audit", "statutory audit",
    ],
    FileCategory.LAW: [
        "law", "legal", "corporate law", "company law", "contract",
        "partnership", "ipc", "business law",
    ],
    FileCategory.GENERAL: [
        "general", "miscellaneous", "other", "misc",
    ],
}


def detect_file_type(file_name: str, mime_type: Optional[str] = None) -> FileType:
    """Determine file type from extension and/or MIME type."""
    if mime_type and mime_type in MIME_TO_TYPE:
        return MIME_TO_TYPE[mime_type]
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    return EXT_TO_TYPE.get(ext, FileType.OTHER)


def get_file_extension(file_name: str) -> str:
    """Extract file extension."""
    if "." in file_name:
        return file_name.rsplit(".", 1)[-1].lower()
    return ""


def get_file_icon(file_type: FileType) -> str:
    """Return emoji icon for file type."""
    return TYPE_ICONS.get(file_type, "📁")


def infer_category(file_name: str, parent_folder_name: Optional[str] = None) -> FileCategory:
    """Infer file category from its name and parent folder name."""
    text = f"{file_name} {parent_folder_name or ''}".lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return FileCategory.UNCATEGORIZED


def format_file_size(size_bytes: Optional[int]) -> str:
    """Format byte size into human-readable string."""
    if not size_bytes:
        return "Unknown size"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def build_drive_url(file_id: str) -> str:
    """Build Google Drive view URL for a file."""
    return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"


def build_drive_download_url(file_id: str) -> str:
    """Build Google Drive direct download URL."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def sanitize_filename(name: str) -> str:
    """Clean file name for display."""
    # Remove extension for display
    if "." in name:
        name = name.rsplit(".", 1)[0]
    # Limit length
    return name[:80] if len(name) > 80 else name


def truncate_name(name: str, max_len: int = 60) -> str:
    """Truncate a file name with ellipsis."""
    if len(name) <= max_len:
        return name
    return name[:max_len - 3] + "..."


CATEGORY_DISPLAY: dict[str, str] = {
    "ca_foundation": "📗 CA Foundation",
    "ca_intermediate": "📘 CA Intermediate",
    "ca_final": "📕 CA Final",
    "class_11": "🏫 Class 11",
    "class_12": "🎓 Class 12",
    "commerce": "💼 Commerce",
    "economics": "📈 Economics",
    "accounts": "🧮 Accounts",
    "business_studies": "🏢 Business Studies",
    "taxation": "💰 Taxation",
    "audit": "🔍 Audit",
    "law": "⚖️ Law",
    "general": "📁 General",
    "uncategorized": "❓ Uncategorized",
}


def get_category_display(category_key: str) -> str:
    return CATEGORY_DISPLAY.get(category_key, f"📁 {category_key.replace('_', ' ').title()}")
