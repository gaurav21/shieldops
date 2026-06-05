# 🛡️ ShieldOps — Trust Control Plane for Autonomous Security Remediation

> Devin AI + Datadog + GitHub — from scan to verified fix, autonomously.

ShieldOps orchestrates **autonomous coding agents** to remediate security vulnerabilities that existing tools can't touch. Dependabot bumps versions and walks away when the build breaks. ShieldOps reads the CHANGELOG, fixes the call sites, iterates until green, and routes the change through a policy boundary so a human can approve it in two minutes.

## The Problem

Detection is solved. SAST, DAST, SCA — the scanner market is commoditized. What isn't solved is **remediation**.

- Industry MTTR for critical vulnerabilities: **60–90 days**
- Dependabot PRs that merge without human intervention: **~40%**
- The other 60%? Build breaks. The PR sits red. An engineer closes it with "needs investigation." The CVE stays open.

**The 20% of vulnerabilities that break the build are 100% of the pain.**

## How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                     ShieldOps Pipeline                           │
│                                                                  │
│  Scan ──▶ Triage ──▶ Devin Fleet ──▶ Policy Boundary ──▶ Ship   │
│                                          │                       │
│                                    ┌─────┴─────┐                │
│                                    │           │                 │
│                               Auto-merge   Human Review   Block  │
│                                    │           │            │    │
│                                    ▼           ▼            ▼    │
│                               GitHub PR   Evidence     Alert +   │
│                                merged     Bundle       Escalate  │
│                                                                  │
│  Every step ──▶ Datadog (metrics, events, audit trail)           │
└──────────────────────────────────────────────────────────────────┘
```

| Stage | What Happens |
|-------|-------------|
| **01 — Scan** | `pip-audit`, `npm audit`, `trivy`, `semgrep` — consumes any scanner output |
| **02 — Triage** | Severity × reachability × fix availability × complexity → ranked list with labels |
| **03 — Devin Fleet** | Context-aware prompts. Reads CHANGELOGs, fixes breaking call sites, iterates on test failures |
| **04 — Policy Boundary** | Auto-merge (high confidence, tests pass) · Human review (breaking change, evidence bundle) · Block (low confidence, tests fail) |
| **05 — Evidence Bundle** | What changed, why, blast radius, confidence score — 2-minute reviewer approval |
| **06 — Datadog** | Fleet health, trust split, cost per fix, full audit trail |

## Real Results: Apache Superset (500K LOC)

We pointed ShieldOps at [Apache Superset](https://github.com/apache/superset) — 500K lines of Python, 200+ dependencies.

### The Hero: Flask 2.3.3 → 3.x

Dependabot opens a PR bumping Flask. Build breaks — breaking imports, changed APIs. PR sits red forever.

**Devin read the Flask 3.x CHANGELOG, found all version constraints across 5 files, updated `pyproject.toml`, `requirements/base.txt`, `requirements/development.txt`, fixed integration test imports, fixed security dataset tests, and verified no breaking API calls remained.**

Result: [**PR #10**](https://github.com/gaurav21/superset/pull/10) — `+11/−12` across 5 files. Clean. Mergeable. Zero human intervention.

### All Devin-Authored PRs

| PR | What | Changes | Link |
|----|------|---------|------|
| **#8** | Dockerfile hardening — SHA256 digests, dev-pkg cleanup, healthcheck | `+20/−4` | [View PR](https://github.com/gaurav21/superset/pull/8) |
| **#9** | Paramiko CVE-2026-44405 — 3.5.1→5.0.0, breaking changes handled | `+8/−4` | [View PR](https://github.com/gaurav21/superset/pull/9) |
| **#10** | **Flask 2.3→3.x — major version upgrade across 500K LOC codebase** | `+11/−12` | [View PR](https://github.com/gaurav21/superset/pull/10) |

Plus **7 auto-created issues** with severity labels (1 CRITICAL, 3 HIGH, 2 MEDIUM) and **4 PRs improving ShieldOps itself** (error handling, security fixes, unit tests 0→40%, code refactoring).

### Key Metrics

| Metric | Value |
|--------|-------|
| Devin sessions launched | 3 |
| PRs delivered | 3 |
| Time to first PR | < 8 minutes |
| Human intervention rate | 0% |
| Breaking changes handled | 2 (paramiko + Flask) |

## The Trust Boundary

ShieldOps isn't removing the human — it's making the human's job trivial.

| Tier | When | What Happens |
|------|------|-------------|
| 🟢 **Auto-Merge** | Tests pass, no breaking changes, high confidence, patch/minor | PR merges automatically |
| 🟡 **Human Review** | Major upgrade, breaking changes fixed, sensitive paths | Evidence bundle → 2-minute approval |
| 🔴 **Block** | Tests fail or confidence too low | Nothing merges. Alert fires. Human loops in. |

## Architecture

```
src/
├── main.py                          # FastAPI app + orchestrator
├── config.py                        # Environment configuration
├── scanner/
│   ├── vulnerability_scanner.py     # Multi-scanner ingestion
│   ├── issue_creator.py             # Auto-create GitHub issues
│   └── models.py                    # Vulnerability data models
├── orchestrator/
│   ├── devin_client.py              # Devin REST API wrapper
│   ├── session_manager.py           # Session lifecycle + polling
│   ├── triage.py                    # Priority scoring engine
│   └── prompt_builder.py            # Context-aware prompts
├── policy/
│   ├── boundary.py                  # Auto-merge / review / block
│   └── evidence.py                  # Evidence bundle generation
├── observability/
│   ├── metrics.py                   # Custom Datadog metrics
│   ├── events.py                    # Lifecycle event tracking
│   ├── dashboard.py                 # Dashboard creation via API
│   └── monitors.py                  # Alert + SLO creation
└── webhooks/
    ├── github_webhook.py            # GitHub event handler
    └── scheduler.py                 # Cron-based scan scheduler
