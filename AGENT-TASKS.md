# ShieldOps — Agent Task Specs
**Repo:** https://github.com/gaurav21/shieldops  
**Branch to target:** `master`  
**Run tasks in order — each subsequent task may import from a previous one.**

---

## TASK 1 — Fix `requirements.txt`: add all missing dependencies

**File:** `requirements.txt`  
**What exists:** Only 5 deps: `fastapi`, `uvicorn`, `httpx`, `pydantic`, `python-dotenv`  
**What to do:** Replace the entire file with the full dependency list below.

```
fastapi==0.115.12
uvicorn[standard]==0.34.3
httpx==0.28.1
pydantic==2.11.4
python-dotenv==1.1.0
datadog-api-client==2.31.0
datadog==0.50.1
PyGithub==2.5.0
APScheduler==3.10.4
pip-audit==2.7.3
semgrep==1.73.0
```

**Done when:** `pip install -r requirements.txt` succeeds with no conflicts.

---

## TASK 2 — Create `src/orchestrator/policy.py`: the Trust Boundary

**File to create:** `src/orchestrator/policy.py`  
**What exists:** This file does not exist yet.  
**What to do:** Create the policy engine that consumes Devin's structured output and emits a routing decision + reason.

Implement the following exactly:

```python
"""
policy.py — Trust Boundary for ShieldOps
Routes each Devin remediation result to one of three outcomes:
  AUTO_MERGE_READY  → safe to merge without human review
  HUMAN_REVIEW      → PR created, labeled needs-human, reviewer packet attached
  BLOCKED           → no PR merged, issue commented, Datadog alert fired
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

# Sensitive file paths in Apache Superset that force HUMAN_REVIEW
SENSITIVE_PATHS = [
    "superset/sql_lab.py",
    "superset/views/",
    "superset/security/",
    "superset/db_engine_specs/",
    "superset/connectors/",
    "superset/models/core.py",
]

SENSITIVE_KEYWORDS = ["auth", "crypto", "password", "token", "secret", "sql", "injection"]


class PolicyDecision(str, Enum):
    AUTO_MERGE_READY = "auto_merge_ready"
    HUMAN_REVIEW = "human_review"
    BLOCKED = "blocked"


@dataclass
class PolicyResult:
    decision: PolicyDecision
    reason: str
    risk_flags: list[str]
    reviewer_notes: str


def evaluate(
    severity: str,                        # "critical" | "high" | "medium" | "low"
    vuln_type: str,                       # "dependency" | "sast" | "container"
    upgrade_type: str,                    # "patch" | "minor" | "major"
    tests_passed: bool,
    breaking_changes_detected: bool,
    confidence: float,                    # 0.0–1.0 from Devin structured output
    files_touched: list[str],
    reachability_assessment: Optional[str] = None,
    devin_status: str = "success",        # "success" | "partial" | "failed" | "error" | "timed_out"
) -> PolicyResult:
    """
    Apply routing logic and return a PolicyResult.
    Logic is explicit and ordered — first matching rule wins.
    """
    risk_flags = []

    # --- Collect all risk flags ---
    if not tests_passed:
        risk_flags.append("tests_failed")
    if confidence < 0.5:
        risk_flags.append("low_confidence")
    if devin_status in ("error", "timed_out", "failed"):
        risk_flags.append(f"devin_status_{devin_status}")
    if breaking_changes_detected:
        risk_flags.append("breaking_changes_detected")
    if upgrade_type == "major":
        risk_flags.append("major_version_bump")
    if vuln_type in ("sast", "container"):
        risk_flags.append(f"complex_vuln_type_{vuln_type}")
    if any(_is_sensitive(f) for f in files_touched):
        risk_flags.append("sensitive_path_touched")

    # --- BLOCKED: agent could not produce a trustworthy result ---
    if not tests_passed:
        return PolicyResult(
            decision=PolicyDecision.BLOCKED,
            reason="Tests did not pass — no PR should be merged.",
            risk_flags=risk_flags,
            reviewer_notes="Devin session produced a failing build. Investigate manually or re-queue.",
        )
    if confidence < 0.5:
        return PolicyResult(
            decision=PolicyDecision.BLOCKED,
            reason=f"Devin confidence too low ({confidence:.0%}) to trust the output.",
            risk_flags=risk_flags,
            reviewer_notes="Confidence below 50%. The fix may be incomplete or incorrect. Do not merge.",
        )
    if devin_status in ("error", "timed_out", "failed"):
        return PolicyResult(
            decision=PolicyDecision.BLOCKED,
            reason=f"Devin session ended with status '{devin_status}'.",
            risk_flags=risk_flags,
            reviewer_notes="Session did not complete successfully. No PR should exist. Retry or escalate.",
        )

    # --- HUMAN_REVIEW: agent succeeded but change needs a human eye ---
    human_review_reasons = []
    if upgrade_type == "major":
        human_review_reasons.append("major version bump")
    if breaking_changes_detected:
        human_review_reasons.append("breaking changes detected and remediated by Devin")
    if vuln_type in ("sast", "container"):
        human_review_reasons.append(f"vulnerability type '{vuln_type}' involves code logic, not a dependency pin")
    if any(_is_sensitive(f) for f in files_touched):
        human_review_reasons.append("sensitive path touched (auth/SQL/crypto/views)")
    if 0.5 <= confidence < 0.8:
        human_review_reasons.append(f"confidence {confidence:.0%} — within acceptable range but not high")

    if human_review_reasons:
        return PolicyResult(
            decision=PolicyDecision.HUMAN_REVIEW,
            reason="Human review required: " + "; ".join(human_review_reasons),
            risk_flags=risk_flags,
            reviewer_notes=(
                "PR is labeled `needs-human`. Review the evidence bundle below. "
                "Expected review time: ~2 minutes. All tests pass."
            ),
        )

    # --- AUTO_MERGE_READY: low-risk, high-confidence, tests green ---
    return PolicyResult(
        decision=PolicyDecision.AUTO_MERGE_READY,
        reason=(
            f"Patch/minor dependency fix, tests pass, confidence {confidence:.0%}, "
            "no sensitive paths, no breaking changes."
        ),
        risk_flags=risk_flags,
        reviewer_notes="Safe to auto-merge. No human action required.",
    )


def _is_sensitive(filepath: str) -> bool:
    """Return True if the file touches a sensitive area of the codebase."""
    for pattern in SENSITIVE_PATHS:
        if filepath.startswith(pattern):
            return True
    lower = filepath.lower()
    return any(kw in lower for kw in SENSITIVE_KEYWORDS)
```

