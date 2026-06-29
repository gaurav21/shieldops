# BofA × Devin — 45-Minute Meeting Script

**Audience:** VP-level engineering & technology leaders at Bank of America
**Goal:** Secure a 2-week pilot commitment on one Angular repo
**Structure:** 20 min pitch + discovery → 15 min live demo → 10 min close + Q&A

---

## PHASE 1: PITCH + DISCOVERY (20 minutes)

---

### 0:00–1:30 — Opening & Context Setting (Slide #0: Title)

> "Thank you for the time today. I know your calendars are packed, so I want to make this count.
>
> I'm Gaurav from Cognition — we build Devin, the AI software engineer. Before I show you anything, I want to spend a few minutes on what we've learned about BofA's priorities, validate that with you, and then do a live demo tailored to exactly what matters to your team.
>
> Quick format: about 20 minutes of conversation, 15 minutes of live demo, and then we'll talk next steps. Sound good?"

**💡 Why this works:** Sets the collaborative tone. VPs hate being "pitched at" — this frames it as a working session.

---

### 1:30–4:00 — Why Cognition in 60 Seconds (Slide #1: Built for Regulated Industries)

> "Before we get into BofA specifics — three things that matter for your context.
>
> **First — we're already in the banks.** Goldman Sachs, Itaú, Nubank, Citi. SOC 2 Type II. Zero data retention with LLM providers. This isn't our first conversation with a tier-1 financial institution.
>
> **Second — Devin is a full computer, not a copilot.** It runs in its own VM — shell, browser, IDE. It can run your build, execute your test suite, spin up the frontend and visually verify nothing broke. No other AI coding tool does this.
>
> **Third — multi-model.** We route each sub-task to the best model. You're not betting on one AI lab staying ahead forever. The frontier shifts every six months — your investment is safe."

*Advance slide*

**💡 Timing note:** Move briskly here. This is credibility setup, not the pitch. 90 seconds max.

---

### 4:00–8:00 — Research & Discovery Part 1 (Slide #2: What We Know About BofA)

> "So here's what we've researched about Bank of America — and I want to check whether this maps to what your team is actually feeling.
>
> You run a $13.5 billion technology budget, with roughly $4 billion carved out for new strategic initiatives. Hari Gopalkrishnan was promoted to CTIO mid-2025, and his stated strategy is moving from one-off applications to enterprise-wide reusable capabilities across roughly 3,000 business processes.
>
> His own framing of the challenge — and I'll quote him: *'This stuff is very hard to govern. If you overdo it, you stall innovation.'*
>
> That governance-versus-velocity tension is exactly where Devin fits — auditable, cited-code PRs that scale engineering throughput without loosening control."

*Pause — pivot to the right column*

> "From our previous conversations, we identified three areas where Devin maps directly to your priorities:"

*Point to each card:*

> "**Angular migration** — customer-facing apps still on Angular 14, which has been EOL since November 2023. Manual estimate is 6 to 8 dev-weeks per app.
>
> **Security remediation** — the perpetual SonarQube and Veracode backlog that ties up developer capacity.
>
> **OCC compliance** — test coverage gaps on compliance-critical paths, which I understand is a board-level concern."

---

### 🔍 ANGULAR DISCOVERY — THE KEY CONVERSATION (8:00–14:00)

> "Now — I want to go deeper on the Angular migration specifically, because that's where we think the pilot makes the most sense. Can I ask a few questions?"

**Question 1 — Scale & Business Impact**
> "How many Angular 14 applications are we talking about? And are these primarily customer-facing digital banking, internal tooling, or a mix?"

*Listen. Then:*
> "And what's the downstream impact? Is the Angular EOL showing up in compliance conversations, or is it more of an engineering backlog concern right now?"

**💡 What you're listening for:** Number of apps = size of the deal. Customer-facing = higher urgency = faster procurement.

**Question 2 — What's Blocked Progress**
> "What's stopped the migration so far? Is it capacity — not enough hands? Complexity — breaking changes are too risky? Or is it a prioritization issue — it keeps getting bumped by feature work?"

*Listen. Then depending on answer:*

- If **capacity**: "That's exactly the pattern we see. Itaú had the same problem — 59 services to migrate, not enough senior engineers to do it safely. Devin ran them at 6× the speed of manual."
- If **complexity/risk**: "Makes sense. The regression risk is real. That's why Devin's approach is different — it runs `ng build` and `ng test` in its own VM, iterates until green, and only opens the PR when everything passes. Your engineers review the output, not babysit the process."
- If **prioritization**: "That tells me the cost of *not* doing it hasn't hit the threshold yet. But with Angular 14 EOL, every month is compliance exposure. What if you could clear 10 repos in the time it takes to manually do one?"

**Question 3 — Current Tooling**
> "What AI coding tools are your teams using today? Copilot? Cursor? Something internal?"

