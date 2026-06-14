"""
CA Vault Bot - Main Entry Point
Initializes the database, Redis, search engine, scheduler, and runs the bot.
"""
from __future__ import annotations

import asyncio
import sys

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass  # uvloop not available on Windows

from config.settings import settings
from utils.logger import setup_logging, get_logger
from database.engine import init_database, close_database
from cache.redis_client import get_cache, close_redis
from search.engine import get_search_engine
from indexer.scheduler import start_scheduler, stop_scheduler
from indexer.engine import get_indexing_engine
from database.repositories import CategoryRepository
from database.engine import get_session
from bot.application import create_application

# Setup logging first
setup_logging(level=settings.log_level, fmt=settings.log_format)
logger = get_logger(__name__)


async def startup() -> None:
    """Initialize all services before the bot starts."""
    logger.info("=" * 60)
    logger.info("CA Vault Bot — Starting up")
    logger.info("=" * 60)

    # Database
    logger.info("Initializing database...")
    await init_database()

    # Seed default categories
    logger.info("Seeding default categories...")
    async with get_session() as session:
        cat_repo = CategoryRepository(session)
        await cat_repo.ensure_defaults()

    # Redis ping
    logger.info("Connecting to Redis...")
    try:
        cache = await get_cache()
        redis = cache.redis
        await redis.ping()
        logger.info("Redis connection successful.")
    except Exception as e:
        logger.warning(f"Redis not available: {e}. Caching will be degraded.")

    # Pre-load search engine
    logger.info("Loading search index...")
    try:
        engine = get_search_engine()
        await engine._ensure_cache()
        logger.info(f"Search index loaded: {len(engine._file_cache)} files.")
    except Exception as e:
        logger.warning(f"Search cache pre-load failed: {e}")

    # Start background scheduler
    logger.info("Starting background scheduler...")
    start_scheduler()

    # Run initial index if no files are indexed yet
    try:
        engine = get_search_engine()
        if not engine._file_cache:
            logger.info("No files indexed. Starting initial index run...")
            indexer = get_indexing_engine()
            asyncio.create_task(indexer.run_full_index())
    except Exception as e:
        logger.warning(f"Initial index check failed: {e}")

    logger.info("Startup complete. Bot is ready!")


async def shutdown() -> None:
    """Cleanup resources on shutdown."""
    logger.info("Shutting down CA Vault Bot...")
    stop_scheduler()
    await close_database()
    await close_redis()
    logger.info("Shutdown complete.")


async def run_bot() -> None:
    """Main bot run loop."""
    await startup()

    app = create_application()

    async with app:
        await app.start()
        logger.info("Bot started. Polling for updates...")
        await app.updater.start_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )

        # Wait for stop signal
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            await app.updater.stop()
            await app.stop()

    await shutdown()


def main() -> None:
    """Entry point."""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
