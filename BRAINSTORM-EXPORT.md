# ShieldOps — Complete Project Export for Brainstorming

> **Use this document to brainstorm, critique, improve, and extend the project in another LLM session.**

---

## CONTEXT: Who Am I & What's This For

**Person:** Gaurav Sharma — Sales Engineer at Datadog, based in Singapore. Deep Datadog expertise. Systems thinker who ships fast. Builder mindset.

**Challenge:** Technical take-home for **Cognition (the company behind Devin AI)**. This is for a Sales Engineer / Solutions Engineer role. The evaluation is designed to simulate a real-world engagement with an engineering team adopting Devin.

**Time constraint:** 2-3 hours. Focus on a working end-to-end demo over polish.

**What they're evaluating:**
1. Translate ambiguous problems into working systems
2. Leverage Devin as a **core primitive** (not just a helper tool)
3. Communicate both **technical execution** and **business impact**

---

## THE CHALLENGE (Exact Brief)

### Part 1: Select a Use Case
- Fork/clone Apache Superset: https://github.com/apache/superset
- Identify and create issues in the fork (vulnerability findings, dependency upgrades, code quality issues)

### Part 2: Build an Event-Driven Automation
Using the Devin API (https://docs.devin.ai/api-reference/overview):
- Build a working automation that remediates the issues created
- Must be triggered by an event (webhook, repo activity, ticket creation, scan results, or scheduled/periodic trigger)
- Must programmatically initiate and manage Devin sessions
- Must produce observable outputs (PRs, issues, reports, status updates)

### Part 3: Incorporate Observability
- Basic analytics or reporting to demonstrate system effectiveness
- Status of active and completed tasks
- Success/failure signals
- Throughput or progress tracking
- Must answer: "If I were an engineering leader, how would I know this is working?"

### Deliverables
1. **Working project** — Devin successfully remediates the selected issues
2. **Loom video (5 min)** — Present to VP of Engineering + senior ICs:
   - What: Problem framing — what workflow problem, why it matters
   - How: Demo the system + walk through architecture/code
   - Why: Why Devin is uniquely suited (what's not possible without an autonomous coding agent)
   - When: Next steps for a real customer engagement
3. **GitHub repositories:**
   - Solution repo (with Docker, clear README)
   - Forked Superset with issues and remediations

---

## MY UNFAIR ADVANTAGES

1. **I'm a Datadog SE** — I can build production-grade observability that most candidates can't. Real dashboards, real monitors, real metrics. Not console.log.
2. **I have Datadog MCP tools** — I can programmatically create dashboards, monitors, SLOs, send events, and emit custom metrics through Datadog's API.
3. **"Pitch to a VP of Engineering"** — that's literally my day job. I know how to frame technical solutions as business value.
4. **Security vulnerability remediation** is a problem every VP loses sleep over — it's relatable, urgent, and measurable.

---

## THE PROJECT: ShieldOps — Autonomous Security Remediation Platform

### One-Sentence Pitch
"What if every security vulnerability in your codebase was automatically detected, triaged, fixed by an AI agent, and verified — with a Datadog dashboard showing your VP exactly what's happening in real-time?"

### The Problem (The Story)
- Apache Superset has 200+ Python dependencies and 1000+ npm packages
- Vulnerability scanners find CVEs — but who fixes them?
- Engineers hate dependency upgrade tickets. They sit in backlog for weeks.
- Compliance asks: "What's your mean time to remediate?" Answer: "...we don't track that"
- This is the **security debt death spiral** every engineering org faces

### The Solution (How ShieldOps Works)
```
Instead of: Scan → Create ticket → Assign engineer → Wait weeks → PR → Review → Merge
We build:   Scan → Auto-triage → Devin fixes it → PR created → Tests pass → Dashboard shows it all
```

### Architecture
```
                    ┌─────────────────────────────────┐
                    │     GitHub (Superset Fork)       │
                    │  Issues │ PRs │ Webhooks         │
                    └─────┬───────────────┬────────────┘
                          │               │
                   webhook│          PR/status
                          ▼               │
┌──────────────┐   ┌──────────────────────┴──────┐   ┌──────────────┐
│  Vulnerability│   │      ShieldOps Orchestrator  │   │   Devin API  │
│  Scanner     │──▶│      (FastAPI + Docker)       │──▶│   Sessions   │
│              │   │                               │   │              │
│ • pip-audit  │   │  • Webhook receiver           │   │ • Fix vulns  │
│ • npm audit  │   │  • Issue triage & priority    │   │ • Create PRs │
│ • semgrep    │   │  • Devin session management   │   │ • Run tests  │
│ • trivy      │   │  • Progress tracking          │   │              │
└──────────────┘   │  • GitHub issue updates       │   └──────────────┘
                   │  • Metric emission            │
                   └──────────────┬────────────────┘
                                  │
                   ┌──────────────▼────────────────┐
                   │         Datadog                │
                   │                                │
                   │  📊 Dashboard: Command Center  │
                   │  🚨 Monitors: Failure alerts   │
                   │  📈 Metrics: Throughput/MTTR   │
                   │  📝 Events: Lifecycle tracking │
                   │  🎯 SLOs: Remediation targets  │
                   └────────────────────────────────┘
```

### Event-Driven Triggers (Multiple Types)
| Trigger | How It Works |
|---------|-------------|
| **GitHub Webhook** | Issue labeled `devin-auto-fix` → Devin starts working |
| **New Security Issue** | Issue created with `security` label → auto-remediation |
| **Scheduled Scan** | Daily cron scans the repo → finds new vulns → creates issues → Devin fixes |
| **Manual API** | `POST /scan` → trigger on demand |

### Smart Triage Engine
Not all vulns are equal. ShieldOps scores each one with a weighted formula:
- **Severity** (40%) — Critical=100, High=75, Medium=50, Low=25
- **Fix Available** (25%) — Known fix version=100, No fix=30
- **Type** (20%) — Dependency upgrades (easy, 90) vs SAST findings (complex, 50)
- **Age** (15%) — Older vulns escalate (max at ~2 days)

Outputs a priority score 0-100, estimated complexity (simple/moderate/complex), and a remediate/skip decision.

### Context-Aware Prompt Engineering
Each vulnerability type gets a tailored Devin prompt:
- **Python dependency** — Clone repo, find all references in requirements files, upgrade, check CHANGELOG for breaking changes, run pytest, create PR
- **npm dependency** — Navigate to superset-frontend/, upgrade, check peer deps, run npm test + npm build, create PR
- **Container** — Review Dockerfiles, upgrade base image or OS packages, verify docker build
- **SAST finding** — Navigate to exact file:line, understand the security context, apply minimal fix, run relevant tests

### Devin API Integration Details

**API Version:** v1 (stable, well-documented)
**Base URL:** `https://api.devin.ai/v1`
**Auth:** Bearer token (starts with `cog_`)

**Key endpoints used:**
```
POST /v1/sessions          — Create session (prompt, title, tags, max_acu_limit, structured_output_schema)
GET  /v1/session/{id}      — Get status (status_enum, pull_request_url, structured_output)
POST /v1/session/{id}/message — Send follow-up message
GET  /v1/sessions          — List all sessions
```

**Session lifecycle:**
1. Create with targeted prompt + tags + structured output schema
2. Poll every 15s until status changes from "running"
3. On completion: check for pull_request_url or structured_output
4. Status values: running, blocked, stopped, error, timed_out

**Structured output schema** (requested from Devin):
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string", "enum": ["success", "partial", "failed"]},
    "pr_url": {"type": "string"},
    "changes_summary": {"type": "string"},
    "tests_passed": {"type": "boolean"},
    "notes": {"type": "string"}
  }
}
```

**Session management:**
- Max 3 concurrent sessions (configurable via semaphore)
- 1-hour timeout per session
- Tags for tracking: severity, type, package, issue number
- Max 10 ACU per session (cost control)

---

## WHAT'S ALREADY BUILT (~3,000 lines of Python)

### Project Structure
```
devin-devsecsops/
├── docker-compose.yml          # One command to run everything
├── Dockerfile                  # Python 3.12 + scanners pre-installed
├── requirements.txt            # FastAPI, httpx, uvicorn, pydantic
├── .env.example                # All configuration variables
├── README.md                   # Comprehensive documentation
│
├── src/
│   ├── main.py                 # FastAPI app + ShieldOpsOrchestrator (the brain)
│   ├── config.py               # Config from environment variables
│   │
│   ├── scanner/
│   │   ├── models.py                  # Vulnerability, ScanResult, Severity, RemediationStatus enums
│   │   ├── vulnerability_scanner.py   # Runs pip-audit, npm audit, trivy, semgrep (async, real parsers)
│   │   └── issue_creator.py           # Creates GitHub issues via API (dedup, labels, formatting)
│   │
│   ├── orchestrator/
│   │   ├── devin_client.py            # Full Devin REST API wrapper
│   │   ├── session_manager.py         # Session lifecycle (create, poll, callback, stats)
│   │   ├── triage.py                  # Priority scoring engine (weighted multi-factor)
│   │   └── prompt_builder.py          # 5 prompt templates by vuln type
│   │
│   ├── webhooks/
│   │   ├── github_webhook.py          # GitHub webhook handler (signature verification, issue/PR events)
│   │   └── scheduler.py              # Cron-based scan scheduler (asyncio loop)
│   │
│   ├── observability/
│   │   ├── metrics.py                 # 13 custom Datadog metrics via HTTP API
│   │   ├── events.py                  # Lifecycle events to Datadog
│   │   ├── dashboard.py               # Programmatic 12-widget dashboard creation
│   │   └── monitors.py                # 4 alerting monitors
│   │
│   └── reporting/
│       └── github_reporter.py         # Comments on GitHub issues with session status
│
├── scripts/
│   ├── setup_datadog.py               # One-shot Datadog resource creation
│   └── demo.py                        # Demo script with mock vulnerabilities for recording
│
└── MASTER-PLAN.md                     # Full project plan
```

### Key Design Decisions
1. **FastAPI** — async-first for concurrent Devin sessions + webhook handling
2. **httpx** — async HTTP client for Devin API, GitHub API, Datadog API
3. **No database** — in-memory vulnerability store (demo scope; production would use PostgreSQL)
4. **Callback-based** — SessionManager fires callbacks on status changes, which metrics/events/reporter all subscribe to
5. **Semaphore for concurrency** — Max 3 Devin sessions at once (configurable)
6. **Docker** — everything packaged, including vulnerability scanners

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/health` | GET | Health check (Devin API connectivity) |
| `/status` | GET | Full pipeline status — all vulns, sessions, metrics |
| `/metrics` | GET | Current pipeline metrics (also sent to Datadog) |
| `/scan` | POST | Trigger manual vulnerability scan |
| `/setup/datadog` | POST | Create Datadog dashboard & monitors |
| `/webhook/github` | POST | GitHub webhook receiver (signature-verified) |

