# ShieldOps Demo — Talk Track (~5 min)

**You are:** Gaurav Sharma, Pre-Sales Engineer at Cognition (Devin)
**Audience:** VP of Engineering + Senior ICs evaluating Devin
**Tone:** Confident, conversational, technical but business-aware. You built this — own it.

---

## Pre-Demo Setup (Open these tabs)

1. **Terminal** — ready to create a GitHub issue
2. **GitHub** — `gaurav21/superset` issues list
3. **Devin session** — https://app.devin.ai/sessions/872a39a23033451f95a94bbaf80bb65c (Flask hero — scroll to planner + shell)
4. **PR #10** — Flask hero PR (conversation tab showing evidence bundle)
5. **PR #10 Files** — the actual diff
6. **Code** — `trigger.py` open to structured output schema, `policy.py` open
7. **Datadog** — ShieldOps dashboard: https://app.datadoghq.com/dashboard/uph-3r7-nfs
8. **ShieldOps Dashboard** — `http://100.97.242.71:8000/`

---

## [0:00–0:40] WHAT — The Problem

> "Hi, I'm Gaurav. I'm going to show you something we built in under a day that solves a problem every engineering org has — and that no existing tool actually fixes.
>
> Here's the problem: **detection is solved. Remediation isn't.**
>
> You already run scanners — Dependabot, Snyk, Trivy, npm audit. They find hundreds of vulnerabilities. They even open PRs. But here's the reality: *(pause)* about 40% of Dependabot PRs merge cleanly. The other 60%? The build breaks. A senior engineer closes it, says 'needs investigation,' and the CVE sits open for weeks — sometimes months.
>
> Industry MTTR for critical vulnerabilities is 60 to 90 days. Not because nobody found them — because the *fix* requires judgment. Reading changelogs, handling breaking changes, navigating dependency conflicts, iterating until tests pass. That's senior engineer time. And those engineers are on your roadmap, not your security backlog.
>
> So we asked: what if Devin could do that work?"

---

## [0:40–1:50] HOW — Live Demo

**SHOW:** Terminal

> "ShieldOps is event-driven. Nothing starts by hand. Watch — I'm going to create a security issue on our fork of Apache Superset. Half a million lines of code, 200+ Python dependencies."

*(Create the issue live via `gh` or show it being created)*

> "The moment that issue lands with the `shieldops` label, GitHub fires a webhook to my orchestrator. It triages by severity, and launches a Devin session — fully autonomous."

**SHOW:** ShieldOps dashboard or terminal logs showing webhook → session created

> "There — session created, Devin is working. That runs a few minutes, so let me show you one that already finished — the hard one."

**SHOW:** PR #10 conversation

> "This is the hero. Flask 2.3.3, end-of-life, no more security patches. The fix is Flask 3 — a major version upgrade. And this is exactly where Dependabot stops and walks away.
>
> Flask 3 removes three core helpers that Superset depends on. And there's a trap: the obvious fix — upgrading Flask-SQLAlchemy to the latest — would force SQLAlchemy 2.0, which Superset is pinned below. A naive version bump breaks the build three different ways."

**SHOW:** PR #10 Files tab

> "Here's what Devin did. It read the changelog, fixed all three breaking changes, and caught the dependency trap — it chose Flask-SQLAlchemy 3.0.5 *specifically* because 3.1 would force a version Superset can't take. Five files changed. 7,700 tests passing. Zero follow-up messages from me.
>
> *(pause)* That's not a script bumping a number. That's an engineer reasoning about a codebase. And it took 18 minutes instead of half a day."

---

## [1:50–2:40] INSIDE DEVIN — How It Actually Works