**Done when:** `python -c "from src.orchestrator.policy import evaluate, PolicyDecision; print('OK')"` exits 0.

---

## TASK 3 — Create `src/reporting/evidence_bundle.py`: the reviewer packet

**File to create:** `src/reporting/evidence_bundle.py`  
**What exists:** `src/reporting/github_reporter.py` exists. This is a new file alongside it.  
**What to do:** Create a module that builds a structured markdown evidence bundle from a Devin session result + policy decision. This bundle gets posted as the PR body and as a comment on the originating GitHub issue.

```python
"""
evidence_bundle.py — Build the 2-minute reviewer approval packet.
Called after every Devin session that produces a HUMAN_REVIEW or AUTO_MERGE_READY decision.
"""

from dataclasses import dataclass
from typing import Optional
from src.orchestrator.policy import PolicyResult, PolicyDecision


@dataclass
class DevinSessionResult:
    session_id: str
    pr_url: Optional[str]
    status: str                          # success | partial | failed
    changes_summary: str
    tests_passed: bool
    breaking_changes_detected: bool
    breaking_changes_notes: str
    reachability_assessment: str
    confidence: float
    files_touched: list[str]
    notes: str
    duration_seconds: int
    acu_used: float


@dataclass
class VulnerabilityContext:
    cve_id: str
    package: str
    current_version: str
    fixed_version: str
    severity: str
    advisory_url: str
    upgrade_type: str                    # patch | minor | major


def build(
    vuln: VulnerabilityContext,
    result: DevinSessionResult,
    policy: PolicyResult,
) -> str:
    """
    Return a markdown string suitable for use as a GitHub PR body or issue comment.
    Aim: reviewer approves in < 2 minutes with full confidence.
    """
    decision_badge = {
        PolicyDecision.AUTO_MERGE_READY: "🟢 AUTO-MERGE READY",
        PolicyDecision.HUMAN_REVIEW: "🟡 NEEDS HUMAN REVIEW",
        PolicyDecision.BLOCKED: "🔴 BLOCKED — DO NOT MERGE",
    }[policy.decision]

    risk_section = (
        "\n".join(f"- ⚠️ `{flag}`" for flag in policy.risk_flags)
        if policy.risk_flags
        else "- ✅ No risk flags"
    )

    files_section = (
        "\n".join(f"- `{f}`" for f in result.files_touched[:20])
        if result.files_touched
        else "- _(none reported)_"
    )
    if len(result.files_touched) > 20:
        files_section += f"\n- _...and {len(result.files_touched) - 20} more_"

    bundle = f"""## {decision_badge}

> **Policy reason:** {policy.reason}

---

### 🔍 Vulnerability
| Field | Value |
|---|---|
| CVE | [{vuln.cve_id}]({vuln.advisory_url}) |
| Package | `{vuln.package}` |
| Upgrade | `{vuln.current_version}` → `{vuln.fixed_version}` ({vuln.upgrade_type}) |
| Severity | `{vuln.severity.upper()}` |

---

### 🤖 What Devin Did
{result.changes_summary}

---

### 🧪 Test Result
| | |
|---|---|
| Tests passed | {"✅ Yes" if result.tests_passed else "❌ No"} |
| Breaking changes | {"⚠️ Yes — see below" if result.breaking_changes_detected else "✅ None detected"} |
| Confidence | {result.confidence:.0%} |

{"**Breaking changes handled:**" + chr(10) + result.breaking_changes_notes if result.breaking_changes_detected else ""}

---

### 🎯 Reachability
{result.reachability_assessment or "_Not assessed_"}

---

### 📁 Files Touched ({len(result.files_touched)})
{files_section}

---

### ⚠️ Risk Flags
{risk_section}

---

### 📋 Reviewer Notes
{policy.reviewer_notes}

---

### 📊 Session Metadata
| | |
|---|---|
| Session ID | `{result.session_id}` |
| Duration | {result.duration_seconds // 60}m {result.duration_seconds % 60}s |
| ACU used | {result.acu_used:.1f} |
| Devin status | `{result.status}` |

_Generated by ShieldOps — Trust Control Plane for Autonomous Engineering_
"""
    return bundle.strip()
```