### Mock Vulnerabilities (for demo)
The demo script includes 8 realistic vulnerabilities based on common Superset dependencies:
1. Flask CVE-2023-30861 (HIGH) — session fixation
2. Werkzeug CVE-2024-34069 (CRITICAL) — RCE via debugger
3. SQLAlchemy CVE-2024-1135 (CRITICAL) — SQL injection
4. nth-check ReDoS (HIGH) — npm
5. postcss information exposure (MEDIUM) — npm
6. Jinja2 CVE-2024-22195 (MEDIUM) — XSS via xmlattr
7. cryptography CVE-2024-26130 (HIGH) — NULL pointer dereference
8. SAST: SQL injection in sql_lab.py (HIGH) — semgrep finding

---

## DATADOG INTEGRATION (DEEP DETAIL)

### Custom Metrics (13 total, prefix: `shieldops.`)

**Scan metrics:**
- `shieldops.scan.vulnerabilities_found` (gauge) — per scanner tag
- `shieldops.scan.duration_seconds` (gauge) — per scanner tag

**Vulnerability gauges:**
- `shieldops.vulnerabilities.open` (gauge) — current count
- `shieldops.vulnerabilities.fixed` (gauge) — total fixed
- `shieldops.vulnerabilities.by_severity` (gauge) — by severity tag

