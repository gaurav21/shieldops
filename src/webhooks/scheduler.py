from __future__ import annotations

"""Scheduled scan trigger — runs vulnerability scans on a cron schedule."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ScanScheduler:
    """Simple async scheduler for periodic vulnerability scans."""

    def __init__(self, orchestrator, interval_hours: float = 24):
        self.orchestrator = orchestrator
        self.interval_seconds = interval_hours * 3600
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def start(self):
        """Start the scheduler in the background."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Scan scheduler started — interval: {self.interval_seconds/3600:.1f}h")

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Scan scheduler stopped")

    async def _run(self):
        """Main scheduler loop."""
        # Run first scan immediately
        await self._execute_scan()

        while self._running:
            try:
                await asyncio.sleep(self.interval_seconds)
                if self._running:
                    await self._execute_scan()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)  # Wait before retry

    async def _execute_scan(self):
        """Execute a full scan → triage → remediate cycle."""
        logger.info(f"Starting scheduled scan at {datetime.utcnow().isoformat()}")
        try:
            await self.orchestrator.run_full_pipeline()
        except Exception:
            logger.exception("Scheduled scan failed")

    async def trigger_manual_scan(self):
        """Trigger an immediate scan (for API endpoint)."""
        logger.info("Manual scan triggered")
        await self._execute_scan()