**Done when:** `python -c "from src.reporting.evidence_bundle import build; print('OK')"` exits 0.

---

## TASK 4 — Update `src/orchestrator/prompt_builder.py`: add breaking-change instructions

**File to edit:** `src/orchestrator/prompt_builder.py`  
**What exists:** A prompt builder that constructs Devin prompts from vulnerability data.  
**What to do:**

1. Find the function that builds the main remediation prompt (likely named `build_prompt`, `build_remediation_prompt`, or similar).
2. Add the following block to the prompt body, immediately before the structured output instruction at the end of the prompt:

```
IMPORTANT — your job is not just to bump the version number. Do all of the following:

1. Read the CHANGELOG or release notes between {current_version} and {fixed_version}.
2. Identify every breaking change, renamed symbol, or removed API in those notes.
3. Search the codebase for every usage of the affected symbols and fix them all.
4. Run the full test suite. If tests fail, read the failure output, fix the root cause, and re-run. Iterate until tests are green.
5. In your structured output, set:
   - breaking_changes_detected: true/false
   - breaking_changes_notes: a plain-English description of what breaking changes you found and how you handled them
   - reachability_assessment: whether the vulnerable code path is actually used in this codebase (check imports and call sites)
   - confidence: a number 0.0-1.0 reflecting how certain you are the fix is complete and correct
   - files_touched: the list of every file you modified

Do NOT open a PR until tests are green. If you cannot get tests green within your ACU budget, set status to "partial" and explain in notes.
```

3. Also update the `structured_output_schema` dict passed to the Devin API to include these fields if not already present:

```python
STRUCTURED_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "partial", "failed"],
        },
        "pr_url": {"type": "string"},
        "changes_summary": {"type": "string"},
        "tests_passed": {"type": "boolean"},
        "breaking_changes_detected": {"type": "boolean"},
        "breaking_changes_notes": {"type": "string"},
        "reachability_assessment": {"type": "string"},
        "confidence": {"type": "number"},
        "files_touched": {
            "type": "array",
            "items": {"type": "string"},
        },
        "notes": {"type": "string"},
    },
    "required": [
        "status", "tests_passed", "breaking_changes_detected",
        "confidence", "files_touched",
    ],
}
```

**Done when:** The prompt builder returns a string containing the phrase "Read the CHANGELOG" and the `STRUCTURED_OUTPUT_SCHEMA` dict contains the key `"breaking_changes_detected"`.

---

## TASK 5 — Update `src/orchestrator/session_manager.py`: track interventions

**File to edit:** `src/orchestrator/session_manager.py`  
**What exists:** A session manager that creates Devin sessions, polls for completion, and handles timeouts.  
**What to do:** Add intervention tracking so we can measure `intervention_rate` (the % of sessions that required a follow-up message from the orchestrator).

1. Add an `intervention_count: int = 0` field to the session state (whatever data structure tracks session lifecycle — dict, dataclass, or class attribute).
2. Wherever the code calls `POST /v1/session/{id}/message` (the follow-up message endpoint), increment `intervention_count` for that session.
3. When a session reaches a terminal state (`stopped`, `error`, `timed_out`, or the polling loop exits), emit this Datadog metric:
```python
from datadog import statsd
statsd.gauge(
    "shieldops.devin.intervention_count",
    intervention_count,
    tags=[f"session_id:{session_id}", f"severity:{severity}"],
)
# Also emit a boolean flag: 1 if any intervention happened, 0 if none
statsd.gauge(
    "shieldops.devin.needed_intervention",
    1 if intervention_count > 0 else 0,
    tags=[f"session_id:{session_id}"],
)
```
4. Return `intervention_count` as part of the session result dict/dataclass so `main.py` can include it in logs and the Datadog event.

**Done when:** The session result object has an `intervention_count` field and the two metrics above are emitted at session close.

---

## TASK 6 — Update `src/observability/metrics.py`: add V2 fleet and trust metrics

