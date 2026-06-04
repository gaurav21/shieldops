# 🛡️ ShieldOps — Autonomous Security Remediation Platform

> **Scan → Triage → Fix → Verify → Report — All Automatically**

ShieldOps is an event-driven automation platform that detects security vulnerabilities in your codebase and uses [Devin AI](https://devin.ai) to automatically remediate them — with full [Datadog](https://datadoghq.com) observability.

![Architecture](docs/architecture-diagram.png)

## 🎯 The Problem

Every engineering team faces the same security debt spiral:
- Vulnerability scanners find 50+ issues per quarter
- Engineers are busy shipping features — nobody wants to touch dependency upgrades
- Security tickets sit in backlog for weeks or months
- Compliance asks "What's your mean time to remediate?" — awkward silence

**ShieldOps changes that.** Vulnerabilities get found, triaged, and fixed autonomously — while your engineers focus on what matters.

## ⚡ How It Works

```
GitHub Webhook / Scheduled Scan
        │
        ▼
┌─────────────────────────┐
│  ShieldOps Orchestrator │
│                         │
│  1. Scan (pip-audit,    │     ┌──────────────┐
│     npm audit, trivy,   │────▶│  Devin AI    │
│     semgrep)            │     │  Sessions    │
│  2. Triage & prioritize │     │              │
│  3. Create GitHub issues│     │  • Fix vuln  │
│  4. Dispatch to Devin   │     │  • Run tests │
│  5. Track & report      │     │  • Create PR │
│                         │     └──────────────┘
└────────────┬────────────┘
             │
    ┌────────▼────────┐
    │    Datadog      │
    │                 │
    │ • Dashboard     │
    │ • Metrics       │
    │ • Monitors      │
    │ • Events        │
    └─────────────────┘
```

### Event-Driven Triggers

| Trigger | How It Works |
|---------|-------------|
| **GitHub Webhook** | Issue labeled `devin-auto-fix` → Devin starts working |
| **New Security Issue** | Issue created with `security` label → auto-remediation |
| **Scheduled Scan** | Daily cron scans the repo → finds new vulns → creates issues → Devin fixes |
| **Manual API** | `POST /scan` → trigger on demand |

### Smart Triage

Not all vulnerabilities are equal. ShieldOps scores each one:
- **Severity** (40%) — Critical > High > Medium > Low
- **Fix Available** (25%) — Known fix version gets priority
- **Type** (20%) — Dependency upgrades (easy) vs SAST findings (complex)
- **Age** (15%) — Older vulnerabilities escalate

### Datadog Observability

The **ShieldOps Command Center** dashboard answers the VP's question: *"Is this working?"*

- 📊 Open vulnerabilities (burn-down chart)
- 🤖 Active Devin sessions
- ✅ Success rate
- ⏱️ Mean Time to Remediate
- 📈 PRs created over time
- 🚨 Alerts on failures

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- [Devin API Key](https://docs.devin.ai/api-reference/overview)
- [GitHub Personal Access Token](https://github.com/settings/tokens) (repo scope)
- [Datadog API & App Keys](https://app.datadoghq.com/organization-settings/api-keys)

### 1. Clone & Configure

```bash
git clone https://github.com/gsharma21/devin-devsecsops.git
cd devin-devsecsops
cp .env.example .env
# Edit .env with your API keys
```

### 2. Run

```bash
docker compose up --build
```

### 3. Setup Datadog Dashboard

```bash
curl -X POST http://localhost:8000/setup/datadog
```

### 4. Trigger a Scan

```bash
# Manual scan
curl -X POST http://localhost:8000/scan

# Or configure the GitHub webhook:
# Settings → Webhooks → Add webhook
# URL: https://your-domain/webhook/github
# Events: Issues, Pull requests
```

### 5. Monitor

```bash
# Check pipeline status
curl http://localhost:8000/status

# View metrics
curl http://localhost:8000/metrics

# Health check
curl http://localhost:8000/health
```

## 📊 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/health` | GET | Health check (Devin API connectivity) |
| `/status` | GET | Full pipeline status with vulnerability list |
| `/metrics` | GET | Current pipeline metrics |
| `/scan` | POST | Trigger manual vulnerability scan |
| `/setup/datadog` | POST | Create Datadog dashboard & monitors |
| `/webhook/github` | POST | GitHub webhook receiver |

## 🏗️ Architecture

```
src/
├── main.py                    # FastAPI app + ShieldOps orchestrator
├── config.py                  # Configuration from environment
│
├── scanner/                   # Vulnerability detection
│   ├── vulnerability_scanner.py   # pip-audit, npm audit, trivy, semgrep
│   ├── issue_creator.py           # Create GitHub issues from findings
│   └── models.py                  # Vulnerability & scan data models
│
├── orchestrator/              # Devin session management
│   ├── devin_client.py            # Devin REST API wrapper
│   ├── session_manager.py         # Session lifecycle & polling
│   ├── triage.py                  # Priority scoring engine
│   └── prompt_builder.py          # Context-aware Devin prompts
│
├── webhooks/                  # Event sources
│   ├── github_webhook.py          # GitHub webhook handler
│   └── scheduler.py               # Cron-based scan scheduler
│
├── observability/             # Datadog integration
│   ├── metrics.py                 # Custom metric emission
│   ├── events.py                  # Lifecycle event tracking
│   ├── dashboard.py               # Dashboard creation via API
│   └── monitors.py                # Alert & SLO creation
│
└── reporting/                 # Status reporting
    └── github_reporter.py         # Issue comment updates
```

## 🔑 Datadog Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `shieldops.vulnerabilities.open` | Gauge | Current open vulnerabilities |
| `shieldops.vulnerabilities.fixed` | Gauge | Total fixed vulnerabilities |
| `shieldops.vulnerabilities.by_severity` | Gauge | Open vulns by severity tag |
| `shieldops.devin.sessions.created` | Count | Devin sessions started |
| `shieldops.devin.sessions.completed` | Count | Sessions finished successfully |
| `shieldops.devin.sessions.failed` | Count | Sessions that errored |
| `shieldops.devin.sessions.active` | Gauge | Currently running sessions |
| `shieldops.devin.session.duration_seconds` | Gauge | Time per session |
| `shieldops.remediation.mttr_seconds` | Gauge | Mean Time to Remediate |
| `shieldops.remediation.prs_created` | Count | PRs opened by Devin |
| `shieldops.remediation.success_rate` | Gauge | % successful remediations |
| `shieldops.scan.duration_seconds` | Gauge | Scan execution time |
| `shieldops.scan.vulnerabilities_found` | Gauge | Vulns found per scan |

## 🎥 Demo Video

[Watch the 5-minute Loom walkthrough →](#)

## 📝 Blog Post

[Building an Autonomous DevSecOps Pipeline with Devin + Datadog →](#)

## 🌐 Presentation

[ShieldOps Technical Presentation →](#)

---

## Why Devin?

Traditional approaches to vulnerability remediation:
1. **Manual** — Engineer reads advisory, upgrades package, tests, creates PR. Takes hours per vulnerability.
2. **Dependabot** — Creates PRs but doesn't handle breaking changes, complex upgrades, or SAST findings.
3. **ShieldOps + Devin** — Understands the codebase, reads changelogs, handles breaking changes, runs tests, iterates on failures.

Devin isn't just a bot that bumps version numbers. It's an autonomous agent that can:
- Read a CVE advisory and understand the impact
- Navigate a complex monorepo (Superset: 500K+ lines)
- Handle cascading dependency changes
- Fix test failures caused by upgrades
- Write meaningful PR descriptions

That's the difference between automation and intelligence.

---

*Built by [Gaurav Sharma](https://github.com/gsharma21) as a demonstration of event-driven AI-powered DevSecOps.*
