from __future__ import annotations

"""ShieldOps Configuration."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DevinConfig:
    api_key: str = ""
    org_id: str = ""
    base_url: str = "https://api.devin.ai/v1"
    max_concurrent_sessions: int = 3
    session_timeout: int = 3600
    poll_interval: int = 15


@dataclass
class GitHubConfig:
    token: str = ""
    repo_owner: str = ""
    repo_name: str = ""
    webhook_secret: str = ""

    @property
    def repo_full_name(self) -> str:
        return f"{self.repo_owner}/{self.repo_name}"

    @property
    def repo_url(self) -> str:
        return f"https://github.com/{self.repo_full_name}"


@dataclass
class DatadogConfig:
    api_key: str = ""
    app_key: str = ""
    site: str = "datadoghq.com"
    metric_prefix: str = "shieldops"


@dataclass
class ScannerConfig:
    scan_types: list = field(default_factory=lambda: ["pip-audit", "npm-audit", "trivy", "semgrep"])
    schedule_cron: str = "0 2 * * *"


@dataclass
class Config:
    devin: DevinConfig = field(default_factory=DevinConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    datadog: DatadogConfig = field(default_factory=DatadogConfig)
    scanner: ScannerConfig = field(default_factory=ScannerConfig)
    port: int = 8000
    log_level: str = "INFO"
    # Event-driven trigger config
    trigger_label: str = "shieldops"
    poll_interval_seconds: int = 15
    session_timeout_seconds: int = 3600
    skip_signature_check: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            devin=DevinConfig(
                api_key=os.getenv("DEVIN_API_KEY", ""),
                org_id=os.getenv("DEVIN_ORG_ID", ""),
                max_concurrent_sessions=int(os.getenv("MAX_CONCURRENT_DEVIN_SESSIONS", "3")),
                session_timeout=int(os.getenv("DEVIN_SESSION_TIMEOUT", "3600")),
            ),
            github=GitHubConfig(
                token=os.getenv("GITHUB_TOKEN", ""),
                repo_owner=os.getenv("GITHUB_REPO_OWNER", "gaurav21"),
                repo_name=os.getenv("GITHUB_REPO_NAME", "superset"),
                webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET", ""),
            ),
            datadog=DatadogConfig(
                api_key=os.getenv("DD_API_KEY", ""),
                app_key=os.getenv("DD_APP_KEY", ""),
                site=os.getenv("DD_SITE", "datadoghq.com"),
            ),
            scanner=ScannerConfig(
                scan_types=os.getenv("SCAN_TYPES", "pip-audit,npm-audit,trivy,semgrep").split(","),
                schedule_cron=os.getenv("SCAN_SCHEDULE_CRON", "0 2 * * *"),
            ),
            port=int(os.getenv("SHIELDOPS_PORT", "8000")),
            log_level=os.getenv("SHIELDOPS_LOG_LEVEL", "INFO"),
            trigger_label=os.getenv("TRIGGER_LABEL", "shieldops"),
            poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "15")),
            session_timeout_seconds=int(os.getenv("SESSION_TIMEOUT_SECONDS", "3600")),
            skip_signature_check=os.getenv("SKIP_SIGNATURE_CHECK", "0") == "1",
        )
