"""
CA Vault Bot - Message Templates
All formatted message strings for the bot.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from database.models import DriveFile, DriveSource, SearchKeyword, User
from utils.file_utils import (
    format_file_size, get_file_icon, get_category_display, sanitize_filename
)
from utils.helpers import format_datetime, time_ago, truncate


# ── Welcome & Registration ─────────────────────────────────────────────────────

WELCOME_MESSAGE = """
🎓 *Welcome to CA Vault\\!*

Your ultimate study resource hub for CA & Commerce students\\.

📚 *What's inside:*
• Notes, Books & Lectures
• Question Banks & MCQs
• RTPs, MTPs & Scanners
• PDF, PPT, ZIP, Video files

Please enter your *full name* to get started:
"""

WELCOME_BACK = """
👋 *Welcome back, {name}\\!*

Your study resources are ready\\. What would you like to do today?
"""

REGISTRATION_SUCCESS = """
✅ *Registration Complete\\!*

Welcome aboard, *{name}*\\! 🎉

You now have access to thousands of CA & Commerce study resources\\.
"""


# ── Main Menu ─────────────────────────────────────────────────────────────────

def main_menu_text(name: str) -> str:
    safe_name = name.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]")
    return (
        f"🏠 *CA Vault \\— Main Menu*\n\n"
        f"Hello, *{safe_name}*\\! Choose an option:\n\n"
        f"🔍 *Search Resources* — Find study material\n"
        f"📚 *Categories* — Browse by subject\n"
        f"⭐ *Favorites* — Your saved resources\n"
        f"📜 *History* — Recent searches\n"
        f"📊 *Dashboard* — Your activity\n"
        f"ℹ️ *Help* — How to use"
    )


# ── Search ────────────────────────────────────────────────────────────────────

SEARCH_PROMPT = """
🔍 *Search Resources*

Type your search query below\\.

*Examples:*
• `financial accounting`
• `ca inter taxation`
• `audit notes pdf`
• `mcq question bank`

Supports fuzzy matching — typos are okay\\!
"""

def search_results_header(query: str, total: int, page: int, total_pages: int) -> str:
    safe_query = query.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]").replace(".", "\\.").replace("!", "\\!").replace("(", "\\(").replace(")", "\\)").replace("-", "\\-")
    return (
        f"🔍 *Search Results for:* `{safe_query}`\n\n"
        f"📊 Found *{total}* resources \\| Page *{page}/{total_pages}*\n\n"
        f"👇 Select a file to view details:"
    )


NO_RESULTS_MESSAGE = """
😔 *No Results Found*

No resources matched your query\\. Try:
• Different keywords
• Shorter search terms
• Check spelling

💡 *Tip:* Try searching for subject names like `accounts`, `tax`, `audit`
"""


# ── File Detail ───────────────────────────────────────────────────────────────

def file_detail_text(file: DriveFile, is_favorite: bool) -> str:
    icon = get_file_icon(file.file_type)
    name = file.file_name.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]").replace(".", "\\.").replace("!", "\\!").replace("(", "\\(").replace(")", "\\)").replace("-", "\\-")
    category = get_category_display(file.category if isinstance(file.category, str) else file.category.value)
    size = format_file_size(file.file_size)
    ext = (file.extension or "Unknown").upper()
    modified = time_ago(file.modified_time)
    fav_status = "⭐ In Favorites" if is_favorite else "☆ Not Saved"

    lines = [
        f"{icon} *{name}*",
        f"",
        f"📁 *Type:* {ext}",
        f"🗂️ *Category:* {category}",
        f"📦 *Size:* {size}",
        f"🕐 *Updated:* {modified}",
        f"{fav_status}",
    ]
    if file.parent_folder_name:
        folder = file.parent_folder_name.replace("_", "\\_").replace("*", "\\*")
        lines.insert(3, f"📂 *Folder:* {folder}")

    return "\n".join(lines)


# ── Categories ────────────────────────────────────────────────────────────────

CATEGORIES_HEADER = """
📚 *Study Categories*

