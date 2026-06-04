#!/usr/bin/env python3
from __future__ import annotations

"""Create demo security issues on the Superset fork using PyGithub."""

import os
import sys

from github import Github

ISSUES = [
    {
        "title": "[CRITICAL] CVE-2024-34064: Upgrade Jinja2 from 3.0.3 to 3.1.4",
        "labels": ["security", "dependency", "devin-auto-fix", "critical"],
        "body": (
            "pip-audit detected CVE-2024-34064 in Jinja2 3.0.3. Fixed in 3.1.4. CVSS 5.4. "
            "This is a minor version bump but Jinja2 minor versions have occasionally introduced "
            "API changes. Devin: please check the CHANGELOG between 3.0.3 and 3.1.4, fix any "
            "call-site changes, run the test suite, and open a PR."
        ),
    },
    {
        "title": "[HIGH] CVE-2023-30861: Upgrade Flask from 2.2.5 to 3.0.3 (BREAKING CHANGE EXPECTED)",
        "labels": ["security", "dependency", "devin-auto-fix", "high"],
        "body": (
            "pip-audit detected CVE-2023-30861 in Flask 2.2.5. The fix requires upgrading to "
            "Flask 3.0.x which is a MAJOR version bump. Flask 3.0 removes several APIs used in "
            "Superset (including flask.ext, some request context APIs). Devin: read the Flask 3.0 "
            "migration guide, identify every breaking change that affects this codebase, fix all "
            "affected call sites, run tests, iterate until green. This is the hard case — do not "
            "just bump the version number."
        ),
    },
    {
        "title": "[HIGH] GHSA-c2qf-rxjj-qqgw: Upgrade webpack from 5.88.2 to 5.94.0",
        "labels": ["security", "dependency", "devin-auto-fix", "high"],
        "body": (
            "npm audit found GHSA-c2qf-rxjj-qqgw in webpack 5.88.2 in superset-frontend/. "
            "Fixed in 5.94.0. Minor version bump. Devin: update package.json, run npm install, "
            "run the frontend test suite, open a PR."
        ),
    },
    {
        "title": "[MEDIUM] Base image vulnerability: upgrade python:3.9-slim to python:3.12-slim",
        "labels": ["security", "container", "devin-auto-fix", "medium"],
        "body": (
            "trivy scan found multiple CVEs in the python:3.9-slim base image. Upgrading to "
            "python:3.12-slim resolves them. Devin: update the Dockerfile base image, rebuild "
            "the image locally to verify it builds, run any smoke tests, open a PR with the "
            "updated Dockerfile."
        ),
    },
    {
        "title": "[MEDIUM] SAST: Potential SQL injection via string formatting in sql_lab.py",
        "labels": ["security", "sast", "medium"],
        "body": (
            "semgrep flagged a pattern matching potential SQL injection via f-string formatting "
            "in superset/sql_lab.py. Review the flagged lines, determine if they are actually "
            "exploitable given the surrounding context, and if so apply parameterised queries. "
            "This requires human judgment — label does NOT include devin-auto-fix."
        ),
    },
    {
        "title": "[MEDIUM] CVE-2024-37891: Upgrade urllib3 from 1.26.18 to 2.2.2",
        "labels": ["security", "dependency", "devin-auto-fix", "medium"],
        "body": (
            "pip-audit detected CVE-2024-37891 in urllib3 1.26.18. Fixed in 2.2.2. This is a "
            "major version bump (urllib3 v2 changes several APIs). Devin: check what urllib3 APIs "
            "Superset uses, consult the urllib3 v2 migration guide, fix call sites, run tests."
        ),
    },
]

LABELS_TO_CREATE = {
    "security": "d73a4a",
    "dependency": "0e8a16",
    "devin-auto-fix": "0075ca",
    "critical": "b60205",
    "high": "d93f0b",
    "medium": "fbca04",
    "container": "5319e7",
    "sast": "f9d0c4",
}


def main():
    token = os.getenv("GITHUB_TOKEN")
    target = os.getenv("TARGET_REPO", "gaurav21/superset")

    if not token:
        print("❌ GITHUB_TOKEN not set")
        sys.exit(1)

    g = Github(token)
    repo = g.get_repo(target)
    print(f"🛡️ Creating issues on {target}")

    # Ensure labels exist
    existing_labels = {l.name for l in repo.get_labels()}
    for name, color in LABELS_TO_CREATE.items():
        if name not in existing_labels:
            repo.create_label(name=name, color=color)
            print(f"  Created label: {name}")

    # Create issues
    created = []
    for issue_def in ISSUES:
        issue = repo.create_issue(
            title=issue_def["title"],
            body=issue_def["body"],
            labels=issue_def["labels"],
        )
        created.append(issue)
        print(f"  ✅ #{issue.number}: {issue.title}")

    print(f"\n✅ Created {len(created)} issues:")
    for issue in created:
        print(f"  {issue.html_url}")


if __name__ == "__main__":
    main()
