from __future__ import annotations

"""Devin API client wrapper."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx

from ..config import DevinConfig

logger = logging.getLogger(__name__)


@dataclass
class DevinSession:
    session_id: str
    url: str
    status: str
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    pull_request_url: Optional[str] = None
    structured_output: Optional[dict] = None
    status_detail: Optional[str] = None


class DevinClient:
    """Wrapper for the Devin REST API."""

    def __init__(self, config: DevinConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        # v3 API uses org-scoped URLs
        base = config.base_url.rstrip("/")
        if config.org_id and "/v3/" not in base:
            self.base_url = f"https://api.devin.ai/v3/organizations/{config.org_id}"
        else:
            self.base_url = base

    async def create_session(
        self,
        prompt: str,
        title: Optional[str] = None,
        tags: Optional[list[str]] = None,
        playbook_id: Optional[str] = None,
        idempotent: bool = False,
        max_acu_limit: Optional[int] = None,
        structured_output_schema: Optional[dict] = None,
    ) -> DevinSession:
        """Create a new Devin session."""
        payload = {"prompt": prompt}
        if title:
            payload["title"] = title
        if tags:
            payload["tags"] = tags
        if playbook_id:
            payload["playbook_id"] = playbook_id
        if idempotent:
            payload["idempotent"] = True
        if max_acu_limit:
            payload["max_acu_limit"] = max_acu_limit
        if structured_output_schema:
            payload["structured_output_schema"] = structured_output_schema

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/sessions",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            session = DevinSession(
                session_id=data["session_id"],
                url=data.get("url", f"https://app.devin.ai/sessions/{data['session_id']}"),
                status=data.get("status", "running"),
            )
            logger.info(f"Created Devin session: {session.session_id} — {session.url}")
            return session

    async def get_session(self, session_id: str) -> DevinSession:
        """Get current status of a Devin session (v3 API compatible)."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{self.base_url}/sessions/{session_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()

            # v3: pull_requests is an array of {pr_url, pr_state}
            # v1: pull_request_url is a string
            pr_url = None
            pull_requests = data.get("pull_requests")
            if pull_requests and len(pull_requests) > 0:
                pr_url = pull_requests[0].get("pr_url")
            if not pr_url:
                pr_url = data.get("pull_request_url")

            return DevinSession(
                session_id=session_id,
                url=data.get("url", ""),
                status=data.get("status_enum", data.get("status", "unknown")),
                title=data.get("title"),
                pull_request_url=pr_url,
                structured_output=data.get("structured_output"),
                status_detail=data.get("status_detail"),
            )

    async def send_message(self, session_id: str, message: str) -> bool:
        """Send a follow-up message to a Devin session."""
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/sessions/{session_id}/message",
                    headers=self.headers,
                    json={"message": message},
                )
                resp.raise_for_status()
                logger.info(f"Sent message to session {session_id}")
                return True
            except httpx.HTTPError as e:
                logger.error(f"Failed to message session {session_id}: {e}")
                return False

    async def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DevinSession]:
        """List Devin sessions."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{self.base_url}/sessions",
                headers=self.headers,
                params={"limit": limit, "offset": offset},
            )
            resp.raise_for_status()
            data = resp.json()

            sessions = []
            for s in data.get("items", data.get("sessions", [])):
                # v3: pull_requests array
                pr_url = None
                prs = s.get("pull_requests")
                if prs and len(prs) > 0:
                    pr_url = prs[0].get("pr_url")
                if not pr_url:
                    pr_url = s.get("pull_request_url")

                sessions.append(DevinSession(
                    session_id=s["session_id"],
                    url=s.get("url", ""),
                    status=s.get("status_enum", s.get("status", "unknown")),
                    title=s.get("title"),
                    pull_request_url=pr_url,
                    status_detail=s.get("status_detail"),
                ))
            return sessions

    async def is_healthy(self) -> bool:
        """Check API connectivity."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"{self.base_url}/sessions",
                    headers=self.headers,
                    params={"limit": 1},
                )
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Devin API health check failed: {e}")
            return False
