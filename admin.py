"""
CA Vault Bot - Admin Command Handlers
Handles /adddrive, /removedrive, /listdrives, /reindex, /admin, /broadcast
"""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.keyboards import admin_menu_keyboard, back_to_menu_keyboard
from bot.messages import (
    admin_dashboard_text, drives_list_text, REINDEX_STARTED,
    reindex_complete_text, ERROR_ADMIN_ONLY
)
from services.user_service import get_user_service
from services.drive_service import get_drive_service
from utils.helpers import is_valid_drive_id
from utils.logger import get_logger

logger = get_logger(__name__)


async def _check_admin(update: Update) -> bool:
    """Return True if the user is an admin."""
    telegram_id = update.effective_user.id
    user_service = get_user_service()
    if not await user_service.is_admin(telegram_id):
        await update.message.reply_text(
            ERROR_ADMIN_ONLY,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return False
    return True


async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/admin — Show admin panel."""
    if not await _check_admin(update):
        return

    telegram_id = update.effective_user.id
    user_service = get_user_service()
    stats = await user_service.get_admin_stats()

    await update.message.reply_text(
        admin_dashboard_text(stats),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=admin_menu_keyboard(),
    )


async def add_drive_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /adddrive <folder_id> [name] [--shared]
    Add a new Google Drive folder to index.
    """
    if not await _check_admin(update):
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "📌 *Usage:*\n`/adddrive FOLDER_ID [Name] [--shared]`\n\n"
            "• `FOLDER_ID` — Google Drive folder ID \\(required\\)\n"
            "• `Name` — Display name \\(optional\\)\n"
            "• `\\-\\-shared` — Flag for shared drives\n\n"
            "*Example:*\n`/adddrive 1BxiMVs0XRA5nFMdKvBdBZjgmUUq CA Final Notes`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    drive_id = args[0]
    if not is_valid_drive_id(drive_id):
        await update.message.reply_text(
            "❌ Invalid Drive ID format\\. Drive IDs are alphanumeric strings of 10\\+ characters\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    is_shared = "--shared" in args
    name_parts = [a for a in args[1:] if a != "--shared"]
    name = " ".join(name_parts) if name_parts else ""

    telegram_id = update.effective_user.id
    drive_service = get_drive_service()

    status_msg = await update.message.reply_text("⏳ Verifying drive access\\.\\.\\.", parse_mode=ParseMode.MARKDOWN_V2)

    source, error = await drive_service.add_drive(
        drive_id=drive_id,
        name=name,
        description=None,
        is_shared_drive=is_shared,
        added_by=telegram_id,
    )

    await status_msg.delete()

    if error:
        await update.message.reply_text(error, parse_mode=ParseMode.MARKDOWN_V2)
        return

    safe_name = str(source.name).replace("_", "\\_").replace("*", "\\*").replace(".", "\\.").replace("-", "\\-")
    await update.message.reply_text(
        f"✅ *Drive Added Successfully\\!*\n\n"
        f"*Name:* {safe_name}\n"
        f"*ID:* `{source.drive_id}`\n"
        f"*Shared Drive:* {'Yes' if source.is_shared_drive else 'No'}\n\n"
        f"Use `/reindex` to start indexing this drive\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=back_to_menu_keyboard(),
    )


async def remove_drive_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/removedrive <folder_id> — Remove a drive source."""
    if not await _check_admin(update):
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "📌 *Usage:*\n`/removedrive FOLDER_ID`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    drive_id = args[0]
    drive_service = get_drive_service()
    removed = await drive_service.remove_drive(drive_id)

    if removed:
        await update.message.reply_text(
            f"✅ Drive `{drive_id}` removed\\. Files remain indexed but won't be re\\-scanned\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        await update.message.reply_text(
            f"❌ Drive `{drive_id}` not found\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )


async def list_drives_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/listdrives — List all drive sources."""
    if not await _check_admin(update):
        return

    drive_service = get_drive_service()
    drives = await drive_service.list_drives()

    await update.message.reply_text(
        drives_list_text(drives),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def reindex_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/reindex [drive_id] — Trigger a full re-index."""
    if not await _check_admin(update):
        return

    telegram_id = update.effective_user.id
    specific_drive = context.args[0] if context.args else None

    await update.message.reply_text(
        REINDEX_STARTED,
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    import asyncio
    async def _do_reindex():
        from indexer.engine import get_indexing_engine
        from search.engine import get_search_engine
        engine = get_indexing_engine()
        stats = await engine.run_full_index(
            triggered_by=telegram_id,
            specific_drive_id=specific_drive,
        )
        await get_search_engine().refresh_cache()
        await update.message.reply_text(
            reindex_complete_text(stats),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    asyncio.create_task(_do_reindex())


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/stats — Show bot statistics."""
    if not await _check_admin(update):
        return

    user_service = get_user_service()
    stats = await user_service.get_admin_stats()

    await update.message.reply_text(
        admin_dashboard_text(stats),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=admin_menu_keyboard(),
    )


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/broadcast <message> — Send message to all users."""
    if not await _check_admin(update):
        return

    if not context.args:
        await update.message.reply_text(
            "📌 *Usage:*\n`/broadcast Your message here`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    message_text = " ".join(context.args)
    from database.engine import get_session
    from database.repositories import UserRepository

    async with get_session() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all(limit=10000)

    sent = 0
    failed = 0
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=f"📢 *Announcement*\n\n{message_text}",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📢 *Broadcast Complete*\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
