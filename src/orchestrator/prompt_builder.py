from __future__ import annotations

"""Build context-aware prompts for Devin sessions.

v2: Every prompt now explicitly asks Devin to:
- Read the CHANGELOG between versions
- Find and fix ALL breaking call sites
- Report breaking_changes_detected, confidence, reachability_assessment, files_touched
- These fields feed the Policy Engine and Evidence Bundle

The difference between "version bump" and "the thing Dependabot can't do" is in the prompt.
"""

from ..scanner.models import Vulnerability, VulnerabilityType


# The structured output instruction appended to every prompt
STRUCTURED_OUTPUT_INSTRUCTION = """
**IMPORTANT — Structured Output Required:**
When you complete this task, you MUST provide a structured output with these fields:
- `status`: "success", "partial", or "failed"
- `pr_url`: URL of the pull request you created (if any)
- `changes_summary`: 2-3 sentence summary of what you changed and why
- `tests_passed`: true/false — did the test suite pass after your changes?
- `breaking_changes_detected`: true/false — did upgrading require fixing any breaking API changes, import changes, or call site modifications beyond just bumping a version number?
- `breaking_changes_notes`: if breaking changes were detected, describe what broke and how you fixed it
- `reachability_assessment`: is the vulnerable code path actually imported/used in this codebase? State "reachable" (with evidence), "not reachable" (with evidence), or "unknown"
- `confidence`: 0.0 to 1.0 — how confident are you that this fix is correct and complete? 1.0 = certain, 0.5 = uncertain, below 0.5 = guessing
- `files_touched`: list of file paths you modified
- `notes`: any caveats, warnings, or things a reviewer should know
"""


