# ShieldOps v2 — Build Spec (Reframed for the VP + the Cognition Evaluator)

> **What this is:** A rewrite of the original brainstorm, restructured around a single
> insight: *Devin is the headliner, trust is the product, and observability proves the
> trust.* Use this to build, record, and ship. Sections marked **[KEEP]**, **[ADD]**,
> **[RE-WEIGHT]**, and **[CUT]** tell you what to do with the ~3,000 lines already built.

---

## 0. The one thing that changed

The original demo led with a beautiful Datadog dashboard and treated Devin as the engine
inside it. That inverts the assignment. The evaluator is **Cognition** — they want to see
Devin used as a *core primitive*, doing work that is impossible without an autonomous coding
agent. A sophisticated VP of Engineering, meanwhile, doesn't get excited by "we opened a PR
in 43 minutes" — they get nervous, because an agent that opens 47 PRs just created 47 review
tasks and a trust problem.

**The reframe, in one line:**

> ShieldOps isn't a faster vulnerability scanner. It's a **trust control plane for an
> autonomous engineering workforce** — it lets Devin do the judgment-heavy remediation work
> that Dependabot *can't*, routes each change through a policy boundary so humans only review
> what actually needs a human, and uses Datadog to prove the fleet is safe to run.

Everything below serves that sentence.

---

## 1. Context (unchanged)

- **Person:** Gaurav Sharma — Sales Engineer at Datadog, Singapore. Deep Datadog expertise, ships fast.
- **Challenge:** Technical take-home for **Cognition (Devin AI)**, for a Sales/Solutions Engineer role.
- **Time budget:** 2–3 hours. Working end-to-end demo over polish.
- **Evaluated on:** (1) turning an ambiguous problem into a working system, (2) using Devin as a *core primitive*, (3) communicating technical execution **and** business impact.
- **Deliverables:** working project + 5-min Loom (to a VP of Eng + senior ICs) + two GitHub repos (solution + forked Superset).

---

## 2. The problem — restated so a VP actually nods

The old framing ("scanners find vulns, nobody fixes them, backlog grows") is true but
shallow, and it walks straight into the Dependabot question. Reframe it around the two things
a VP actually loses sleep over:

1. **The bottleneck is review and trust, not detection or even the diff.** Scanning is solved.
   Even *writing* a dependency bump is mostly solved (Dependabot/Renovate do it for free). The
   real cost is: a senior engineer has to figure out whether the CVE is even reachable, whether
   the upgrade breaks something, and then own the merge. That work doesn't scale, and it's where
   weeks disappear.
2. **The 20% that tooling can't touch is 100% of the pain.** Dependabot opens a PR and gives up
   the moment a version bump breaks an import or a call signature. That broken PR sits red in the
   queue forever. *That* is the death spiral — not the easy bumps, the hard ones.

So the question ShieldOps answers is not "can we fix vulns faster?" It's:

> "Can an autonomous agent take the breaking-change upgrades that humans avoid, fix them
> properly, and hand me back **only the few PRs that genuinely need my judgment** — with the
> evidence to approve them in two minutes instead of thirty?"

---

## 3. The wedge — why this is not Dependabot **[ADD — make this central]**

This is the most important slide/section. Build the whole demo to prove it.