**File to edit:** `src/observability/metrics.py`  
**What exists:** Metrics for vulnerability counts and Devin session counts (the V1 set).  
**What to do:** Add the following new metric emission functions. Do not remove existing functions — append these.

```python
def record_policy_decision(decision: str, severity: str, upgrade_type: str):
    """Emit when the policy engine routes a remediation."""
    statsd.increment(
        "shieldops.policy.decision",
        tags=[
            f"decision:{decision}",          # auto_merge_ready | human_review | blocked
            f"severity:{severity}",
            f"upgrade_type:{upgrade_type}",
        ],
    )

def record_breaking_change_handled(package: str, severity: str):
    """Emit when Devin successfully handles a breaking-change upgrade."""
    statsd.increment(
        "shieldops.remediation.breaking_changes_handled",
        tags=[f"package:{package}", f"severity:{severity}"],
    )

def record_time_to_merged_verified(seconds: int, severity: str, upgrade_type: str):
    """
    Real MTTR: time from vulnerability detected to PR merged and verified.
    This is the metric that replaces 'time to open a PR'.
    """
    statsd.gauge(
        "shieldops.remediation.time_to_merged_verified_seconds",
        seconds,
        tags=[f"severity:{severity}", f"upgrade_type:{upgrade_type}"],
    )

def record_confidence(confidence: float, decision: str):
    """Distribution of Devin's self-reported confidence per session."""
    statsd.gauge(
        "shieldops.remediation.confidence",
        confidence,
        tags=[f"decision:{decision}"],
    )

def record_acu_cost(acu_used: float, session_id: str, severity: str):
    """Cost per session in ACU units — feeds cost-per-fix calculation."""
    statsd.gauge(
        "shieldops.devin.cost_acu",
        acu_used,
        tags=[f"session_id:{session_id}", f"severity:{severity}"],
    )

def record_reviewer_minutes_saved(minutes_saved: float, decision: str):
    """
    Estimated review time saved vs. manual remediation.
    Baseline assumption: manual fix = 45 min for patch/minor, 120 min for major.
    Auto-merge-ready saves the full baseline. Human-review saves 80%.
    """
    statsd.gauge(
        "shieldops.remediation.reviewer_minutes_saved",
        minutes_saved,
        tags=[f"decision:{decision}"],
    )
    statsd.increment(
        "shieldops.remediation.reviewer_minutes_saved_cumulative",
        int(minutes_saved),
        tags=[f"decision:{decision}"],
    )

def record_unreachable_vuln_deprioritized(count: int):
    """Track how many CVEs were deprioritized because the code path is unreachable."""
    statsd.gauge("shieldops.triage.unreachable_deprioritized", count)
```

**Done when:** All 7 functions exist in `metrics.py` and each calls `statsd.increment` or `statsd.gauge` with the metric names exactly as written above.

---

## TASK 7 — Update `src/observability/dashboard.py`: rebuild to V2 widget order

**File to edit:** `src/observability/dashboard.py`  
**What exists:** A dashboard creation script that uses the Datadog API to create the "ShieldOps Command Center" dashboard. The current widget order is vulnerability-centric (V1).  
**What to do:** Rebuild the `create_dashboard()` function (or equivalent) so the widget order matches V2 exactly:

**Row 1 — THE FLEET RIGHT NOW** (4 query_value widgets side by side):
- `shieldops.devin.sessions.active` — title: "Active Sessions"
- `shieldops.devin.sessions.blocked` — title: "Blocked / Stuck"
- `shieldops.devin.cost_acu` (sum, last 1h) — title: "ACU Burn Rate (1h)"
- `shieldops.devin.needed_intervention` (avg as %) — title: "Intervention Rate"

**Row 2 — IS IT SAFE TO RUN?** (2 widgets):
- Pie/donut: `shieldops.policy.decision` grouped by `decision` tag — title: "Trust Split: Auto vs Human vs Blocked"
- Distribution: `shieldops.remediation.confidence` — title: "Confidence Distribution"

**Row 3 — THE THING DEPENDABOT CAN'T DO** (2 widgets):
- Timeseries + big number: `shieldops.remediation.breaking_changes_handled` — title: "Breaking Changes Handled (Dependabot Can't)"
- Timeseries: `shieldops.remediation.time_to_merged_verified_seconds` with a reference line at 14400 (4h target) — title: "Time to Merged & Verified"

**Row 4 — WHAT IS IT WORTH?** (2 widgets):
- Query value: `shieldops.remediation.reviewer_minutes_saved_cumulative` — title: "Reviewer-Minutes Saved (Total)"
- Timeseries: `shieldops.devin.cost_acu` per `session_id` — title: "ACU Cost per Session"

**Row 5 — SECURITY POSTURE** (2 widgets — same as V1, now supporting cast):
- Timeseries: `shieldops.vulnerabilities.open` by `severity` — title: "Open Vulnerabilities (Burn-Down)"
- Bar: `shieldops.scan.vulnerabilities_found` — title: "Vulns Found per Scan"