class PromptBuilder:
    """Generates targeted prompts for Devin based on vulnerability type."""

    def __init__(self, repo_url: str, repo_name: str = "superset"):
        self.repo_url = repo_url
        self.repo_name = repo_name

    def build_prompt(self, vuln: Vulnerability) -> str:
        """Build the best prompt for Devin based on vulnerability type."""
        builder = {
            VulnerabilityType.PYTHON_DEPENDENCY: self._python_dep_prompt,
            VulnerabilityType.NPM_DEPENDENCY: self._npm_dep_prompt,
            VulnerabilityType.CONTAINER: self._container_prompt,
            VulnerabilityType.SAST: self._sast_prompt,
            VulnerabilityType.CODE_QUALITY: self._code_quality_prompt,
        }
        base = builder.get(vuln.vuln_type, self._generic_prompt)(vuln)
        return base + STRUCTURED_OUTPUT_INSTRUCTION

    def _python_dep_prompt(self, vuln: Vulnerability) -> str:
        return f"""You are an autonomous security engineer fixing a vulnerability in Apache Superset.

**Repository:** {self.repo_url}
**Issue:** {vuln.title}
**CVE:** {vuln.cve_id or "N/A"}
**Advisory:** {vuln.advisory_url or "N/A"}
**Package:** `{vuln.package_name}` — upgrade from `{vuln.current_version}` to `{vuln.fixed_version or "latest secure version"}`

**Your job is to do what Dependabot CAN'T — handle the hard part:**

1. Clone the repository: {self.repo_url}
2. Find all references to `{vuln.package_name}` in requirements files (requirements/*.txt, setup.cfg, pyproject.toml)
3. **BEFORE upgrading:** Read the CHANGELOG / release notes between `{vuln.current_version}` and `{vuln.fixed_version or "latest"}`. Identify ALL breaking changes, deprecated APIs, and renamed functions.
4. Upgrade `{vuln.package_name}` to `{vuln.fixed_version or "the latest secure version"}`
5. **THE CRITICAL STEP — this is what makes you different from Dependabot:**
   - Run the tests. If they fail, READ the error messages carefully.
   - Find every call site in the Superset codebase that uses changed/removed/renamed APIs.
   - Fix each one to be compatible with the new version.
   - Re-run the tests. Iterate until green.
6. Check if `{vuln.package_name}` is actually imported/used in the Superset source code (not just in requirements). Report this as reachability_assessment.
7. Run the test suite: `python -m pytest tests/ -x --timeout=120` (or relevant subset)
8. Create a pull request with:
   - Title: "fix(security): Upgrade {vuln.package_name} to {vuln.fixed_version or 'latest'} ({vuln.cve_id or 'security fix'})"
   - Description explaining the vulnerability, what changed, and any breaking changes you fixed
   - Reference the CVE/advisory

**Important:**
- If the upgrade causes breaking changes that you successfully fix, that's the MOST VALUABLE outcome — report it clearly in breaking_changes_detected and breaking_changes_notes
- Be honest about your confidence level — it's better to report 0.7 confidence than to claim 1.0 when you're unsure
- Don't refactor unrelated code
- Target branch: `master`
"""

    def _npm_dep_prompt(self, vuln: Vulnerability) -> str:
        return f"""You are an autonomous security engineer fixing a frontend vulnerability in Apache Superset.

**Repository:** {self.repo_url}
**Issue:** {vuln.title}
**Advisory:** {vuln.advisory_url or "N/A"}
**Package:** `{vuln.package_name}` — upgrade to `{vuln.fixed_version or "latest secure version"}`

**Your job is to do what Dependabot CAN'T — handle breaking upgrades and transitive deps:**

1. Clone the repository: {self.repo_url}
2. Navigate to `superset-frontend/`
3. **BEFORE upgrading:** Check the package's CHANGELOG/releases between the current and target version. Note any breaking changes or peer dependency changes.
4. Upgrade `{vuln.package_name}`:
   - If it's a direct dependency: `npm install {vuln.package_name}@{vuln.fixed_version or "latest"}`
   - If it's a transitive dependency: add a resolution/override in package.json
5. Check peer dependency warnings — fix any conflicts.
6. **THE CRITICAL STEP:**
   - Run `npm test -- --watchAll=false`. If tests fail, read the errors.
   - Find and fix every import, API call, or usage that changed.
   - Re-run until green.
7. Run `npm run build` to verify the build works.
8. Run `npm audit` to verify the vulnerability is resolved.
9. Check if `{vuln.package_name}` is actually imported in the frontend source code. Report as reachability_assessment.
10. Create a pull request with:
    - Title: "fix(security): Upgrade {vuln.package_name} to {vuln.fixed_version or 'latest'}"
    - Description of the advisory, breaking changes (if any), and how you fixed them

**Important:**
- Report breaking changes honestly — they're the most valuable thing you can demonstrate
- Be honest about confidence level
- Target branch: `master`
"""

    def _container_prompt(self, vuln: Vulnerability) -> str:
        return f"""You are an autonomous security engineer fixing a container vulnerability in Apache Superset.

**Repository:** {self.repo_url}
**Issue:** {vuln.title}
**CVE:** {vuln.cve_id or "N/A"}
**Package:** `{vuln.package_name}` `{vuln.current_version}` → `{vuln.fixed_version or "latest"}`

**Task:**
1. Clone the repository: {self.repo_url}
2. Review Dockerfile(s) — `Dockerfile` and any in `docker/`
3. If it's a base image issue, update the FROM line to a newer tag
4. If it's an OS-level package, add explicit package upgrade in Dockerfile
5. Pin specific versions for reproducibility
6. Verify: `docker build -t superset-test .` should succeed
7. Create a pull request with description and evidence

**Important:** Pin versions, don't change image structure unnecessarily. Target branch: `master`
"""

    def _sast_prompt(self, vuln: Vulnerability) -> str:
        return f"""You are an autonomous security engineer fixing a code security finding in Apache Superset.

**Repository:** {self.repo_url}
**Finding:** {vuln.title}
**Description:** {vuln.description}
**Location:** `{vuln.file_path}`{f" line {vuln.line_number}" if vuln.line_number else ""}
**Rule:** `{vuln.package_name}`

**Task:**
1. Clone the repository: {self.repo_url}
2. Navigate to `{vuln.file_path}`{f" line {vuln.line_number}" if vuln.line_number else ""}
3. **Understand the context** before changing anything:
   - What does this code do?
   - Is this code path actually reachable from user input? (Report as reachability_assessment)
   - What's the actual security risk?
4. Apply the minimal fix:
   - SQL injection → parameterized queries
   - XSS → input sanitization/escaping
   - Auth issues → proper checks
   - Insecure random → cryptographic random
5. Run the relevant test file
6. Create a pull request explaining the vulnerability, the context, and the fix

**Important:** Understand before fixing. Minimal, targeted changes only. Be honest about confidence. Target branch: `master`
"""

    def _code_quality_prompt(self, vuln: Vulnerability) -> str:
        return self._sast_prompt(vuln)

    def _generic_prompt(self, vuln: Vulnerability) -> str:
        return f"""You are an autonomous security engineer fixing a vulnerability in Apache Superset.

**Repository:** {self.repo_url}
**Issue:** {vuln.title}
**Description:** {vuln.description}
**Package:** `{vuln.package_name}` `{vuln.current_version}`
{f"**Fix version:** `{vuln.fixed_version}`" if vuln.fixed_version else ""}

**Task:**
1. Clone the repository: {self.repo_url}
2. Investigate the vulnerability — is it reachable?
3. Fix it properly
4. Run tests, iterate until green
5. Create a pull request with evidence

Target branch: `master`
"""
