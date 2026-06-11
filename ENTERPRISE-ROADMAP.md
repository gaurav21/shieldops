# ShieldOps — Enterprise Roadmap

## Current State (Demo-Grade ✅)
- Single repo (hardcoded in `.env`)
- Single user, no auth beyond optional API key
- In-memory state (lost on restart)
- Manual `docker compose up` deployment
- Devin as sole remediation agent
- GitHub Issues as trigger surface
- Datadog observability (optional)

## Enterprise Vision
**"Connect any GitHub repo → ShieldOps scans, triages, remediates, tracks — autonomously."**

Think: GitHub App install → org-wide security remediation fleet.

---

## Phase 1: Multi-Repo Foundation (Week 1-2)

### 1.1 GitHub App (replaces PAT + webhook)
- **GitHub App** with org-level install (not per-repo PATs)
- OAuth flow: user installs → selects repos → ShieldOps gets scoped access
- Webhook auto-configured on install (no manual setup)
- Per-repo settings stored in DB

### 1.2 Database (replaces in-memory state)
- PostgreSQL for persistent state
- Tables: `organizations`, `repositories`, `scans`, `vulnerabilities`, `sessions`, `policy_decisions`, `audit_log`
- Migration framework (Alembic)

### 1.3 Multi-Repo Config
- Each repo gets its own scan config:
  - Scan types (pip-audit, npm audit, trivy, semgrep)
  - Policy overrides (auto-merge thresholds, blocked paths)
  - Schedule (daily/weekly/on-push)
  - Notification channels

### 1.4 Onboarding Flow
```
Install GitHub App → Select repos → Configure scan types → First scan runs
     ↓                    ↓                  ↓                    ↓
  OAuth callback    Store repo list    Default policies      Results in dashboard
```

---

## Phase 2: Dashboard & Multi-Tenancy (Week 3-4)

### 2.1 Real Dashboard (Next.js or React)
- **Org overview**: repos connected, total vulns, fix rate, MTTR
- **Per-repo view**: vulnerabilities, Devin sessions, PRs, policy decisions
- **Session live view**: real-time Devin session progress
- **Policy editor**: visual trust boundary configuration
- **Audit trail**: every action with timestamps

### 2.2 Multi-Tenancy
- Org-based isolation
- API keys per org
- Role-based access: admin, reviewer, viewer
- SSO (GitHub OAuth → org membership check)

### 2.3 Notifications
- Slack/Teams/Discord integration
- Email digests (daily/weekly vulnerability summary)
- Telegram bot (you already have this muscle)

---

## Phase 3: Agent Fleet & Intelligence (Week 5-6)

### 3.1 Multi-Agent Support
- **Devin** (current) — complex remediation
- **OpenClaw/Claude** — lighter fixes, PR reviews
- **Codex** — alternative for simpler patches
- Agent selection based on complexity/cost/speed
- Fallback chain: try cheapest agent first → escalate

### 3.2 Self-Learning
- Track which remediations succeed post-merge
- Learn patterns: "Flask upgrades need these specific fixes"
- Confidence calibration from historical outcomes
- Cost optimization: route simple bumps to cheaper agents

### 3.3 Advanced Scanning
- **SAST integration**: Semgrep, CodeQL
- **Container scanning**: Trivy, Grype
- **Secret detection**: TruffleHog, GitLeaks
- **License compliance**: check dependency licenses
- **Custom rules**: org-specific vulnerability patterns

---

## Phase 4: Enterprise Features (Week 7-8)

### 4.1 Compliance & Governance
- SOC2 audit trail (immutable log of all actions)
- Change approval workflows (CISO sign-off for critical)
- SLA tracking (MTTR by severity, contractual targets)
- Compliance reports (PDF/CSV export)

### 4.2 Fleet Operations
- Org-wide campaigns: "Fix all log4j across 200 repos"
- Priority queuing: critical vulns first, rate-limited
- Budget controls: max Devin ACU spend per day/week
- Dry-run mode: generate PRs but don't create them

### 4.3 API & Integrations
- REST API for CI/CD integration
- GitHub Actions marketplace action
- Jira/Linear ticket creation
- PagerDuty/OpsGenie escalation
- Datadog integration (already done ✅)

### 4.4 Self-Hosted Option
- Helm chart for k8s deployment
- Docker Compose for single-node
- Air-gapped mode (no external agent calls)

---

## Quick Wins (Can Ship This Week)

1. **GitHub App boilerplate** — OAuth install flow, webhook auto-config
2. **SQLite → PostgreSQL migration** — persistent state across restarts
3. **Multi-repo support in trigger.py** — accept webhooks from any repo, not just one
4. **Onboarding API** — `POST /api/repos` to connect a new repo
5. **Dashboard: repo selector** — dropdown to switch between connected repos

---

## Architecture: Enterprise

```
┌─────────────────────────────────────────────────────────────┐
│                    ShieldOps Cloud / Self-Hosted             │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Dashboard │  │ REST API │  │ Webhooks │  │ Scheduler  │ │
│  │ (Next.js) │  │ (FastAPI)│  │ Receiver │  │ (APScheduler)│
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘ │
│       │              │              │               │        │
│       └──────────────┴──────┬───────┴───────────────┘        │
│                             │                                │
│                    ┌────────┴────────┐                       │
│                    │  Orchestrator   │                       │
│                    │  (per-repo)     │                       │
│                    └────────┬────────┘                       │
│              ┌──────────────┼──────────────┐                 │
│              │              │              │                 │
│        ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐          │
│        │  Scanner   │ │  Triage   │ │  Policy   │          │
│        │  Engine    │ │  Engine   │ │  Engine   │          │
│        └───────────┘ └───────────┘ └───────────┘          │
│              │                                              │
│        ┌─────┴──────────────────────────┐                   │
│        │         Agent Fleet            │                   │
│        │  ┌───────┐ ┌───────┐ ┌──────┐ │                   │
│        │  │ Devin │ │Claude │ │Codex │ │                   │
│        │  └───────┘ └───────┘ └──────┘ │                   │
│        └────────────────────────────────┘                   │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐  │
│  │ PostgreSQL │  │  Redis     │  │ Datadog / Self-Obs  │  │
│  │ (state)    │  │ (queue)    │  │ (metrics + events)  │  │
│  └────────────┘  └────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                    │
    ┌────┴────┐          ┌────┴────┐
    │ GitHub  │          │ Slack/  │
    │ App API │          │ Teams   │
    └─────────┘          └─────────┘
```

---

## Competitive Positioning

| Feature | Dependabot | Snyk | Renovate | **ShieldOps** |
|---------|-----------|------|----------|--------------|
| Bump versions | ✅ | ✅ | ✅ | ✅ |
| Fix breaking changes | ❌ | ❌ | ❌ | **✅ (Devin)** |
| Run tests & iterate | ❌ | ❌ | ❌ | **✅** |
| Major version upgrades | ❌ | ❌ | Partial | **✅** |
| Trust boundary/policy | ❌ | Basic | ❌ | **✅ (3-tier)** |
| Evidence bundles | ❌ | ❌ | ❌ | **✅** |
| Multi-agent | ❌ | ❌ | ❌ | **✅** |
| Self-learning | ❌ | ❌ | ❌ | **✅** |
| Observability built-in | ❌ | Dashboard | ❌ | **✅ (Datadog)** |

**Moat:** Nobody else has an autonomous agent that reads changelogs, fixes call sites, runs tests, and iterates to green. Dependabot bumps and prays.
