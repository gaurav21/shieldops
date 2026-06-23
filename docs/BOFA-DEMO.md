# ShieldOps — BofA Enterprise Demo Guide

## Overview

This demo showcases ShieldOps handling **three enterprise use cases** for Bank of America's engineering organization, extending beyond security vulnerability remediation into framework migrations, cloud migrations, and compliance test coverage.

## Prerequisites

1. **ShieldOps running**: `docker compose up -d` or local dev server
2. **Devin API access**: Valid API key in `.env`
3. **GitHub repos created**:
   - `gaurav21/bofa-digital-banking-frontend` (Angular app)
   - `gaurav21/bofa-enterprise-services` (Java microservices)
4. **GitHub Issues created**: Run `python scripts/create_bofa_issues.py`
5. **Dashboard open**: `http://localhost:8000/static/dashboard.html`

## Demo Flow

### Setup (2 min)
1. Open ShieldOps dashboard — show the control plane
2. Explain: *"ShieldOps started as automated security remediation. Today I'll show how the same orchestration pattern extends to three critical enterprise challenges BofA faces."*

---

### Use Case 1: Angular 14 → 18 Migration (🔄 Migration)

**The Problem**: Angular 14 hit EOL in Nov 2023. OCC flagged this in their last examination. 47 NgModules, 23 legacy Material components, 312 tests — manual migration estimated at 6-8 developer-weeks.

**Demo Steps**:
1. Click **"🔄 Angular 14→18 Migration"** on the dashboard
2. Show the GitHub issue created with full migration scope
3. ShieldOps triages: detects `shieldops-migration` label → routes to migration prompt builder
4. Devin session launches with the Angular upgrade prompt
5. Walk through what Devin is doing:
   - Reading Angular changelogs
   - Converting NgModules → standalone
   - Replacing MatLegacy* → Mat*
   - Running `ng build` and `ng test`
6. Show the PR with structured output: files changed, breaking changes, confidence score
7. Policy engine decides: **human review required** (migration affects customer-facing app)

**Key Talking Points**:
- *"6-8 weeks of developer time → 4 hours with ShieldOps + Devin"*
- *"The migration prompt includes every breaking change pattern — Devin doesn't miss call sites"*
- *"Policy engine correctly flags this for human review — it's a customer-facing app"*

---

### Use Case 2: Cloud Migration — Spring Boot → Lambda (☁️ Cloud)

**The Problem**: BofA's cloud-first mandate requires migrating on-prem services to AWS. The Notification Service handles 50K messages/day through IBM MQ with strict ordering guarantees. Manual migration: 3-4 months with a specialized team.

**Demo Steps**:
1. Click **"☁️ Cloud Migration: Spring Boot → Lambda"** on the dashboard
2. Show the two related issues: service migration + MQ → SQS FIFO
3. ShieldOps detects `shieldops-cloud-migration` → routes to cloud migration prompt
4. Devin session launches with full infrastructure mapping:
   - IBM MQ queues → SQS FIFO with MessageGroupId mapping
   - Oracle → Aurora PostgreSQL dialect conversion
   - LDAP → Cognito auth migration
   - Spring Boot DI → Lambda handler patterns
5. Show the structured output focusing on:
   - Message ordering preservation strategy
   - SLA impact analysis
   - Risk assessment

**Key Talking Points**:
- *"The prompt encodes BofA-specific constraints: message ordering, data residency, dual-run period"*
- *"Devin maps 14 IBM MQ queues to SQS FIFO with correct MessageGroupId patterns"*
- *"This is the kind of migration that usually requires a specialized consulting team"*

---

### Use Case 3: OCC Exam Prep — Test Coverage (🧪 Coverage)

**The Problem**: OCC examiners require test coverage evidence for compliance-critical code. Current coverage: 34% overall, with audit and KYC paths at 0%. Exam is in 8 weeks.

**Demo Steps**:
1. Click **"🧪 Test Coverage: Compliance Paths"** on the dashboard
2. Show the two issues: coverage gaps + audit service bootstrap
3. ShieldOps detects `shieldops-coverage` → routes to coverage prompt
4. Devin session launches:
   - First: bootstrap test infrastructure for audit service (0 tests → JUnit 5 setup)
   - Then: generate compliance-focused tests for critical paths
5. Show the coverage report in structured output:
   - Before: 0% on audit paths
   - After: 80%+ with compliance-specific test patterns
6. Highlight test quality: audit trail tests, RBAC enforcement tests, PII validation

**Key Talking Points**:
- *"The audit service had zero tests. ShieldOps bootstrapped the entire test infrastructure AND wrote compliance-specific tests"*
- *"These aren't generic tests — they validate audit trail completeness, RBAC enforcement, data encryption"*
- *"8-week OCC deadline → ShieldOps delivers coverage evidence in hours"*

---

## Persona-Specific Talking Points

### VP Engineering (Strategic Buyer)
- **ROI**: "3 use cases, each saving weeks of developer time. That's 10-15 developer-weeks reclaimed."
- **Risk reduction**: "OCC exam prep alone could prevent a consent order worth millions in fines."
- **Scale**: "This isn't a one-time fix. Every Angular upgrade, every cloud migration follows the same pattern."
- **Developer happiness**: "Your best engineers are doing migration busywork. ShieldOps frees them for product work."

### Security Engineer (Technical Champion)
- **Policy engine**: "Every PR gets a policy decision — auto-merge, human review, or blocked. You control the rules."
- **Structured output**: "Devin reports confidence scores, breaking changes, files touched. Full audit trail."
- **Compliance**: "Test coverage reports map directly to OCC examination requirements."
- **Integration**: "GitHub Issues in → PRs out. Fits your existing workflow."

### Chief Architect (Technical Evaluator)
- **Prompt engineering**: "The migration prompts encode enterprise-specific patterns — NgModule → standalone, IBM MQ → SQS FIFO ordering."
- **Extensibility**: "TaskType enum — add new task types in minutes. The orchestration pattern is generic."
- **Guardrails**: "Policy engine prevents auto-merge on customer-facing changes. Confidence thresholds are configurable."
- **Cloud patterns**: "Outbox pattern for MQ → SQS, dual-write for data migration, canary deployment strategy — all encoded in prompts."

---

## Fallback Plan

If Devin API is slow or unavailable:

1. **Use pre-recorded session**: Show `scripts/demo_replay.py` with recorded session data
2. **Walk through prompts**: Open `src/orchestrator/migration_prompts.py` and show the prompt templates
3. **Show the architecture**: Dashboard + triage → prompt builder → Devin → policy → PR flow
4. **Use existing security demo**: Fall back to the Flask/Paramiko vulnerability demos (always work)

### Quick Recovery Commands
```bash
# Check Devin API status
curl -s https://api.devin.ai/v1/health | jq .

# Restart ShieldOps
docker compose restart shieldops

# Run with mock Devin (simulated sessions)
MOCK_DEVIN=true python -m src.main
```

---

## Demo Checklist

- [ ] ShieldOps dashboard loads at `localhost:8000`
- [ ] Both GitHub repos exist and are accessible
- [ ] 6 demo issues created (`python scripts/create_bofa_issues.py`)
- [ ] Devin API key valid (test with health check)
- [ ] Network is stable (Devin sessions need ~5 min each)
- [ ] Browser zoom at 90% for dashboard visibility
- [ ] Terminal ready for fallback commands
- [ ] Demo replay script tested as backup
