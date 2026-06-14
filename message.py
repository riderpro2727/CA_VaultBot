"""
CA Vault Bot - General Message Handler
Handles text messages outside conversations (search input, etc.)
"""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.keyboards import search_results_keyboard, back_to_menu_keyboard, cancel_keyboard
from bot.messages import (
    search_results_header, NO_RESULTS_MESSAGE,
    ERROR_NOT_REGISTERED, ERROR_RATE_LIMIT
)
from services.search_service import get_search_service
from services.user_service import get_user_service
from middlewares.rate_limiter import check_rate_limit
from utils.helpers import sanitize_query, get_page_info
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle plain text messages — treat as search queries if user
    has signaled intent to search.
    """
    if not update.message or not update.message.text:
        return

    telegram_id = update.effective_user.id
    text = update.message.text.strip()

    # Check if user is awaiting search input (set by callback handler)
    if not context.user_data.get("awaiting_search"):
        # No active search context — show main menu hint
        await update.message.reply_text(
            "💡 Use the menu buttons to navigate\\.\n\nPress /start to open the menu\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=back_to_menu_keyboard(),
        )
        return

    # Clear awaiting flag
    context.user_data.pop("awaiting_search", None)

    # Validate user
    user_service = get_user_service()
    if not await user_service.is_registered(telegram_id):
        await update.message.reply_text(ERROR_NOT_REGISTERED, parse_mode=ParseMode.MARKDOWN_V2)
        return

    # Rate limit
    allowed = await check_rate_limit(telegram_id, "search")
    if not allowed:
        await update.message.reply_text(ERROR_RATE_LIMIT, parse_mode=ParseMode.MARKDOWN_V2)
        return

    query = sanitize_query(text)
    if not query or len(query) < 2:
        await update.message.reply_text(
            "⚠️ Query too short\\. Please enter at least 2 characters\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=cancel_keyboard("menu:main"),
        )
        return

    # Searching indicator
    status_msg = await update.message.reply_text(
        f"🔍 Searching for *{query[:50]}*\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    search_service = get_search_service()
    per_page = settings.search_results_per_page

    results, total = await search_service.search(
        telegram_id=telegram_id,
        query=query,
        page=1,
        per_page=per_page,
    )

    await status_msg.delete()

    if not results:
        await update.message.reply_text(
            NO_RESULTS_MESSAGE,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=cancel_keyboard("menu:main"),
        )
        return

    page_info = get_page_info(1, total, per_page)
    header = search_results_header(query, total, 1, page_info["total_pages"])

    await update.message.reply_text(
        header,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=search_results_keyboard(results, 1, total, per_page, query),
    )