**Devin session metrics:**
- `shieldops.devin.sessions.created` (count)
- `shieldops.devin.sessions.completed` (count)
- `shieldops.devin.sessions.failed` (count)
- `shieldops.devin.sessions.active` (gauge)
- `shieldops.devin.session.duration_seconds` (gauge) — per session

**Remediation metrics:**
- `shieldops.remediation.mttr_seconds` (gauge) — Mean Time to Remediate
- `shieldops.remediation.prs_created` (count) — PRs opened by Devin
- `shieldops.remediation.success_rate` (gauge) — percentage

### Dashboard: "ShieldOps Command Center" (12 widgets)
```
Row 1: [Open Vulns] [Active Sessions] [Success Rate] [Avg MTTR]     ← query_value widgets
Row 2: [Vulnerability Burn-Down chart] [Devin Session Throughput]     ← timeseries
Row 3: [Vulns by Severity] [PRs Created] [Session Duration by Sev]   ← toplist + timeseries
Row 4: [MTTR Trend (with 1h SLO line)] [Event Stream]                ← timeseries + event_stream
Row 5: [Scan Duration by Scanner] [Vulns Found per Scan]             ← timeseries
Row 6: [Info note about ShieldOps]                                    ← note widget
```

### Monitors (4 alerting rules)
1. **Devin Session Failure Rate High** — Alert if >30% sessions fail in 1h
2. **Critical Vulnerability Open > 4 Hours** — Alert if critical vuln sits unresolved
3. **No Scans Completed in 24 Hours** — Alert if scanner is down
4. **MTTR Exceeding 1-Hour Target** — Alert if remediation is too slow