**Row 6 — AUDIT** (full width):
- Event stream: source `shieldops` — title: "Full Audit Trail (Every Scan, Session, Policy Decision, Merge)"

Also update the dashboard title from "ShieldOps Command Center" to **"ShieldOps — Agent Trust Control Plane"**.

**Done when:** `POST /setup/datadog` creates a dashboard with the title "ShieldOps — Agent Trust Control Plane" and at least 10 widgets.

---

## TASK 8 — Update `src/observability/monitors.py`: replace V1 monitors with V2 trust monitors

**File to edit:** `src/observability/monitors.py`  
**What exists:** Monitors for session failure rate, stale vulnerabilities, scan health.  
**What to do:** Keep the existing monitors but add the following 3 new monitors:

**Monitor A — Intervention Rate Spike:**
```
Name: "[ShieldOps] Devin Fleet Needs Babysitting"
Type: metric alert
Query: avg(last_15m):avg:shieldops.devin.needed_intervention{*} > 0.4
Message: "More than 40% of active Devin sessions required a follow-up message in the last 15 minutes. The fleet may be stuck on a hard class of vulnerability. @slack-shieldops-alerts"
Thresholds: critical=0.4, warning=0.25
Tags: ["shieldops", "trust", "intervention"]
```

**Monitor B — Auto-Merge with Low Confidence (safety net):**
```
Name: "[ShieldOps] ⚠️ Auto-Merge Fired with Low Confidence — Policy Boundary Breach"
Type: metric alert
Query: sum(last_5m):sum:shieldops.policy.decision{decision:auto_merge_ready} by {session_id}.as_count() > 0 AND avg(last_5m):avg:shieldops.remediation.confidence{decision:auto_merge_ready} < 0.8
Message: "A change was routed to AUTO_MERGE_READY with confidence below 0.8. This should never happen if the policy engine is working correctly. Investigate immediately. @pagerduty-shieldops"
Thresholds: critical=1
Tags: ["shieldops", "trust", "policy-breach"]
```

**Monitor C — Session Stuck > 30 Minutes:**
```
Name: "[ShieldOps] Devin Session Stuck"
Type: metric alert
Query: max(last_5m):max:shieldops.devin.sessions.active{*} > 0 AND min(last_30m):min:shieldops.devin.sessions.active{*} > 0
Message: "A Devin session has been active for > 30 minutes without reaching a terminal state. It may be stuck. Session ID available in the event stream. @slack-shieldops-alerts"
Thresholds: critical=1
Tags: ["shieldops", "trust", "stuck"]
```

**Done when:** `POST /setup/datadog` creates monitors including all three names above.

---

## TASK 9 — Add reachability heuristic to `src/scanner/vulnerability_scanner.py` (or `triage.py`)

**File to edit:** Wherever vulnerability triage / scoring happens (`src/scanner/triage.py` or similar).  
**What exists:** A weighted priority scorer: Severity 40% / Fix-available 25% / Type 20% / Age 15%.  
**What to do:** Add a `check_reachability(package: str, repo_path: str) -> bool` function and integrate its result into triage.

```python
import subprocess
import re

def check_reachability(package: str, repo_path: str = ".") -> bool:
    """
    Heuristic: is the vulnerable package actually imported anywhere in the codebase?
    Returns True if reachable (import found), False if likely not reachable.
    This is a grep-based heuristic — fast and good enough for triage prioritisation.
    """
    # Normalise package name: pip uses hyphens, imports use underscores
    import_name = package.replace("-", "_").lower()
    patterns = [
        f"import {import_name}",
        f"from {import_name}",
        f"import {package.lower()}",
        f"from {package.lower()}",
    ]
    for pattern in patterns:
        try:
            result = subprocess.run(
                ["grep", "-r", "--include=*.py", "-l", pattern, repo_path],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout.strip():
                return True
        except subprocess.TimeoutExpired:
            return True  # Assume reachable on timeout (safe default)
    return False


def adjust_priority_for_reachability(base_score: float, is_reachable: bool) -> float:
    """
    Reduce priority score for unreachable packages.
    Unreachable CVEs get deprioritised but NOT removed (they may still matter for containers/transitive deps).
    """
    if not is_reachable:
        return base_score * 0.3   # 70% reduction for unreachable
    return base_score
```

After adding the function, wire it into the existing triage/priority scoring pipeline:
1. Call `check_reachability(package, repo_path)` for each vulnerability.
2. Set `vulnerability.reachable = True/False` on the vulnerability object.
3. Call `adjust_priority_for_reachability(score, is_reachable)` before finalising priority.
4. At the end of a scan, count unreachable CVEs and call `record_unreachable_vuln_deprioritized(count)` from `metrics.py`.

**Done when:** Running `python -c "from src.scanner.vulnerability_scanner import check_reachability; print(check_reachability('fastapi', '.'))"` exits 0 and returns True or False.

