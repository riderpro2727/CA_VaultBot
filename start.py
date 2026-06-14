"""
CA Vault Bot - Start & Registration Handlers
"""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler
from telegram.constants import ParseMode

from bot.keyboards import main_menu_keyboard, back_to_menu_keyboard
from bot.messages import (
    WELCOME_MESSAGE, WELCOME_BACK, REGISTRATION_SUCCESS,
    main_menu_text, ERROR_BANNED
)
from services.user_service import get_user_service
from utils.logger import get_logger

logger = get_logger(__name__)

# Conversation states
AWAITING_NAME = 1


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command — show welcome or main menu."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    telegram_id = user.id
    user_service = get_user_service()

    # Check if banned
    if await user_service.is_banned(telegram_id):
        await update.message.reply_text(ERROR_BANNED, parse_mode=ParseMode.MARKDOWN_V2)
        return ConversationHandler.END

    # Check if registered
    if await user_service.is_registered(telegram_id):
        db_user = await user_service.get_user(telegram_id)
        await user_service.update_last_active(telegram_id)

        name = db_user.name if db_user else user.first_name
        welcome_back = WELCOME_BACK.format(
            name=name.replace("_", r"\_").replace("*", r"\*").replace("[", r"\[").replace("]", r"\]")
        )
        await update.message.reply_text(
            welcome_back,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    # New user — ask for name
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    return AWAITING_NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's name input during registration."""
    if not update.message or not update.message.text:
        return AWAITING_NAME

    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text(
            "⚠️ Name must be at least 2 characters\\. Please enter your name:",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return AWAITING_NAME

    if len(name) > 100:
        name = name[:100]

    telegram_id = update.effective_user.id
    username = update.effective_user.username

    user_service = get_user_service()
    user = await user_service.complete_registration(telegram_id, name)

    safe_name = name.replace("_", r"\_").replace("*", r"\*").replace("[", r"\[").replace("]", r"\]")
    success_msg = REGISTRATION_SUCCESS.format(name=safe_name)

    await update.message.reply_text(
        success_msg,
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    # Show main menu
    await update.message.reply_text(
        main_menu_text(name),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel any ongoing conversation."""
    await update.message.reply_text(
        "❌ Cancelled\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=back_to_menu_keyboard(),
    )
    return ConversationHandler.END


def get_start_conversation_handler() -> ConversationHandler:
    """Build the registration conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            AWAITING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        allow_reentry=True,
        name="registration",
        persistent=False,
    )
