from __future__ import annotations

"""Persistent state store for the /status endpoint.

This is the always-works observability surface — it shows live counts
even without Datadog. Engineering leaders check /status to see if
ShieldOps is doing its job.

State is persisted to data/state.json so sessions survive server restarts.
"""

import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("shieldops.state")


class State:
    """Thread-safe persistent state for the ShieldOps event-driven orchestrator."""

    STATE_FILE = "data/state.json"

    def __init__(self):
        self._lock = threading.Lock()
        self._last_save: float = 0
        self.sessions: dict[str, dict[str, Any]] = {}  # issue_key -> session info
        self.events: list[dict[str, Any]] = []  # append-only audit log
        self.counters: dict[str, int] = {
            "active": 0,
            "completed": 0,
            "blocked": 0,
            "failed": 0,
            "auto_merge": 0,
            "human_review": 0,
        }
        self._load()

    def _load(self):
        """Load state from disk on startup."""
        try:
            path = Path(self.STATE_FILE)
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                self.sessions = data.get("sessions", {})
                self.events = data.get("events", [])[-500:]
                self.counters = {**self.counters, **data.get("counters", {})}
                # Recount active sessions (they may have changed while we were down)
                active = sum(1 for s in self.sessions.values() if s.get("status") == "running")
                self.counters["active"] = active
                logger.info(
                    f"Loaded persisted state: {len(self.sessions)} sessions, "
                    f"{len(self.events)} events, {active} active"
                )
        except Exception as e:
            logger.warning(f"Failed to load persisted state, starting fresh: {e}")

    def _save(self):
        """Save state to disk (debounced — max once per second)."""
        now = time.time()
        if now - self._last_save < 1.0:
            return
        try:
            path = Path(self.STATE_FILE)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump({
                    "sessions": self.sessions,
                    "events": self.events[-500:],
                    "counters": self.counters,
                    "saved_at": time.time(),
                }, f, default=str)
            self._last_save = now
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")

    def register_session(
        self,
        issue_key: str,
        session_id: str,
        session_url: str,
        triage: dict,
        issue: dict,
    ):
        """Register a new Devin session for an issue."""
        with self._lock:
            self.sessions[issue_key] = {
                "status": "running",
                "session_id": session_id,
                "session_url": session_url,
                "triage": triage,
                "issue": {
                    "number": issue.get("number"),
                    "title": issue.get("title"),
                },
                "started_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "policy_decision": None,
                "pr_url": None,
                "error": None,
            }
            self.counters["active"] += 1
            self._save()
        self.record_event(issue_key, "session_created", f"Session {session_id} launched")

    def update_session(self, issue_key: str, **kwargs):
        """Update fields on an existing session."""
        with self._lock:
            if issue_key in self.sessions:
                self.sessions[issue_key].update(kwargs)
                self._save()

    def complete_session(
        self,
        issue_key: str,
        policy_decision: Optional[str] = None,
        pr_url: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Mark a session as completed and update counters."""
        with self._lock:
            if issue_key not in self.sessions:
                return

            session = self.sessions[issue_key]
            session["completed_at"] = datetime.now(timezone.utc).isoformat()
            session["policy_decision"] = policy_decision
            session["pr_url"] = pr_url
            session["error"] = error

            self.counters["active"] = max(0, self.counters["active"] - 1)

            if error:
                session["status"] = "failed"
                self.counters["failed"] += 1
            elif policy_decision == "blocked":
                session["status"] = "blocked"
                self.counters["blocked"] += 1
            else:
                session["status"] = "completed"
                self.counters["completed"] += 1

            if policy_decision == "auto_merge_ready":
                self.counters["auto_merge"] += 1
            elif policy_decision == "human_review":
                self.counters["human_review"] += 1

            self._save()

        stage = "completed" if not error else "failed"
        detail = policy_decision or error or "done"
        self.record_event(issue_key, stage, detail)

    def record_event(self, issue_key: str, stage: str, detail: str):
        """Append an audit event."""
        with self._lock:
            self.events.append({
                "ts": datetime.now(timezone.utc).isoformat(),
                "issue": issue_key,
                "stage": stage,
                "detail": detail,
            })
            # Keep last 500 events to avoid unbounded growth
            if len(self.events) > 500:
                self.events = self.events[-500:]
            self._save()

    def get_running_sessions(self) -> dict[str, dict[str, Any]]:
        """Return sessions that were still running (for restart recovery)."""
        with self._lock:
            return {
                k: dict(v) for k, v in self.sessions.items()
                if v.get("status") == "running"
            }

    def has_session(self, issue_key: str) -> bool:
        """Check if an issue already has a session (dedup)."""
        with self._lock:
            return issue_key in self.sessions

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full state for /status."""
        with self._lock:
            return {
                "counters": dict(self.counters),
                "sessions": {
                    k: dict(v) for k, v in self.sessions.items()
                },
                "recent_events": list(self.events[-50:]),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