---

## TASK 10 — Create `scripts/setup_superset_issues.py`: scaffold the Superset fork demo issues

**File to create:** `scripts/setup_superset_issues.py`  
**What exists:** `scripts/setup_datadog.py` exists. This is a new companion script.  
**What to do:** Create a standalone script that uses PyGithub to create 6 labelled security issues on a target repo (the Superset fork). The script reads `GITHUB_TOKEN` and `TARGET_REPO` (e.g. `gaurav21/superset`) from environment variables.

The script must:
1. Create these labels if they don't exist: `security`, `dependency`, `devin-auto-fix`, `critical`, `high`, `medium`, `container`, `sast`
2. Create the following 6 issues in order. Each issue title, body, and label set must be exactly as specified:

**Issue 1 — Critical Python dep:**
- Title: `[CRITICAL] CVE-2024-34064: Upgrade Jinja2 from 3.0.3 to 3.1.4`
- Labels: `security`, `dependency`, `devin-auto-fix`, `critical`
- Body: `pip-audit detected CVE-2024-34064 in Jinja2 3.0.3. Fixed in 3.1.4. CVSS 5.4. This is a minor version bump but Jinja2 minor versions have occasionally introduced API changes. Devin: please check the CHANGELOG between 3.0.3 and 3.1.4, fix any call-site changes, run the test suite, and open a PR.`

**Issue 2 — Major version breaking change (the hero case):**
- Title: `[HIGH] CVE-2023-30861: Upgrade Flask from 2.2.5 to 3.0.3 (BREAKING CHANGE EXPECTED)`
- Labels: `security`, `dependency`, `devin-auto-fix`, `high`
- Body: `pip-audit detected CVE-2023-30861 in Flask 2.2.5. The fix requires upgrading to Flask 3.0.x which is a MAJOR version bump. Flask 3.0 removes several APIs used in Superset (including flask.ext, some request context APIs). Devin: read the Flask 3.0 migration guide, identify every breaking change that affects this codebase, fix all affected call sites, run tests, iterate until green. This is the hard case — do not just bump the version number.`

**Issue 3 — npm advisory:**
- Title: `[HIGH] GHSA-c2qf-rxjj-qqgw: Upgrade webpack from 5.88.2 to 5.94.0`
- Labels: `security`, `dependency`, `devin-auto-fix`, `high`
- Body: `npm audit found GHSA-c2qf-rxjj-qqgw in webpack 5.88.2 in superset-frontend/. Fixed in 5.94.0. Minor version bump. Devin: update package.json, run npm install, run the frontend test suite, open a PR.`

**Issue 4 — Container/Dockerfile:**
- Title: `[MEDIUM] Base image vulnerability: upgrade python:3.9-slim to python:3.12-slim`
- Labels: `security`, `container`, `devin-auto-fix`, `medium`
- Body: `trivy scan found multiple CVEs in the python:3.9-slim base image. Upgrading to python:3.12-slim resolves them. Devin: update the Dockerfile base image, rebuild the image locally to verify it builds, run any smoke tests, open a PR with the updated Dockerfile.`

**Issue 5 — SAST finding:**
- Title: `[MEDIUM] SAST: Potential SQL injection via string formatting in sql_lab.py`
- Labels: `security`, `sast`, `medium`
- Body: `semgrep flagged a pattern matching potential SQL injection via f-string formatting in superset/sql_lab.py. Review the flagged lines, determine if they are actually exploitable given the surrounding context, and if so apply parameterised queries. This requires human judgment — label does NOT include devin-auto-fix.`

**Issue 6 — Medium Python dep:**
- Title: `[MEDIUM] CVE-2024-37891: Upgrade urllib3 from 1.26.18 to 2.2.2`
- Labels: `security`, `dependency`, `devin-auto-fix`, `medium`
- Body: `pip-audit detected CVE-2024-37891 in urllib3 1.26.18. Fixed in 2.2.2. This is a major version bump (urllib3 v2 changes several APIs). Devin: check what urllib3 APIs Superset uses, consult the urllib3 v2 migration guide, fix call sites, run tests.`

3. Print a summary of all created issue URLs at the end.

**Done when:** `python scripts/setup_superset_issues.py` creates all 6 issues on the target repo and prints their URLs.

---

## TASK 11 — Update `README.md`: rewrite to V2 narrative, fix broken references

**File to edit:** `README.md`  
**What exists:** The current README tells the V1 story (scan → triage → Devin → dashboard).  
**What to do:** Make the following targeted edits — do not rewrite everything, just fix the broken parts:

1. **Fix the clone URL** in the Quick Start section. Change:
   ```
   git clone https://github.com/gsharma21/devin-devsecsops.git
   cd devin-devsecsops
   ```
   To:
   ```
   git clone https://github.com/gaurav21/shieldops.git
   cd shieldops
   ```

