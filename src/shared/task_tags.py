from __future__ import annotations

"""Shared tag-building utilities for RemediationTask."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..orchestrator.session_manager import RemediationTask


def build_task_tags(task: RemediationTask, include_triage: bool = False) -> list[str]:
    """Build Datadog tags from a RemediationTask.

    Args:
        task: The remediation task to extract tags from.
        include_triage: If True, also include triage-level tags
            (complexity, predicted_route).
    """
    tags = [
        f"severity:{task.vuln.severity.value}",
        f"type:{task.vuln.vuln_type.value}",
        f"package:{task.vuln.package_name}",
    ]
    if include_triage:
        tags.extend([
            f"complexity:{task.decision.estimated_complexity}",
            f"predicted_route:{task.decision.predicted_route}",
        ])
    return tags