*Listen. Then:*
> "Got it. The key difference — those tools help your engineers write code faster. Devin *does* the migration for them. It's not autocomplete. It's an autonomous engineer that takes the ticket, reads the codebase, makes every change, runs the tests, and opens the PR. Your engineers review it like they'd review any junior engineer's work."

**💡 What you're listening for:** If they have Copilot, you're not replacing it — you're adding a different capability. If they have nothing, you're the first mover.

**Question 4 — Success Criteria**
> "If we ran a pilot on one repo — what would make it a clear win for your team? Is it time to merge? PR quality? Zero regressions? Something else?"

*Listen carefully. Write down exactly what they say. This becomes your pilot success criteria.*

> "Got it. Let me show you exactly what that looks like."

---

### 14:00–16:00 — Angular Detail + Transition to Demo (Slide #5: Angular 14 → 17+)

> "So here's what Devin actually does on an Angular migration.
>
> Every breaking change between 14 and 17 — NgModules to Standalone, MatLegacy to Mat, deprecated RxJS operators — Devin handles all of it. Not just the find-and-replace parts. The structural changes, the import rewiring, the template updates.
>
> And critically — it validates. `ng build --production` and `ng test` must both pass. If they don't, Devin reads the error, fixes it, and re-runs. It iterates until green.
>
> **Why lead with Angular?** Four reasons:
> - Hard EOL — every month is compliance exposure
> - Most proven use case — Itaú ran 59 at 6×
> - Fully verifiable — build passes or it doesn't
> - Parallelizable — run 10 repos simultaneously
>
> Let me show you this live."

---

### 16:00–18:00 — Kick Off Demo Sessions (Slide #3: Demo Transition)

> "Here's what I'm going to do. I'll kick off two Devin sessions right now — one for the Angular migration, one for a security vulnerability fix — so they run while I walk you through the interface.
>
> This is real. No recordings. No slides pretending to be a demo. Devin is going to read a real codebase, make real changes, and open a real PR."

*Start sessions in Devin*

---

## PHASE 2: LIVE DEMO (15 minutes)

---

### 18:00–20:00 — Devin Interface Overview (2 min)

> "While Devin is working, let me orient you.
>
> This is Devin's workspace — it has its own IDE, its own terminal, its own browser. Full Linux VM. It's not running in your developer's IDE — it's a completely isolated environment.
>
> On the left is the conversation — this is where you'd give Devin instructions, just like you'd brief an engineer. On the right is what Devin is actually doing — you can see it reading files, running commands, making changes in real-time."

---

### 20:00–26:00 — Angular Migration Walkthrough (6 min)

Walk through the Angular session as it runs:

> "So Devin is now reading the codebase. Watch — it's identifying every Angular 14 pattern that needs to change.
>
> [As Devin works] See here — it found the NgModule declarations and is converting them to standalone components. It's not using a template. It's reading *this specific codebase* and making the right changes for *this code*.
>
> [When it runs tests] Now it's running `ng build`. If this fails — and it might — watch what happens. It reads the error output, understands what broke, and fixes it. This is the loop that saves your engineers weeks.
>
> [When PR opens] And here's the PR. Full diff, cited rationale for every change, test results attached. Your engineer reviews this exactly like they'd review any other PR. Branch protections, required reviewers — same governance process."

**💡 VP hook during demo:**
> "Think about what just happened in [X] minutes. Your team would estimate this at 6 to 8 weeks. Now multiply that by [number of apps they mentioned]. That's the capacity unlock we're talking about."

---

### 26:00–29:00 — Security Vuln Fix (3 min)

> "Now let me show the security session. This is the other big use case we discussed.
>
> Devin read the CVE advisory, found every affected call site in the codebase, applied the fix, and ran the tests. This isn't Dependabot bumping a version and breaking the build — Devin fixes the actual code.
>
> Itaú auto-resolves 70% of their SonarQube and Veracode findings this way. One organization measured it at 20× efficiency — 30 minutes per vuln manually, 90 seconds with Devin."

---

### 29:00–31:00 — Visual Testing Differentiator (2 min)

> "One more thing I want to show you — and this is something no other AI coding tool can do.
>
> [Show browser in Devin VM] Devin spun up the frontend and is actually clicking through the UI. It's visually verifying that the migration didn't break the user experience. For customer-facing digital banking apps, this is critical — you can't ship a migration that changes how a form renders.
>
> Copilot can't do this. Cursor can't do this. They don't have a browser. Devin does."

---

### 31:00–33:00 — Knowledge & Playbooks (2 min)

> "Last piece — this is how we scale.
>
> [Show Knowledge/Playbooks] Once we configure the patterns for your Angular migration, Devin applies them across every repo. You're not re-briefing it every time. Configure once, run across your fleet.
>
> This is what Gopalkrishnan's team is trying to do with enterprise-wide reusable capabilities — except applied to engineering automation. One playbook, thousands of processes."