### Events (Lifecycle Tracking)
Every step emits a Datadog event with tags:
- `🔍 Scan completed: 8 vulnerabilities found (2 critical, 3 high, 3 medium)`
- `🤖 Devin session created for werkzeug — severity:critical`
- `✅ PR created for werkzeug — duration: 847s`
- `❌ Remediation failed for nth-check — tests failed`

---

## THE VP PITCH NARRATIVE

> "Imagine you're the VP of Engineering at a company running Apache Superset. 
> Your security team just told you there are 47 known vulnerabilities in your dependencies.
> Your engineers are busy shipping features. Nobody wants to touch dependency upgrades.
> 
> **ShieldOps changes that.**
>
> Every night, it scans your codebase. When it finds vulnerabilities, it triages them by severity.
> Critical CVEs? Devin starts working immediately — autonomously.
> It reads the advisory, understands your codebase, upgrades the dependency, runs tests, and opens a PR.
> 
> You don't assign tickets. You don't context-switch engineers. You review PRs.
>
> And this dashboard? This tells you everything:
> - 12 vulnerabilities found this week
> - 10 already fixed by Devin
> - Mean time to remediate: 43 minutes
> - Your security posture is improving every single day.
>
> That's not a roadmap. That's running today."

---

## LOOM VIDEO SCRIPT (5 minutes)

**0:00-0:30 — The Hook**
"Every engineering team has security debt. Scanners find hundreds of vulnerabilities, but nobody wants to fix them. The backlog grows, auditors get nervous, and VPs can't answer a simple question: how fast do we fix critical CVEs?"

**0:30-1:00 — The Solution**
"I built ShieldOps — an event-driven automation that scans your codebase, triages vulnerabilities, and uses Devin to autonomously fix them. Let me show you how it works."

**1:00-2:00 — The Demo**
Show: scan running → issues created → Devin sessions → PRs appearing → GitHub comments
"Here's a real scan of Apache Superset — 8 vulnerabilities found, 2 critical. Watch what happens..."

**2:00-3:30 — The Architecture**
Walk through code: triage engine, prompt builder, session manager, Datadog integration
"The triage engine scores each vulnerability on severity, fix availability, and complexity. The prompt builder gives Devin specific, context-aware instructions — not just 'fix this bug.'"

