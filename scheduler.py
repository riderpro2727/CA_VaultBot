"""
CA Vault Bot - Background Scheduler
Manages periodic indexing jobs using APScheduler.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import settings
from indexer.engine import get_indexing_engine
from utils.logger import get_logger

logger = get_logger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


async def _periodic_index_job():
    """Background task: run full index on schedule."""
    logger.info("Scheduled index run starting...")
    engine = get_indexing_engine()
    result = await engine.run_full_index()
    logger.info(f"Scheduled index run result: {result}")


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
        _scheduler.add_job(
            _periodic_index_job,
            trigger=IntervalTrigger(minutes=settings.index_scan_interval_minutes),
            id="periodic_index",
            name="Periodic Drive Index",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
        )
    return _scheduler


def start_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info(
            f"Scheduler started. Index interval: {settings.index_scan_interval_minutes} minutes."
        )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