Browse resources by subject or course:
"""

def category_results_header(category_name: str, total: int, page: int, total_pages: int) -> str:
    safe = category_name.replace("_", "\\_").replace("*", "\\*")
    return (
        f"📚 *{safe}*\n\n"
        f"Found *{total}* resources \\| Page *{page}/{total_pages}*\n\n"
        f"👇 Select a file:"
    )


# ── Dashboard ─────────────────────────────────────────────────────────────────

def user_dashboard_text(data: dict) -> str:
    name = str(data.get("name", "User")).replace("_", "\\_").replace("*", "\\*")
    join_date = format_datetime(data.get("join_date"))
    last_active = time_ago(data.get("last_active"))
    searches = data.get("search_count", 0)
    downloads = data.get("download_count", 0)
    favorites = data.get("favorites_count", 0)
    score = int(data.get("activity_score", 0))

    # Activity badge
    if score >= 100:
        badge = "🏆 Expert"
    elif score >= 50:
        badge = "⭐ Active"
    elif score >= 20:
        badge = "📚 Regular"
    else:
        badge = "🌱 Beginner"

    return (
        f"📊 *My Dashboard*\n\n"
        f"👤 *Name:* {name}\n"
        f"🎖️ *Badge:* {badge}\n"
        f"📅 *Joined:* {join_date}\n"
        f"🕐 *Last Active:* {last_active}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 *Total Searches:* {searches}\n"
        f"📥 *Downloads:* {downloads}\n"
        f"⭐ *Favorites:* {favorites}\n"
        f"🏅 *Activity Score:* {score}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )


# ── Favorites ─────────────────────────────────────────────────────────────────

def favorites_header(total: int, page: int, total_pages: int) -> str:
    return (
        f"⭐ *My Favorites*\n\n"
        f"*{total}* saved resources \\| Page *{page}/{total_pages}*\n\n"
        f"👇 Select a file:"
    )


NO_FAVORITES = """
⭐ *No Favorites Yet*

You haven't saved any resources yet\\.

Use the ⭐ *Save* button when viewing a file to add it here\\.
"""


# ── Search History ────────────────────────────────────────────────────────────

def history_text(history: list) -> str:
    if not history:
        return "📜 *Search History*\n\nYou haven't searched for anything yet\\."

    lines = ["📜 *Recent Searches*\n"]
    for i, entry in enumerate(history[:15], 1):
        query = entry.query.replace("_", "\\_").replace("*", "\\*").replace(".", "\\.").replace("!", "\\!").replace("(", "\\(").replace(")", "\\)").replace("-", "\\-")
        count = entry.results_count
        when = time_ago(entry.searched_at)
        lines.append(f"{i}\\. `{query}` — *{count}* results \\({when}\\)")

    return "\n".join(lines)


HISTORY_CLEARED = "✅ *Search history cleared\\!*"


# ── Help ──────────────────────────────────────────────────────────────────────

HELP_TEXT = """
ℹ️ *CA Vault Help Guide*

*🔍 How to Search:*
• Tap *Search Resources*
• Type any keyword \\(supports typos\\!\\)
• Browse results with Next/Prev buttons
• Tap any file to see details

*📚 Browsing Categories:*
• Tap *Categories* in the main menu
• Select your subject or course

*📥 Downloading Files:*
• Open a file → tap *Download*
• Files are sent directly if small enough
• Large files: use the *Drive Link*

*⭐ Favorites:*
• Tap ⭐ Save on any file
• Access via *Favorites* in the menu

*📊 Dashboard:*
• Track your searches and downloads
• See your activity score

*💡 Search Tips:*
• Try short keywords: `audit`, `tax`
• Subject names work great
• Abbreviations supported: `gst`, `ca final`

