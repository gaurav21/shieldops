# 🛡️ ShieldOps — Trust Control Plane for Autonomous Security Remediation

> Devin AI + Datadog + GitHub — from scan to verified fix, autonomously.

ShieldOps orchestrates **autonomous coding agents** to remediate security vulnerabilities that existing tools can't touch. Dependabot bumps versions and walks away when the build breaks. ShieldOps reads the CHANGELOG, fixes the call sites, iterates until green, and routes the change through a policy boundary so a human can approve it in two minutes.

## The Problem

Detection is solved. SAST, DAST, SCA — the scanner market is commoditized. What isn't solved is **remediation**.

- Industry MTTR for critical vulnerabilities: **60–90 days**
- Dependabot PRs that merge without human intervention: **~40%**
- The other 60%? Build breaks. The PR sits red. An engineer closes it with "needs investigation." The CVE stays open.

**The 20% of vulnerabilities that break the build are 100% of the pain.**

## Architecture

```
                    ┌─────────────────────────────────┐
                    │         GitHub Issues            │
                    │  (labeled with "shieldops")      │
                    └──────────┬──────────────────────┘
                               │ webhook POST
                               ▼
                    ┌─────────────────────────────────┐
                    │       trigger.py (FastAPI)       │
                    │  • HMAC signature verification   │
                    │  • Issue triage                  │
                    │  • Dedup on repo#issue           │
                    │  • Returns 200 in <1s            │
                    └──────────┬──────────────────────┘
                               │ asyncio.create_task
                               ▼
                    ┌─────────────────────────────────┐
                    │     Devin Session (background)   │
                    │  • Prompt from issue context     │
                    │  • Structured output schema      │
                    │  • Poll every 15s until terminal │
                    └──────────┬──────────────────────┘
                               │ terminal status
                               ▼
                    ┌─────────────────────────────────┐
                    │       Policy Engine              │
                    │  🟢 Auto-merge (high confidence) │
                    │  🟡 Human review (breaking/major)│
                    │  🔴 Blocked (tests fail/low conf)│
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────┴──────────────────────┐
                    │  Evidence Bundle → GitHub issue  │
                    │  Labels applied to issue/PR      │
                    │  Metrics → Datadog               │
                    │  Events → Datadog                │
                    │  State → /status endpoint        │
                    └─────────────────────────────────┘
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook/github` | POST | GitHub webhook receiver — verifies signature, triggers Devin |
| `/status` | GET | Live state — counts, sessions, audit events (no Datadog needed) |
| `/health` | GET | Health check — app up? Devin API reachable? |

## Quick Start

### Prerequisites

