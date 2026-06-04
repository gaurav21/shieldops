from __future__ import annotations

"""Shared constants used across the ShieldOps codebase."""


# Emoji mapping for policy decisions — used in evidence bundles, events, and reports.
# Keys are the string values of PolicyDecision (a str enum), so lookups like
# ``POLICY_DECISION_EMOJI.get(policy.decision)`` work transparently.
POLICY_DECISION_EMOJI: dict[str, str] = {
    "auto_merge_ready": "🟢",
    "human_review": "🟡",
    "blocked": "🔴",
}

# Paths that always require human review — auth, SQL, crypto, user-facing views.
# Shared between the triage engine (pre-routing) and policy engine (post-evaluation).
SENSITIVE_PATHS: list[str] = [
    "superset/sql_lab.py",
    "superset/views/",
    "superset/security/",
    "superset/db_engine_specs/",
    "superset/connectors/",
    "superset/models/core.py",
]