| | Dependabot / Renovate | ShieldOps + Devin |
|---|---|---|
| Easy patch bump | ✅ opens PR | ✅ (don't bother competing here) |
| Bump that breaks imports/call sites | ❌ opens a red PR, stops | ✅ reads the error, fixes call sites, iterates to green |
| Reads the CHANGELOG to anticipate breakage | ❌ | ✅ |
| Reachability / "does this CVE even matter here" | ❌ | ✅ (prompted to check) |
| Decides what a human must review vs what's safe | ❌ | ✅ policy boundary |
| Gives the reviewer an evidence bundle | ❌ | ✅ |

**Demo consequence:** your hero moment (Section 7) must be a *breaking-change* upgrade where a
naive bump fails and Devin recovers. If you only show patch bumps, you've built a slower, more
expensive Dependabot and the evaluator will notice.

---

## 4. Architecture (revised)

The orchestrator, scanner, and Devin client are kept. Two things move to the center: a
**Policy / Trust boundary** and an **agent-centric observability layer**.

```
                    ┌─────────────────────────────────┐
                    │     GitHub (Superset Fork)        │
                    │  Issues │ PRs │ Webhooks          │
                    └─────┬───────────────┬─────────────┘
                          │ webhook        │ PR / status
                          ▼                │
┌──────────────┐   ┌──────────────────────┴──────┐   ┌──────────────┐
│ Scanners     │   │   ShieldOps Orchestrator      │   │  Devin API   │
│ pip-audit    │──▶│   (FastAPI + Docker)          │──▶│  Sessions    │
│ npm audit    │   │                               │   │  (the fleet) │
│ trivy        │   │  1. Triage  (reachability +   │   └──────┬───────┘
│ semgrep      │   │     risk + complexity)        │          │
└──────────────┘   │  2. Devin session mgmt        │◀─────────┘
                   │  3. ★ POLICY / TRUST BOUNDARY │   structured output
                   │     route: auto-merge |       │   + PR + evidence
                   │     human-gate | block        │
                   │  4. Evidence bundle builder   │
                   │  5. Metric / event emission   │
                   └──────────────┬────────────────┘
                                  │
                   ┌──────────────▼────────────────────────────┐
                   │   Datadog — AGENT TRUST CONTROL PLANE       │
                   │                                            │
                   │  ▸ The fleet right now (active/blocked/ACU)│
                   │  ▸ Trust split (auto vs human vs blocked)  │
                   │  ▸ The Dependabot-can't metrics            │
                   │    (breaking changes handled, confidence)  │
                   │  ▸ Cost & reviewer-time saved              │
                   │  ▸ Security posture burn-down              │
                   │  ▸ Full audit event stream                 │
                   └────────────────────────────────────────────┘
```

---

## 5. The Policy / Trust boundary **[ADD — new core component]**

This is the component that makes a VP comfortable running a fleet of agents against their
codebase. Build it as a small, explicit module (`src/orchestrator/policy.py`). It consumes
Devin's structured output + triage data and emits a **routing decision** plus an **evidence
bundle**.

### Routing logic (policy-as-code)

```
INPUT per remediation:
  - vuln: severity, type, reachable?, sensitive_path?
  - devin_result: tests_passed, breaking_changes_detected,
                  confidence, files_touched, changes_summary
  - upgrade: patch | minor | major

DECISION:
  AUTO_MERGE_READY  if  tests_passed
                    and not breaking_changes_detected
                    and upgrade in {patch, minor}
                    and type == dependency
                    and not sensitive_path
                    and confidence >= 0.8
  HUMAN_REVIEW      if  major upgrade
                    or  breaking_changes_detected
                    or  type in {SAST, code_logic}
                    or  sensitive_path (auth, sql, crypto, views)
                    (these still get a PR — just labeled `needs-human`)
  BLOCKED           if  not tests_passed
                    or  confidence < 0.5
                    or  Devin status in {error, timed_out, blocked}
                    (no PR merged; issue commented; alert fired)
```

Sensitive paths for Superset (use to force human review):
`superset/sql_lab.py`, `superset/views/`, anything touching auth, SQL, or crypto.

### Evidence bundle (attached as the PR description / issue comment)

The reviewer should approve a `needs-human` PR in ~2 minutes because everything is there:

- **What changed & why** — Devin's `changes_summary`, the CVE/advisory link.
- **Reachability note** — is the vulnerable code path actually used here? (prompt Devin to state this)
- **Breaking changes** — what the CHANGELOG flagged and what Devin did about it.
- **Proof it works** — test command + result (pass/fail counts), build result.
- **Confidence + caveats** — Devin's self-reported confidence and `notes`.
- **Blast radius** — files touched, sensitive paths flagged.

> This is the quiet genius of the demo: you're not removing the human, you're making the
> human's job trivial and auditable. That's what a VP buys.

---

## 6. Observability, reframed: the Agent Trust Control Plane **[RE-WEIGHT the existing 13 metrics]**

Stop observing *vulnerabilities*. Start observing *the autonomous workforce*. Same Datadog
strength, far better story, and directly on-theme for Cognition.

### Metrics — keep the vuln ones, add the workforce ones (★ = new, do these)

**Vulnerability posture (keep, demote to one row):**
- `shieldops.vulnerabilities.open` / `.fixed` / `.by_severity`
- `shieldops.scan.vulnerabilities_found` / `.duration_seconds`

**★ The fleet (this is the new headline):**
- `shieldops.devin.sessions.active` / `.blocked` / `.completed` / `.failed`
- `shieldops.devin.cost_acu` (per session) → derive **cost per merged fix**
- `shieldops.devin.intervention_rate` — % of sessions needing a human follow-up message
- `shieldops.devin.stuck` (event w/ reason) — where and why Devin blocks

**★ Trust split (the VP's comfort metric):**
- `shieldops.policy.auto_merge_ready` / `.human_review` / `.blocked` (counts)
- `shieldops.remediation.confidence` (distribution)

**★ The "Dependabot can't" metrics (the wedge, quantified):**
- `shieldops.remediation.breaking_changes_handled` (count) — your hero number
- `shieldops.remediation.time_to_merged_verified_seconds` — the *real* MTTR (replaces "time to PR")
- `shieldops.review.reviewer_minutes_saved` — estimate: (baseline review minutes − actual)

### Dashboard: "ShieldOps — Agent Trust Control Plane" (rebuild the 12 widgets in this order)

```
Row 1  THE FLEET RIGHT NOW
       [Active sessions] [Blocked/Stuck] [ACU burn rate] [Intervention rate]
Row 2  IS IT SAFE TO RUN?  (trust split)
       [Auto-merge vs Human-gate vs Blocked — donut] [Confidence distribution]
Row 3  THE THING DEPENDABOT CAN'T DO
       [Breaking changes handled — counter + trend] [Time-to-merged-verified trend w/ target line]
Row 4  WHAT IS IT WORTH?
       [Cost per merged fix] [Reviewer-minutes saved (cumulative)]
Row 5  SECURITY POSTURE  (the classic view, now supporting cast)
       [Open vulns burn-down by severity] [Vulns found per scan]
Row 6  AUDIT
       [Event stream — every scan, session, policy decision, merge]  ← this is your compliance story
```

### Monitors (revised — alert on *trust*, not just failure)

1. **Intervention rate spiking** — fleet needs babysitting; >X% sessions need human messages.
2. **A change auto-merged with low confidence** — policy safety net; should never fire, proves the boundary works.
3. **Session blocked/stuck > N minutes** — agent is stuck, loop a human.
4. **ACU burn / cost per fix exceeding budget** — cost guardrail a VP will ask about.
5. (keep) **Critical vuln open > 4h**, **No scans in 24h**.

---

## 7. The hero demo — prove ONE hard session **[ADD — this wins or loses the eval]**

Answers the brief's "what's not possible without an autonomous coding agent?" *and* solves the
real-vs-demo tension. One genuine, messy, recovered session beats eight mocked successes.

### How to build it

1. **Find a real breaking-change upgrade in the Superset fork.** You need a vuln whose fix
   crosses a version boundary that *actually breaks the build* — so a naive bump fails and Devin
   has to do real work. Candidates to evaluate against the actual fork (verify, don't assume):
   - A **major** version bump (e.g. SQLAlchemy 1.4→2.0-style, Werkzeug/Flask major, Pydantic
     v1→v2, marshmallow major) — these have well-known API breakages.
   - Anything where the fixed version changes a function signature or removes a symbol Superset imports.
2. **Run Devin on it for real.** Let it fail the first build, read the traceback, locate the
   changed call sites, fix them, re-run tests to green, open the PR.
3. **Capture the artifacts** (you'll replay these in the Loom, no live ACU risk):
   - The first failing test/build output.
   - Devin reading the error and the CHANGELOG.
   - The fix to the call sites.
   - Tests going green.
   - The final PR **with the evidence bundle** and a `needs-human` label.
4. **Contrast it explicitly:** "Here's what Dependabot does with this exact upgrade —" (show a
   red, abandoned PR or just state it) "— and here's what Devin did."

> Pre-run everything that costs ACUs/time. Show *real* artifacts, not mocks. The mock-vuln set
> (the existing 8) is fine for showing throughput/fleet behavior, but the autonomy claim must
> rest on at least one real, hard, recovered session.

---

## 8. Triage (revised) **[KEEP scoring, ADD reachability + policy routing]**

Keep the weighted scorer; add two ideas that matter to the new story:

- **Reachability flag** — does the vulnerable symbol actually get imported/called in Superset?
  Even a cheap heuristic (grep for the import) lets you say "we deprioritized 30 CVEs that
  aren't reachable" — a line every security-aware VP loves, and a direct answer to "is this just
  noise?"
- **Policy pre-routing** — triage now also predicts the likely route (auto/human/block) so the
  dashboard can show projected reviewer load *before* sessions even run.

Existing weights stay useful: Severity 40% / Fix-available 25% / Type 20% / Age 15% → priority
0–100 + complexity estimate.

---

## 9. Devin API integration **[KEEP — this is solid, build on it]**

The existing client, session manager, prompt builder, and structured-output schema are good.
Two additions tie them to the new components:

### Structured output schema — extend it

```json
{
  "type": "object",
  "properties": {
    "status":                 {"type": "string", "enum": ["success", "partial", "failed"]},
    "pr_url":                 {"type": "string"},
    "changes_summary":        {"type": "string"},
    "tests_passed":           {"type": "boolean"},
    "breaking_changes_detected": {"type": "boolean"},
    "breaking_changes_notes": {"type": "string"},
    "reachability_assessment":{"type": "string"},
    "confidence":             {"type": "number"},
    "files_touched":          {"type": "array", "items": {"type": "string"}},
    "notes":                  {"type": "string"}
  }
}
```

The new fields (`breaking_changes_detected`, `confidence`, `reachability_assessment`,
`files_touched`) are exactly what the policy engine and evidence bundle consume. Without them,
Section 5 has nothing to route on — so prompt Devin to fill them.

### Prompt builder — add the explicit "do the hard part" instruction

For dependency upgrades, the prompt must tell Devin to: read the CHANGELOG between current and
target versions, find and fix *all* call sites affected by breaking changes, run the relevant
tests, iterate until green, and report breaking changes + confidence + reachability in the
structured output. That instruction is the difference between "version bump" and "the thing
Dependabot can't do."

### Session mechanics (keep)
- Base URL `https://api.devin.ai/v1`, Bearer `cog_...`
- `POST /v1/sessions` (prompt, title, tags, `max_acu_limit`, `structured_output_schema`)
- `GET /v1/session/{id}` (poll every 15s; `status_enum`, `pull_request_url`, `structured_output`)
- `POST /v1/session/{id}/message` (follow-up — this *is* the intervention you measure)
- Max 3 concurrent (semaphore), 1h timeout, `max_acu_limit: 10`, idempotent per issue, tags for tracking.

---

## 10. What to do with the existing ~3,000 lines

| Component | Action | Why |
|---|---|---|
| `scanner/` (pip-audit, npm, trivy, semgrep) | **KEEP** | Solid foundation, real parsers. |
| `orchestrator/devin_client.py` | **KEEP** | Good API wrapper. |
| `orchestrator/session_manager.py` | **KEEP + extend** | Add intervention tracking (count follow-up messages). |
| `orchestrator/triage.py` | **KEEP + add** | Add reachability flag + policy pre-route. |
| `orchestrator/prompt_builder.py` | **EDIT** | Add the "fix all call sites / report breaking changes + confidence" instruction. |
| `orchestrator/policy.py` | **ADD (new)** | The trust boundary. The most important new file. |
| `reporting/evidence_bundle.py` | **ADD (new)** | Builds the reviewer's 2-minute approval packet. |
| `observability/metrics.py` | **RE-WEIGHT** | Add fleet/trust/cost/breaking-change metrics; demote vuln-only metrics. |
| `observability/dashboard.py` | **REBUILD** | New widget order (Section 6) — fleet first, posture last. |
| `observability/monitors.py` | **EDIT** | Trust-oriented monitors (Section 6). |
| `observability/events.py` | **KEEP + add** | Emit a policy-decision event per remediation (audit trail). |
| `webhooks/` + `scheduler.py` | **KEEP** | Event-driven triggers already satisfy the brief. |
| `scripts/demo.py` | **KEEP for throughput, ADD hero replay** | Mocks fine for fleet view; add the real-session replay. |
| Presentation website | **CUT** | Not in the brief; "working demo over polish." A clean README is your presentation. |
| Blog post | **CUT (or defer)** | Signals time spent on marketing over bulletproofing the core. Revisit only if everything else is done. |

---

## 11. Metrics that actually move a VP (use these numbers in the Loom)

Drop "time to PR: 43 min." Lead with:

- **"N breaking-change upgrades fixed autonomously — the ones Dependabot abandons."**
- **"Time to a *merged, verified* fix"** (not time to open a PR).
- **"X reviewer-hours saved"** — concrete, board-friendly.
- **"$ / ACU per merged fix"** — proves it's economically sane, pre-empts the cost question.
- **"% auto-merge-safe vs % needing a human"** — proves the fleet is controllable.
- **"30 unreachable CVEs deprioritized"** — proves it cuts noise, not just adds throughput.

---

## 12. Loom script (5 min, rewritten around the reframe)

**0:00–0:30 — Hook (the real problem):**
"Scanners find hundreds of CVEs. Dependabot opens PRs for the easy ones — and gives up the
moment an upgrade breaks the build. Those broken PRs are where security debt actually lives.
And nobody can tell their VP which fixes are safe to merge without a human."

**0:30–1:15 — The hero session (lead with Devin, not the dashboard):**
Show the real breaking-change session. Naive bump fails → Devin reads the traceback and
CHANGELOG → fixes the call sites → tests green → PR with evidence bundle. "Dependabot can't do
this. This is the difference between automation and an autonomous engineer."

**1:15–2:15 — The system around it:**
Scan → triage (with reachability) → Devin fleet → **policy boundary** → auto-merge vs
human-gate vs block. "I'm not removing the human. I'm making sure a human only sees the few
changes that need judgment — with everything they need to approve in two minutes."

**2:15–3:30 — The control plane (now your Datadog strength lands on-theme):**
The Agent Trust Control Plane dashboard. "This is what lets a VP actually *run* a fleet of
agents: active sessions, how often they need help, cost per fix, what auto-merged safely, and
the audit trail of every decision."

**3:30–4:30 — The numbers + failures-as-trust:**
The VP metrics (Section 11). Then show a real failure: "This session got stuck — the monitor
caught it, looped in a human, nothing merged silently. That's the system working."

**4:30–5:00 — Why Devin + next steps:**
"Detection and easy bumps are solved. The judgment-heavy, breaking-change work wasn't —
until an autonomous agent could do it safely behind a policy boundary. Next: wire into CI on
every merge, expand the auto-merge policy as trust grows, scale across repos."

---

## 13. VP pitch narrative (rewritten)

> "You already have a scanner. You probably have Dependabot. So why is your critical-CVE
> backlog still weeks deep? Because the easy bumps are automated and the *hard* ones — the
> upgrades that break the build — still land on a senior engineer's desk, and they avoid them.
>
> ShieldOps puts an autonomous engineer on exactly that work. Devin takes the breaking-change
> upgrades, fixes the call sites, proves the tests pass, and routes the result through a policy
> boundary: safe changes are merge-ready, risky ones come to a human with a two-minute evidence
> packet, and anything it can't verify is blocked and flagged.
>
> This dashboard is how you trust it: how many agents are working right now, how often they need
> help, what it costs per fix, what merged safely, and a full audit trail. You're not buying a
> faster scanner. You're buying the ability to run an autonomous engineering workforce —
> *safely* — starting today."

---

## 14. Build checklist (priority order)

### Must do (the core claim)
- [ ] Fork Superset → `gsharma21/superset`; run real scans (pip-audit, npm audit).
- [ ] Create 6–8 real issues with proper labels.
- [ ] **Find one real breaking-change upgrade and run Devin on it for real (the hero session).**
- [ ] Build `policy.py` (routing) + `evidence_bundle.py`.
- [ ] Extend the Devin structured-output schema + prompt for breaking-change/confidence/reachability.
- [ ] Re-weight metrics; rebuild the dashboard in the new order; update monitors.
- [ ] Record the Loom around the new script.
- [ ] Clean README (this is your presentation) + push solution repo.

### Strong if time allows
- [ ] Reachability heuristic in triage (the "30 CVEs deprioritized" line).
- [ ] Reviewer-minutes-saved + cost-per-fix derivations wired into Datadog.
- [ ] A second real session for fleet/throughput credibility.

### Cut unless everything above is done
- [ ] ~~Presentation website~~
- [ ] ~~Blog post~~

---

## 15. Appendix — Devin API reference (kept verbatim for build)

**Auth:** `export DEVIN_API_KEY="cog_..."` → header `Authorization: Bearer $DEVIN_API_KEY`

**Create session:**
```bash
curl -X POST "https://api.devin.ai/v1/sessions" \
  -H "Authorization: Bearer $DEVIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Upgrade <pkg> to fix <CVE>. Read the CHANGELOG between current and target version, find and fix ALL call sites affected by breaking changes, run the relevant tests, iterate until green. Report breaking_changes_detected, confidence, reachability_assessment, files_touched in structured output.",
    "title": "[ShieldOps] <pkg> <CVE>",
    "tags": ["shieldops", "severity:high", "package:<pkg>"],
    "max_acu_limit": 10,
    "structured_output_schema": { ...see Section 9... }
  }'
```

**Poll:**
```bash
curl "https://api.devin.ai/v1/session/$SESSION_ID" -H "Authorization: Bearer $DEVIN_API_KEY"
# status_enum: running | blocked | stopped | error | timed_out
# also: pull_request_url, structured_output
```

**Superset context for picking the hero case:**
~500K LOC, 200+ Python deps, 1000+ npm deps. Vuln-heavy areas: `requirements/*`,
`superset-frontend/package.json`, `Dockerfile`, `superset/sql_lab.py`, `superset/views/`.
Look in `requirements/` for a pinned dependency whose CVE fix requires a **major** version jump —
that's where a naive bump breaks and Devin earns its keep.

---

*Build the hero session first. Everything else is in service of proving that Devin did
something a human was avoiding and a script can't do — and that you made it safe to trust.*
