from __future__ import annotations

"""Shared reachability-check utilities.

Both the triage engine and the vulnerability scanner need to determine whether a
package is actually imported in the target codebase. This module provides the
canonical implementation so the logic isn't duplicated.
"""

import os
import subprocess
from typing import Optional

from ..scanner.models import VulnerabilityType

# Multiplier applied to priority scores for unreachable packages.
UNREACHABLE_PRIORITY_MULTIPLIER: float = 0.3


def check_package_reachability(
    package_name: str,
    vuln_type: VulnerabilityType,
    repo_path: str,
) -> Optional[bool]:
    """Determine if a package is actually used in the codebase.

    Returns:
        True  — import/usage found (reachable).
        False — definitely not imported (unreachable).
        None  — cannot determine (non-dependency type, repo missing, etc.).
    """
    if vuln_type not in (VulnerabilityType.PYTHON_DEPENDENCY, VulnerabilityType.NPM_DEPENDENCY):
        return None

    if not os.path.isdir(repo_path):
        return None

    pkg = package_name.replace("-", "_")

    try:
        if vuln_type == VulnerabilityType.PYTHON_DEPENDENCY:
            result = subprocess.run(
                ["grep", "-r", "-l", "--include=*.py",
                 f"\\(import {pkg}\\|from {pkg}\\)", repo_path],
                capture_output=True, text=True, timeout=10,
            )
            return len(result.stdout.strip()) > 0

        elif vuln_type == VulnerabilityType.NPM_DEPENDENCY:
            frontend = os.path.join(repo_path, "superset-frontend")
            search_dir = frontend if os.path.isdir(frontend) else repo_path
            result = subprocess.run(
                ["grep", "-r", "-l", "--include=*.ts", "--include=*.tsx",
                 "--include=*.js", "--include=*.jsx",
                 package_name, search_dir],
                capture_output=True, text=True, timeout=10,
            )
            return len(result.stdout.strip()) > 0

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    return None


def adjust_priority_for_reachability(base_score: float, is_reachable: bool) -> float:
    """Reduce priority score for unreachable packages."""
    if not is_reachable:
        return base_score * UNREACHABLE_PRIORITY_MULTIPLIER
    return base_score
