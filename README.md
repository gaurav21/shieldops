# 🛡️ ShieldOps — Autonomous Security Remediation with Devin AI

> From vulnerability scan to verified PR — autonomously. Devin AI + Datadog + GitHub.

ShieldOps orchestrates **autonomous coding agents** to remediate security vulnerabilities that existing tools can't touch. Dependabot bumps versions and walks away when the build breaks. ShieldOps reads the CHANGELOG, fixes the call sites, iterates until green, and routes the change through a policy boundary so a human can approve it in two minutes.

**Live demo target:** [Apache Superset](https://github.com/apache/superset) — 500K LOC, 200+ Python dependencies.

### 🎥 [Watch the 5-minute demo](https://www.loom.com/share/ce5d7d5ce927444cad7ddc92cf75c74f)

[![ShieldOps Demo](https://cdn.loom.com/sessions/thumbnails/ce5d7d5ce927444cad7ddc92cf75c74f-with-play.gif)](https://www.loom.com/share/ce5d7d5ce927444cad7ddc92cf75c74f)

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Devin API key](https://app.devin.ai/) (`cog_` prefix)
- [GitHub personal access token](https://github.com/settings/tokens) with `repo` scope
- [Datadog API & App keys](https://app.datadoghq.com/organization-settings/api-keys) *(optional — observability works without Datadog via `/status`)*

### 1. Clone and configure

```bash
git clone https://github.com/gaurav21/shieldops.git
cd shieldops
cp .env.example .env
```

Edit `.env` with your keys:

```env
# Required
DEVIN_API_KEY=cog_your_key_here       # From https://app.devin.ai/
DEVIN_ORG_ID=org-your_org_id          # Your Devin organization ID

# Required for webhook trigger
GITHUB_TOKEN=ghp_your_token_here      # GitHub PAT with repo scope
GITHUB_REPO_OWNER=your_username       # Your GitHub username
GITHUB_REPO_NAME=superset             # Target repository name
GITHUB_WEBHOOK_SECRET=your_secret     # Any string — must match GitHub webhook config

# Optional (Datadog observability)
DD_API_KEY=your_dd_api_key            # Datadog API key
DD_APP_KEY=your_dd_app_key            # Datadog Application key
DD_SITE=datadoghq.com                 # Or your Datadog region (e.g., us5.datadoghq.com)
```

### 2. Run with Docker

```bash
docker compose up -d
```

### 3. Verify

```bash
# Health check — should return {"ok": true, "devin_api": true}
curl http://localhost:8000/health

# Live status — counters, sessions, audit log
curl http://localhost:8000/status
```

### 4. Open the Dashboard

Open **http://localhost:8000** in your browser. The ShieldOps control plane dashboard shows:

- **Metric cards** — Active / Completed / Blocked / Auto-Merge / Human Review (click to filter)
- **Devin Sessions (Live)** — real-time status of all Devin sessions in your org
- **Sessions table** — triage results, policy decisions, confidence scores, PR links
- **Audit log** — every event: webhook received, session created, policy decision, evidence posted
- **Action buttons** — trigger demo issues directly from the UI (no GitHub webhook needed)

No Datadog required — the dashboard works standalone out of the box.

### 4. Run without Docker

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn trigger:app --host 0.0.0.0 --port 8000
```

## How It Works

### Event-Driven Pipeline

```
GitHub Issue (labeled "shieldops")
    │ webhook POST
    ▼
ShieldOps Orchestrator (FastAPI)
    │ • HMAC signature verification
    │ • Severity triage
    │ • Dedup on repo#issue
    │ • Returns 200 in <1s
    ▼
Devin Session (autonomous, background)
    │ • Structured output contract
    │ • Polls every 15s until terminal
    ▼
Policy Engine (Trust Boundary)
    ├── 🟢 AUTO-MERGE    — tests pass, high confidence, patch/minor
    ├── 🟡 HUMAN REVIEW  — major upgrade, breaking changes, sensitive paths
    └── 🔴 BLOCKED       — tests fail, low confidence, Devin errored
    │
    ▼
Evidence Bundle → GitHub PR comment + labels
Metrics → Datadog (14 custom metrics, 4 monitors)
Events → Audit trail (/status endpoint)
```

### Triggering Remediation

**Option A: GitHub Webhook (production)**

Configure a webhook on your fork:
- **URL:** `https://your-public-url/webhook/github`
- **Content type:** `application/json`
- **Secret:** Same as `GITHUB_WEBHOOK_SECRET` in `.env`
- **Events:** Select "Issues"

Then create an issue with the `shieldops` label — ShieldOps handles the rest.

**Option B: Local Replay (no webhook needed)**

Set `SKIP_SIGNATURE_CHECK=1` in `.env`, then:

```bash
curl -X POST http://localhost:8000/webhook/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issues" \
  -d '{
    "action": "labeled",
    "issue": {
      "number": 1,
      "title": "[CRITICAL] Flask 2.3.3 EOL — upgrade to Flask 3.x",
      "body": "Flask 2.3.3 has reached end-of-life. Upgrade to 3.x.",
      "labels": [{"name": "shieldops"}, {"name": "critical"}]
    }
  }'
```

**Option C: Dashboard UI**

Open `http://localhost:8000` and click any of the demo issue buttons to trigger a session.

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web dashboard — live sessions, metrics, actions |
| `/health` | GET | Health check (app + Devin API connectivity) |
| `/status` | GET | Full state: counters, sessions, audit events, live Devin fleet |
| `/devin/sessions` | GET | List all Devin sessions in the org |
| `/webhook/github` | POST | GitHub webhook receiver (HMAC-verified) |
| `/api/simulate` | POST | Trigger demo sessions from the dashboard |

## The Trust Boundary

ShieldOps never auto-merges anything risky. Every Devin session returns a **structured output contract**:

```json
{
  "status": "success",
  "tests_passed": true,
  "breaking_changes_detected": true,
  "confidence": 0.92,
  "files_touched": ["requirements/base.txt", "superset/views/base.py"],
  "reachability_assessment": "reachable — used in security-critical paths",
  "changes_summary": "Upgraded Flask 2.3.3 → 3.1.1, fixed 3 breaking changes"
}
```

The policy engine (`src/orchestrator/policy.py`) routes each result:

| Decision | When | What Happens |
|----------|------|-------------|
| 🟢 **Auto-Merge** | Tests pass, confidence ≥80%, patch/minor, no sensitive paths | PR labeled `auto-merge-ready` |
| 🟡 **Human Review** | Major upgrade, breaking changes, sensitive paths, or 50-80% confidence | Evidence bundle posted, PR labeled `needs-human-review` |
| 🔴 **Blocked** | Tests fail, confidence <50%, or Devin errored | Alert fired, nothing merges |

## Real Results: Apache Superset

| PR | What | Decision | Details |
|----|------|----------|---------|
| [#10](https://github.com/gaurav21/superset/pull/10) | **Flask 2.3.3 → 3.x** (the hero) | 🟡 Human Review | 5 files, 3 breaking changes handled, 7,700 tests passing |
| [#18](https://github.com/gaurav21/superset/pull/18) | PyJWT CVE fix | 🟢 Auto-Merged | Full autonomous loop — scan → fix → test → merge |
| [#9](https://github.com/gaurav21/superset/pull/9) | Paramiko CVE-2026-44405 | 🟢 Auto-Merge Ready | Breaking changes handled cleanly |
| [#8](https://github.com/gaurav21/superset/pull/8) | Dockerfile hardening | 🟢 Auto-Merge Ready | SHA256 digests, dev-pkg cleanup, healthcheck |
| [#11](https://github.com/gaurav21/superset/pull/11) | npm audit findings | 🟡 Human Review | Multiple frontend dependency fixes |
| [#12](https://github.com/gaurav21/superset/pull/12) | Flask EOL (second run) | 🟡 Human Review | Additional Flask remediation |

**10 PRs** created across **10 Devin sessions**, **8+ vulnerabilities** remediated.

## Observability

### Without Datadog (always works)

- **`/status`** — live counters (active/completed/blocked), session state, policy decisions, audit trail
- **`/devin/sessions`** — real-time Devin fleet status
- **Web dashboard** at `/` — clickable metric cards, session tables, audit log

### With Datadog

ShieldOps creates a full observability suite:

- **Dashboard:** "ShieldOps — Agent Trust Control Plane" (6 widget groups)
- **14 custom metrics:** `shieldops.devin.*`, `shieldops.policy.*`, `shieldops.remediation.*`, `shieldops.vulnerabilities.*`
- **4 monitors:** failure rate, policy breach, stuck sessions, intervention rate
- **Events:** full audit trail in Event Explorer (`source:shieldops`)

## Project Structure

```
├── trigger.py                  # 🎯 FastAPI entry point — webhook + orchestration
├── src/
│   ├── config.py               # Environment configuration
│   ├── orchestrator/
│   │   ├── devin_client.py     # Devin REST API wrapper (v3 org-scoped)
│   │   ├── policy.py           # Trust boundary — auto-merge / review / block
│   │   ├── prompt_builder.py   # Context-aware prompts + structured output schema
│   │   ├── session_manager.py  # Session lifecycle + polling
│   │   └── triage.py           # Severity scoring engine
│   ├── observability/
│   │   ├── state.py            # Persistent state store (/status endpoint)
│   │   ├── metrics.py          # DogStatsD + HTTP metric emission
│   │   ├── events.py           # Datadog event tracking
│   │   ├── dashboard.py        # Programmatic dashboard creation
│   │   └── monitors.py         # Alerting monitor definitions
│   ├── reporting/
│   │   ├── evidence_bundle.py  # 2-minute reviewer approval packet
│   │   └── github_reporter.py  # Issue/PR comment + label posting
│   └── scanner/
│       ├── models.py           # Vulnerability data models
│       └── vulnerability_scanner.py
├── static/
│   └── dashboard.html          # Web dashboard UI
├── scripts/
│   └── create_issues.py        # Create demo issues via gh CLI
├── docs/
│   └── index.html              # Presentation site (GitHub Pages)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example                # All configuration variables
```

## Links

- 📊 [Presentation](https://gaurav21.github.io/shieldops/) — Architecture, decision tree, results
- 🐙 [Demo target repo](https://github.com/gaurav21/superset) — Apache Superset fork with all PRs + issues
- 📝 [Blog post](https://avyay.ai/blog/shieldops-autonomous-security) — Full technical deep-dive

---

*Built by [Gaurav Sharma](https://github.com/gaurav21)*
