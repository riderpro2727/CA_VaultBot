"""
CA Vault Bot - Application Builder
Registers all handlers with the PTB application.
"""
from __future__ import annotations

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config.settings import settings
from handlers import (
    get_start_conversation_handler,
    handle_callback,
    admin_panel_command,
    add_drive_command,
    remove_drive_command,
    list_drives_command,
    reindex_command,
    stats_command,
    broadcast_command,
    handle_text_message,
)
from utils.logger import get_logger

logger = get_logger(__name__)


def create_application() -> Application:
    """Create and configure the PTB Application."""
    app = (
        Application.builder()
        .token(settings.bot_token)
        .concurrent_updates(True)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .get_updates_read_timeout(42)
        .build()
    )

    # ── Registration / Start ───────────────────────────────────────────────────
    app.add_handler(get_start_conversation_handler(), group=0)

    # ── Admin Commands ─────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("admin", admin_panel_command), group=1)
    app.add_handler(CommandHandler("adddrive", add_drive_command), group=1)
    app.add_handler(CommandHandler("removedrive", remove_drive_command), group=1)
    app.add_handler(CommandHandler("listdrives", list_drives_command), group=1)
    app.add_handler(CommandHandler("reindex", reindex_command), group=1)
    app.add_handler(CommandHandler("stats", stats_command), group=1)
    app.add_handler(CommandHandler("broadcast", broadcast_command), group=1)

    # ── Inline Callbacks ───────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(handle_callback), group=2)

    # ── General Text Messages ──────────────────────────────────────────────────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message),
        group=3,
    )

    logger.info("All handlers registered.")
    return app
