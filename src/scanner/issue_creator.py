from __future__ import annotations

"""Create GitHub issues from scan results."""

import logging
from typing import Optional

import httpx

from .models import ScanResult, Vulnerability
from ..config import GitHubConfig

logger = logging.getLogger(__name__)


class IssueCreator:
    """Creates GitHub issues from vulnerability scan results."""

    def __init__(self, config: GitHubConfig):
        self.config = config
        self.headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.base_url = f"https://api.github.com/repos/{config.repo_full_name}"

    async def create_issues_from_scan(
        self,
        scan_result: ScanResult,
        max_issues: int = 10,
        min_severity: str = "medium",
    ) -> list[Vulnerability]:
        """Create GitHub issues for vulnerabilities, returns updated vulns with issue numbers."""
        severity_order = ["critical", "high", "medium", "low", "unknown"]
        min_idx = severity_order.index(min_severity)

        # Filter and sort by severity
        eligible = [
            v for v in scan_result.vulnerabilities
            if severity_order.index(v.severity.value) <= min_idx
        ]
        eligible.sort(key=lambda v: v.severity.priority_score, reverse=True)

        # Deduplicate by package name (take highest severity)
        seen_packages = set()
        deduplicated = []
        for v in eligible:
            if v.package_name not in seen_packages:
                seen_packages.add(v.package_name)
                deduplicated.append(v)

        # Check existing issues to avoid duplicates
        existing = await self._get_existing_issues()
        existing_titles = {i["title"] for i in existing}

        created = []
        async with httpx.AsyncClient() as client:
            for vuln in deduplicated[:max_issues]:
                issue_data = vuln.to_github_issue()

                # Skip if similar issue exists
                if any(vuln.package_name in t for t in existing_titles):
                    logger.info(f"Skipping {vuln.package_name} — similar issue exists")
                    continue

                # Ensure labels exist
                await self._ensure_labels(client, issue_data["labels"])

                try:
                    resp = await client.post(
                        f"{self.base_url}/issues",
                        headers=self.headers,
                        json=issue_data,
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    vuln.github_issue_number = result["number"]
                    created.append(vuln)
                    logger.info(
                        f"Created issue #{result['number']}: {issue_data['title']}"
                    )
                except httpx.HTTPError as e:
                    logger.error(f"Failed to create issue for {vuln.package_name}: {e}")

        return created

    async def comment_on_issue(self, issue_number: int, body: str) -> bool:
        """Add a comment to a GitHub issue."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/issues/{issue_number}/comments",
                    headers=self.headers,
                    json={"body": body},
                )
                resp.raise_for_status()
                return True
            except httpx.HTTPError as e:
                logger.error(f"Failed to comment on #{issue_number}: {e}")
                return False

    async def close_issue(self, issue_number: int, comment: Optional[str] = None) -> bool:
        """Close a GitHub issue, optionally with a comment."""
        async with httpx.AsyncClient() as client:
            try:
                if comment:
                    await self.comment_on_issue(issue_number, comment)

                resp = await client.patch(
                    f"{self.base_url}/issues/{issue_number}",
                    headers=self.headers,
                    json={"state": "closed"},
                )
                resp.raise_for_status()
                return True
            except httpx.HTTPError as e:
                logger.error(f"Failed to close #{issue_number}: {e}")
                return False

    async def _get_existing_issues(self) -> list[dict]:
        """Get existing open issues with security labels."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/issues",
                    headers=self.headers,
                    params={"labels": "security,devin-auto-fix", "state": "open", "per_page": 100},
                )
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPError as e:
                logger.warning(f"Failed to fetch existing issues, duplicates may be created: {e}")
                return []

    async def _ensure_labels(self, client: httpx.AsyncClient, labels: list[str]):
        """Ensure labels exist in the repo."""
        label_colors = {
            "security": "d73a4a",
            "devin-auto-fix": "0075ca",
            "dependency": "0e8a16",
            "critical": "b60205",
            "high": "d93f0b",
            "medium": "fbca04",
            "low": "c5def5",
        }
        for label in labels:
            try:
                resp = await client.get(
                    f"{self.base_url}/labels/{label}",
                    headers=self.headers,
                )
                if resp.status_code == 404:
                    await client.post(
                        f"{self.base_url}/labels",
                        headers=self.headers,
                        json={
                            "name": label,
                            "color": label_colors.get(label, "ededed"),
                        },
                    )
            except httpx.HTTPError as e:
                logger.warning(f"Failed to ensure label '{label}' exists: {e}")
