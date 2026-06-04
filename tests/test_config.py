"""Tests for src/config.py — configuration dataclasses and from_env loading."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.config import Config, DevinConfig, GitHubConfig, DatadogConfig, ScannerConfig


class TestDevinConfig:
    def test_defaults(self):
        cfg = DevinConfig()
        assert cfg.api_key == ""
        assert cfg.base_url == "https://api.devin.ai/v1"
        assert cfg.max_concurrent_sessions == 3
        assert cfg.session_timeout == 3600
        assert cfg.poll_interval == 15


class TestGitHubConfig:
    def test_repo_full_name(self):
        cfg = GitHubConfig(repo_owner="owner", repo_name="repo")
        assert cfg.repo_full_name == "owner/repo"

    def test_repo_url(self):
        cfg = GitHubConfig(repo_owner="owner", repo_name="repo")
        assert cfg.repo_url == "https://github.com/owner/repo"

    def test_defaults(self):
        cfg = GitHubConfig()
        assert cfg.token == ""
        assert cfg.webhook_secret == ""


class TestDatadogConfig:
    def test_defaults(self):
        cfg = DatadogConfig()
        assert cfg.site == "datadoghq.com"
        assert cfg.metric_prefix == "shieldops"
        assert cfg.api_key == ""
        assert cfg.app_key == ""


class TestScannerConfig:
    def test_defaults(self):
        cfg = ScannerConfig()
        assert cfg.scan_types == ["pip-audit", "npm-audit", "trivy", "semgrep"]
        assert cfg.schedule_cron == "0 2 * * *"


class TestConfig:
    def test_defaults(self):
        cfg = Config()
        assert cfg.port == 8000
        assert cfg.log_level == "INFO"
        assert isinstance(cfg.devin, DevinConfig)
        assert isinstance(cfg.github, GitHubConfig)
        assert isinstance(cfg.datadog, DatadogConfig)
        assert isinstance(cfg.scanner, ScannerConfig)

    def test_from_env_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            cfg = Config.from_env()
        assert cfg.devin.api_key == ""
        assert cfg.github.repo_owner == "gsharma21"
        assert cfg.github.repo_name == "superset"
        assert cfg.datadog.site == "datadoghq.com"
        assert cfg.port == 8000

    def test_from_env_custom_values(self):
        env = {
            "DEVIN_API_KEY": "test-key",
            "DEVIN_ORG_ID": "org-123",
            "MAX_CONCURRENT_DEVIN_SESSIONS": "5",
            "DEVIN_SESSION_TIMEOUT": "7200",
            "GITHUB_TOKEN": "ghp_test",
            "GITHUB_REPO_OWNER": "myorg",
            "GITHUB_REPO_NAME": "myrepo",
            "GITHUB_WEBHOOK_SECRET": "secret123",
            "DD_API_KEY": "dd-key",
            "DD_APP_KEY": "dd-app-key",
            "DD_SITE": "us5.datadoghq.com",
            "SCAN_TYPES": "pip-audit,trivy",
            "SCAN_SCHEDULE_CRON": "0 6 * * *",
            "SHIELDOPS_PORT": "9000",
            "SHIELDOPS_LOG_LEVEL": "DEBUG",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = Config.from_env()

        assert cfg.devin.api_key == "test-key"
        assert cfg.devin.org_id == "org-123"
        assert cfg.devin.max_concurrent_sessions == 5
        assert cfg.devin.session_timeout == 7200
        assert cfg.github.token == "ghp_test"
        assert cfg.github.repo_owner == "myorg"
        assert cfg.github.repo_name == "myrepo"
        assert cfg.github.webhook_secret == "secret123"
        assert cfg.datadog.api_key == "dd-key"
        assert cfg.datadog.app_key == "dd-app-key"
        assert cfg.datadog.site == "us5.datadoghq.com"
        assert cfg.scanner.scan_types == ["pip-audit", "trivy"]
        assert cfg.scanner.schedule_cron == "0 6 * * *"
        assert cfg.port == 9000
        assert cfg.log_level == "DEBUG"

    def test_from_env_partial_overrides(self):
        env = {"DEVIN_API_KEY": "key-only"}
        with patch.dict(os.environ, env, clear=True):
            cfg = Config.from_env()
        assert cfg.devin.api_key == "key-only"
        assert cfg.github.repo_owner == "gsharma21"