- Python 3.11+
- [Devin API key](https://docs.devin.ai)
- [GitHub token](https://github.com/settings/tokens) with repo access
- [Datadog API key](https://app.datadoghq.com/organization-settings/api-keys) (optional)
- [gh CLI](https://cli.github.com/) (for creating demo issues)

### 1. Setup

```bash
git clone https://github.com/gaurav21/shieldops.git
cd shieldops
cp .env.example .env
# Edit .env — add your DEVIN_API_KEY, GITHUB_TOKEN, GITHUB_WEBHOOK_SECRET

pip install -r requirements.txt
```

### 2. Run Locally

```bash
# Start the webhook server
uvicorn trigger:app --host 0.0.0.0 --port 8000

# Verify it's running
curl http://localhost:8000/health
```

### 3. Expose via Tunnel (for GitHub webhooks)

```bash
# Option A: ngrok
ngrok http 8000

# Option B: Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8000

# Option C: Tailscale Funnel
tailscale funnel 8000
```

Then configure the tunnel URL as a GitHub webhook:
- **URL:** `https://<your-tunnel>/webhook/github`
- **Content type:** `application/json`
- **Secret:** Same as `GITHUB_WEBHOOK_SECRET` in `.env`
- **Events:** Select "Issues"

### 4. Create Demo Issues

```bash
# Creates 4 labeled issues that trigger ShieldOps
python scripts/create_issues.py
```

### 5. Watch It Work

```bash
# Check live status
curl http://localhost:8000/status | python -m json.tool

# Watch the logs
# (uvicorn output shows session creation, polling, policy decisions)
```

### 6. Local Replay Testing (no GitHub webhook needed)

```bash
# Set SKIP_SIGNATURE_CHECK=1 in .env, then:
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

## How It Works

### Event Flow

1. **Issue Created/Labeled** → GitHub sends webhook to `/webhook/github`
2. **Signature Verified** → HMAC-SHA256 check (or skip for local testing)
3. **Triage** → Severity, type, predicted policy route determined from labels/title
4. **Dedup** → `repo#issue` key prevents double-launches on re-labeling
5. **Devin Session** → Background task creates session with structured output schema
6. **Poll** → Every 15s until terminal status (finished/stopped/error/timed_out)
7. **Policy** → Structured output fed to policy engine → auto-merge / human-review / blocked
8. **Evidence** → Markdown bundle posted as issue comment
9. **Labels** → `auto-merge-ready` / `needs-human-review` / `blocked` applied
10. **Metrics** → DogStatsD + Datadog Events for full observability

### The Trust Boundary

| Tier | When | What Happens |
|------|------|-------------|
| 🟢 **Auto-Merge** | Tests pass, no breaking changes, high confidence, patch/minor | PR merges automatically |
| 🟡 **Human Review** | Major upgrade, breaking changes fixed, sensitive paths | Evidence bundle → 2-minute approval |
| 🔴 **Block** | Tests fail or confidence too low | Nothing merges. Alert fires. Human loops in. |

## Real Results: Apache Superset (500K LOC)

We pointed ShieldOps at [Apache Superset](https://github.com/apache/superset) — 500K lines of Python, 200+ dependencies.

### The Hero: Flask 2.3.3 → 3.x

Dependabot opens a PR bumping Flask. Build breaks — breaking imports, changed APIs. PR sits red forever.

**Devin read the Flask 3.x CHANGELOG, found all version constraints across 5 files, updated `pyproject.toml`, `requirements/base.txt`, `requirements/development.txt`, fixed integration test imports, fixed security dataset tests, and verified no breaking API calls remained.**

Result: [**PR #10**](https://github.com/gaurav21/superset/pull/10) — `+11/−12` across 5 files. Clean. Mergeable.

### All Devin-Authored PRs

| PR | What | Changes | Link |
|----|------|---------|------|
| **#8** | Dockerfile hardening — SHA256 digests, dev-pkg cleanup, healthcheck | `+20/−4` | [View PR](https://github.com/gaurav21/superset/pull/8) |
| **#9** | Paramiko CVE-2026-44405 — 3.5.1→5.0.0, breaking changes handled | `+8/−4` | [View PR](https://github.com/gaurav21/superset/pull/9) |
| **#10** | **Flask 2.3→3.x — major version upgrade across 500K LOC codebase** | `+11/−12` | [View PR](https://github.com/gaurav21/superset/pull/10) |

## Datadog Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `shieldops.devin.sessions.created` | Count | Sessions launched |
| `shieldops.devin.sessions.completed` | Count | Sessions finished |
| `shieldops.devin.sessions.failed` | Count | Sessions that failed |
| `shieldops.devin.sessions.active` | Gauge | Currently running |
| `shieldops.policy.decision` | Count | Policy decisions by type |
| `shieldops.remediation.confidence` | Gauge | Devin confidence per session |
| `shieldops.remediation.breaking_changes_handled` | Count | Breaking changes fixed |
| `shieldops.remediation.reviewer_minutes_saved` | Gauge | Estimated time saved |
| `shieldops.devin.cost_acu` | Gauge | ACU cost per session |

## Project Structure

```
├── trigger.py                       # 🎯 Event-driven entry point (FastAPI)
├── src/
│   ├── config.py                    # Environment configuration
│   ├── orchestrator/
│   │   ├── devin_client.py          # Devin REST API wrapper
│   │   ├── session_manager.py       # Session lifecycle + polling
│   │   ├── triage.py                # Priority scoring engine
│   │   ├── policy.py                # Auto-merge / review / block boundary
│   │   └── prompt_builder.py        # Context-aware Devin prompts
│   ├── reporting/
│   │   ├── evidence_bundle.py       # 2-minute reviewer approval packet
│   │   └── github_reporter.py       # Issue/PR comment posting
│   ├── observability/
│   │   ├── state.py                 # In-memory state for /status
│   │   ├── metrics.py               # DogStatsD metric emission
│   │   ├── events.py                # Datadog event tracking
│   │   ├── dashboard.py             # Dashboard creation via API
│   │   └── monitors.py              # Alert + SLO creation
│   └── scanner/
│       ├── models.py                # Vulnerability data models
│       ├── vulnerability_scanner.py # Multi-scanner ingestion
│       └── issue_creator.py         # GitHub issue creation
├── scripts/
│   └── create_issues.py             # Create demo issues with `gh`
├── requirements.txt
├── .env.example
└── README.md
```

## Why Not Just Dependabot?

| | Dependabot | ShieldOps + Devin |
|---|---|---|
| Patch/minor bumps | ✅ | ✅ |
| Breaking-change upgrades | ❌ Opens a red PR, stops | ✅ Fixes call sites, iterates to green |
| Reads CHANGELOGs | ❌ | ✅ |
| Reachability analysis | ❌ | ✅ |
| Policy routing (auto-merge / review / block) | ❌ | ✅ |
| Evidence bundle for reviewer | ❌ | ✅ |
| Datadog observability | ❌ | ✅ |

## Links

- 📊 [Presentation](https://avyay.ai/blog/shieldops-autonomous-security) — Full technical walkthrough
- 🐙 [Demo target repo](https://github.com/gaurav21/superset) — Apache Superset fork with all PRs + issues

---

*Built by [Gaurav Sharma](https://github.com/gaurav21) — [Avyay AI](https://avyay.ai)*