*📞 Support:* Contact admin if you need help
"""


# ── Admin Dashboard ───────────────────────────────────────────────────────────

def admin_dashboard_text(stats: dict) -> str:
    top_searches = stats.get("top_searches", [])
    top_files = stats.get("top_files", [])
    drive_stats = stats.get("drive_stats", {})
    recent_runs = stats.get("recent_runs", [])

    top_s_lines = []
    for kw in top_searches[:5]:
        safe_kw = str(kw.keyword).replace("_", "\\_").replace("*", "\\*").replace(".", "\\.").replace("(", "\\(").replace(")", "\\)").replace("-", "\\-").replace("!", "\\!")
        top_s_lines.append(f"  • `{safe_kw}` \\({kw.search_count}x\\)")

    top_f_lines = []
    for f in top_files[:5]:
        safe_name = truncate(f.file_name, 35).replace("_", "\\_").replace("*", "\\*").replace(".", "\\.").replace("(", "\\(").replace(")", "\\)").replace("-", "\\-").replace("!", "\\!")
        top_f_lines.append(f"  • {safe_name} \\({f.download_count}↓\\)")

    last_run = ""
    if recent_runs:
        r = recent_runs[0]
        last_run = (
            f"\n\n🔄 *Last Index Run:*\n"
            f"  Status: `{r.status}`\n"
            f"  Scanned: {r.files_scanned} files\n"
            f"  Added: \\+{r.files_added} \\| Removed: \\-{r.files_removed}"
        )

    return (
        f"🛡️ *Admin Dashboard*\n\n"
        f"━━━━ 👥 *Users* ━━━━\n"
        f"Total: *{stats.get('total_users', 0)}* \\| Active Today: *{stats.get('active_today', 0)}*\n\n"
        f"━━━━ 🔍 *Searches* ━━━━\n"
        f"Today: *{stats.get('today_searches', 0)}* \\| This Week: *{stats.get('weekly_searches', 0)}*\n\n"
        f"━━━━ 💾 *Storage* ━━━━\n"
        f"Drives: *{drive_stats.get('total_drives', 0)}* \\| Files: *{stats.get('total_files', 0)}*\n\n"
        f"━━━━ 🔥 *Top Searches* ━━━━\n"
        + ("\n".join(top_s_lines) if top_s_lines else "  None yet") +
        f"\n\n━━━━ 📥 *Top Downloads* ━━━━\n"
        + ("\n".join(top_f_lines) if top_f_lines else "  None yet")
        + last_run
    )


def drives_list_text(drives: list) -> str:
    if not drives:
        return "💾 *Drive Sources*\n\nNo drives configured yet\\. Use `/adddrive` to add one\\."

    lines = ["💾 *Drive Sources*\n"]
    for d in drives:
        status = "✅ Active" if d.is_active else "❌ Inactive"
        name = str(d.name).replace("_", "\\_").replace("*", "\\*").replace(".", "\\.").replace("(", "\\(").replace(")", "\\)").replace("-", "\\-").replace("!", "\\!")
        scanned = time_ago(d.last_scanned)
        lines.append(
            f"{status} *{name}*\n"
            f"  ID: `{d.drive_id}`\n"
            f"  Files: {d.total_files} \\| Last scanned: {scanned}\n"
        )
    return "\n".join(lines)


# ── Indexing ──────────────────────────────────────────────────────────────────

REINDEX_STARTED = """
🔄 *Re\\-indexing started\\!*

Scanning all drive sources\\.\\.\\. This may take a few minutes\\.
You'll be notified when complete\\.
"""

def reindex_complete_text(stats: dict) -> str:
    return (
        f"✅ *Re\\-indexing Complete\\!*\n\n"
        f"📁 Scanned: *{stats.get('scanned', 0)}* files\n"
        f"➕ Added: *{stats.get('added', 0)}*\n"
        f"🗑️ Removed: *{stats.get('removed', 0)}*\n"
        f"✏️ Updated: *{stats.get('updated', 0)}*\n\n"
        f"Search cache has been refreshed\\."
    )


# ── Errors ────────────────────────────────────────────────────────────────────

ERROR_GENERIC = "❌ *Something went wrong\\.* Please try again later\\."
ERROR_NOT_REGISTERED = "⚠️ Please use /start to register first\\."
ERROR_ADMIN_ONLY = "🔒 *This command is for admins only\\.*"
ERROR_BANNED = "🚫 *You have been banned from using this bot\\.*"
ERROR_RATE_LIMIT = "⏱️ *Slow down\\!* You're searching too fast\\. Please wait a moment\\."