2. **Replace the "How It Works" intro paragraph** (the text right after `## ⚡ How It Works`). Change to:
   ```
   ShieldOps is a **trust control plane for autonomous security remediation**. It doesn't compete with Dependabot on easy patch bumps — it handles the 20% of vulnerabilities that Dependabot abandons: breaking-change upgrades that require reading migration guides, fixing call sites, iterating on test failures, and producing evidence a reviewer can approve in two minutes.
   ```

3. **Add a "Why Not Just Use Dependabot?" section** immediately after the ASCII architecture diagram, before "## 🚀 Quick Start":
   ```markdown
   ## 🆚 Why Not Just Dependabot?
   
   | | Dependabot | ShieldOps + Devin |
   |---|---|---|
   | Patch/minor bumps | ✅ | ✅ |
   | Breaking-change upgrades | ❌ Opens a red PR, stops | ✅ Fixes call sites, iterates to green |
   | Reads CHANGELOG to anticipate breakage | ❌ | ✅ |
   | Reachability — "does this CVE matter here?" | ❌ | ✅ |
   | Routes changes: auto-merge vs human-gate vs block | ❌ | ✅ |
   | Gives the reviewer an evidence bundle | ❌ | ✅ |
   ```

4. **Update the "Datadog Observability" description** under the ASCII diagram. Replace the sentence about the ShieldOps Command Center dashboard to say:
   ```
   The **ShieldOps Agent Trust Control Plane** dashboard answers the VP's question: *"Is it safe to run a fleet of autonomous agents against my codebase?"*
   ```

5. **Replace the dead Loom link** `[Watch the 5-minute Loom walkthrough →](#)` with `[Watch the 5-minute Loom walkthrough →](docs/DEMO.md)` and create an empty `docs/DEMO.md` with placeholder text `# Demo — coming soon`.

**Done when:** `grep "gsharma21" README.md` returns nothing and `grep "trust control plane" README.md` returns a match.

---

## TASK 12 — Wire policy + evidence bundle into `src/main.py`

**File to edit:** `src/main.py`  
**What exists:** The main FastAPI orchestration loop. After a Devin session completes, it presumably updates the GitHub issue and emits metrics.  
**What to do:** Insert the policy + evidence bundle steps into the post-session processing flow. Find the code path that runs after a Devin session reaches a terminal state and add:

```python
# After Devin session completes — add these steps:

from src.orchestrator.policy import evaluate as policy_evaluate, PolicyDecision
from src.reporting.evidence_bundle import build as build_evidence, DevinSessionResult, VulnerabilityContext
from src.observability.metrics import (
    record_policy_decision,
    record_breaking_change_handled,
    record_confidence,
    record_acu_cost,
    record_reviewer_minutes_saved,
)

# 1. Parse structured output from Devin session
structured = session_result.get("structured_output", {})
tests_passed = structured.get("tests_passed", False)
breaking_changes_detected = structured.get("breaking_changes_detected", False)
confidence = structured.get("confidence", 0.0)
files_touched = structured.get("files_touched", [])
changes_summary = structured.get("changes_summary", "No summary provided.")
breaking_changes_notes = structured.get("breaking_changes_notes", "")
reachability_assessment = structured.get("reachability_assessment", "")
notes = structured.get("notes", "")
devin_status = structured.get("status", "failed")

# 2. Run policy engine
policy_result = policy_evaluate(
    severity=vuln.severity,
    vuln_type=vuln.vuln_type,        # "dependency" | "sast" | "container"
    upgrade_type=vuln.upgrade_type,  # "patch" | "minor" | "major"
    tests_passed=tests_passed,
    breaking_changes_detected=breaking_changes_detected,
    confidence=confidence,
    files_touched=files_touched,
    reachability_assessment=reachability_assessment,
    devin_status=devin_status,
)

# 3. Emit metrics
record_policy_decision(policy_result.decision.value, vuln.severity, vuln.upgrade_type)
record_confidence(confidence, policy_result.decision.value)
if session_result.get("acu_used"):
    record_acu_cost(session_result["acu_used"], session_id, vuln.severity)
if breaking_changes_detected and policy_result.decision != PolicyDecision.BLOCKED:
    record_breaking_change_handled(vuln.package, vuln.severity)

# Estimate reviewer minutes saved
baseline_minutes = 120 if vuln.upgrade_type == "major" else 45
if policy_result.decision == PolicyDecision.AUTO_MERGE_READY:
    record_reviewer_minutes_saved(baseline_minutes, "auto_merge_ready")
elif policy_result.decision == PolicyDecision.HUMAN_REVIEW:
    record_reviewer_minutes_saved(baseline_minutes * 0.8, "human_review")

# 4. Build evidence bundle and post to GitHub PR / issue
evidence_md = build_evidence(
    vuln=VulnerabilityContext(
        cve_id=vuln.cve_id,
        package=vuln.package,
        current_version=vuln.current_version,
        fixed_version=vuln.fixed_version,
        severity=vuln.severity,
        advisory_url=vuln.advisory_url or "",
        upgrade_type=vuln.upgrade_type,
    ),
    result=DevinSessionResult(
        session_id=session_id,
        pr_url=session_result.get("pull_request_url"),
        status=devin_status,
        changes_summary=changes_summary,
        tests_passed=tests_passed,
        breaking_changes_detected=breaking_changes_detected,
        breaking_changes_notes=breaking_changes_notes,
        reachability_assessment=reachability_assessment,
        confidence=confidence,
        files_touched=files_touched,
        notes=notes,
        duration_seconds=session_result.get("duration_seconds", 0),
        acu_used=session_result.get("acu_used", 0.0),
    ),
    policy=policy_result,
)
# Post evidence_md to the GitHub PR body and/or issue comment
# (use the existing github_reporter functions)

# 5. Apply GitHub PR label based on policy decision
if policy_result.decision == PolicyDecision.AUTO_MERGE_READY:
    # add label: "shieldops:auto-merge-ready"
    pass
elif policy_result.decision == PolicyDecision.HUMAN_REVIEW:
    # add label: "needs-human"
    pass
elif policy_result.decision == PolicyDecision.BLOCKED:
    # add label: "shieldops:blocked"
    # fire a Datadog event at "error" level
    pass
```

