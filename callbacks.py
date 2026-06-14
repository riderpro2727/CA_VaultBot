"""
CA Vault Bot - Callback Query Handler
Central dispatcher for all inline keyboard callbacks.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

from bot.keyboards import (
    main_menu_keyboard, categories_keyboard, search_results_keyboard,
    category_results_keyboard, file_detail_keyboard, favorites_keyboard,
    history_keyboard, back_to_menu_keyboard, cancel_keyboard,
    admin_menu_keyboard, drive_list_keyboard, drive_action_keyboard,
    confirm_keyboard
)
from bot.messages import (
    main_menu_text, CATEGORIES_HEADER, search_results_header,
    NO_RESULTS_MESSAGE, category_results_header, file_detail_text,
    favorites_header, NO_FAVORITES, history_text, HISTORY_CLEARED,
    HELP_TEXT, user_dashboard_text, admin_dashboard_text,
    drives_list_text, ERROR_NOT_REGISTERED, ERROR_ADMIN_ONLY,
    ERROR_GENERIC, SEARCH_PROMPT, ERROR_RATE_LIMIT
)
from services.user_service import get_user_service
from services.drive_service import get_drive_service
from services.search_service import get_search_service
from middlewares.rate_limiter import check_rate_limit, check_download_limit
from utils.helpers import sanitize_query, get_page_info
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


async def _safe_edit(query, text: str, reply_markup=None, parse_mode=ParseMode.MARKDOWN_V2):
    """Edit message text safely, ignoring 'message not modified' errors."""
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main callback dispatcher."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data or ""
    telegram_id = update.effective_user.id

    # Quick guard for noop
    if data == "noop":
        return

    try:
        # ── Menu Navigation ───────────────────────────────────────────────────
        if data.startswith("menu:"):
            await handle_menu(query, context, data, telegram_id)

        # ── Search Pagination ─────────────────────────────────────────────────
        elif data.startswith("search:page:"):
            await handle_search_page(query, context, data, telegram_id)

        # ── Category Browse ───────────────────────────────────────────────────
        elif data.startswith("cat:"):
            await handle_category(query, context, data, telegram_id)

        # ── File Actions ──────────────────────────────────────────────────────
        elif data.startswith("file:"):
            await handle_file_action(query, context, data, telegram_id)

        # ── Favorites Pagination ──────────────────────────────────────────────
        elif data.startswith("fav:"):
            await handle_favorites_page(query, context, data, telegram_id)

        # ── History Actions ───────────────────────────────────────────────────
        elif data.startswith("history:"):
            await handle_history_action(query, context, data, telegram_id)

        # ── Admin Actions ─────────────────────────────────────────────────────
        elif data.startswith("admin:"):
            await handle_admin_action(query, context, data, telegram_id)

        # ── Confirmation ──────────────────────────────────────────────────────
        elif data.startswith("confirm:"):
            await handle_confirm(query, context, data, telegram_id)

    except Exception as e:
        logger.error(f"Callback error for data={data!r}: {e}", exc_info=True)
        try:
            await query.answer("❌ An error occurred. Please try again.", show_alert=True)
        except Exception:
            pass


# ── Menu Handlers ─────────────────────────────────────────────────────────────

async def handle_menu(query, context, data: str, telegram_id: int) -> None:
    action = data.split(":", 1)[1]

    if action == "main":
        user_service = get_user_service()
        db_user = await user_service.get_user(telegram_id)
        name = db_user.name if db_user else "User"
        await _safe_edit(
            query,
            main_menu_text(name),
            reply_markup=main_menu_keyboard(),
        )

    elif action == "search":
        await _safe_edit(
            query,
            SEARCH_PROMPT,
            reply_markup=cancel_keyboard("menu:main"),
        )
        context.user_data["awaiting_search"] = True

    elif action == "categories":
        await _safe_edit(
            query,
            CATEGORIES_HEADER,
            reply_markup=categories_keyboard(),
        )

    elif action == "favorites":
        await show_favorites(query, context, telegram_id, page=1)

    elif action == "history":
        await show_history(query, context, telegram_id)

    elif action == "dashboard":
        user_service = get_user_service()
        data_dict = await user_service.get_dashboard_data(telegram_id)
        if not data_dict:
            await _safe_edit(query, ERROR_NOT_REGISTERED)
            return
        await _safe_edit(
            query,
            user_dashboard_text(data_dict),
            reply_markup=back_to_menu_keyboard(),
        )

    elif action == "help":
        await _safe_edit(
            query,
            HELP_TEXT,
            reply_markup=back_to_menu_keyboard(),
        )


# ── Search Pagination ─────────────────────────────────────────────────────────

async def handle_search_page(query, context, data: str, telegram_id: int) -> None:
    """Handle search result page navigation: search:page:{page}:{query}:{?cat}"""
    parts = data.split(":", 3)
    if len(parts) < 4:
        return

    page = int(parts[2])
    rest = parts[3]  # query[:cat] or just query

    # Extract optional category
    category_filter = None
    if ":" in rest:
        query_str, category_filter = rest.rsplit(":", 1)
    else:
        query_str = rest

    query_str = sanitize_query(query_str)
    per_page = settings.search_results_per_page

    # Rate limit
    allowed = await check_rate_limit(telegram_id, "search")
    if not allowed:
        await query.answer(ERROR_RATE_LIMIT.replace("\\", ""), show_alert=True)
        return

    search_service = get_search_service()
    results, total = await search_service.search(
        telegram_id=telegram_id,
        query=query_str,
        category_filter=category_filter,
        page=page,
        per_page=per_page,
    )

    if not results:
        await _safe_edit(query, NO_RESULTS_MESSAGE, reply_markup=back_to_menu_keyboard())
        return

    page_info = get_page_info(page, total, per_page)
    text = search_results_header(query_str, total, page, page_info["total_pages"])

    await _safe_edit(
        query,
        text,
        reply_markup=search_results_keyboard(results, page, total, per_page, query_str, category_filter),
    )


# ── Category Handlers ─────────────────────────────────────────────────────────

async def handle_category(query, context, data: str, telegram_id: int) -> None:
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "page":
        # cat:page:{category}:{page}
        if len(parts) >= 4:
            category = parts[2]
            page = int(parts[3])
            await show_category_results(query, context, telegram_id, category, page)
    else:
        # cat:{category_key}
        category = action
        await show_category_results(query, context, telegram_id, category, page=1)


async def show_category_results(query, context, telegram_id: int, category: str, page: int) -> None:
    from utils.file_utils import get_category_display
    search_service = get_search_service()
    per_page = settings.search_results_per_page

    results, total = await search_service.search_by_category(category, page=page, per_page=per_page)
    category_display = get_category_display(category).replace("_", " ").strip()

    if not results:
        await _safe_edit(
            query,
            f"📚 *{category_display}*\n\nNo resources found in this category\\.",
            reply_markup=categories_keyboard(),
        )
        return

    page_info = get_page_info(page, total, per_page)
    text = category_results_header(category_display, total, page, page_info["total_pages"])

    await _safe_edit(
        query,
        text,
        reply_markup=category_results_keyboard(results, page, total, per_page, category),
    )


# ── File Action Handlers ──────────────────────────────────────────────────────

async def handle_file_action(query, context, data: str, telegram_id: int) -> None:
    parts = data.split(":", 2)
    if len(parts) < 3:
        return

    action = parts[1]
    file_id = parts[2]

    drive_service = get_drive_service()

    if action == "view":
        await show_file_detail(query, context, telegram_id, file_id)

    elif action == "download":
        await handle_download(query, context, telegram_id, file_id)

    elif action == "fav":
        file = await drive_service.get_file(file_id)
        if not file:
            await query.answer("File not found!", show_alert=True)
            return

        is_fav = await drive_service.is_favorite(telegram_id, file_id)
        if is_fav:
            success, msg = await drive_service.remove_favorite(telegram_id, file_id)
        else:
            success, msg = await drive_service.add_favorite(telegram_id, file_id)

        await query.answer(msg.replace("\\", ""), show_alert=False)

        # Refresh the file view
        await show_file_detail(query, context, telegram_id, file_id)


async def show_file_detail(query, context, telegram_id: int, file_id: str) -> None:
    """Show detailed file view."""
    drive_service = get_drive_service()
    file = await drive_service.get_file(file_id)

    if not file:
        await query.answer("⚠️ File not found or removed.", show_alert=True)
        return

    # Track click
    await drive_service.record_file_click(file_id)

    is_fav = await drive_service.is_favorite(telegram_id, file_id)
    text = file_detail_text(file, is_fav)

    await _safe_edit(
        query,
        text,
        reply_markup=file_detail_keyboard(file, is_fav),
    )


async def handle_download(query, context, telegram_id: int, file_id: str) -> None:
    """Handle file download request."""
    allowed = await check_download_limit(telegram_id)
    if not allowed:
        await query.answer(
            "⏱️ Download limit reached. Please wait before downloading more.",
            show_alert=True
        )
        return

    drive_service = get_drive_service()
    file = await drive_service.get_file(file_id)
    if not file:
        await query.answer("File not found!", show_alert=True)
        return

    # Check size
    file_size = file.file_size or 0
    max_size = settings.telegram_max_file_size

    if file_size > max_size:
        # Too large — send drive link
        await query.answer(
            f"📦 File too large ({round(file_size/1024/1024, 1)} MB). Opening Drive link...",
            show_alert=True
        )
        return

    # Try to download and send
    await query.answer("📥 Preparing download...", show_alert=False)

    try:
        file_bytes = await drive_service.try_direct_download(file)
        if file_bytes:
            chat_id = query.message.chat_id
            await query.message.reply_document(
                document=file_bytes,
                filename=file.file_name,
                caption=f"📄 *{file.file_name[:100]}*\n\n📦 {round(len(file_bytes)/1024/1024, 2)} MB",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            await drive_service.record_file_download(file_id)
            user_service = get_user_service()
            await user_service.increment_download_count(telegram_id)
        else:
            await query.answer(
                "Could not download. Use the Drive Link button instead.",
                show_alert=True
            )
    except Exception as e:
        logger.error(f"Download error for {file_id}: {e}")
        await query.answer(
            "Download failed. Use the Drive Link button instead.",
            show_alert=True
        )


# ── Favorites Pagination ──────────────────────────────────────────────────────

async def handle_favorites_page(query, context, data: str, telegram_id: int) -> None:
    parts = data.split(":")
    if parts[1] == "page" and len(parts) >= 3:
        page = int(parts[2])
    else:
        page = 1
    await show_favorites(query, context, telegram_id, page)


async def show_favorites(query, context, telegram_id: int, page: int) -> None:
    drive_service = get_drive_service()
    per_page = settings.search_results_per_page

    files, total = await drive_service.get_favorites(telegram_id, page=page, per_page=per_page)

    if not files:
        await _safe_edit(
            query,
            NO_FAVORITES,
            reply_markup=back_to_menu_keyboard(),
        )
        return

    page_info = get_page_info(page, total, per_page)
    text = favorites_header(total, page, page_info["total_pages"])

    await _safe_edit(
        query,
        text,
        reply_markup=favorites_keyboard(files, page, total, per_page),
    )


# ── History Handlers ──────────────────────────────────────────────────────────

async def handle_history_action(query, context, data: str, telegram_id: int) -> None:
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "clear":
        await _safe_edit(
            query,
            "⚠️ *Clear Search History*\n\nAre you sure you want to clear all your search history?",
            reply_markup=confirm_keyboard("clear_history"),
        )
    else:
        await show_history(query, context, telegram_id)


async def show_history(query, context, telegram_id: int) -> None:
    search_service = get_search_service()
    history = await search_service.get_history(telegram_id, limit=20)
    text = history_text(history)
    await _safe_edit(
        query,
        text,
        reply_markup=history_keyboard(bool(history)),
    )


# ── Confirm Handlers ──────────────────────────────────────────────────────────

async def handle_confirm(query, context, data: str, telegram_id: int) -> None:
    parts = data.split(":", 1)
    action = parts[1] if len(parts) > 1 else ""

    if action == "clear_history":
        search_service = get_search_service()
        deleted = await search_service.clear_history(telegram_id)
        await _safe_edit(
            query,
            f"✅ *Cleared {deleted} search history entries\\.*",
            reply_markup=back_to_menu_keyboard(),
        )


# ── Admin Action Handlers ─────────────────────────────────────────────────────

async def handle_admin_action(query, context, data: str, telegram_id: int) -> None:
    user_service = get_user_service()
    if not await user_service.is_admin(telegram_id):
        await query.answer("🔒 Admin only!", show_alert=True)
        return

    parts = data.split(":", 2)
    action = parts[1] if len(parts) > 1 else ""
    param = parts[2] if len(parts) > 2 else ""

    if action == "menu":
        await _safe_edit(
            query,
            "🛡️ *CA Vault Admin Panel*\n\nSelect an option:",
            reply_markup=admin_menu_keyboard(),
        )

    elif action == "dashboard":
        stats = await user_service.get_admin_stats()
        await _safe_edit(
            query,
            admin_dashboard_text(stats),
            reply_markup=admin_menu_keyboard(),
        )

    elif action == "drives":
        drive_service = get_drive_service()
        drives = await drive_service.list_drives()
        await _safe_edit(
            query,
            drives_list_text(drives),
            reply_markup=drive_list_keyboard(drives),
        )

    elif action == "drive_info":
        drive_service = get_drive_service()
        drives = await drive_service.list_drives()
        drive = next((d for d in drives if d.drive_id == param), None)
        if not drive:
            await query.answer("Drive not found!", show_alert=True)
            return
        info = (
            f"💾 *Drive Info*\n\n"
            f"*Name:* {str(drive.name).replace('_', chr(92)+'_').replace('*', chr(92)+'*')}\n"
            f"*ID:* `{drive.drive_id}`\n"
            f"*Files:* {drive.total_files}\n"
            f"*Status:* {'✅ Active' if drive.is_active else '❌ Inactive'}\n"
            f"*Shared Drive:* {'Yes' if drive.is_shared_drive else 'No'}"
        )
        await _safe_edit(
            query,
            info,
            reply_markup=drive_action_keyboard(drive.drive_id),
        )

    elif action == "reindex":
        await _safe_edit(
            query,
            "🔄 *Re\\-indexing all drives\\.\\.\\.*\n\nThis may take a few minutes\\.",
            reply_markup=back_to_menu_keyboard(),
        )
        asyncio.create_task(_run_reindex_and_notify(
            telegram_id,
            query.message.chat_id,
            context,
        ))

    elif action == "index_drive":
        await query.answer(f"🔄 Indexing drive {param[:20]}...", show_alert=True)
        asyncio.create_task(_run_reindex_and_notify(
            telegram_id,
            query.message.chat_id,
            context,
            specific_drive_id=param,
        ))

    elif action == "remove_drive":
        await _safe_edit(
            query,
            f"⚠️ *Remove Drive*\n\nAre you sure you want to remove drive `{param}`?",
            reply_markup=confirm_keyboard(f"remove_drive:{param}"),
        )

    elif action == "add_drive":
        context.user_data["admin_action"] = "awaiting_drive_id"
        await _safe_edit(
            query,
            "➕ *Add New Drive*\n\nPlease send the Google Drive folder ID:\n\n"
            "Format: `/adddrive FOLDER_ID [Name]`\n\n"
            "Example: `/adddrive 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs7 CA Final Notes`",
            reply_markup=cancel_keyboard("admin:drives"),
        )

    elif action == "users":
        stats = await user_service.get_admin_stats()
        top_users = stats.get("top_users", [])
        lines = ["👥 *Top Active Users*\n"]
        for i, u in enumerate(top_users[:10], 1):
            uname = (u.username or "N/A")
            safe_name = str(u.name).replace("_", "\\_").replace("*", "\\*")
            lines.append(
                f"{i}\\. *{safe_name}* \\(@{uname}\\)\n"
                f"   Searches: {u.search_count} \\| Score: {int(u.activity_score)}"
            )
        await _safe_edit(
            query,
            "\n".join(lines) if len(lines) > 1 else "👥 *No users yet*",
            reply_markup=admin_menu_keyboard(),
        )

    elif action == "analytics":
        stats = await user_service.get_admin_stats()
        cat_stats = stats.get("category_stats", [])
        lines = ["📈 *Category Analytics*\n"]
        for cs in cat_stats[:10]:
            from utils.file_utils import get_category_display
            cat_name = get_category_display(cs["category"])
            lines.append(f"  {cat_name}: *{cs['count']}* files")
        await _safe_edit(
            query,
            "\n".join(lines) if len(lines) > 1 else "📈 *No analytics yet*",
            reply_markup=admin_menu_keyboard(),
        )

    elif action == "deadlinks":
        from database.engine import get_session
        from database.repositories import DriveFileRepository
        async with get_session() as session:
            file_repo = DriveFileRepository(session)
            dead = await file_repo.get_dead_links()
        if not dead:
            await query.answer("✅ No dead links found!", show_alert=True)
            return
        lines = [f"🔗 *Dead Links \\({len(dead)}\\)*\n"]
        for f in dead[:10]:
            safe_name = str(f.file_name[:40]).replace("_", "\\_").replace("*", "\\*").replace(".", "\\.").replace("(", "\\(").replace(")", "\\)").replace("-", "\\-").replace("!", "\\!")
            lines.append(f"• {safe_name}")
        await _safe_edit(
            query,
            "\n".join(lines),
            reply_markup=admin_menu_keyboard(),
        )


async def _run_reindex_and_notify(
    telegram_id: int,
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    specific_drive_id: Optional[str] = None,
) -> None:
    """Run reindex in background and notify admin when done."""
    from indexer.engine import get_indexing_engine
    from bot.messages import reindex_complete_text, REINDEX_STARTED

    try:
        engine = get_indexing_engine()
        stats = await engine.run_full_index(
            triggered_by=telegram_id,
            specific_drive_id=specific_drive_id,
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=reindex_complete_text(stats),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        # Refresh search engine cache
        from search.engine import get_search_engine
        await get_search_engine().refresh_cache()
    except Exception as e:
        logger.error(f"Reindex notification failed: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ *Reindex failed:* `{str(e)[:200]}`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