*(This is the section that sells the product — show, don't tell)*

**SHOW:** Open the Devin session link for the Flask hero: https://app.devin.ai/sessions/872a39a23033451f95a94bbaf80bb65c

> "Let me show you what's actually happening inside Devin. This isn't a black box — every session is fully transparent."

**SHOW:** Devin's planner / thought process

> "First — the planner. Devin breaks the task into steps. You can see it read the prompt, identified this as a major version upgrade, and planned its approach: read the changelog first, identify breaking changes, then fix them one at a time. This isn't auto-complete — it's *planning*."

**SHOW:** Devin's shell (terminal output)

> "It has a full development environment — shell, editor, browser. Watch: it cloned the repo, ran the test suite first to get a baseline, then made changes and re-ran tests. When a test failed, it read the error, reasoned about the fix, and iterated. Just like your engineers do — except it didn't context-switch to Slack halfway through."

**SHOW:** Devin's editor view (code changes)

> "Here in the editor — you can see exactly which files it touched and what it changed. It's not generating code blindly. It searched the codebase for every import of the deprecated Flask helpers, traced the call sites, and fixed each one."

**SHOW:** Point to the structured output / session timeline

> "And critically — at the end, it produces **structured output**. Not a chat message I have to parse — machine-readable data: tests passed, confidence 92%, breaking changes detected and handled, files touched. This is what makes Devin an **API primitive**, not just a chatbot. I can build a policy engine on top of this."

**Transition line:**

> "And that's exactly what I did."

---

## [2:40–3:20] THE TRUST BOUNDARY — Architecture

**SHOW:** Code — structured output schema in `trigger.py`

> "Every Devin session gets a **structured output contract**. Tests passed, breaking changes, confidence, files touched, reachability assessment. That contract is what turns Devin into a primitive I can build automation on — not an AI I have to babysit."

**SHOW:** `policy.py`

> "This feeds the **trust boundary** — the policy engine. Three tiers:
>
> - **Green — auto-merge:** tests pass, high confidence, patch or minor. Ships without a human.
> - **Yellow — human review:** major upgrade, breaking changes, or sensitive paths. Reviewer gets an evidence bundle.
> - **Red — blocked:** tests fail or confidence too low. Nothing merges. Alert fires.
>
> That Flask PR? Major version upgrade, breaking changes — routed to human review automatically. PR #18, a PyJWT patch bump? Auto-merged itself. No human involved at all."

**SHOW:** PR #10 evidence bundle comment

> "And here's the reviewer experience. Not a wall of code — a 2-minute decision packet. Breaking changes handled, tests passing, confidence 92%, session link to dig deeper. *(pause)* Your engineers are *reviewing*, not *rubber-stamping* — and nothing risky ships without a human in the loop."

---

## [3:20–3:50] HOW — Observability (The VP Beat)

**SHOW:** Datadog dashboard

> "And here's how you'd know this is working at scale. This is the control plane — and I'm watching the *agents*, not the vulnerabilities.
>
> Fleet status: how many sessions are running right now. Trust split: what auto-merged versus what went to a human versus what got blocked. Cost per fix in ACUs — a fraction of engineer time. And the vulnerability burn-down: your security backlog actually shrinking.
>
> Four monitors behind this: failure rate spike, policy boundary breach, stuck sessions, intervention rate too high. If the fleet needs babysitting, you'll know before it matters."

**SHOW:** ShieldOps web dashboard

> "And for real-time without Datadog — the status endpoint. Every session, every triage decision, every policy outcome, live. Click a metric card, filter to just the blocked sessions or just what's running. Full audit trail."

---

## [3:50–4:30] WHY — Why Devin

> "So why does this need an autonomous agent? Why not Copilot, or better scripting?
>
> Three things only Devin can do here:
>
> **One — end-to-end execution with judgment.** You saw it inside the session. Devin didn't just suggest a fix — it cloned the repo, read the changelog, traced call sites, made changes, ran 7,700 tests, hit a failure, reasoned about it, fixed it, and re-ran until green. A code suggestion tool gives you a snippet. Devin gives you a *passing build*.
>
> **Two — unlimited parallelism.** I showed you one upgrade. But imagine your backlog has 50 open CVEs across 10 repos. Devin runs 50 sessions simultaneously — each one isolated, each one with its own structured output feeding the same policy engine. What takes a team months happens in an afternoon. That's not faster engineering — that's a fundamentally different operating model.
>
> **Three — self-verification.** The structured output isn't a guess — it's evidence from execution. Tests passed: true. Confidence: 0.95. That's what lets the policy engine auto-merge PR #18 without a human touching it. You can't build that trust loop on code suggestions."

---

## [4:30–5:00] WHEN — Next Steps

> "In a real engagement, here's how I'd roll this out:
>
> **Week one:** Pilot on one repo. Everything routed to human review — your team watches Devin's PRs and builds trust.
>
> **Week two:** Widen the auto-merge policy for low-risk fixes. Patch bumps with passing tests ship automatically. Your team focuses review time on the major upgrades.
>
> **Month one:** Scale across your estate. One engineer's setup, every repo in your org, one control plane. The security backlog that's been growing for years starts shrinking — without pulling your best engineers off the roadmap."
>
> *(pause)*
>
> "That's ShieldOps: autonomous remediation you can put into production, because you can see it and you can trust it. Thanks for watching."

---

## Timing Checkpoints

| Time | You should be at... |
|------|-------------------|
| 0:40 | Done with problem framing, about to trigger live |
| 1:10 | Live trigger done, pivoting to hero PR |
| 1:50 | Hero done, opening Devin session |
| 2:40 | Done inside Devin, into policy/trust boundary |
| 3:20 | Into Datadog dashboard |
| 3:50 | Starting "Why Devin" |
| 4:30 | Starting close |
| 5:00 | Done |

## If Running Over (Cut in Order)

1. **Shorten the live trigger** — just mention it, don't wait for logs. "I just created an issue — webhook fires, Devin starts. Let me show you one that already finished."
2. **Shorten Inside Devin** — show the planner + one shell command, skip the editor walkthrough. Key line: "It planned, executed, tested, iterated — structured output at the end."
3. **In Why Devin** — drop the parallelism point (two points is enough)
4. **In Next Steps** — drop week two, go straight from pilot to scale

## Key Lines to Nail (Practice These)

- "Detection is solved. Remediation isn't."
- "That's not a script bumping a number. That's an engineer reasoning about a codebase."
- "This is what makes Devin an API primitive, not just a chatbot."
- "Your engineers are reviewing, not rubber-stamping."
- "What takes a team months happens in an afternoon."
- "One engineer's setup, every repo in your org, one control plane."

## Tabs to Pre-Open

1. Terminal — `gh issue create` ready
2. GitHub — `gaurav21/superset` issues list
3. **Devin session** — https://app.devin.ai/sessions/872a39a23033451f95a94bbaf80bb65c (Flask hero)
4. PR #10 conversation — evidence bundle visible
5. PR #10 files — the diff
6. Code — `trigger.py` (structured output schema), `policy.py`
7. Datadog — ShieldOps dashboard: https://app.datadoghq.com/dashboard/uph-3r7-nfs
8. ShieldOps dashboard — http://100.97.242.71:8000/

## Delivery Notes

- **First 3 seconds:** Camera + smile + "Hi, I'm Gaurav." Set the trust.
- **Talk to the VP.** The ICs will validate the code — the VP needs the business case.
- **Pause before impact lines.** Let them land.
- **Don't read.** Know the opener, the hero story, and the close cold.
- **Numbers are real.** 7,700 tests, 5 files, 18 minutes, 92% confidence — say them only when they're on screen.