---

## PHASE 3: CLOSE + NEXT STEPS (10 minutes)

---

### 33:00–35:00 — Itaú Case Study (Slide #6)

> "Quick proof point before we talk next steps.
>
> Itaú Unibanco — $500 billion in assets, one of the most regulated banks in the world.
>
> 59 services migrated from .NET to Java at 6× the speed. 800 database objects migrated at 5×. 70% of security vulnerabilities auto-resolved. Test coverage went from 50% to over 90%.
>
> Same regulatory environment as BofA. Same complexity. Same need for auditable, verifiable changes."

---

### 35:00–37:00 — Competitive Differentiation (Slide #7)

> "If you're evaluating other options — here's the honest comparison.
>
> **Model independence** — we're not locked to one AI provider. Multi-model routing means you get the best model for each task. Copilot is locked to OpenAI. Cursor is locked to whoever they partner with.
>
> **Full VM** — shell, browser, IDE. Other tools run in containers. No browser testing, no visual verification.
>
> **Transformation partner** — I'm not handing you a license and a docs page. I'm embedded in your org. I configure the Knowledge, Playbooks, and Automations specifically for your codebase and your workflows."

---

### 37:00–39:00 — Security Slide (Slide #8)

> "I know security is going to come up in procurement, so let me address it upfront.
>
> Each Devin session runs in its own isolated VM — not a container, a full virtual machine. Code never leaves your network if you choose the VPC deployment option. SOC 2 Type II certified. Code is never used for training — that's contractual, not just policy.
>
> Every change Devin makes goes through your existing PR review process. Branch protections, required reviewers — your governance doesn't change."

---

### 39:00–43:00 — Next Steps & Pilot Proposal (Slide #9)

> "Here's what I'd propose.
>
> **Step one:** Pick one Angular 14 repo. Ideally something your team has already estimated — so we can measure the delta.
>
> **Step two:** Two-week sprint. Agreed success metrics upfront — [reference what they said during discovery about success criteria]. We run Devin against it, your engineers review the PRs.
>
> **Step three:** If it works — and based on what Itaú saw, I'm confident it will — we expand. Angular fleet first. Then security remediation. Then compliance coverage.
>
> What would make this a win for your team? And who else needs to be in the room to make a pilot decision?"

**💡 Critical discovery questions at close:**
- "What does your procurement process look like for a pilot like this?"
- "Is there a security review that needs to happen before we can connect to a repo?"
- "Who on your team would be the day-to-day point of contact for the pilot?"
- "What's the timeline pressure? Is there a compliance deadline driving the Angular migration?"

---

### 43:00–45:00 — Q&A Buffer

> "What questions do you have? Happy to go deeper on anything — I have backup slides on ROI modeling, cloud migration, compliance coverage, and the full security architecture."

*Use appendix slides (10-15) as needed based on questions.*

---

## CHEAT SHEET — Objection Handling

| Objection | Response |
|-----------|----------|
| "We already have Copilot" | "Great — keep it. Copilot helps your engineers write code faster. Devin does the migration *for* them. Different capability, not a replacement." |
| "How do we know the PRs are good?" | "67% merge rate — up from 34% last year. And your engineers review every PR. Branch protections don't change." |
| "What about hallucinations / bad code?" | "Devin runs the build and tests. If they fail, it fixes and re-runs. The validation loop is built in — it doesn't ship broken code." |
| "Security concerns — code leaving our network" | "VPC deployment option. Code never leaves your network. SOC 2 Type II. Zero training on your data — contractual." |
| "We need to evaluate other vendors" | "Absolutely. I'd encourage it. When you do, ask one question: can it run the build? Can it open a browser and verify the UI? That's the test." |
| "Not the right time" | "Understood. Every month on Angular 14 is compliance exposure. When does the next OCC review cycle start? We should have results before then." |
| "Need to involve more stakeholders" | "Makes sense. Who should be in the room? I can tailor the next session to their priorities — security team gets the architecture deep-dive, engineering leads get the demo." |

---

## TIMING GUARDRAILS

| Segment | Allocated | Hard Stop |
|---------|-----------|-----------|
| Opening + Why Cognition | 4 min | 4:00 |
| Research + Discovery | 10 min | 14:00 |
| Angular detail + demo setup | 4 min | 18:00 |
| **Live Demo** | **15 min** | **33:00** |
| Itaú + Why Devin + Security | 6 min | 39:00 |
| Next Steps + Q&A | 6 min | 45:00 |

**If running long on discovery (good problem):** Cut Itaú to 60 seconds, skip competitive slide (they can read it), go straight to Next Steps.

**If demo has issues:** Switch to the pre-recorded backup. Say: "Let me show you a completed session from earlier today so we don't waste your time waiting." Never apologize for AI reliability — it proves the point that human review is always in the loop.