```

## Quick Start

```bash
git clone https://github.com/gaurav21/shieldops.git
cd shieldops
cp .env.example .env
# Add your API keys: DEVIN_API_KEY, GITHUB_TOKEN, DD_API_KEY, DD_APP_KEY

docker compose up --build

# Create Datadog dashboard + monitors
curl -X POST http://localhost:8000/setup/datadog

# Trigger a scan
curl -X POST http://localhost:8000/scan
```

## Datadog Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `shieldops.vulnerabilities.open` | Gauge | Current open vulnerabilities |
| `shieldops.vulnerabilities.fixed` | Gauge | Total fixed |
| `shieldops.devin.sessions.active` | Gauge | Currently running sessions |
| `shieldops.devin.session.duration_seconds` | Gauge | Time per session |
| `shieldops.remediation.mttr_seconds` | Gauge | Mean Time to Remediate |
| `shieldops.remediation.prs_created` | Count | PRs opened by Devin |
| `shieldops.remediation.success_rate` | Gauge | % successful remediations |
| `shieldops.policy.auto_merged` | Count | PRs auto-merged |
| `shieldops.policy.human_reviewed` | Count | PRs sent to human review |
| `shieldops.policy.blocked` | Count | PRs blocked |

## Links

- 📊 [Presentation](https://avyay.ai/blog/shieldops-autonomous-security) — Full technical walkthrough
- 🐙 [Demo target repo](https://github.com/gaurav21/superset) — Apache Superset fork with all PRs + issues

## Why Not Just Dependabot?

| | Dependabot | ShieldOps + Devin |
|---|---|---|
| Patch/minor bumps | ✅ | ✅ |
| Breaking-change upgrades | ❌ Opens a red PR, stops | ✅ Fixes call sites, iterates to green |
| Reads CHANGELOGs | ❌ | ✅ |
| Reachability analysis | ❌ | ✅ |
| Policy routing (auto-merge / review / block) | ❌ | ✅ |
| Evidence bundle for reviewer | ❌ | ✅ |

---

*Built by [Gaurav Sharma](https://github.com/gaurav21) — [Avyay AI](https://avyay.ai)*
