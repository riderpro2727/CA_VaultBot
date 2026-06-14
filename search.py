"""
CA Vault Bot - Search Handlers
Handles search queries, pagination, and file viewing.
"""
from __future__ import annotations

from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CommandHandler, filters
)
from telegram.constants import ParseMode

from bot.keyboards import (
    search_results_keyboard, file_detail_keyboard,
    cancel_keyboard, back_to_menu_keyboard
)
from bot.messages import (
    SEARCH_PROMPT, search_results_header, NO_RESULTS_MESSAGE,
    file_detail_text, ERROR_RATE_LIMIT, ERROR_NOT_REGISTERED
)
from services.search_service import get_search_service
from services.drive_service import get_drive_service
from services.user_service import get_user_service
from middlewares.rate_limiter import check_rate_limit
from utils.helpers import sanitize_query, get_page_info
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

AWAITING_SEARCH = 10


async def search_prompt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the search input prompt."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            SEARCH_PROMPT,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=cancel_keyboard("menu:main"),
        )
    else:
        await update.message.reply_text(
            SEARCH_PROMPT,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=cancel_keyboard("menu:main"),
        )
    return AWAITING_SEARCH


async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the search query entered by the user."""
    if not update.message or not update.message.text:
        return AWAITING_SEARCH

    telegram_id = update.effective_user.id
    raw_query = update.message.text.strip()

    # Validate user
    user_service = get_user_service()
    if not await user_service.is_registered(telegram_id):
        await update.message.reply_text(
            ERROR_NOT_REGISTERED, parse_mode=ParseMode.MARKDOWN_V2
        )
        return ConversationHandler.END

    # Rate limit
    allowed = await check_rate_limit(telegram_id, "search")
    if not allowed:
        await update.message.reply_text(
            ERROR_RATE_LIMIT, parse_mode=ParseMode.MARKDOWN_V2
        )
        return AWAITING_SEARCH

    query = sanitize_query(raw_query)
    if not query or len(query) < 2:
        await update.message.reply_text(
            "⚠️ Search query too short\\. Please enter at least 2 characters\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return AWAITING_SEARCH

    # Store in context
    context.user_data["last_search"] = query
    context.user_data["search_page"] = 1

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
        return ConversationHandler.END

    page_info = get_page_info(1, total, per_page)
    text = search_results_header(query, total, 1, page_info["total_pages"])

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=search_results_keyboard(results, 1, total, per_page, query),
    )
    return ConversationHandler.END


def get_search_conversation_handler() -> ConversationHandler:
    """Build the search conversation handler."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^/search$"), search_prompt_handler),
        ],
        states={
            AWAITING_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", lambda u, c: ConversationHandler.END),
        ],
        allow_reentry=True,
        name="search_conversation",
        persistent=False,
    )