Adapt variable names to match whatever the existing codebase uses for the session result and vulnerability objects.

**Done when:** The `/scan` endpoint runs without import errors, and after a (mocked) session result, the policy decision is logged and a metric is emitted.

---

## TASK 13 — Create `scripts/demo_replay.py`: deterministic demo replay script

**File to create:** `scripts/demo_replay.py`  
**What exists:** `scripts/demo.py` exists for throughput demonstration.  
**What to do:** Create a separate script that replays a pre-captured hero session in a deterministic way — suitable for the Loom demo recording without burning ACU budget live.

The script should:
1. Accept a `--mode` flag: `live` (real Devin session) or `replay` (use cached artifacts).
2. In `replay` mode, load session artifacts from `docs/hero_session/` (a directory you should also create with placeholder files: `session_result.json`, `pr_diff.txt`, `test_output.txt`).
3. Pass the loaded session result through the real policy engine and evidence bundle builder.
4. Post the evidence bundle to a specified GitHub issue (passed as `--issue-url`).
5. Print a step-by-step narration to stdout, suitable for following along during screen recording:
   ```
   [00:00] Starting ShieldOps demo replay
   [00:01] Loading vulnerability: CVE-2023-30861 — Flask 2.2.5 → 3.0.3 (MAJOR, HIGH)
   [00:02] Triage score: 87/100 | Upgrade type: major | Reachable: YES
   [00:03] Devin session: [replaying from cached artifacts]
   [00:08] First attempt: tests FAILED — 3 import errors in superset/views/
   [00:12] Devin reads Flask 3.0 migration guide...
   [00:18] Devin fixes 3 call sites across 2 files
   [00:24] Re-running tests... PASSED (247/247)
   [00:25] Policy engine: HUMAN_REVIEW (major version bump + breaking changes)
   [00:26] Evidence bundle built — posting to GitHub issue...
   [00:27] ✅ Demo complete. PR URL: [from session_result.json]
   ```
6. In `live` mode, actually call the Devin API and run the full pipeline on `CVE-2023-30861` against the Flask dependency.

**Done when:** `python scripts/demo_replay.py --mode replay --issue-url https://github.com/gaurav21/superset/issues/2` runs without errors and prints the narration steps.

---

## Execution Order Summary

Run in this exact sequence — tasks build on each other:

```
TASK 1  → requirements.txt (foundation for all imports)
TASK 2  → policy.py (needed by tasks 6, 12)
TASK 3  → evidence_bundle.py (needed by tasks 12, 13)
TASK 4  → prompt_builder.py (can run in parallel with 3)
TASK 5  → session_manager.py (can run in parallel with 3-4)
TASK 6  → metrics.py (needed by task 12)
TASK 7  → dashboard.py (independent, needs task 6 metric names)
TASK 8  → monitors.py (independent)
TASK 9  → reachability heuristic (independent)
TASK 10 → setup_superset_issues.py (independent, but run after repo exists)
TASK 11 → README.md (independent, do last to reflect all changes)
TASK 12 → main.py wiring (depends on tasks 2, 3, 6)
TASK 13 → demo_replay.py (depends on tasks 2, 3 — do last)
```

---

## One task you must do manually (not for the coding agent)

**Fork Apache Superset** to your GitHub account (`gaurav21/superset`), then run Task 10 against it. After that, trigger a real Devin session on Issue #2 (the Flask 3.0 breaking-change case) using `--mode live` from Task 13. Capture the session artifacts (session_result.json, pr_diff.txt, test_output.txt) and save them to `docs/hero_session/`. This is the only step that requires you directly — everything else above is agent-executable.
