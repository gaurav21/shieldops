"""
ShieldOps Task Types — Extended beyond security vulnerabilities.

Supports: security fixes, framework migrations, test coverage gaps,
and cloud infrastructure migrations.
"""

from enum import Enum


class TaskType(str, Enum):
    SECURITY = "security"
    MIGRATION = "migration"
    COVERAGE = "coverage"
    CLOUD_MIGRATION = "cloud_migration"

    @property
    def label(self) -> str:
        """Human-readable label for dashboard display."""
        return {
            "security": "🛡️ Security Fix",
            "migration": "🔄 Framework Migration",
            "coverage": "🧪 Test Coverage",
            "cloud_migration": "☁️ Cloud Migration",
        }[self.value]

    @property
    def github_label(self) -> str:
        """GitHub issue label for this task type."""
        return {
            "security": "shieldops-security",
            "migration": "shieldops-migration",
            "coverage": "shieldops-coverage",
            "cloud_migration": "shieldops-cloud-migration",
        }[self.value]