**3:30-4:30 — The Datadog Dashboard**
Show the Command Center: "This is what a VP of Engineering sees. Open vulnerabilities trending down. Success rate at 87%. Mean time to remediate: 43 minutes. Every session tracked, every failure alerted."

**4:30-5:00 — Why Devin + Next Steps**
"Devin isn't just bumping version numbers — it reads changelogs, handles breaking changes, iterates on test failures. That's the difference between automation and intelligence. Next step? Plug this into any CI/CD pipeline. Add policy-as-code. Scale to every repo in your org."

---

## REMAINING WORK

### Must Do (Before Submission)
- [ ] Fork Superset to personal GitHub (`gsharma21/superset`)
- [ ] Run real vulnerability scans on Superset (pip-audit, npm audit)
- [ ] Create 6-8 real issues in the fork with proper labels
- [ ] Set up Devin API key and test session creation
- [ ] Run at least 2-3 real Devin sessions that produce PRs
- [ ] Create the Datadog dashboard (can use our MCP tools OR the script)
- [ ] Record Loom video
- [ ] Push solution repo to GitHub

### Nice to Have
- [ ] Presentation website (clean single-page site explaining the project)
- [ ] Blog post ("Building an Autonomous DevSecOps Pipeline with Devin + Datadog")
- [ ] Screenshot of Datadog dashboard with real data
- [ ] Architecture diagram (clean SVG/PNG)

---

## PRESENTATION WEBSITE CONCEPT

**URL:** Could deploy to Vercel, Netlify, or GitHub Pages
**Framework:** Simple HTML + Tailwind CSS (fast to build), or React/Next.js

### Sections
1. **Hero** — "ShieldOps: Autonomous Security Remediation" + tagline
2. **The Problem** — Security debt crisis with stats/visuals
3. **How It Works** — Architecture diagram, step-by-step flow
4. **Demo** — Embedded Loom video
5. **Results** — Metrics cards (vulns found, fixed, MTTR, success rate)
6. **Dashboard** — Datadog screenshot embed
7. **Technical** — Architecture deep-dive, code snippets
8. **GitHub** — Links to both repos
9. **About** — Built by Gaurav Sharma

---

## BLOG POST OUTLINE

**Title:** "Building an Autonomous DevSecOps Pipeline: How Devin + Datadog Can Remediate Vulnerabilities While You Sleep"

1. **The Problem** — Security debt is engineering's quiet crisis
   - Stats: average time to fix critical CVE is 60+ days
   - The human bottleneck: scanning is automated, fixing isn't
   
2. **The Architecture** — Event-driven automation with Devin as a core primitive
   - Why event-driven (not batch)
   - Webhook + scheduled + manual triggers
   - Separation of scanning, triage, remediation, observability
   
3. **The Scanner** — Finding real vulnerabilities in Apache Superset
   - pip-audit for Python CVEs
   - npm audit for frontend
   - trivy for container images
   - semgrep for SAST
   
4. **The Triage Engine** — Not all vulns are equal
   - Weighted scoring model
   - Complexity estimation
   - Why simple dependency upgrades go first
   
5. **The Devin Integration** — Autonomous coding agent as infrastructure
   - Session management patterns
   - Context-aware prompt engineering
   - Handling failures and timeouts
   - Structured output for reliable results
   
6. **The Observability Layer** — Why Datadog is essential (not optional)
   - Custom metrics for pipeline health
   - Dashboard design for engineering leaders
   - Alerting on failure patterns
   - MTTR as the north star metric
   
7. **Results** — What happened when we let Devin loose
   - X vulnerabilities found, Y fixed
   - Average time to PR: Z minutes
   - Success rate
   
8. **Lessons Learned**
   - Prompt engineering matters enormously for code agents
   - Structured output > unstructured for automation
   - Start with easy wins (dependency bumps) before SAST
   
9. **What's Next**
   - CI/CD integration (scan on every merge)
   - Policy-as-code (auto-approve dependency bumps, human review for code changes)
   - Multi-repo scaling
   - Cost optimization (ACU budgeting)

---

## COMPETITIVE DIFFERENTIATION vs OTHER CANDIDATES

