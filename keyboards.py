"""
CA Vault Bot - Inline Keyboard Builders
All keyboard layouts for the bot UI.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import DriveFile
from utils.file_utils import (
    get_file_icon, truncate_name, get_category_display, CATEGORY_DISPLAY
)
from utils.helpers import get_page_info


# ── Main Menu ─────────────────────────────────────────────────────────────────

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 Search Resources", callback_data="menu:search"),
            InlineKeyboardButton("📚 Categories", callback_data="menu:categories"),
        ],
        [
            InlineKeyboardButton("⭐ Favorites", callback_data="menu:favorites"),
            InlineKeyboardButton("📜 Search History", callback_data="menu:history"),
        ],
        [
            InlineKeyboardButton("📊 My Dashboard", callback_data="menu:dashboard"),
            InlineKeyboardButton("ℹ️ Help", callback_data="menu:help"),
        ],
    ])


# ── Categories ────────────────────────────────────────────────────────────────

def categories_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """Display categories in a paginated grid."""
    cats = list(CATEGORY_DISPLAY.items())
    # Split into rows of 2
    rows = []
    for i in range(0, len(cats), 2):
        row = []
        for key, label in cats[i:i+2]:
            row.append(InlineKeyboardButton(label, callback_data=f"cat:{key}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


# ── Search Results ────────────────────────────────────────────────────────────

def search_results_keyboard(
    files: List[DriveFile],
    page: int,
    total: int,
    per_page: int,
    query: str,
    category_filter: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """Paginated search results with file select buttons."""
    page_info = get_page_info(page, total, per_page)
    rows = []

    for file in files:
        icon = get_file_icon(file.file_type)
        name = truncate_name(file.file_name, 45)
        rows.append([
            InlineKeyboardButton(
                f"{icon} {name}",
                callback_data=f"file:view:{file.file_id}"
            )
        ])

    # Pagination row
    nav_row = []
    if page_info["has_prev"]:
        cat_part = f":{category_filter}" if category_filter else ""
        nav_row.append(InlineKeyboardButton(
            "◀️ Prev",
            callback_data=f"search:page:{page-1}:{query}{cat_part}"
        ))

    nav_row.append(InlineKeyboardButton(
        f"📄 {page}/{page_info['total_pages']}",
        callback_data="noop"
    ))

    if page_info["has_next"]:
        cat_part = f":{category_filter}" if category_filter else ""
        nav_row.append(InlineKeyboardButton(
            "Next ▶️",
            callback_data=f"search:page:{page+1}:{query}{cat_part}"
        ))

    if nav_row:
        rows.append(nav_row)

    rows.append([
        InlineKeyboardButton("🔍 New Search", callback_data="menu:search"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu:main"),
    ])

    return InlineKeyboardMarkup(rows)


# ── Category Results ──────────────────────────────────────────────────────────

def category_results_keyboard(
    files: List[DriveFile],
    page: int,
    total: int,
    per_page: int,
    category: str,
) -> InlineKeyboardMarkup:
    page_info = get_page_info(page, total, per_page)
    rows = []

    for file in files:
        icon = get_file_icon(file.file_type)
        name = truncate_name(file.file_name, 45)
        rows.append([
            InlineKeyboardButton(
                f"{icon} {name}",
                callback_data=f"file:view:{file.file_id}"
            )
        ])

    nav_row = []
    if page_info["has_prev"]:
        nav_row.append(InlineKeyboardButton(
            "◀️ Prev", callback_data=f"cat:page:{category}:{page-1}"
        ))
    nav_row.append(InlineKeyboardButton(
        f"📄 {page}/{page_info['total_pages']}", callback_data="noop"
    ))
    if page_info["has_next"]:
        nav_row.append(InlineKeyboardButton(
            "Next ▶️", callback_data=f"cat:page:{category}:{page+1}"
        ))
    if nav_row:
        rows.append(nav_row)

    rows.append([
        InlineKeyboardButton("📚 Categories", callback_data="menu:categories"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(rows)


# ── File Detail ───────────────────────────────────────────────────────────────

def file_detail_keyboard(
    file: DriveFile,
    is_favorite: bool,
    back_data: Optional[str] = None,
) -> InlineKeyboardMarkup:
    fav_label = "💔 Remove Fav" if is_favorite else "⭐ Save"
    rows = [
        [
            InlineKeyboardButton("📥 Download", callback_data=f"file:download:{file.file_id}"),
            InlineKeyboardButton("🔗 Drive Link", url=file.google_drive_url),
        ],
        [
            InlineKeyboardButton(fav_label, callback_data=f"file:fav:{file.file_id}"),
            InlineKeyboardButton("🔍 Search Again", callback_data="menu:search"),
        ],
    ]
    back_btn = InlineKeyboardButton("◀️ Back", callback_data=back_data or "menu:main")
    rows.append([back_btn, InlineKeyboardButton("🏠 Menu", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


# ── Favorites ─────────────────────────────────────────────────────────────────

def favorites_keyboard(
    files: List[DriveFile],
    page: int,
    total: int,
    per_page: int,
) -> InlineKeyboardMarkup:
    page_info = get_page_info(page, total, per_page)
    rows = []

    for file in files:
        icon = get_file_icon(file.file_type)
        name = truncate_name(file.file_name, 45)
        rows.append([
            InlineKeyboardButton(
                f"{icon} {name}",
                callback_data=f"file:view:{file.file_id}"
            )
        ])

    nav_row = []
    if page_info["has_prev"]:
        nav_row.append(InlineKeyboardButton(
            "◀️ Prev", callback_data=f"fav:page:{page-1}"
        ))
    nav_row.append(InlineKeyboardButton(
        f"📄 {page}/{page_info['total_pages']}", callback_data="noop"
    ))
    if page_info["has_next"]:
        nav_row.append(InlineKeyboardButton(
            "Next ▶️", callback_data=f"fav:page:{page+1}"
        ))
    if nav_row:
        rows.append(nav_row)

    rows.append([
        InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(rows)


# ── Search History ────────────────────────────────────────────────────────────

def history_keyboard(has_history: bool) -> InlineKeyboardMarkup:
    rows = []
    if has_history:
        rows.append([
            InlineKeyboardButton("🗑️ Clear History", callback_data="history:clear"),
        ])
    rows.append([
        InlineKeyboardButton("🔍 New Search", callback_data="menu:search"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(rows)


# ── Confirm Actions ───────────────────────────────────────────────────────────

def confirm_keyboard(action: str, label: str = "✅ Confirm") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(label, callback_data=f"confirm:{action}"),
            InlineKeyboardButton("❌ Cancel", callback_data="menu:main"),
        ]
    ])


# ── Admin Keyboards ───────────────────────────────────────────────────────────

def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Dashboard", callback_data="admin:dashboard"),
            InlineKeyboardButton("💾 Drives", callback_data="admin:drives"),
        ],
        [
            InlineKeyboardButton("🔄 Re-index", callback_data="admin:reindex"),
            InlineKeyboardButton("🔍 Dead Links", callback_data="admin:deadlinks"),
        ],
        [
            InlineKeyboardButton("👥 Users", callback_data="admin:users"),
            InlineKeyboardButton("📈 Analytics", callback_data="admin:analytics"),
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main"),
        ],
    ])


def drive_list_keyboard(drives, admin: bool = True) -> InlineKeyboardMarkup:
    rows = []
    for drive in drives:
        status = "✅" if drive.is_active else "❌"
        rows.append([
            InlineKeyboardButton(
                f"{status} {drive.name[:35]}",
                callback_data=f"admin:drive_info:{drive.drive_id}"
            )
        ])
    rows.append([
        InlineKeyboardButton("➕ Add Drive", callback_data="admin:add_drive"),
        InlineKeyboardButton("◀️ Back", callback_data="admin:menu"),
    ])
    return InlineKeyboardMarkup(rows)


def drive_action_keyboard(drive_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Index This Drive", callback_data=f"admin:index_drive:{drive_id}"),
            InlineKeyboardButton("🗑️ Remove Drive", callback_data=f"admin:remove_drive:{drive_id}"),
        ],
        [
            InlineKeyboardButton("◀️ Back to Drives", callback_data="admin:drives"),
        ],
    ])


# ── Cancel / Back ─────────────────────────────────────────────────────────────

def cancel_keyboard(back_data: str = "menu:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data=back_data)]
    ])


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main")]
    ])
