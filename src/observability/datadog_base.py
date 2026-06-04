from __future__ import annotations

"""Shared base class for all Datadog API clients.

Eliminates duplicated init, header setup, HTTP helpers, and metric-point
builders that were previously copy-pasted across metrics.py, events.py,
dashboard.py, and monitors.py.
"""

import logging
from typing import Optional

import httpx

from ..config import DatadogConfig

logger = logging.getLogger(__name__)


class DatadogBaseClient:
    """Base class providing common Datadog API plumbing.

    Subclasses get ``self.config``, ``self.base_url``, ``self.headers``,
    and a set of low-level HTTP + metric helpers for free.
    """

    def __init__(self, config: DatadogConfig, *, api_version: str = "v1",
                 needs_app_key: bool = False):
        self.config = config
        self.base_url = f"https://api.{config.site}/api/{api_version}"
        self.headers: dict[str, str] = {
            "DD-API-KEY": config.api_key,
            "Content-Type": "application/json",
        }
        if needs_app_key:
            self.headers["DD-APPLICATION-KEY"] = config.app_key

    # --- HTTP helpers ---

    async def _post(self, path: str, json: dict, *, timeout: int = 15) -> Optional[httpx.Response]:
        """POST to ``{base_url}/{path}`` with standard error handling."""
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{self.base_url}/{path}",
                                     headers=self.headers, json=json)
            return resp

    async def _get(self, path: str, *, timeout: int = 15,
                   params: Optional[dict] = None) -> Optional[httpx.Response]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{self.base_url}/{path}",
                                    headers=self.headers, params=params)
            return resp

    async def _put(self, path: str, json: dict, *, timeout: int = 30) -> Optional[httpx.Response]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.put(f"{self.base_url}/{path}",
                                    headers=self.headers, json=json)
            return resp

    # --- Metric-point builders ---

    @staticmethod
    def gauge_point(metric: str, value: float, timestamp: int,
                    tags: list[str]) -> dict:
        return {
            "metric": metric,
            "type": 3,
            "points": [{"timestamp": timestamp, "value": value}],
            "tags": tags,
        }

    @staticmethod
    def count_point(metric: str, value: float, timestamp: int,
                    tags: list[str]) -> dict:
        return {
            "metric": metric,
            "type": 1,
            "points": [{"timestamp": timestamp, "value": value}],
            "tags": tags,
        }

    # --- Common submission helpers ---

    async def submit_series(self, series: list[dict]) -> None:
        """Submit a batch of metric points to the Datadog series endpoint."""
        if not self.config.api_key:
            logger.debug("No DD API key — skipping metric submission")
            return
        try:
            resp = await self._post("series", json={"series": series}, timeout=10)
            if resp and resp.status_code not in (200, 202):
                logger.warning(f"Datadog metrics returned {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to submit metrics: {e}")

    async def send_event(self, title: str, text: str,
                         alert_type: str = "info",
                         tags: Optional[list[str]] = None) -> None:
        """Send a single event to Datadog."""
        if not self.config.api_key:
            logger.debug(f"No DD API key — event: {title}")
            return
        try:
            resp = await self._post("events", json={
                "title": title,
                "text": text,
                "alert_type": alert_type,
                "source_type_name": "shieldops",
                "tags": tags or [],
            }, timeout=10)
            if resp and resp.status_code in (200, 202):
                logger.debug(f"Event sent: {title}")
        except Exception as e:
            logger.error(f"Failed to send event: {e}")

    def has_keys(self, *, need_app_key: bool = False) -> bool:
        """Return True if the required API keys are configured."""
        if not self.config.api_key:
            return False
        if need_app_key and not self.config.app_key:
            return False
        return True