| What most candidates will do | What I'm doing |
|---|---|
| Log to console / stdout | Full Datadog dashboard a VP would actually use |
| Fix 1-2 issues manually through Devin | Build a scan → triage → fix → verify → report pipeline |
| Show Devin doing one thing | Show Devin as a fleet of concurrent autonomous workers |
| Miss the business angle entirely | Frame everything as "reduce security MTTR by 10x" |
| Build a toy script | Build a Dockerized, API-driven platform with real observability |
| No presentation beyond code | Website + blog + polished Loom |
| Generic issues | Real CVEs from actual Superset dependencies |

---

## KEY QUESTIONS FOR BRAINSTORMING

1. **Is the use case strong enough?** Security vulnerability remediation seems universally relatable, but is there a more impressive/unexpected angle?

2. **Should I emphasize the Datadog integration more?** It's my unique strength — should the dashboard be THE centerpiece of the demo?

3. **What's the best way to frame "Why Devin?" in the video?** The brief specifically asks: what can this do that wouldn't be possible without an autonomous coding agent?

4. **Website: worth the time?** It's not in the requirements but could differentiate. 30-45 min investment. Worth it?

5. **Blog: worth the time?** Same question. Shows thought leadership but takes time away from polishing the core deliverables.

6. **What failure modes should I address?** Devin sessions can fail. How should I present this in the demo — as a strength (observability catches it) or minimize it?

7. **How to handle the "real" vs "demo" tension?** The Devin sessions take time and cost ACUs. Should I pre-run some sessions for the demo, or show it live?

8. **Any angle I'm missing?** Am I thinking about this the right way? What would make a Cognition evaluator say "this person gets it"?

---

## TECHNICAL DETAILS FOR DEVIN API

### Authentication
```bash
export DEVIN_API_KEY="cog_your_key_here"
# Header: Authorization: Bearer $DEVIN_API_KEY
```

### Create Session
```bash
curl -X POST "https://api.devin.ai/v1/sessions" \
  -H "Authorization: Bearer $DEVIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Fix the vulnerability in issue #42...",
    "title": "[ShieldOps] Upgrade flask to 2.3.2",
    "tags": ["shieldops", "severity:high", "package:flask"],
    "max_acu_limit": 10,
    "structured_output_schema": {
      "type": "object",
      "properties": {
        "status": {"type": "string", "enum": ["success", "partial", "failed"]},
        "pr_url": {"type": "string"},
        "changes_summary": {"type": "string"},
        "tests_passed": {"type": "boolean"}
      }
    }
  }'
```

### Poll Session
```bash
curl "https://api.devin.ai/v1/session/$SESSION_ID" \
  -H "Authorization: Bearer $DEVIN_API_KEY"

# Response includes: status_enum, pull_request_url, structured_output
# Status values: running, blocked, stopped, error, timed_out
```

### Key API Features Used
- **Tags** — for filtering and tracking sessions by vulnerability
- **Structured output** — JSON schema for reliable machine-readable results
- **max_acu_limit** — cost control per session
- **Idempotent sessions** — prevent duplicate sessions for same issue
- **Session messages** — send follow-up instructions if session gets stuck

---

## APACHE SUPERSET CONTEXT

- **Size:** ~500K lines of code (Python backend + TypeScript/React frontend)
- **Dependencies:** 200+ Python packages, 1000+ npm packages
- **Docker:** Has Dockerfile and docker-compose setup
- **Testing:** pytest for Python, Jest for TypeScript
- **CI:** GitHub Actions
- **Architecture:** Flask + SQLAlchemy + React
- **Known vulnerability-heavy areas:**
  - `requirements/` — multiple requirements files (base, testing, development)
  - `superset-frontend/package.json` — massive npm dependency tree
  - `Dockerfile` — base image with OS-level packages
  - `superset/sql_lab.py` — SQL execution engine (potential SAST findings)
  - `superset/views/` — web views (potential XSS findings)

---

*This document contains everything built so far + the full plan. Use it to brainstorm improvements, critique the approach, suggest alternative angles, or extend the project.*
